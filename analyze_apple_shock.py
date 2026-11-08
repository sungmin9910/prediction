import glob
import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.svm import OneClassSVM
from sklearn.neighbors import LocalOutlierFactor
from sklearn.tree import DecisionTreeClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
)

# 한글 폰트 설정 (Windows Malgun Gothic)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

os.makedirs('results', exist_ok=True)

# 1. 데이터 로드
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

# 2. 사과 운송 도메인 특성 엔지니어링 (Feature Engineering)
# 그룹별(주행 세션별) 시계열 변화량 계산
df['speed_diff'] = df.groupby('run_id')['speed'].diff().fillna(0).abs()
df['g_force_prev1'] = df.groupby('run_id')['g_force'].shift(1).fillna(df['g_force'])
df['g_force_roll_mean3'] = df.groupby('run_id')['g_force'].transform(lambda x: x.rolling(3, min_periods=1).mean())
df['g_force_roll_std3'] = df.groupby('run_id')['g_force'].transform(lambda x: x.rolling(3, min_periods=1).std()).fillna(0)
df['impact_energy_idx'] = df['g_force'] * np.log1p(df['speed'])

# 도메인 기준 실제 사과 손상 위험 충격 여부 (Ground Truth for Evaluation)
# 농산물 수송 연구 기준 1.8G 이상이거나 기기에서 '충격' 상태가 발생한 경우를 위험(1)으로 정의
df['is_shock_gt'] = ((df['g_force'] >= 1.8) | (df['status'].str.contains('충격', na=False))).astype(int)

shock_count = df['is_shock_gt'].sum()
shock_ratio = shock_count / len(df)
print(f"사과 손상 위험 충격(>=1.8G 또는 충격 이벤트) 건수: {shock_count}건 ({shock_ratio*100:.2f}%)")

# 3. [1단계] 비지도 학습 기반 이상 충격 탐지 (Unsupervised Anomaly Detection)
unsupervised_features = ['g_force', 'speed', 'speed_diff', 'g_force_roll_std3', 'impact_energy_idx']
X_unsup = df[unsupervised_features].copy()
scaler = StandardScaler()
X_unsup_scaled = scaler.fit_transform(X_unsup)

# (a) Isolation Forest
iso_forest = IsolationForest(n_estimators=200, contamination=0.04, random_state=42)
df['iso_pred'] = (iso_forest.fit_predict(X_unsup_scaled) == -1).astype(int)
df['iso_score'] = -iso_forest.score_samples(X_unsup_scaled)

# (b) One-Class SVM
oc_svm = OneClassSVM(kernel='rbf', nu=0.04, gamma='scale')
df['ocsvm_pred'] = (oc_svm.fit_predict(X_unsup_scaled) == -1).astype(int)

# (c) Local Outlier Factor (LOF)
lof = LocalOutlierFactor(n_neighbors=20, contamination=0.04)
df['lof_pred'] = (lof.fit_predict(X_unsup_scaled) == -1).astype(int)

# (d) K-Means 클러스터링 (강의 7장 연계: K=3 안전 운행 / 고속 주행 / 이상 충격 클러스터)
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
df['kmeans_cluster'] = kmeans.fit_predict(X_unsup_scaled)
# 평균 g_force가 가장 높은 클러스터를 이상 충격 클러스터로 매핑
cluster_g_means = df.groupby('kmeans_cluster')['g_force'].mean()
shock_cluster_id = cluster_g_means.idxmax()
df['kmeans_pred'] = (df['kmeans_cluster'] == shock_cluster_id).astype(int)

unsup_results = {}
for name, col in [
    ('Isolation Forest', 'iso_pred'),
    ('One-Class SVM', 'ocsvm_pred'),
    ('Local Outlier Factor (LOF)', 'lof_pred'),
    ('K-Means (Cluster Analysis)', 'kmeans_pred')
]:
    acc = accuracy_score(df['is_shock_gt'], df[col])
    prec = precision_score(df['is_shock_gt'], df[col], zero_division=0)
    rec = recall_score(df['is_shock_gt'], df[col], zero_division=0)
    f1 = f1_score(df['is_shock_gt'], df[col], zero_division=0)
    unsup_results[name] = {
        'accuracy': round(acc * 100, 2),
        'precision': round(prec * 100, 2),
        'recall': round(rec * 100, 2),
        'f1': round(f1 * 100, 2),
        'detected_count': int(df[col].sum())
    }
    print(f"[비지도] {name}: Acc={acc*100:.2f}%, Prec={prec*100:.2f}%, Recall={rec*100:.2f}%, F1={f1*100:.2f}%")

# 4. [2단계] 강의 연계 지도 학습 모델 비교 및 GridSearchCV 튜닝
# (Decision Tree vs Random Forest vs MLP)
# 타깃: Isolation Forest가 탐지한 이상 충격 또는 도메인 충격 라벨 예측
# 피처: 현재 주행 환경 및 직전 시계열 진동 특성 (g_force 직접 노출을 제외하거나 센서 결합 특성 사용)
# 여기서는 센서 종합 피처(진동 변동성, 직전 충격, 속도, 속도 변화량, 온습도, 충격 에너지)로 학습
sup_features = ['speed', 'speed_diff', 'g_force_prev1', 'g_force_roll_mean3', 'g_force_roll_std3', 'temperature', 'humidity']
X_sup = df[sup_features]
y_sup = df['is_shock_gt']

X_train, X_test, y_train, y_test = train_test_split(
    X_sup, y_sup, test_size=0.25, random_state=42, stratify=y_sup
)

scaler_sup = StandardScaler()
X_train_scaled = scaler_sup.fit_transform(X_train)
X_test_scaled = scaler_sup.transform(X_test)

sup_results = {}

# (1) Decision Tree (강의 3~4주차)
dt = DecisionTreeClassifier(max_depth=5, random_state=42)
dt.fit(X_train, y_train)
dt_pred = dt.predict(X_test)
dt_prob = dt.predict_proba(X_test)[:, 1]

# (2) Random Forest + GridSearchCV (강의 4주차 RF_gridsearch.ipynb 방식)
param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [5, 8, 12],
    'min_samples_split': [2, 5]
}
rf_base = RandomForestClassifier(random_state=42)
grid_search = GridSearchCV(rf_base, param_grid, cv=5, scoring='f1', n_jobs=-1)
grid_search.fit(X_train, y_train)
best_rf = grid_search.best_estimator_
rf_pred = best_rf.predict(X_test)
rf_prob = best_rf.predict_proba(X_test)[:, 1]

# (3) MLP Deep Learning (강의 6주차 MLP)
mlp = MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=300, random_state=42)
mlp.fit(X_train_scaled, y_train)
mlp_pred = mlp.predict(X_test_scaled)
mlp_prob = mlp.predict_proba(X_test_scaled)[:, 1]

for name, pred, prob in [
    ('Decision Tree (3주차)', dt_pred, dt_prob),
    ('Random Forest + GridSearch (4주차)', rf_pred, rf_prob),
    ('MLP 신경망 (6주차)', mlp_pred, mlp_prob)
]:
    acc = accuracy_score(y_test, pred)
    prec = precision_score(y_test, pred, zero_division=0)
    rec = recall_score(y_test, pred, zero_division=0)
    f1 = f1_score(y_test, pred, zero_division=0)
    auc = roc_auc_score(y_test, prob)
    sup_results[name] = {
        'accuracy': round(acc * 100, 2),
        'precision': round(prec * 100, 2),
        'recall': round(rec * 100, 2),
        'f1': round(f1 * 100, 2),
        'roc_auc': round(auc * 100, 2)
    }
    print(f"[지도] {name}: Acc={acc*100:.2f}%, F1={f1*100:.2f}%, AUC={auc*100:.2f}%")

print("Best RF Params:", grid_search.best_params_)

# 특성 중요도 저장
feat_imp = pd.Series(best_rf.feature_importances_, index=sup_features).sort_values(ascending=False)
print("\nFeature Importances:\n", feat_imp)

# 5. 발표 자료용 고해상도 차트 4종 생성
# Chart 1: 사과 운송 충격량(G-force) 분포 및 위험 등급 기준
plt.figure(figsize=(10, 5.5), dpi=150)
plt.plot(df.index, df['g_force'], color='#4A90E2', alpha=0.7, linewidth=0.8, label='실시간 충격 가속도 (G-force)')
plt.axhline(1.8, color='#E74C3C', linestyle='--', linewidth=2, label='사과 타박상 위험 임계치 (1.8G)')
plt.axhline(1.3, color='#F39C12', linestyle=':', linewidth=1.5, label='주의 진동 기준 (1.3G)')
shock_pts = df[df['is_shock_gt'] == 1]
plt.scatter(shock_pts.index, shock_pts['g_force'], color='#E74C3C', s=25, zorder=5, label=f'이상 충격 감지 ({len(shock_pts)}건)')
plt.title('사과 운송 전 구간 충격 가속도(G-force) 시계열 추이 및 이상 충격 지점', fontsize=14, fontweight='bold', pad=12)
plt.xlabel('데이터 시계열 인덱스 (총 4,945건 주행 기록)', fontsize=11)
plt.ylabel('충격 가속도 (G-force)', fontsize=11)
plt.legend(loc='upper right', frameon=True)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('results/fig1_shock_timeseries.png')
plt.close()

# Chart 2: Isolation Forest 비지도 이상 탐지 결과 (속도 vs 충격량)
plt.figure(figsize=(9, 5.5), dpi=150)
normal_pts = df[df['iso_pred'] == 0]
anom_pts = df[df['iso_pred'] == 1]
plt.scatter(normal_pts['speed'], normal_pts['g_force'], c='#2ECC71', alpha=0.4, s=20, label=f'정상 운송 구간 ({len(normal_pts)}건)')
plt.scatter(anom_pts['speed'], anom_pts['g_force'], c='#E74C3C', alpha=0.85, s=45, marker='^', label=f'Isolation Forest 이상 충격 탐지 ({len(anom_pts)}건)')
plt.axhline(1.8, color='#C0392B', linestyle='--', alpha=0.7, label='1.8G 사과 손상 기준선')
plt.title('비지도 학습(Isolation Forest) 기반 주행 속도별 사과 이상 충격 탐지 분포', fontsize=13, fontweight='bold', pad=12)
plt.xlabel('트럭 주행 속도 (km/h)', fontsize=11)
plt.ylabel('충격 가속도 (G-force)', fontsize=11)
plt.legend(loc='upper right', frameon=True)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('results/fig2_isolation_forest_scatter.png')
plt.close()

# Chart 3: 모델 성능 비교 (비지도 & 지도 학습 모델 F1 / Accuracy 비교)
fig, axes = plt.subplots(1, 2, figsize=(12, 5), dpi=150)

# 3-1: 비지도 모델 비교
unsup_names = list(unsup_results.keys())
unsup_f1s = [unsup_results[k]['f1'] for k in unsup_names]
unsup_accs = [unsup_results[k]['accuracy'] for k in unsup_names]
x = np.arange(len(unsup_names))
w = 0.35
axes[0].bar(x - w/2, unsup_accs, w, label='정확도 (Accuracy %)', color='#3498DB')
axes[0].bar(x + w/2, unsup_f1s, w, label='F1-Score (%)', color='#E67E22')
axes[0].set_title('[1단계] 비지도 이상 탐지 모델 성능 비교', fontsize=12, fontweight='bold')
axes[0].set_xticks(x)
axes[0].set_xticklabels(['Isolation\nForest', 'One-Class\nSVM', 'LOF', 'K-Means\n(7장 군집)'], fontsize=9.5)
axes[0].set_ylim(0, 108)
axes[0].legend()
axes[0].grid(axis='y', alpha=0.3)
for i, v in enumerate(unsup_f1s):
    axes[0].text(i + w/2, v + 1.5, f"{v:.1f}%", ha='center', fontsize=8.5, fontweight='bold')

# 3-2: 지도학습 모델 비교
sup_names = list(sup_results.keys())
sup_f1s = [sup_results[k]['f1'] for k in sup_names]
sup_aucs = [sup_results[k]['roc_auc'] for k in sup_names]
x2 = np.arange(len(sup_names))
axes[1].bar(x2 - w/2, sup_aucs, w, label='ROC-AUC (%)', color='#2ECC71')
axes[1].bar(x2 + w/2, sup_f1s, w, label='F1-Score (%)', color='#9B59B6')
axes[1].set_title('[2단계] 강의 연계 예측 모델 성능 비교', fontsize=12, fontweight='bold')
axes[1].set_xticks(x2)
axes[1].set_xticklabels(['Decision Tree\n(3주차)', 'Random Forest\n+GridSearch (4주차)', 'MLP 딥러닝\n(6주차)'], fontsize=9.5)
axes[1].set_ylim(0, 108)
axes[1].legend()
axes[1].grid(axis='y', alpha=0.3)
for i, v in enumerate(sup_f1s):
    axes[1].text(i + w/2, v + 1.5, f"{v:.1f}%", ha='center', fontsize=8.5, fontweight='bold')

plt.tight_layout()
plt.savefig('results/fig3_model_comparison.png')
plt.close()

# Chart 4: Random Forest 특성 중요도 (Feature Importance)
plt.figure(figsize=(8.5, 4.8), dpi=150)
kor_labels = {
    'g_force_roll_mean3': '최근 3구간 평균 진동(G)',
    'g_force_roll_std3': '최근 3구간 진동 변동성(Std)',
    'g_force_prev1': '직전 시점 충격량(G)',
    'speed': '트럭 주행 속도(km/h)',
    'speed_diff': '순간 속도 변화량(급가감속)',
    'humidity': '화물칸 습도(%)',
    'temperature': '화물칸 온도(°C)'
}
imp_df = feat_imp.rename(index=kor_labels)
colors = sns.color_palette('viridis', len(imp_df))
bars = plt.barh(imp_df.index[::-1], imp_df.values[::-1] * 100, color=colors[::-1])
plt.title('Random Forest 기반 사과 손상 충격 예측 핵심 변수 중요도 (%)', fontsize=13, fontweight='bold', pad=12)
plt.xlabel('특성 중요도 (Feature Importance %)', fontsize=11)
for bar in bars:
    w_val = bar.get_width()
    plt.text(w_val + 0.8, bar.get_y() + bar.get_height()/2, f"{w_val:.1f}%", va='center', fontsize=9.5, fontweight='bold')
plt.xlim(0, max(imp_df.values * 100) + 10)
plt.grid(axis='x', alpha=0.3)
plt.tight_layout()
plt.savefig('results/fig4_feature_importance.png')
plt.close()

# 실험 결과 요약 JSON 저장
summary = {
    'total_rows': int(len(df)),
    'num_trips': int(df['run_id'].nunique()),
    'shock_count': int(shock_count),
    'shock_ratio_pct': round(shock_ratio * 100, 2),
    'unsupervised_results': unsup_results,
    'supervised_results': sup_results,
    'best_rf_params': grid_search.best_params_,
    'feature_importances_pct': {k: round(float(v)*100, 2) for k, v in feat_imp.items()}
}
with open('results/experiment_summary.json', 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print("실험 및 차트 4종 생성 완료!")
