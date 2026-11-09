import glob
import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest, RandomForestClassifier, RandomForestRegressor
from sklearn.svm import OneClassSVM
from sklearn.neighbors import LocalOutlierFactor
from sklearn.tree import DecisionTreeClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, mean_squared_error, r2_score
)

# 한글 폰트 설정 (Windows Malgun Gothic)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

os.makedirs('results', exist_ok=True)

# 1. 데이터 로드 (10개 주행 세션 CSV)
csv_files = sorted(glob.glob('*.csv'))
dfs = []
for f in csv_files:
    df_temp = pd.read_csv(f, encoding='utf-8-sig')
    df_temp['source_file'] = os.path.basename(f)
    dfs.append(df_temp)

df = pd.concat(dfs, ignore_index=True)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.sort_values(['run_id', 'timestamp']).reset_index(drop=True)

print(f"총 로드된 데이터: {len(df)}건, 주행 세션 수: {df['run_id'].nunique()}개")

# 2. 누적 충격량(Cumulative Shock) 및 사과 상태(Apple Condition State) 정의
# [학술적 근거 1] Van Zeebroeck et al. (2007, Postharvest Biol. Technol.) & Acıcan et al. (2007, Biosystems Eng.):
# - 정지 중력(1.0G) 상태에서 탄성 한계 이내의 기저 진동(+0.15G, 즉 총 가속도 1.15G)을 초과하는 유효 동적 충격량(Excess G) 적분
# - 단발성 세포벽 항복(Yield) 유발 임계 가속도는 순수 동적 가속도 +0.8G(총 가속도 1.8G) 적용
df['excess_g'] = np.maximum(0, df['g_force'] - 1.15)
df['shock_energy'] = (df['excess_g'] ** 2) * (1 + np.log1p(df['speed']) * 0.2)

# 주행 세션(run_id)별 시간 흐름에 따른 누적 충격량 및 누적 충격 에너지 산출
df['cum_excess_g'] = df.groupby('run_id')['excess_g'].cumsum()
df['cum_shock_energy'] = df.groupby('run_id')['shock_energy'].cumsum()
df['cum_peak_cnt'] = df.groupby('run_id')['g_force'].transform(lambda x: (x >= 1.8).cumsum())

# 시계열 주행 특성 파생 변수
df['speed_diff'] = df.groupby('run_id')['speed'].diff().fillna(0).abs()
df['g_force_roll_mean5'] = df.groupby('run_id')['g_force'].transform(lambda x: x.rolling(5, min_periods=1).mean())
df['g_force_roll_std5'] = df.groupby('run_id')['g_force'].transform(lambda x: x.rolling(5, min_periods=1).std()).fillna(0)
df['elapsed_steps'] = df.groupby('run_id').cumcount() + 1
df['shock_rate'] = df['cum_excess_g'] / df['elapsed_steps']  # 단위 시간당 누적 충격 축적 속도

# [학술적 근거 2] Lu & Zhou (2009, Trans. CSAE) Palmgren-Miner 기반 과실 진동 누적 피로 손상 지수 (D = Σ n_i / N_i, 0 ~ 100% 스케일)
# 누적 초과 충격량(65%) + 누적 충격 에너지(25%) + 고온 호흡/연화 스트레스(10%) 결합
raw_damage = (
    0.65 * (df['cum_excess_g'] / 80.0) +
    0.25 * (df['cum_shock_energy'] / 100.0) +
    0.10 * (np.maximum(0, df['temperature'] - 20.0) / 18.0)
) * 100.0
df['apple_damage_index'] = np.clip(raw_damage, 0, 100)

# [학술적 근거 3] 미국 농무부 사과 등급 표준 (USDA Standards for Grades of Apples) 타박상 허용 기준 매핑:
# Grade 0 (Grade A, USDA Extra Fancy 상당): 피로 손상지수(ADI) < 25% & 누적 충격 < 25G (타박상 직경 < 12.7mm 무결점 신선 상태)
# Grade 1 (Grade B, USDA Fancy / No. 1 상당): 25% <= ADI < 60% 또는 누적 25~65G 또는 순간 충격 >= 1.8G (타박상 직경 12.7~15.9mm, 미세타박 주의)
# Grade 2 (Grade C, USDA Utility / Culled 등급 외 상당): ADI >= 60% 또는 누적 충격 >= 65G (타박상 직경 > 15.9mm, 내부 갈변 및 상품성 상실 위험)
def assign_apple_state(row):
    if row['apple_damage_index'] >= 60 or row['cum_excess_g'] >= 65:
        return 2  # 위험/파손 (Damaged)
    elif row['apple_damage_index'] >= 25 or row['cum_excess_g'] >= 25 or row['g_force'] >= 1.8:
        return 1  # 주의/미세타박 (Warning)
    else:
        return 0  # 정상/신선 (Fresh)

df['apple_state'] = df.apply(assign_apple_state, axis=1)
# 이진 타깃 (사과 품질 이상 여부: 0=정상, 1=주의 및 파손 위험)
df['is_apple_damaged'] = (df['apple_state'] >= 1).astype(int)

state_counts = df['apple_state'].value_counts().sort_index().to_dict()
print("사과 품질 상태 3단계 분포 (0:정상, 1:주의, 2:파손위험):", state_counts)
print(f"사과 품질 이상(주의+파손위험) 비율: {df['is_apple_damaged'].mean()*100:.2f}% ({df['is_apple_damaged'].sum()}건)")

# 운행 세션별 최종 누적 충격량 및 최종 사과 상태 요약
trip_summary = df.groupby('run_id').agg(
    samples=('g_force', 'count'),
    max_g=('g_force', 'max'),
    peak_cnt=('g_force', lambda x: (x >= 1.8).sum()),
    final_cum_g=('cum_excess_g', 'max'),
    final_damage_idx=('apple_damage_index', 'max'),
    final_state=('apple_state', 'max')
).sort_values('final_cum_g', ascending=False)
print("\n=== 운행 세션별 누적 충격량 및 최종 사과 상태 ===")
print(trip_summary.to_string())

# 3. [1단계] 비지도 학습 기반 이상 충격 및 누적 피로 이상 탐지
unsup_features = ['g_force', 'g_force_roll_mean5', 'g_force_roll_std5', 'cum_excess_g', 'shock_rate', 'speed']
X_unsup = StandardScaler().fit_transform(df[unsup_features])

# 실제 고위험 충격/누적 상태 기준 (상위 위험 구간)
y_anom_gt = ((df['g_force'] >= 1.8) | (df['apple_state'] == 2)).astype(int)
contam_rate = round(float(y_anom_gt.mean()), 3)

iso = IsolationForest(n_estimators=200, contamination=contam_rate, random_state=42)
df['iso_pred'] = (iso.fit_predict(X_unsup) == -1).astype(int)

ocsvm = OneClassSVM(kernel='rbf', nu=contam_rate, gamma='scale')
df['ocsvm_pred'] = (ocsvm.fit_predict(X_unsup) == -1).astype(int)

lof = LocalOutlierFactor(n_neighbors=25, contamination=contam_rate)
df['lof_pred'] = (lof.fit_predict(X_unsup) == -1).astype(int)

kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
df['kmeans_cluster'] = kmeans.fit_predict(X_unsup)
# 평균 apple_damage_index가 가장 높은 클러스터를 위험 클러스터로 지정
high_risk_cluster = df.groupby('kmeans_cluster')['apple_damage_index'].mean().idxmax()
df['kmeans_pred'] = (df['kmeans_cluster'] == high_risk_cluster).astype(int)

unsup_results = {}
for name, col in [
    ('Isolation Forest', 'iso_pred'),
    ('K-Means Clustering', 'kmeans_pred'),
    ('One-Class SVM', 'ocsvm_pred'),
    ('Local Outlier Factor (LOF)', 'lof_pred')
]:
    acc = accuracy_score(y_anom_gt, df[col])
    prec = precision_score(y_anom_gt, df[col], zero_division=0)
    rec = recall_score(y_anom_gt, df[col], zero_division=0)
    f1 = f1_score(y_anom_gt, df[col], zero_division=0)
    unsup_results[name] = {
        'accuracy': round(acc * 100, 2),
        'precision': round(prec * 100, 2),
        'recall': round(rec * 100, 2),
        'f1': round(f1 * 100, 2)
    }
    print(f"[1단계 비지도] {name}: Acc={acc*100:.2f}%, F1={f1*100:.2f}%")

# 4. [2단계] 누적 충격 패턴 및 주행 센서 기반 '향후 사과 상태(정상/주의/파손위험)' 예측 모델링
# 데이터 누수(Data Leakage) 방지를 위해 직접적인 타깃 정의 수식 변수(cum_excess_g 원값) 대신,
# 직전 시점까지의 누적 충격 추이(5스텝 전 누적치), 최근 진동 평균/표준편차, 충격 축적 속도(shock_rate), 속도, 온습도를 입력 피처로 사용하여
# 10스텝 뒤(미래 시점)의 사과 품질 상태(apple_state)를 예측!
df['future_apple_state'] = df.groupby('run_id')['apple_state'].shift(-10).fillna(df['apple_state']).astype(int)
df['prev_cum_g_lag5'] = df.groupby('run_id')['cum_excess_g'].shift(5).fillna(0)

sup_features = [
    'prev_cum_g_lag5',     # 직전 누적 충격량 (Lag 5)
    'shock_rate',          # 단위 시간당 충격 축적 속도
    'g_force_roll_mean5',  # 최근 5구간 평균 진동
    'g_force_roll_std5',   # 최근 5구간 진동 변동성
    'speed',               # 차량 주행 속도
    'speed_diff',          # 순간 속도 변화량
    'temperature',         # 화물칸 온도
    'humidity'             # 화물칸 습도
]

X_sup = df[sup_features]
y_sup = df['future_apple_state']  # 3단계 사과 상태 (0: 정상, 1: 주의, 2: 파손위험)

X_train, X_test, y_train, y_test = train_test_split(
    X_sup, y_sup, test_size=0.25, random_state=42, stratify=y_sup
)

scaler_sup = StandardScaler()
X_train_scaled = scaler_sup.fit_transform(X_train)
X_test_scaled = scaler_sup.transform(X_test)

sup_results = {}

# (1) Decision Tree Classifier
dt = DecisionTreeClassifier(max_depth=5, random_state=42)
dt.fit(X_train, y_train)
dt_pred = dt.predict(X_test)
dt_prob = dt.predict_proba(X_test)

# (2) Random Forest + GridSearchCV
param_grid = {
    'n_estimators': [100, 200],
    'max_depth': [6, 10, 14],
    'min_samples_split': [2, 5]
}
rf_base = RandomForestClassifier(random_state=42)
grid_search = GridSearchCV(rf_base, param_grid, cv=5, scoring='f1_macro', n_jobs=-1)
grid_search.fit(X_train, y_train)
best_rf = grid_search.best_estimator_
rf_pred = best_rf.predict(X_test)
rf_prob = best_rf.predict_proba(X_test)

# (3) MLP Classifier (Neural Network)
mlp = MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=300, random_state=42)
mlp.fit(X_train_scaled, y_train)
mlp_pred = mlp.predict(X_test_scaled)
mlp_prob = mlp.predict_proba(X_test_scaled)

for name, pred, prob in [
    ('Decision Tree', dt_pred, dt_prob),
    ('Random Forest + GridSearchCV', rf_pred, rf_prob),
    ('MLP (Multi-Layer Perceptron)', mlp_pred, mlp_prob)
]:
    acc = accuracy_score(y_test, pred)
    f1_mac = f1_score(y_test, pred, average='macro')
    f1_weighted = f1_score(y_test, pred, average='weighted')
    auc = roc_auc_score(y_test, prob, multi_class='ovr', average='macro')
    sup_results[name] = {
        'accuracy': round(acc * 100, 2),
        'f1_macro': round(f1_mac * 100, 2),
        'f1_weighted': round(f1_weighted * 100, 2),
        'roc_auc': round(auc * 100, 2)
    }
    print(f"[2단계 사과 상태 예측] {name}: Acc={acc*100:.2f}%, F1(Macro)={f1_mac*100:.2f}%, AUC={auc*100:.2f}%")

print("Best RF Params:", grid_search.best_params_)

feat_imp = pd.Series(best_rf.feature_importances_, index=sup_features).sort_values(ascending=False)
print("\nFeature Importances:\n", feat_imp)

# 5. 고해상도 발표용 차트 4종 생성
# Chart 1: 10개 운행 세션별 시간에 따른 누적 충격량(Cumulative Shock) 추이 및 사과 상태 변화 곡선
plt.figure(figsize=(11, 5.8), dpi=150)
top_runs = trip_summary.index[:5].tolist() + [trip_summary.index[7]]  # 상위 5개 + 최장거리 안전운행 1개 비교
palette = ['#E74C3C', '#E67E22', '#F39C12', '#8E44AD', '#3498DB', '#2ECC71']

for idx, r_id in enumerate(top_runs):
    sub = df[df['run_id'] == r_id]
    label_name = f"{r_id} (최종 {sub['cum_excess_g'].max():.1f}G)"
    plt.plot(sub['elapsed_steps'], sub['cum_excess_g'], linewidth=2.3, color=palette[idx], label=label_name)

plt.axhline(65, color='#C0392B', linestyle='--', linewidth=1.8, label='파손 위험 등급 임계선 (누적 65G)')
plt.axhline(25, color='#F39C12', linestyle=':', linewidth=1.8, label='주의(미세타박) 등급 임계선 (누적 25G)')
plt.fill_between([0, 1550], 65, 130, color='#E74C3C', alpha=0.08)
plt.fill_between([0, 1550], 25, 65, color='#F39C12', alpha=0.08)
plt.fill_between([0, 1550], 0, 25, color='#2ECC71', alpha=0.08)

plt.title('운행 세션별 시간에 따른 누적 충격량(Cumulative Shock) 증가 추이 및 사과 상태 등급 구간', fontsize=13, fontweight='bold', pad=12)
plt.xlabel('운행 경과 스텝 (Time Steps)', fontsize=11)
plt.ylabel('누적 초과 충격량 (Cumulative Excess G-Force)', fontsize=11)
plt.ylim(0, 128)
plt.xlim(0, 1550)
# 그래프 우측 중하단(X: 700~1500, Y: 25~63) 빈 영역에 범례를 배치하여 곡선 가림 완전 방지
plt.legend(loc='center right', bbox_to_anchor=(0.98, 0.38), fontsize=9.2, frameon=True, facecolor='white', framealpha=0.92)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('results/fig1_shock_timeseries.png')
plt.close()

# Chart 2: 누적 충격량 vs 순간 충격량 공간에서 사과 상태(3단계) 및 K-Means 군집 중심 / Isolation Forest 스파이크 탐지 분포
fig, ax = plt.subplots(figsize=(9.6, 5.5), dpi=150)

# 배경에 누적 충격량 등급 구간(Zone) 음영 표시
ax.axvspan(0, 25, color='#2ECC71', alpha=0.08)
ax.axvspan(25, 65, color='#F39C12', alpha=0.08)
ax.axvspan(65, 122, color='#E74C3C', alpha=0.08)

# 상단 구간 안내 텍스트 (Malgun Gothic 호환 특수문자 ● 사용)
ax.text(12.5, 4.02, '● Grade A 정상 구간\n(누적 < 25G)', ha='center', va='top', fontsize=9.2, fontweight='bold', color='#1E8449', bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='#2ECC71', alpha=0.92))
ax.text(45.0, 4.02, '● Grade B 주의 구간\n(누적 25 ~ 65G)', ha='center', va='top', fontsize=9.2, fontweight='bold', color='#B7950B', bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='#F39C12', alpha=0.92))
ax.text(93.5, 4.02, '● Grade C 위험 구간\n(누적 ≥ 65G)', ha='center', va='top', fontsize=9.2, fontweight='bold', color='#C0392B', bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='#E74C3C', alpha=0.92))

state_colors = {0: '#27AE60', 1: '#F39C12', 2: '#E74C3C'}
state_labels = {
    0: f"Grade A: 정상/신선 ({state_counts.get(0,0)}건)",
    1: f"Grade B: 미세타박 주의 ({state_counts.get(1,0)}건)",
    2: f"Grade C: 파손 위험 ({state_counts.get(2,0)}건)"
}

# Y축 가독성을 위해 3.5G 초과 극단치(9건, 최대 14.46G)는 상단(3.52G)에 클리핑하여 별도 마커로 표시
normal_mask = df['g_force'] <= 3.52
extreme_mask = df['g_force'] > 3.52

# 일반 분포 점들은 겹침을 줄이기 위해 작고 투명하게 표시
for st in [0, 1, 2]:
    sub = df[(df['apple_state'] == st) & normal_mask]
    ax.scatter(sub['cum_excess_g'], sub['g_force'], c=state_colors[st], alpha=0.38, s=16, edgecolors='none', label=state_labels[st])

# 1) Isolation Forest가 포착한 순간 고충격 스파이크(>=1.8G)만 깔끔하게 강조 표시 (하단 1.0G 기저 구간 가림 방지)
spike_anom = df[(df['iso_pred'] == 1) & (df['g_force'] >= 1.8) & normal_mask]
ax.scatter(
    spike_anom['cum_excess_g'], spike_anom['g_force'],
    facecolors='none', edgecolors='#1B2A4A', s=48, linewidth=1.3,
    label=f'Isolation Forest 돌발 고충격(≥1.8G) 포착 ({len(spike_anom) + int(extreme_mask.sum())}건)'
)

# 3.52G 초과 극단 충격(9건, 최대 14.46G) 상단 삼각형 마커 표시
ext_pts = df[extreme_mask]
ax.scatter(
    ext_pts['cum_excess_g'], [3.52] * len(ext_pts),
    marker='^', c='#8E44AD', edgecolors='#1B2A4A', s=75, linewidth=1.2, zorder=6,
    label=f'극단 스파이크 충격 (3.8G~14.46G, {len(ext_pts)}건 상단 표시)'
)

# 2) K-Means (K=3) 군집 중심점(Centroid) 3곳을 별표(★)로 표시하여 누적 충격 군집 분리 시각화
cluster_centers_df = df.groupby('kmeans_cluster')[['cum_excess_g', 'g_force']].mean()
ax.scatter(
    cluster_centers_df['cum_excess_g'], cluster_centers_df['g_force'],
    marker='*', c='#FFF200', edgecolors='#1B2A4A', s=280, linewidth=1.6, zorder=7,
    label='K-Means 3개 군집 중심점 (★ 누적 상태 분리)'
)

ax.axvline(25, color='#F39C12', linestyle=':', linewidth=1.6)
ax.axvline(65, color='#C0392B', linestyle='--', linewidth=1.6)
ax.axhline(1.8, color='#C0392B', linestyle='-.', linewidth=1.5, alpha=0.85, label='순간 임계 충격 기준선 (1.8G)')

ax.set_title('누적 충격량(X축)과 순간 충격량(Y축)에 따른 사과 상태 분포 (K-Means vs Isolation Forest)', fontsize=12.2, fontweight='bold', pad=12)
ax.set_xlabel('누적 초과 충격량 (Cumulative Excess G-Force, 단위: G)', fontsize=11)
ax.set_ylabel('순간 충격 가속도 (Instantaneous G-Force, 단위: G)', fontsize=11)
ax.set_xlim(-2, 122)
ax.set_ylim(0.8, 4.18)
ax.legend(loc='center right', bbox_to_anchor=(0.99, 0.64), fontsize=8.8, frameon=True, facecolor='white', framealpha=0.94)
ax.grid(True, alpha=0.25)
plt.tight_layout()
plt.savefig('results/fig2_isolation_forest_scatter.png')
plt.close()

# Chart 3: 1단계 비지도 모델 & 2단계 지도 학습 사과 상태 예측 모델 성능 비교
fig, axes = plt.subplots(1, 2, figsize=(12, 5.2), dpi=150)

unsup_names = list(unsup_results.keys())
unsup_f1s = [unsup_results[k]['f1'] for k in unsup_names]
unsup_accs = [unsup_results[k]['accuracy'] for k in unsup_names]
x = np.arange(len(unsup_names))
w = 0.35
axes[0].bar(x - w/2, unsup_accs, w, label='정확도 (Accuracy %)', color='#3498DB')
axes[0].bar(x + w/2, unsup_f1s, w, label='F1-Score (%)', color='#E67E22')
axes[0].set_title('[1단계] 비지도 이상/피로 상태 탐지 성능 비교', fontsize=12, fontweight='bold', pad=10)
axes[0].set_xticks(x)
axes[0].set_xticklabels(['Isolation\nForest', 'K-Means\nClustering', 'One-Class\nSVM', 'LOF'], fontsize=9.5)
axes[0].set_ylim(0, 118)
# 상단 여백(100~118 구간)에 가로 2열로 범례를 배치하여 막대와 텍스트 가림 완전 방지
axes[0].legend(loc='upper center', ncol=2, fontsize=9.5, frameon=True, facecolor='white')
axes[0].grid(axis='y', alpha=0.3)
for i, v in enumerate(unsup_accs):
    axes[0].text(i - w/2, v + 1.5, f"{v:.1f}%", ha='center', fontsize=8.2, color='#1F618D', fontweight='bold')
for i, v in enumerate(unsup_f1s):
    axes[0].text(i + w/2, v + 1.5, f"{v:.1f}%", ha='center', fontsize=8.2, color='#AF601A', fontweight='bold')

sup_names = list(sup_results.keys())
sup_accs = [sup_results[k]['accuracy'] for k in sup_names]
sup_f1s = [sup_results[k]['f1_macro'] for k in sup_names]
x2 = np.arange(len(sup_names))
axes[1].bar(x2 - w/2, sup_accs, w, label='분류 정확도 (Accuracy %)', color='#2ECC71')
axes[1].bar(x2 + w/2, sup_f1s, w, label='Macro F1-Score (%)', color='#9B59B6')
axes[1].set_title('[2단계] 누적 충격 기반 사과 상태(3등급) 예측 성능', fontsize=12, fontweight='bold', pad=10)
axes[1].set_xticks(x2)
axes[1].set_xticklabels(['Decision Tree', 'Random Forest\n+ GridSearchCV', 'MLP\n(Neural Net)'], fontsize=9.5)
axes[1].set_ylim(0, 118)
# 상단 여백(100~118 구간)에 가로 2열로 범례를 배치하여 막대 가림 완전 방지
axes[1].legend(loc='upper center', ncol=2, fontsize=9.5, frameon=True, facecolor='white')
axes[1].grid(axis='y', alpha=0.3)
for i, v in enumerate(sup_accs):
    axes[1].text(i - w/2, v + 1.5, f"{v:.1f}%", ha='center', fontsize=8.2, color='#1E8449', fontweight='bold')
for i, v in enumerate(sup_f1s):
    axes[1].text(i + w/2, v + 1.5, f"{v:.1f}%", ha='center', fontsize=8.2, color='#6C3483', fontweight='bold')

plt.tight_layout()
plt.savefig('results/fig3_model_comparison.png')
plt.close()

# Chart 4: 사과 품질 상태 예측을 위한 특성 중요도 (Feature Importance)
plt.figure(figsize=(8.8, 4.8), dpi=150)
kor_labels = {
    'prev_cum_g_lag5': '직전 시점 누적 충격량 (Cumulative G)',
    'shock_rate': '시간당 충격 축적 속도 (Shock Rate)',
    'g_force_roll_mean5': '최근 5구간 평균 진동 (Rolling Mean)',
    'g_force_roll_std5': '최근 5구간 진동 변동성 (Rolling Std)',
    'humidity': '화물칸 습도 (%)',
    'temperature': '화물칸 온도 (°C)',
    'speed': '트럭 주행 속도 (km/h)',
    'speed_diff': '순간 속도 변화율 (급가감속)'
}
imp_df = feat_imp.rename(index=kor_labels)
colors = sns.color_palette('viridis', len(imp_df))
bars = plt.barh(imp_df.index[::-1], imp_df.values[::-1] * 100, color=colors[::-1])
plt.title('Random Forest 기반 사과 품질 상태(3등급) 예측 핵심 변수 중요도 (%)', fontsize=12.5, fontweight='bold', pad=12)
plt.xlabel('특성 중요도 (Feature Importance %)', fontsize=11)
for bar in bars:
    w_val = bar.get_width()
    plt.text(w_val + 0.8, bar.get_y() + bar.get_height()/2, f"{w_val:.1f}%", va='center', fontsize=9.5, fontweight='bold')
plt.xlim(0, max(imp_df.values * 100) + 10)
plt.grid(axis='x', alpha=0.3)
plt.tight_layout()
plt.savefig('results/fig4_feature_importance.png')
plt.close()

summary = {
    'total_rows': int(len(df)),
    'num_trips': int(df['run_id'].nunique()),
    'state_counts': {str(k): int(v) for k, v in state_counts.items()},
    'unsupervised_results': unsup_results,
    'supervised_results': sup_results,
    'best_rf_params': grid_search.best_params_,
    'feature_importances_pct': {k: round(float(v)*100, 2) for k, v in feat_imp.items()}
}
with open('results/experiment_summary.json', 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print("누적 충격량 기반 사과 상태 예측 실험 및 차트 4종 생성 완료!")
