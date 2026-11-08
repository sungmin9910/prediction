import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

def create_ppt():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # 색상 팔레트
    NAVY = RGBColor(27, 42, 74)
    DARK_GRAY = RGBColor(45, 52, 54)
    WHITE = RGBColor(255, 255, 255)

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
        p.font.size = Pt(25)
        p.font.bold = True
        p.font.color.rgb = WHITE
        p.font.name = '맑은 고딕'

        if subtitle_text:
            p2 = tf.add_paragraph()
            p2.text = subtitle_text
            p2.font.size = Pt(13)
            p2.font.color.rgb = RGBColor(200, 214, 229)
            p2.font.name = '맑은 고딕'

    def add_textbox_bullets(slide, left, top, width, height, items, font_size=16):
        tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
        tf = tb.text_frame
        tf.word_wrap = True
        for idx, item in enumerate(items):
            p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
            p.text = item
            p.font.size = Pt(font_size)
            p.font.name = '맑은 고딕'
            p.font.color.rgb = DARK_GRAY
            p.space_after = Pt(8)
            if item.startswith("■") or item.startswith("▶") or item.startswith("["):
                p.font.bold = True
                p.font.color.rgb = NAVY

    # Slide 1: 표지
    s1 = prs.slides.add_slide(blank_layout)
    bg1 = s1.shapes.add_shape(1, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = NAVY
    bg1.line.fill.background()

    tb1 = s1.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(11.3), Inches(4.2))
    tf1 = tb1.text_frame
    tf1.word_wrap = True

    p = tf1.paragraphs[0]
    p.text = "스마트 신선 물류(사과 운송) IoT 센서 기반\n과육 손상 유발 이상 충격 탐지 및 예측 모델링"
    p.font.size = Pt(36)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p.font.name = '맑은 고딕'
    p.space_after = Pt(24)

    p2 = tf1.add_paragraph()
    p2.text = "비지도 이상 탐지(Isolation Forest, K-Means)와 지도 학습(Decision Tree, Random Forest, MLP) 비교 연구"
    p2.font.size = Pt(20)
    p2.font.color.rgb = RGBColor(255, 204, 102)
    p2.font.name = '맑은 고딕'
    p2.space_after = Pt(40)

    p3 = tf1.add_paragraph()
    p3.text = "• 실험 데이터: 화물 차량 IoT 트래커 주행 시계열 데이터 (10개 주행 세션, 총 4,945건)\n• 분석 방법론: K-Means, Isolation Forest, One-Class SVM, LOF, Decision Tree, Random Forest (GridSearchCV), MLP"
    p3.font.size = Pt(16)
    p3.font.color.rgb = RGBColor(220, 225, 235)
    p3.font.name = '맑은 고딕'

    # Slide 2: 연구 배경 및 문제 정의
    s2 = prs.slides.add_slide(blank_layout)
    add_header(s2, "1. 연구 배경 및 문제 정의", "신선 농산물(사과) 유통 과정에서 발생하는 기계적 충격 및 품질 저하 문제")
    bullets_s2 = [
        "■ 도메인 배경: 사과 운송 중 기계적 충격에 의한 타박상(Bruising) 발생",
        "  • 사과는 수송 중 노면 진동 및 적재 충격에 의해 세포벽이 손상되어 내부 갈변(타박상)이 쉽게 발생함",
        "  • 농산물 물류 표준 연구에 의하면 약 1.8G 이상의 가속도 충격 인가 시 과육 손상률이 급격히 증가함",
        "",
        "■ 기술적 한계 및 2단계 모델링(Two-Stage Modeling) 도입 필요성",
        "  • 운송 과정에서는 개별 화물의 손상 여부를 실시간으로 개방하여 라벨링(Labeling)하는 것이 불가능함",
        "  • 따라서 사전 라벨 없이 다변량 센서 분포로부터 이상 충격을 검출하는 비지도 학습(Unsupervised Learning)과,",
        "    직전 시계열 진동 특성으로부터 위험 충격을 분류하는 지도 학습(Supervised Learning)의 결합이 요구됨",
        "",
        "■ 연구 목표",
        "  1) [1단계 - 비지도 이상 탐지] Isolation Forest, K-Means, One-Class SVM, LOF 기반 이상 충격 검출 성능 비교",
        "  2) [2단계 - 지도 학습 예측] Decision Tree, Random Forest(GridSearchCV), MLP 모델 성능 평가 및 주요 변수 규명"
    ]
    add_textbox_bullets(s2, 0.8, 1.45, 11.7, 5.6, bullets_s2, font_size=16)

    # Slide 3: 수집 데이터셋 및 파생 변수 설계
    s3 = prs.slides.add_slide(blank_layout)
    add_header(s3, "2. 실험 데이터셋 명세 및 특성 공학 (Feature Engineering)", "화물 차량 IoT 트래커(Carrier-C6) 다변량 시계열 센서 데이터 (N = 4,945)")
    bullets_s3 = [
        "■ 수집 데이터셋 개요",
        "  • 수집 기간 및 규모: 2026-10-02 ~ 2026-10-20 (총 10개 운송 세션, 4,945개 시계열 샘플)",
        "  • 수집 디바이스: 화물 운송 트래커 3기 (carrier-c6-01, carrier-c6-02, carrier-c6-04)",
        "",
        "■ 원시 센서 변수(Raw Features) 및 기초 통계량",
        "  • 충격 가속도 (g_force): 평균 1.17G (표준편차 0.35G), 중위수 1.10G, 상위 1% 임계값 2.25G, 최댓값 14.46G",
        "  • 차량 주행 속도 (speed) 및 환경 변수: 정차(0 km/h) ~ 고속 주행 구간 / 평균 온도 27.3°C, 평균 습도 41.0%",
        "  • 손상 위험 충격 정의(Ground Truth): g_force ≥ 1.8G 또는 기기 충격 이벤트 발생 샘플 (총 175건, 3.54%)",
        "",
        "■ 시계열 파생 변수 생성 (Time-Series Feature Engineering)",
        "  • 국소 구간 이동 평균 (g_force_roll_mean3) 및 이동 표준편차 (g_force_roll_std3): 직전 3시점 진동 강도 및 변동성 정량화",
        "  • 속도 변화율 (speed_diff = |v_t - v_{t-1}|): 급가속 및 급제동에 의한 관성 영향 반영",
        "  • 충격 에너지 지수 (impact_energy_idx = g_force × log(1 + speed)): 주행 속도와 가속도의 복합 물리량 산출"
    ]
    add_textbox_bullets(s3, 0.8, 1.45, 11.7, 5.6, bullets_s3, font_size=15)

    # Slide 4: 시계열 충격 분포 시각화
    s4 = prs.slides.add_slide(blank_layout)
    add_header(s4, "3. 탐색적 데이터 분석 (EDA): 전 구간 충격 가속도 추이", "정상 주행 기저 진동(1.0~1.3G) 구간 내 돌발적으로 발생하는 1.8G 이상 이상 충격(175건) 분포")
    if os.path.exists('results/fig1_shock_timeseries.png'):
        s4.shapes.add_picture('results/fig1_shock_timeseries.png', Inches(0.8), Inches(1.4), width=Inches(11.7))

    # Slide 5: 1단계 비지도 이상 탐지 모델 정의 (학술적 정의로 수정)
    s5 = prs.slides.add_slide(blank_layout)
    add_header(s5, "4. [1단계] 비지도 이상 탐지(Unsupervised Anomaly Detection) 모델 정의", "사전 라벨(Label) 없이 다변량 센서 공간의 분할 깊이·군집 중심·결정 경계·국소 밀도를 학습")
    bullets_s5 = [
        "■ ① Isolation Forest (Tree-based Isolation Ensemble)",
        "  • 정의: 무작위 특성(Feature) 및 분할 임계값을 기준으로 이진 탐색 트리(iTree)를 재귀적으로 구성하여 샘플을 고립시키는 기법",
        "  • 원리: 정상 데이터는 루트에서 리프 노드까지의 평균 경로 길이 E(h(x))가 긴 반면, 희소한 이상치는 짧은 경로에서 조기 분리됨",
        "",
        "■ ② K-Means Clustering (Centroid-based Partitioning, 강의 7장 군집 분석)",
        "  • 정의: 클러스터 내 오차제곱합(WCSS)을 최소화하도록 K개의 중심점(Centroid)을 반복 갱신하여 주행 상태를 군집화 (K = 3)",
        "",
        "■ ③ One-Class SVM (Kernel Boundary-based Method)",
        "  • 정의: RBF 커널을 통해 입력 데이터를 고차원 특징 공간으로 사상한 후, 정상 주행 데이터를 감싸는 최적 초평면 경계를 학습",
        "",
        "■ ④ Local Outlier Factor (LOF, Density-based Method)",
        "  • 정의: k-최근접 이웃(k-NN) 기반 국소 도달 가능 밀도(Local Reachability Density)를 산출하여 주변 대비 저밀도 이상치 검출"
    ]
    add_textbox_bullets(s5, 0.8, 1.45, 11.7, 5.6, bullets_s5, font_size=15)

    # Slide 6: 비지도 학습(Isolation Forest) 탐지 시각화
    s6 = prs.slides.add_slide(blank_layout)
    add_header(s6, "5. [1단계 실험 결과] Isolation Forest 이상 충격 탐지 분포", "정차 상태 상·하차 충격(v = 0)과 주행 중 노면 충격(v > 0)의 비지도 분리 (Accuracy 96.62%)")
    if os.path.exists('results/fig2_isolation_forest_scatter.png'):
        s6.shapes.add_picture('results/fig2_isolation_forest_scatter.png', Inches(0.6), Inches(1.4), width=Inches(7.6))
    bullets_s6 = [
        "■ 다변량 분포 내 이상치 검출 결과",
        "• 정상 운송 군집(Inlier): 4,747건 (녹색)",
        "• 이상 충격 검출(Outlier): 198건 (적색 삼각형)",
        "",
        "■ 검출된 이상 충격의 물리적 유형 분류",
        "1) 정차 중 상·하차 충격 (speed = 0 km/h)",
        "   - 적재 및 하역 작업 시 화물 취급 부주의로",
        "     인해 발생하는 수직 낙하·적재 충격 (최대 6.4G)",
        "2) 주행 중 동적 노면 충격 (speed > 10 km/h)",
        "   - 과속방지턱 통과, 도로 요철 및 급제동 시",
        "     발생하는 주행 진동 충격 (최대 14.46G)",
        "",
        "■ 비지도 모델 정량 평가 요약",
        "• Isolation Forest가 Accuracy 96.62%,",
        "  F1-Score 55.23%로 비교 모델 중 최고 성능 기록"
    ]
    add_textbox_bullets(s6, 8.4, 1.5, 4.6, 5.5, bullets_s6, font_size=14)

    # Slide 7: 2단계 강의 연계 지도 학습 모델 정의 (학술적 정의로 수정)
    s7 = prs.slides.add_slide(blank_layout)
    add_header(s7, "6. [2단계] 지도 학습 예측 모델 정의 및 하이퍼파라미터 최적화", "단일 결정 트리(Decision Tree), 배깅 앙상블(Random Forest), 다층 신경망(MLP) 비교 설계")
    bullets_s7 = [
        "■ ① Decision Tree Classifier (CART 알고리즘, 강의 3~4주차)",
        "  • 정의: 지니 불순도(Gini Impurity) 감소량을 극대화하는 방향으로 특징 공간을 재귀적 이진 분할하는 분류 모델 (max_depth = 5)",
        "  • 특성: 의사결정 규칙의 해석 가능성이 우수하나, 단일 트리 구조 특성상 학습 데이터에 대한 분산(Variance)이 큼",
        "",
        "■ ② Random Forest & GridSearchCV (Bagging Ensemble, 강의 4주차)",
        "  • 정의: 부트스트랩 샘플링(Bootstrap)과 무작위 특성 서브셋을 통해 다수의 결정 트리를 병렬 학습·집계하는 배깅 앙상블 모델",
        "  • 최적화: 5-Fold 교차 검증 기반 GridSearchCV 수행 → 최적 파라미터 도출 (n_estimators = 200, max_depth = 5, min_samples_split = 2)",
        "",
        "■ ③ Multi-Layer Perceptron (MLPClassifier, 강의 6주차 딥러닝)",
        "  • 정의: 다층 은닉층(64, 32 노드), ReLU 활성화 함수 및 오차 역전파(Backpropagation)를 통해 비선형 결정 경계를 학습하는 신경망"
    ]
    add_textbox_bullets(s7, 0.8, 1.45, 11.7, 5.6, bullets_s7, font_size=15)

    # Slide 8: 모델 성능 비교 차트
    s8 = prs.slides.add_slide(blank_layout)
    add_header(s8, "7. 모델별 정량적 성능 비교 결과 (1단계 비지도 & 2단계 지도 학습)", "GridSearchCV를 적용한 Random Forest 모델이 Accuracy 97.74%, F1 67.44%, ROC-AUC 98.97% 달성")
    if os.path.exists('results/fig3_model_comparison.png'):
        s8.shapes.add_picture('results/fig3_model_comparison.png', Inches(0.6), Inches(1.45), width=Inches(12.1))

    # Slide 9: 특성 중요도 (Feature Importance) 분석
    s9 = prs.slides.add_slide(blank_layout)
    add_header(s9, "8. 특성 중요도(Feature Importance) 기반 충격 발생 요인 분석", "Random Forest 분석 결과: 직전 구간의 연속 진동 평균 및 변동성 지표가 전체 기여도의 85.3% 차지")
    if os.path.exists('results/fig4_feature_importance.png'):
        s9.shapes.add_picture('results/fig4_feature_importance.png', Inches(0.5), Inches(1.5), width=Inches(7.6))
    bullets_s9 = [
        "■ 주요 변수 기여도 산출 결과 (상위 3개 변수 = 85.3%)",
        "1위: 최근 3구간 이동 평균 진동 (42.1%)",
        "2위: 최근 3구간 진동 표준편차 (25.5%)",
        "3위: 직전 시점 충격 가속도 (17.8%)",
        "",
        "■ 도메인 해석 및 공학적 시사점",
        "• 단순 주행 속도(speed, 2.7%)나 환경 변수보다",
        "  불규칙 노면 진입 시 발생하는 '단기 진동 에너지의",
        "  누적 및 변동성 급증'이 위험 충격의 핵심 선행 지표임",
        "• 따라서 실시간 이동 표준편차 모니터링을 통해",
        "  강한 충격 발생 직전 사전 경보(Early Warning) 구현 가능"
    ]
    add_textbox_bullets(s9, 8.3, 1.5, 4.7, 5.5, bullets_s9, font_size=14)

    # Slide 10: 결론 및 기대 효과
    s10 = prs.slides.add_slide(blank_layout)
    add_header(s10, "9. 결론 및 스마트 콜드체인 적용 기대 효과", "비지도 이상 탐지와 앙상블 예측 모델의 결합을 통한 농산물 유통 품질 관리 고도화")
    bullets_s10 = [
        "■ 연구 결론 요약",
        "  1) 실제 화물 트럭 IoT 센서 데이터(4,945건)를 활용하여 사과 손상 임계치(1.8G) 이상의 위험 충격 특성 규명",
        "  2) [1단계 비지도 탐지] Isolation Forest가 고차원 센서 공간에서 상·하차 충격과 주행 충격을 가장 효과적으로 분리 (Acc 96.62%)",
        "  3) [2단계 지도 예측] GridSearchCV 기반 Random Forest가 단일 Decision Tree 대비 과적합을 억제하며 최고 성능 달성 (AUC 98.97%)",
        "",
        "■ 실무 적용 및 기대 효과",
        "  • 실시간 감속 의사결정 지원: 주행 중 단기 진동 변동성(Rolling Std) 급증 시 운전자에게 감속 경보를 발령하여 과육 타박상 예방",
        "  • 물류 파손 책임 규명: 속도 및 조도 센서 결합 분석을 통해 상·하차 작업 중 파손(v = 0)과 운송 중 파손(v > 0)의 원인 분리",
        "  • 데이터 기반 품질 검수: 운송 세션별 누적 이상 충격 빈도를 정량화하여 도착지 검수 우선순위 산정에 활용"
    ]
    add_textbox_bullets(s10, 0.8, 1.45, 11.7, 5.6, bullets_s10, font_size=16)

    out_path = "사과_운송_이상충격_예측_발표자료.pptx"
    prs.save(out_path)
    print(f"학술/발표 표준 버전 PPTX 재생성 완료: {out_path}")

if __name__ == "__main__":
    create_ppt()
