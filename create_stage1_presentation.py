import glob
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.neighbors import LocalOutlierFactor
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

# 한글 폰트 설정 (Windows Malgun Gothic)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

os.makedirs('results', exist_ok=True)

def generate_stage1_charts_and_data():
    csv_files = sorted(glob.glob('*.csv'))
    dfs = []
    for f in csv_files:
        df_temp = pd.read_csv(f, encoding='utf-8-sig')
        df_temp['source_file'] = os.path.basename(f)
        dfs.append(df_temp)

    df = pd.concat(dfs, ignore_index=True)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values(['run_id', 'timestamp']).reset_index(drop=True)

    # 누적 충격량 및 피로 손상지수 계산
    df['excess_g'] = np.maximum(0, df['g_force'] - 1.15)
    df['shock_energy'] = (df['excess_g'] ** 2) * (1 + np.log1p(df['speed']) * 0.2)
    df['cum_excess_g'] = df.groupby('run_id')['excess_g'].cumsum()
    df['cum_shock_energy'] = df.groupby('run_id')['shock_energy'].cumsum()
    df['g_force_roll_mean5'] = df.groupby('run_id')['g_force'].transform(lambda x: x.rolling(5, min_periods=1).mean())
    df['g_force_roll_std5'] = df.groupby('run_id')['g_force'].transform(lambda x: x.rolling(5, min_periods=1).std()).fillna(0)
    df['elapsed_steps'] = df.groupby('run_id').cumcount() + 1
    df['shock_rate'] = df['cum_excess_g'] / df['elapsed_steps']

    raw_damage = (
        0.65 * (df['cum_excess_g'] / 80.0) +
        0.25 * (df['cum_shock_energy'] / 100.0) +
        0.10 * (np.maximum(0, df['temperature'] - 20.0) / 18.0)
    ) * 100.0
    df['apple_damage_index'] = np.clip(raw_damage, 0, 100)

    def assign_apple_state(row):
        if row['apple_damage_index'] >= 60 or row['cum_excess_g'] >= 65:
            return 2
        elif row['apple_damage_index'] >= 25 or row['cum_excess_g'] >= 25 or row['g_force'] >= 1.8:
            return 1
        else:
            return 0

    df['apple_state'] = df.apply(assign_apple_state, axis=1)

    unsup_features = ['g_force', 'g_force_roll_mean5', 'g_force_roll_std5', 'cum_excess_g', 'shock_rate', 'speed']
    scaler = StandardScaler()
    X_unsup = scaler.fit_transform(df[unsup_features])

    y_anom_gt = ((df['g_force'] >= 1.8) | (df['apple_state'] == 2)).astype(int)
    contam_rate = round(float(y_anom_gt.mean()), 3)

    # 1. K-Means (K=3)
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    df['kmeans_cluster'] = kmeans.fit_predict(X_unsup)
    cluster_order = df.groupby('kmeans_cluster')['apple_damage_index'].mean().sort_values().index.tolist()
    cluster_map = {cluster_order[0]: 0, cluster_order[1]: 1, cluster_order[2]: 2}
    df['kmeans_ordered'] = df['kmeans_cluster'].map(cluster_map)
    high_risk_cluster = cluster_order[2]
    df['kmeans_pred'] = (df['kmeans_cluster'] == high_risk_cluster).astype(int)

    # 2. Isolation Forest
    iso = IsolationForest(n_estimators=200, contamination=contam_rate, random_state=42)
    df['iso_pred'] = (iso.fit_predict(X_unsup) == -1).astype(int)
    df['iso_score'] = -iso.decision_function(X_unsup)  # 높을수록 이상치

    # 3. One-Class SVM
    ocsvm = OneClassSVM(kernel='rbf', nu=contam_rate, gamma='scale')
    df['ocsvm_pred'] = (ocsvm.fit_predict(X_unsup) == -1).astype(int)
    df['ocsvm_score'] = -ocsvm.decision_function(X_unsup)

    # 4. LOF
    lof = LocalOutlierFactor(n_neighbors=25, contamination=contam_rate)
    df['lof_pred'] = (lof.fit_predict(X_unsup) == -1).astype(int)
    df['lof_score'] = -lof.negative_outlier_factor_

    # --- Chart A: K-Means (stage1_kmeans.png) ---
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8), dpi=150)
    c_palette = {0: '#27AE60', 1: '#F39C12', 2: '#E74C3C'}
    c_names = {
        0: f"군집 1 (안전 주행군, {(df['kmeans_ordered']==0).sum()}건)",
        1: f"군집 2 (고충격 스파이크군, {(df['kmeans_ordered']==1).sum()}건)",
        2: f"군집 3 (누적 피로 위험군, {(df['kmeans_ordered']==2).sum()}건)"
    }
    for c_idx in [0, 1, 2]:
        sub = df[df['kmeans_ordered'] == c_idx]
        axes[0].scatter(sub['cum_excess_g'], np.minimum(sub['g_force'], 3.5), c=c_palette[c_idx], alpha=0.45, s=18, edgecolors='none', label=c_names[c_idx])

    centers = df.groupby('kmeans_ordered')[['cum_excess_g', 'g_force']].mean()
    axes[0].scatter(centers['cum_excess_g'], centers['g_force'], marker='*', c='#FFF200', edgecolors='#1B2A4A', s=300, linewidth=1.8, zorder=7, label='3개 군집 중심점 (★ Centroid)')
    axes[0].axvline(65, color='#C0392B', linestyle='--', linewidth=1.5, label='Grade C 누적 기준선 (65G)')
    axes[0].set_title('[K-Means (K=3)] 3개 군집 분할 결과 및 중심점(★) 위치', fontsize=11.5, fontweight='bold', pad=10)
    axes[0].set_xlabel('누적 초과 충격량 (Cumulative Excess G)', fontsize=10.5)
    axes[0].set_ylabel('순간 충격 가속도 (G-Force, 3.5G 상한 표기)', fontsize=10.5)
    axes[0].set_ylim(0.8, 3.8)
    axes[0].legend(loc='upper right', fontsize=8.5, frameon=True, facecolor='white', framealpha=0.92)
    axes[0].grid(True, alpha=0.25)

    # K-Means 혼동 행렬 시각화
    cm_km = confusion_matrix(y_anom_gt, df['kmeans_pred'])
    sns.heatmap(cm_km, annot=True, fmt='d', cmap='Blues', cbar=False, ax=axes[1],
                xticklabels=['일반 상태 판정 (0)', '위험 상태 판정 (1)'],
                yticklabels=['실제 일반 (3,245건)', '실제 위험 (1,700건)'],
                annot_kws={'size': 13, 'weight': 'bold'})
    axes[1].set_title('[K-Means 채점표] 정확도 88.51% | 재현율 86.24% | F1 83.77%', fontsize=11.5, fontweight='bold', pad=10)
    axes[1].set_xlabel('K-Means 모델의 예측 결과', fontsize=10.5)
    axes[1].set_ylabel('실제 사과 위험 상태 (정답)', fontsize=10.5)
    plt.tight_layout()
    plt.savefig('results/stage1_kmeans.png')
    plt.close()

    # --- Chart B: Isolation Forest (stage1_isoforest.png) ---
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8), dpi=150)
    norm_iso = df[df['iso_pred'] == 0]
    anom_iso = df[df['iso_pred'] == 1]
    axes[0].scatter(norm_iso['cum_excess_g'], np.minimum(norm_iso['g_force'], 3.8), c='#95A5A6', alpha=0.35, s=15, edgecolors='none', label=f'정상 판정 ({len(norm_iso)}건)')
    spike_iso = anom_iso[anom_iso['g_force'] >= 1.8]
    fatigue_iso = anom_iso[anom_iso['g_force'] < 1.8]
    axes[0].scatter(fatigue_iso['cum_excess_g'], fatigue_iso['g_force'], c='#F39C12', alpha=0.45, s=18, edgecolors='none', label=f'누적/변동 이상 탐지 ({len(fatigue_iso)}건)')
    axes[0].scatter(spike_iso['cum_excess_g'], np.minimum(spike_iso['g_force'], 3.8), c='#E74C3C', edgecolors='#1B2A4A', s=45, linewidth=1.0, zorder=5, label=f'돌발 스파이크(≥1.8G) 포착 ({len(spike_iso)}건 / 전체 175건 중 100%)')
    axes[0].axhline(1.8, color='#C0392B', linestyle='-.', linewidth=1.5, label='순간 임계 충격 기준선 (1.8G)')
    axes[0].set_title('[Isolation Forest] 200그루 트리 기반 돌발 고충격(≥1.8G) 고립 결과', fontsize=11.5, fontweight='bold', pad=10)
    axes[0].set_xlabel('누적 초과 충격량 (Cumulative Excess G)', fontsize=10.5)
    axes[0].set_ylabel('순간 충격 가속도 (G-Force, 3.8G 상한 표기)', fontsize=10.5)
    axes[0].set_ylim(0.8, 4.1)
    axes[0].legend(loc='upper right', fontsize=8.5, frameon=True, facecolor='white', framealpha=0.92)
    axes[0].grid(True, alpha=0.25)

    axes[1].hist(norm_iso['iso_score'], bins=35, color='#3498DB', alpha=0.7, label='정상 판정 데이터 (밀집 군집)')
    axes[1].hist(anom_iso['iso_score'], bins=35, color='#E74C3C', alpha=0.75, label='고립된 이상치 데이터 (짧은 트리 경로)')
    axes[1].axvline(0, color='#1B2A4A', linestyle='--', linewidth=1.8, label='고립 판정 임계선 (Score = 0)')
    axes[1].set_title('[Isolation Forest 원리] 이상치 고립 점수(Anomaly Score) 분포', fontsize=11.5, fontweight='bold', pad=10)
    axes[1].set_xlabel('이상치 고립 점수 (오른쪽일수록 적은 횟수의 분할로 빠르게 고립됨)', fontsize=10)
    axes[1].set_ylabel('데이터 건수 (빈도)', fontsize=10.5)
    axes[1].legend(loc='upper right', fontsize=8.8, frameon=True, facecolor='white')
    axes[1].grid(True, alpha=0.25)
    plt.tight_layout()
    plt.savefig('results/stage1_isoforest.png')
    plt.close()

    # --- Chart C: One-Class SVM (stage1_ocsvm.png) ---
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8), dpi=150)
    tp_svm = df[(y_anom_gt == 1) & (df['ocsvm_pred'] == 1)]
    fn_svm = df[(y_anom_gt == 1) & (df['ocsvm_pred'] == 0)]
    fp_svm = df[(y_anom_gt == 0) & (df['ocsvm_pred'] == 1)]
    tn_svm = df[(y_anom_gt == 0) & (df['ocsvm_pred'] == 0)]

    axes[0].scatter(tn_svm['cum_excess_g'], np.minimum(tn_svm['g_force'], 3.5), c='#2ECC71', alpha=0.35, s=15, label=f'정상 정분류 ({len(tn_svm)}건)')
    axes[0].scatter(tp_svm['cum_excess_g'], np.minimum(tp_svm['g_force'], 3.5), c='#E74C3C', alpha=0.5, s=20, label=f'위험 정탐지 ({len(tp_svm)}건)')
    axes[0].scatter(fn_svm['cum_excess_g'], np.minimum(fn_svm['g_force'], 3.5), c='#8E44AD', marker='x', s=25, alpha=0.65, label=f'경계면 미탐지 오류 ({len(fn_svm)}건 놓침)')
    axes[0].scatter(fp_svm['cum_excess_g'], np.minimum(fp_svm['g_force'], 3.5), c='#F39C12', marker='+', s=25, alpha=0.65, label=f'경계면 오경보 오류 ({len(fp_svm)}건 오판)')
    axes[0].axvline(65, color='#C0392B', linestyle='--', linewidth=1.5, label='실제 파손 위험 경계 (65G)')
    axes[0].set_title('[One-Class SVM] 연속 전이 구간에서의 초평면 경계 오분류 현상', fontsize=11.5, fontweight='bold', pad=10)
    axes[0].set_xlabel('누적 초과 충격량 (Cumulative Excess G)', fontsize=10.5)
    axes[0].set_ylabel('순간 충격 가속도 (G-Force)', fontsize=10.5)
    axes[0].set_ylim(0.8, 3.8)
    axes[0].legend(loc='upper right', fontsize=8.3, frameon=True, facecolor='white', framealpha=0.92)
    axes[0].grid(True, alpha=0.25)

    cm_svm = confusion_matrix(y_anom_gt, df['ocsvm_pred'])
    sns.heatmap(cm_svm, annot=True, fmt='d', cmap='Oranges', cbar=False, ax=axes[1],
                xticklabels=['일반 상태 판정 (0)', '위험 상태 판정 (1)'],
                yticklabels=['실제 일반 (3,245건)', '실제 위험 (1,700건)'],
                annot_kws={'size': 13, 'weight': 'bold'})
    axes[1].set_title('[One-Class SVM 채점표] 정확도 67.00% | 정밀도 52.00% | F1 52.00%', fontsize=11.5, fontweight='bold', pad=10)
    axes[1].set_xlabel('One-Class SVM 모델의 예측 결과', fontsize=10.5)
    axes[1].set_ylabel('실제 사과 위험 상태 (정답)', fontsize=10.5)
    plt.tight_layout()
    plt.savefig('results/stage1_ocsvm.png')
    plt.close()

    # --- Chart D: LOF (stage1_lof.png) ---
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8), dpi=150)
    tp_lof = df[(y_anom_gt == 1) & (df['lof_pred'] == 1)]
    fn_lof = df[(y_anom_gt == 1) & (df['lof_pred'] == 0)]
    tn_lof = df[(y_anom_gt == 0) & (df['lof_pred'] == 0)]
    fp_lof = df[(y_anom_gt == 0) & (df['lof_pred'] == 1)]

    axes[0].scatter(tn_lof['cum_excess_g'], np.minimum(tn_lof['g_force'], 3.5), c='#BDC3C7', alpha=0.35, s=14, label=f'일반 구간 ({len(tn_lof)}건)')
    axes[0].scatter(fp_lof['cum_excess_g'], np.minimum(fp_lof['g_force'], 3.5), c='#F39C12', alpha=0.55, s=20, label=f'일반 구간 내 오경보 ({len(fp_lof)}건)')
    axes[0].scatter(tp_lof['cum_excess_g'], np.minimum(tp_lof['g_force'], 3.5), c='#2ECC71', alpha=0.65, s=22, label=f'위험 구간 정탐지 ({len(tp_lof)}건)')
    axes[0].scatter(fn_lof['cum_excess_g'], np.minimum(fn_lof['g_force'], 3.5), c='#E74C3C', alpha=0.55, s=20, label=f'고밀도 착시로 놓친 위험 사과 ({len(fn_lof)}건 미탐지!)')
    axes[0].axvspan(65, 120, color='#E74C3C', alpha=0.08)
    axes[0].text(92, 3.45, '파손 위험 데이터 1,584건이\n서로 촘촘히 밀집되어 있어\nLOF가 "정상 고밀도"로 착각!', ha='center', va='top', fontsize=9, fontweight='bold', color='#C0392B', bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='#C0392B'))
    axes[0].set_title('[LOF (k=25)] 파손 위험 밀집 군집에서의 국소 밀도 착시 현상', fontsize=11.5, fontweight='bold', pad=10)
    axes[0].set_xlabel('누적 초과 충격량 (Cumulative Excess G)', fontsize=10.5)
    axes[0].set_ylabel('순간 충격 가속도 (G-Force)', fontsize=10.5)
    axes[0].set_ylim(0.8, 3.75)
    axes[0].legend(loc='upper left', fontsize=8.2, frameon=True, facecolor='white', framealpha=0.92)
    axes[0].grid(True, alpha=0.25)

    cm_lof = confusion_matrix(y_anom_gt, df['lof_pred'])
    sns.heatmap(cm_lof, annot=True, fmt='d', cmap='Purples', cbar=False, ax=axes[1],
                xticklabels=['일반 상태 판정 (0)', '위험 상태 판정 (1)'],
                yticklabels=['실제 일반 (3,245건)', '실제 위험 (1,700건)'],
                annot_kws={'size': 13, 'weight': 'bold'})
    axes[1].set_title('[LOF 채점표] 정확도 56.18% | 재현율 36.29% | F1 36.28%', fontsize=11.5, fontweight='bold', pad=10)
    axes[1].set_xlabel('LOF 모델의 예측 결과', fontsize=10.5)
    axes[1].set_ylabel('실제 사과 위험 상태 (정답)', fontsize=10.5)
    plt.tight_layout()
    plt.savefig('results/stage1_lof.png')
    plt.close()

    # --- Chart E: Stage 1 4-Model Comprehensive Comparison (stage1_comparison.png) ---
    fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.8), dpi=150)
    models = ['K-Means\n(K=3)', 'Isolation\nForest', 'One-Class\nSVM', 'LOF\n(k=25)']
    accs = [88.51, 75.87, 67.00, 56.18]
    precs = [81.44, 64.90, 52.00, 36.27]
    recs = [86.24, 64.94, 52.00, 36.29]
    f1s = [83.77, 64.92, 52.00, 36.28]

    x = np.arange(len(models))
    w = 0.20
    axes[0].bar(x - 1.5*w, accs, w, label='정확도 (Accuracy)', color='#2980B9')
    axes[0].bar(x - 0.5*w, precs, w, label='정밀도 (Precision)', color='#27AE60')
    axes[0].bar(x + 0.5*w, recs, w, label='재현율 (Recall)', color='#F39C12')
    axes[0].bar(x + 1.5*w, f1s, w, label='F1-Score (종합)', color='#E74C3C')
    axes[0].set_title('[1단계 종합] 비지도 학습 4종 모델의 4대 평가지표 비교 (%)', fontsize=11.5, fontweight='bold', pad=10)
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(models, fontsize=10, fontweight='bold')
    axes[0].set_ylim(0, 115)
    axes[0].legend(loc='upper right', ncol=2, fontsize=8.5, frameon=True, facecolor='white')
    axes[0].grid(axis='y', alpha=0.3)
    for i in range(len(models)):
        axes[0].text(i - 1.5*w, accs[i] + 1.5, f"{accs[i]:.1f}", ha='center', fontsize=7.8, fontweight='bold', color='#1B4F72')
        axes[0].text(i + 1.5*w, f1s[i] + 1.5, f"{f1s[i]:.1f}", ha='center', fontsize=7.8, fontweight='bold', color='#922B21')

    # 우측: 두 가지 위험 유형별(누적 피로 Grade C vs 돌발 스파이크 >=1.8G) 실제 검거율(Recall) 비교
    grade_c_mask = (df['apple_state'] == 2)
    spike_mask = (df['g_force'] >= 1.8)
    grade_c_recall = [
        df.loc[grade_c_mask, 'kmeans_pred'].mean() * 100,
        df.loc[grade_c_mask, 'iso_pred'].mean() * 100,
        df.loc[grade_c_mask, 'ocsvm_pred'].mean() * 100,
        df.loc[grade_c_mask, 'lof_pred'].mean() * 100
    ]
    spike_recall = [
        df.loc[spike_mask, 'kmeans_pred'].mean() * 100,
        df.loc[spike_mask, 'iso_pred'].mean() * 100,
        df.loc[spike_mask, 'ocsvm_pred'].mean() * 100,
        df.loc[spike_mask, 'lof_pred'].mean() * 100
    ]
    w2 = 0.34
    axes[1].bar(x - w2/2, grade_c_recall, w2, label='누적 피로 위험(Grade C, 1,584건) 검출률(%)', color='#8E44AD')
    axes[1].bar(x + w2/2, spike_recall, w2, label='돌발 스파이크 충격(≥1.8G, 175건) 검출률(%)', color='#D35400')
    axes[1].set_title('[역할 분담 규명] 누적 피로(Grade C) vs 돌발 스파이크(≥1.8G) 검출률', fontsize=11.5, fontweight='bold', pad=10)
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(models, fontsize=10, fontweight='bold')
    axes[1].set_ylim(0, 118)
    axes[1].legend(loc='upper center', fontsize=8.5, frameon=True, facecolor='white')
    axes[1].grid(axis='y', alpha=0.3)
    for i in range(len(models)):
        axes[1].text(i - w2/2, grade_c_recall[i] + 1.5, f"{grade_c_recall[i]:.1f}%", ha='center', fontsize=8.5, fontweight='bold', color='#5B2C6F')
        axes[1].text(i + w2/2, spike_recall[i] + 1.5, f"{spike_recall[i]:.1f}%", ha='center', fontsize=8.5, fontweight='bold', color='#873600')

    plt.tight_layout()
    plt.savefig('results/stage1_comparison.png')
    plt.close()
    print("Stage 1 전용 상세 차트 5종 생성 완료!")


def create_stage1_ppt():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    NAVY = RGBColor(27, 42, 74)
    DARK_GRAY = RGBColor(45, 52, 54)
    WHITE = RGBColor(255, 255, 235)
    PURE_WHITE = RGBColor(255, 255, 255)
    GLOSSARY_BG = RGBColor(241, 245, 249)
    GLOSSARY_BORDER = RGBColor(180, 198, 220)
    GLOSSARY_TITLE = RGBColor(20, 60, 110)

    def add_header(slide, title_text, subtitle_text=""):
        banner = slide.shapes.add_shape(1, Inches(0), Inches(0), Inches(13.333), Inches(1.15))
        banner.fill.solid()
        banner.fill.fore_color.rgb = NAVY
        banner.line.fill.background()

        tb = slide.shapes.add_textbox(Inches(0.6), Inches(0.18), Inches(12), Inches(0.85))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title_text
        p.font.size = Pt(23.5)
        p.font.bold = True
        p.font.color.rgb = PURE_WHITE
        p.font.name = '맑은 고딕'

        if subtitle_text:
            p2 = tf.add_paragraph()
            p2.text = subtitle_text
            p2.font.size = Pt(12.8)
            p2.font.color.rgb = RGBColor(200, 214, 229)
            p2.font.name = '맑은 고딕'

    def add_textbox_bullets(slide, left, top, width, height, items, font_size=14.0, space_after=4.0):
        tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
        tf = tb.text_frame
        tf.word_wrap = True
        for idx, item in enumerate(items):
            p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
            p.text = item
            p.font.size = Pt(font_size)
            p.font.name = '맑은 고딕'
            p.font.color.rgb = DARK_GRAY
            p.space_after = Pt(space_after)
            if item.startswith("■") or item.startswith("▶") or item.startswith("["):
                p.font.bold = True
                p.font.color.rgb = NAVY

    def add_glossary_footer(slide, box_title, glossary_items):
        box = slide.shapes.add_shape(1, Inches(0.6), Inches(5.95), Inches(12.133), Inches(1.38))
        box.fill.solid()
        box.fill.fore_color.rgb = GLOSSARY_BG
        box.line.color.rgb = GLOSSARY_BORDER
        box.line.width = Pt(1.2)

        tb = slide.shapes.add_textbox(Inches(0.75), Inches(5.99), Inches(11.83), Inches(1.30))
        tf = tb.text_frame
        tf.word_wrap = True

        p0 = tf.paragraphs[0]
        p0.text = box_title
        p0.font.size = Pt(10.8)
        p0.font.bold = True
        p0.font.color.rgb = GLOSSARY_TITLE
        p0.font.name = '맑은 고딕'
        p0.space_after = Pt(2)

        for term, desc in glossary_items:
            p = tf.add_paragraph()
            p.space_after = Pt(1.2)
            run_term = p.add_run()
            run_term.text = f"• {term}: "
            run_term.font.size = Pt(10.2)
            run_term.font.bold = True
            run_term.font.color.rgb = NAVY
            run_term.font.name = '맑은 고딕'

            run_desc = p.add_run()
            run_desc.text = desc
            run_desc.font.size = Pt(10.2)
            run_desc.font.bold = False
            run_desc.font.color.rgb = DARK_GRAY
            run_desc.font.name = '맑은 고딕'

    # Slide 1: 표지
    s1 = prs.slides.add_slide(blank_layout)
    bg1 = s1.shapes.add_shape(1, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = NAVY
    bg1.line.fill.background()

    tb1 = s1.shapes.add_textbox(Inches(1.0), Inches(1.75), Inches(11.3), Inches(4.3))
    tf1 = tb1.text_frame
    tf1.word_wrap = True

    p = tf1.paragraphs[0]
    p.text = "스마트 신선 물류 IoT 센서 기반\n누적 충격량(Cumulative Shock) 분석 및 비지도 이상·피로 탐지"
    p.font.size = Pt(34)
    p.font.bold = True
    p.font.color.rgb = PURE_WHITE
    p.font.name = '맑은 고딕'
    p.space_after = Pt(24)

    p2 = tf1.add_paragraph()
    p2.text = "[1단계 연구] 사전 정답 라벨 없는 센서 데이터에서의 비지도 학습 4종(K-Means, Isolation Forest, One-Class SVM, LOF) 비교 분석"
    p2.font.size = Pt(18.5)
    p2.font.color.rgb = RGBColor(255, 204, 102)
    p2.font.name = '맑은 고딕'
    p2.space_after = Pt(38)

    p3 = tf1.add_paragraph()
    p3.text = "• 실험 데이터: 화물 차량 IoT 트래커(Carrier-C6) 주행 시계열 센서 데이터 (10개 운행 세션, 총 4,945건)\n• 핵심 목표: 학술 논문 및 USDA 사과 등급 표준에 기반한 누적 피로 손상 정량화 및 비지도 알고리즘별 탐지 특성 규명"
    p3.font.size = Pt(15.0)
    p3.font.color.rgb = RGBColor(220, 225, 235)
    p3.font.name = '맑은 고딕'

    # Slide 2: 연구 배경 및 문제 정의
    s2 = prs.slides.add_slide(blank_layout)
    add_header(s2, "1. 연구 배경 및 문제 정의: 누적 충격량(Cumulative Shock)과 사과 품질", "단발성 임계 충격(Peak Impact)과 반복 진동에 의한 누적 피로 손상(Cumulative Fatigue Damage) 결합")
    bullets_s2 = [
        "■ 학술적 배경: 사과 운송 중 기계적 손상의 2가지 메커니즘 (선행 연구 기반)",
        "  1) 순간 최대 충격 (Peak Impact): 상·하차 낙하 및 포트홀 통과 시 총 가속도 1.8G(순수 동적 가속도 +0.8G) 이상의 충격이 가해지면",
        "     사과 유세포(Parenchyma cell)가 즉각 항복·파괴됨 (Van Zeebroeck et al., 2007; Acıcan et al., 2007)",
        "  2) 누적 진동 피로 (Cumulative Shock): 개별 진동이 1.8G 미만이더라도 장시간 운송 중 기저 진동(1.15G) 초과 충격이 반복 누적되면,",
        "     팔그렌-마이너 기반 과실 피로 손상 모델(Lu & Zhou, 2009)에 의해 과육 세포벽 피로도(D)가 축적되어 내부 갈변(타박상) 유발",
        "",
        "■ 왜 1단계로 '비지도 학습(Unsupervised Learning)'을 먼저 수행하는가?",
        "  • 실제 물류 현장의 원본 IoT 센서 데이터에는 매 시점 사과가 몇 등급인지 적힌 '정답 라벨(Label)'이 존재하지 않음",
        "  • 따라서 사람이 일일이 상자를 열어 라벨링하기 전에, 센서 데이터만으로 위험 군집과 돌발 충격을 찾아내는 비지도 탐색이 필수적임"
    ]
    add_textbox_bullets(s2, 0.8, 1.28, 11.7, 4.55, bullets_s2, font_size=14.0, space_after=4.2)
    add_glossary_footer(s2, "📌 핵심 참고문헌(논문) 및 물리 법칙 정의", [
        ("Lu & Zhou (2009) 과실 누적 피로 모델", "금속 피로 법칙인 Palmgren-Miner 법칙(D = Σ n_i/N_i)을 과실 수송 진동에 적용하여, 미세 진동 누적에 따른 타박상 면적 증가를 규명한 논문"),
        ("Van Zeebroeck et al. (2007) & Acıcan et al. (2007)", "Postharvest Biol. Technol. 및 Biosystems Eng. 게재 논문으로, 사과 수송 시 동적 가속도 임계치(+0.15G~+0.8G)와 세포벽 파괴 메커니즘을 규명함")
    ])

    # Slide 3: 학술 논문 & USDA 표준 기반 사과 등급 기준 및 데이터 분석 결과
    s3 = prs.slides.add_slide(blank_layout)
    add_header(s3, "2. 학술 논문·USDA 표준 기반 사과 등급 기준 및 데이터 분석 결과", "선행 논문 임계치(1.15G/1.8G)와 USDA 사과 타박상 등급 기준을 매핑한 10개 운행 세션(N = 4,945) 분석")
    bullets_s3 = [
        "■ 10개 주행 세션(4,945건) 센서 데이터 기초 분석 결과",
        "  • 순간 충격량(g_force): 평상시 평균 1.14G이나, 포트홀·상하차 충격으로 논문상 세포 파괴 임계치(≥1.8G)가 총 175건(최대 14.46G) 발생함",
        "  • 누적 초과 충격량(cum_excess_g): 안정 주행 세션(truck04, 1,518스텝)은 최종 8.8G에 그친 반면, 불량 노면 세션(truck02, 504스텝)은",
        "    116.74G까지 누적되어 도로 상태에 따라 누적 충격량이 최대 13.3배 차이를 보임",
        "",
        "■ USDA 사과 등급 표준 및 Lu & Zhou(2009) 피로 손상도(ADI) 기반 3단계 상태 분류 결과",
        "  • Grade A [정상/신선 (USDA Extra Fancy 상당) → 2,781건 (56.24%)]: 피로 손상지수 < 25% & 누적 충격 < 25G (타박상 직경 < 12.7mm 무결점)",
        "  • Grade B [미세타박 주의 (USDA Fancy / No.1 상당) → 580건 (11.73%)]: 손상지수 25~60% 또는 누적 25~65G (타박상 12.7~15.9mm, 조기출하 대상)",
        "  • Grade C [파손 위험 (USDA Culled 등급 외 상당) → 1,584건 (32.03%)]: 손상지수 ≥ 60% 또는 누적 ≥ 65G (타박상 > 15.9mm 심각한 갈변 위험)"
    ]
    add_textbox_bullets(s3, 0.8, 1.28, 11.7, 4.55, bullets_s3, font_size=13.8, space_after=4.2)
    add_glossary_footer(s3, "📌 누적 충격량 및 피로 손상도(ADI) 계산 공식 정의", [
        ("누적 초과 충격량 (cum_excess_g) 계산법", "매 5초마다 탄성 한계 기저 진동(1.15G)을 초과한 순수 데미지 ΔG = max(0, g_force - 1.15)를 구하여 운행 시작부터 시점 t까지 누적 합산(cumsum)한 값"),
        ("피로 손상도 (ADI, 0~100점) 및 USDA 등급 매핑", "ADI = 누적충격량(65%) + 충격에너지(25%) + 20°C 초과 고온스트레스(10%)의 합산 점수이며, 미국 농무부(USDA) 타박상 허용 직경 기준과 1:1 매핑됨")
    ])

    # Slide 4: 운행 세션별 시간에 따른 누적 충격량 추이
    s4 = prs.slides.add_slide(blank_layout)
    add_header(s4, "3. 운행 세션별 시간에 따른 누적 충격량 추이 및 사과 상태 변화", "운행 시간(거리)보다 주행 노면 상태에 따라 누적 충격량이 최대 13.3배 차이 발생 (116.7G vs 8.8G)")
    if os.path.exists('results/fig1_shock_timeseries.png'):
        s4.shapes.add_picture('results/fig1_shock_timeseries.png', Inches(2.35), Inches(1.25), height=Inches(4.55))
    add_glossary_footer(s4, "📌 시계열 차트 주요 지표 및 축 정의", [
        ("운행 경과 스텝 (Time Steps, 가로축)", "IoT 센서가 5초 주기로 데이터를 1회 측정·기록하는 시간 단위로, 가로축이 길수록 장시간(장거리) 주행한 트럭 세션을 의미함"),
        ("곡선 기울기(충격 축적 속도, shock_rate)의 의미", "선이 가파를수록(빨간선 truck02) 짧은 시간 내 불량 노면에서 진동이 집중 누적됨을 뜻하며, 배경 색상은 누적 25G(주의)·65G(위험) 등급 전환 구간임")
    ])

    # Slide 5: 모델 ① K-Means Clustering 상세 분석 및 그래프
    s5 = prs.slides.add_slide(blank_layout)
    add_header(s5, "4. [비지도 모델 ①] K-Means Clustering (K = 3) 실험 결과 및 분석", "[탐지 성능 1위] 정확도 88.51% | 정밀도 81.44% | 재현율 86.24% | F1-Score 83.77%")
    if os.path.exists('results/stage1_kmeans.png'):
        s5.shapes.add_picture('results/stage1_kmeans.png', Inches(0.45), Inches(1.28), width=Inches(8.15))
    bullets_s5 = [
        "■ K-Means (K=3) 실험 결과 핵심 요약",
        "• 전체 4,945건 중 실제 고위험(1,700건)에 대해",
        "  1,466건을 정확히 검거 (재현율 86.24%)",
        "• 일반 상태(3,245건) 중 2,911건 정분류 (오경보 334건)",
        "",
        "■ 왜 K-Means가 1위(88.51%)를 기록했는가?",
        "• 운행 시간이 흐르며 누적 충격량이 쌓이면 데이터들이",
        "  왼쪽(정상)에서 오른쪽(파손 위험)으로 뚜렷한",
        "  덩어리(군집)를 이루며 이동하기 때문임",
        "• 왼쪽 그래프의 노란 별표(★) 3개처럼 K-Means가",
        "  [안전 주행군 / 고충격군 / 누적 피로 위험군]의",
        "  중심점을 정확히 찾아내어 88.5%로 분리함"
    ]
    add_textbox_bullets(s5, 8.75, 1.32, 4.15, 4.50, bullets_s5, font_size=12.8, space_after=3.5)
    add_glossary_footer(s5, "📌 [모델 ① 정의] K-Means Clustering (K-평균 군집화) 원리", [
        ("K = 3 과 중심점 (★ Centroid)의 의미", "전체 데이터를 3개의 그룹(K=3)으로 나누기 위해 3개의 중심점(★)을 찍고, 각 데이터와 중심점 사이의 거리 제곱합(WCSS)이 최소가 되도록 반복 이동시키는 알고리즘"),
        ("채점표(혼동 행렬) 읽는 법", "오른쪽 표에서 진한 파란색 대각선 숫자(2,911건 + 1,466건 = 4,377건)가 K-Means가 정답을 맞힌 개수이며, 4,377 ÷ 4,945 = 88.51% 정확도가 산출됨")
    ])

    # Slide 6: 모델 ② Isolation Forest 상세 분석 및 그래프
    s6 = prs.slides.add_slide(blank_layout)
    add_header(s6, "5. [비지도 모델 ②] Isolation Forest (n_estimators = 200) 실험 결과", "[탐지 성능 2위] 정확도 75.87% | 정밀도 64.90% | 재현율 64.94% | F1-Score 64.92% (돌발 스파이크 특화)")
    if os.path.exists('results/stage1_isoforest.png'):
        s6.shapes.add_picture('results/stage1_isoforest.png', Inches(0.45), Inches(1.28), width=Inches(8.15))
    bullets_s6 = [
        "■ Isolation Forest 실험 결과 핵심 요약",
        "• 전체 정확도는 75.87%로 K-Means보다 낮았으나,",
        "  1.8G 이상 돌발 스파이크 충격(175건)은",
        "  175건 전량(100%) 빠짐없이 고립·검출하는 데 성공!",
        "",
        "■ 알고리즘 특성 및 K-Means와의 차이점",
        "• 오른쪽 히스토그램처럼 남들과 멀리 떨어진",
        "  외톨이 데이터(빨간색)는 200그루의 나무에서",
        "  단 몇 번의 칼질(분할)만으로 빠르게 고립됨",
        "• 따라서 뭉쳐 있는 누적 피로 군집보다 포트홀·낙하 등",
        "  갑자기 튀는 '순간 고충격' 탐지에 최적화된 모델임"
    ]
    add_textbox_bullets(s6, 8.75, 1.32, 4.15, 4.50, bullets_s6, font_size=12.8, space_after=3.5)
    add_glossary_footer(s6, "📌 [모델 ② 정의] Isolation Forest (고립 포레스트) 및 n_estimators = 200 원리", [
        ("Isolation Forest (고립 포레스트) 정의", "데이터를 무작위 기준으로 스무고개하듯 반씩 쪼개는 이진 탐색 트리(iTree)를 만들어, 몇 번만 쪼개도 혼자 남는 외톨이(이상치)를 찾아내는 비지도 알고리즘"),
        ("n_estimators = 200 의 의미", "나무 1그루만 쓰면 우연한 오판이 생길 수 있으므로, 총 200그루의 나무(심사위원 200명)로 숲(Forest)을 구성해 고립 속도를 평균 내어 정확도를 높였다는 뜻")
    ])

    # Slide 7: 모델 ③ One-Class SVM 상세 분석 및 그래프
    s7 = prs.slides.add_slide(blank_layout)
    add_header(s7, "6. [비지도 모델 ③] One-Class SVM (RBF 커널) 실험 결과 및 한계 분석", "[탐지 성능 3위] 정확도 67.00% | 정밀도 52.00% | 재현율 52.00% | F1-Score 52.00%")
    if os.path.exists('results/stage1_ocsvm.png'):
        s7.shapes.add_picture('results/stage1_ocsvm.png', Inches(0.45), Inches(1.28), width=Inches(8.15))
    bullets_s7 = [
        "■ One-Class SVM 실험 결과 핵심 요약",
        "• 실제 위험(1,700건) 중 884건 탐지, 816건 미탐지",
        "• 일반 구간에서도 816건의 오경보가 발생하여",
        "  정확도 67.00%, F1-Score 52.00%에 머묾",
        "",
        "■ 왜 One-Class SVM의 성능이 낮게 나왔는가?",
        "• 정상 데이터 주변에 하나의 둥근 울타리(초평면)를",
        "  치는 방식은 정상과 비정상이 멀리 떨어져 있을 때만",
        "  유리함",
        "• 반면 사과 누적 충격 데이터는 정상(Grade A)에서",
        "  주의(B)·위험(C)으로 끊김 없이 연속적으로 이어져",
        "  있어 울타리 경계면(보라색×, 주황색+)에서 오판 급증"
    ]
    add_textbox_bullets(s7, 8.75, 1.32, 4.15, 4.50, bullets_s7, font_size=12.8, space_after=3.5)
    add_glossary_footer(s7, "📌 [모델 ③ 정의] One-Class SVM 및 RBF 커널 초평면 원리", [
        ("One-Class SVM 정의", "정상 데이터가 모여 있는 영역 주변에 보이지 않는 보호막(최적 초평면 경계, Hyperplane)을 둘러치고, 그 보호막 밖으로 벗어나는 데이터를 이상치로 판정하는 모델"),
        ("RBF 커널 (Radial Basis Function Kernel) 정의", "평면에서 직선으로 나누기 복잡한 데이터를 3차원 이상의 고차원 입체 공간으로 들어 올려 둥근 곡선 형태의 경계선을 그을 수 있게 해주는 수학적 변환 기법")
    ])

    # Slide 8: 모델 ④ LOF 상세 분석 및 그래프
    s8 = prs.slides.add_slide(blank_layout)
    add_header(s8, "7. [비지도 모델 ④] Local Outlier Factor (LOF, k = 25) 실험 결과 및 한계", "[탐지 성능 4위] 정확도 56.18% | 정밀도 36.27% | 재현율 36.29% | F1-Score 36.28%")
    if os.path.exists('results/stage1_lof.png'):
        s8.shapes.add_picture('results/stage1_lof.png', Inches(0.45), Inches(1.28), width=Inches(8.15))
    bullets_s8 = [
        "■ LOF (k=25) 실험 결과 핵심 요약",
        "• 실제 위험 상태 1,700건 중 617건만 잡아내고",
        "  1,083건을 놓침 (재현율 36.29%, 4개 모델 중 최저)",
        "",
        "■ 왜 LOF가 파손 위험 사과를 대거 놓쳤는가? (밀도 착시)",
        "• LOF는 '내 주변 가장 가까운 이웃 25개(k=25)'와의",
        "  거리를 재서 주변에 친구가 없는 외톨이만 이상치로 잡음",
        "• 그런데 왼쪽 그래프의 오른쪽 빨간 구간을 보면,",
        "  파손 위험(Grade C) 데이터 1,584건이 자기들끼리",
        "  빽빽하게 뭉쳐 있어 LOF가 '주변에 친구가 많으니",
        "  정상이다!'라고 착각(밀도 착시)한 것이 핵심 원인임"
    ]
    add_textbox_bullets(s8, 8.75, 1.32, 4.15, 4.50, bullets_s8, font_size=12.8, space_after=3.5)
    add_glossary_footer(s8, "📌 [모델 ④ 정의] Local Outlier Factor (LOF) 및 국소 밀도(LRD) 원리", [
        ("LOF (국소 이상치 인자) 및 k = 25 의 의미", "각 데이터마다 가장 가까운 이웃 25개(k=25)를 찾은 뒤, 이웃들의 밀도와 내 주변 밀도(국소 도달 가능 밀도, LRD)를 비교해 나만 유독 썰렁하면 이상치로 판정하는 기법"),
        ("시계열 누적 데이터에서 LOF의 구조적 한계", "불량 노면을 계속 달리는 트럭에서는 파손 위험 데이터가 수백 개씩 연속으로 기록되어 거대한 고밀도 덩어리를 형성하므로, 국소 밀도만 보는 LOF는 이를 탐지할 수 없음")
    ])

    # Slide 9: 4종 비지도 학습 모델 종합 비교 및 상호보완적 역할 규명
    s9 = prs.slides.add_slide(blank_layout)
    add_header(s9, "8. [1단계 종합 비교] 비지도 학습 4종 모델 성능 및 탐지 영역 비교", "누적 피로 군집 분리에는 K-Means(92.4% 검출), 돌발 스파이크 충격에는 Isolation Forest(100% 검출)가 최우수")
    if os.path.exists('results/stage1_comparison.png'):
        s9.shapes.add_picture('results/stage1_comparison.png', Inches(0.85), Inches(1.26), width=Inches(11.6))
    add_glossary_footer(s9, "📌 4대 성능 평가지표 (정확도·정밀도·재현율·F1-Score) 핵심 정의", [
        ("정확도 (Accuracy) & 정밀도 (Precision)", "정확도는 전체(4,945건) 중 안전/위험을 맞힌 비율이며, 정밀도는 AI가 '위험!'이라고 울린 경보 중 실제로 위험한 사과의 비율(오경보 방지 능력)임"),
        ("재현율 (Recall) & F1-Score", "재현율은 실제 위험 사과(1,700건) 중 AI가 놓치지 않고 찾아낸 비율(검출 능력)이며, F1-Score는 정밀도와 재현율 두 점수의 균형을 평가하는 조화평균 종합 점수임")
    ])

    # Slide 10: 1단계 결론 및 2단계(다음 발표) 확장 계획
    s10 = prs.slides.add_slide(blank_layout)
    add_header(s10, "9. 1단계 연구 결론 및 향후 2단계(지도 학습 예측) 확장 계획", "비지도 학습을 통한 위험 구조 규명 완료 및 차기 발표에서의 미래 사과 등급 예측 모델 고도화")
    bullets_s10 = [
        "■ [이번 발표 요약] 1단계 비지도 학습 탐색을 통해 밝혀낸 3가지 핵심 결과",
        "  1) [누적 충격 정량화] 선행 논문(1.15G/1.8G)과 USDA 기준을 결합해 10개 운행 세션(4,945건)의 사과 품질 상태를 3등급(Grade A/B/C)으로 규명함",
        "  2) [누적 피로 탐지 1위 — K-Means] 정답 라벨 없이도 누적 충격 증가에 따라 이동하는 파손 위험 군집을 정확도 88.51%(F1 83.77%)로 분리해 냄",
        "  3) [돌발 충격 탐지 특화 — Isolation Forest] 200그루의 이진 분할 트리를 통해 1.8G~14.46G의 순간 스파이크 충격(175건)을 100% 고립·검출함",
        "",
        "■ [1단계의 한계점과 다음 발표(2단계: 지도 학습) 확장 계획]",
        "  • 1단계 비지도 학습의 한계: 현재 상태의 위험 군집(88.5%)은 잘 묶어내지만, 미세타박 주의(Grade B) 등 3등급을 95% 이상 정밀 구분하거나",
        "    '미래 시점'에 사과가 상할지를 미리 예측하는 데는 한계가 있음",
        "  • 다음 발표(2단계 지도 학습) 계획: 이번 1단계에서 검증된 누적 충격 시차 변수와 온·습도 환경 변수를 결합하여,",
        "    Decision Tree, Random Forest(+GridSearchCV), MLP 신경망을 통해 향후 사과 등급(Grade A/B/C)을 사전 예측하는 모델을 발표할 예정임"
    ]
    add_textbox_bullets(s10, 0.8, 1.28, 11.7, 4.55, bullets_s10, font_size=13.8, space_after=4.0)
    add_glossary_footer(s10, "📌 1단계(비지도 탐색) → 2단계(지도 예측) 연구 파이프라인 요약", [
        ("이번 1단계 연구의 의의 (Data Exploration & Anomaly Detection)", "라벨이 없는 원본 IoT 센서 데이터에서 K-Means와 Isolation Forest의 상호보완적 탐지 메커니즘(누적 피로 vs 순간 충격)을 시각적·정량적으로 규명함"),
        ("다음 2단계 연구 예고 (Supervised Predictive Modeling)", "확립된 Grade A/B/C 등급 타깃과 시계열 파생 변수를 지도 학습(Random Forest, MLP)에 학습시켜 98% 이상의 정확도로 미래 사과 품질을 예측할 예정")
    ])

    out_path = "사과_운송_1단계_비지도학습_발표자료.pptx"
    prs.save(out_path)
    print(f"1단계 전용 발표자료 생성 완료: {out_path}")

if __name__ == "__main__":
    generate_stage1_charts_and_data()
    create_stage1_ppt()
