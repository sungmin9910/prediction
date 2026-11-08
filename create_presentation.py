import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

def create_ppt():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # 색상 팔레트
    NAVY = RGBColor(27, 42, 74)
    RED_ACCENT = RGBColor(214, 48, 49)
    DARK_GRAY = RGBColor(45, 52, 54)
    LIGHT_BG = RGBColor(245, 247, 250)
    WHITE = RGBColor(255, 255, 255)
    BLUE_ACCENT = RGBColor(9, 132, 227)

    def add_header(slide, title_text, subtitle_text=""):
        # 상단 배너
        banner = slide.shapes.add_shape(1, Inches(0), Inches(0), Inches(13.333), Inches(1.15))
        banner.fill.solid()
        banner.fill.fore_color.rgb = NAVY
        banner.line.fill.background()

        tb = slide.shapes.add_textbox(Inches(0.6), Inches(0.18), Inches(12), Inches(0.85))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title_text
        p.font.size = Pt(26)
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
            p.space_after = Pt(10)
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
    p3.text = "• 활용 데이터: 화물 트럭 IoT 트래커 주행 센서 데이터 (10개 주행 세션, 총 4,945건)\n• 적용 기법: K-Means, Isolation Forest, Decision Tree, Random Forest (GridSearchCV), MLP"
    p3.font.size = Pt(16)
    p3.font.color.rgb = RGBColor(220, 225, 235)
    p3.font.name = '맑은 고딕'

    # Slide 2: 연구 배경 및 문제 정의 (왜 '사과 충격 데이터'인가?)
    s2 = prs.slides.add_slide(blank_layout)
    add_header(s2, "1. 선정 배경 및 문제 정의: 왜 '사과 운송 충격'인가?", "신선 농산물 물류에서 가장 치명적인 품질 저하 요인 = 기계적 충격에 의한 타박상(멍)")
    bullets_s2 = [
        "■ 문제 배경: 사과 유통 손실의 핵심 원인",
        "  • 사과는 수송 중 진동 및 낙하/충격에 의해 과육 내부에 쉽게 타박상(멍, Bruising)이 발생함",
        "  • 농촌진흥청 및 식품공학 연구 기준: 약 1.8G 이상의 가속도 충격 발생 시 상품 가치 급락",
        "",
        "■ 왜 비지도 학습(이상치 탐지) + 지도 학습 예측이 필요한가?",
        "  • 운송 중인 사과 상자를 일일이 열어 멍이 들었는지 실시간으로 확인할 수 없음 (라벨 부족)",
        "  • 따라서 평상시 정상 주행 진동(1.0~1.3G)을 학습하고, 이를 벗어나는 '이상 충격(Anomaly)'을 자동 감지해야 함",
        "  • 나아가 직전 주행 상태(속도 변화, 연속 진동)를 통해 위험 충격을 사전에 분류/예측하는 모델 구축",
        "",
        "■ 프로젝트 핵심 목표",
        "  1) [1단계 - 비지도 학습] Isolation Forest, K-Means 등을 활용한 사과 손상 위험 이상 충격 탐지",
        "  2) [2단계 - 강의 연계 모델] Decision Tree, Random Forest(GridSearchCV), MLP 성능 비교 및 원인 분석"
    ]
    add_textbox_bullets(s2, 0.8, 1.5, 11.7, 5.5, bullets_s2, font_size=17)

    # Slide 3: 수집 데이터셋 소개
    s3 = prs.slides.add_slide(blank_layout)
    add_header(s3, "2. 실험 데이터셋 및 파생 변수(Feature Engineering)", "2026년 10월 실제 화물 차량 IoT 트래커(Carrier-C6) 센서 데이터 4,945건")
    bullets_s3 = [
        "■ 수집 데이터 개요 (총 10개 운송 CSV 파일 통합)",
        "  • 수집 기간: 2026-10-02 ~ 2026-10-20 (총 4,945개 시계열 샘플)",
        "  • 수집 장비: 화물 트래커 3대 (carrier-c6-01, carrier-c6-02, carrier-c6-04)",
        "",
        "■ 주요 센서 변수 및 통계적 특성",
        "  • 충격 가속도 (g_force): 평상시 1.00~1.10G / 상위 1% 2.25G 이상 / 최대 14.46G 기록",
        "  • 주행 속도 (speed): 0 km/h (상·하차 및 정차) ~ 고속 주행 구간",
        "  • 온·습도 / 조도 (temperature, humidity, lux): 평균 27.3°C, 습도 41.0%",
        "  • 사과 손상 위험 이벤트: 1.8G 이상 또는 기기 '충격 발생' 알람 총 175건 (전체의 3.54%)",
        "",
        "■ 사과 물류 맞춤형 파생 변수 (Feature Engineering)",
        "  • 최근 3구간 평균 진동 (g_force_roll_mean3) & 진동 변동성 (g_force_roll_std3): 노면 불안정도 반영",
        "  • 순간 속도 변화량 (speed_diff): 급가속·급브레이크 여부 반영",
        "  • 충격 에너지 지수 (impact_energy_idx): 고속 주행 중 충격일수록 사과 파손 위험 가중"
    ]
    add_textbox_bullets(s3, 0.8, 1.5, 11.7, 5.5, bullets_s3, font_size=16)

    # Slide 4: 시계열 충격 분포 시각화
    s4 = prs.slides.add_slide(blank_layout)
    add_header(s4, "3. 탐색적 데이터 분석 (EDA): 전 구간 충격 가속도 추이", "정상 주행(1.0~1.3G) 구간 속 돌발적으로 발생하는 1.8G 이상 위험 스파이크(175건) 확인")
    if os.path.exists('results/fig1_shock_timeseries.png'):
        s4.shapes.add_picture('results/fig1_shock_timeseries.png', Inches(0.8), Inches(1.4), width=Inches(11.7))

    # Slide 5: 1단계 비지도 학습 모델 원리 소개
    s5 = prs.slides.add_slide(blank_layout)
    add_header(s5, "4. [1단계] 비지도 이상 충격 탐지 모델 원리 (쉬운 이해)", "정답(라벨)을 알려주지 않아도 데이터 스스로 '비정상 충격'을 골라내는 4가지 알고리즘")
    bullets_s5 = [
        "■ ① Isolation Forest (고립 숲 - 메인 추천 모델)",
        "  • 쉬운 원리: 데이터를 무작위로 쪼갤 때, 평범한 데이터(1.0~1.2G)는 빽빽하게 모여 있어 여러 번 쪼개야 분리되지만,",
        "    혼자 튀는 이상 충격(2.0G~14.4G)은 단 한두 번의 칼질(분할)만으로 즉시 고립(Isolate)되는 원리를 이용",
        "",
        "■ ② K-Means 클러스터링 (강의 7장 군집 분석 연계)",
        "  • 쉬운 원리: 비슷한 주행 패턴끼리 K개(3개: 정차/일반주행/위험충격)의 그룹으로 묶어 충격 그룹을 분리",
        "",
        "■ ③ One-Class SVM (단일 클래스 서포트 벡터 머신)",
        "  • 쉬운 원리: 평상시 안전한 주행 데이터들 주변에 '안전 울타리(경계선)'를 치고, 울타리 밖으로 나가면 이상 충격으로 판정",
        "",
        "■ ④ Local Outlier Factor (LOF - 국소 밀도 기반)",
        "  • 쉬운 원리: 내 주변 친구(이웃 데이터)들과 얼마나 떨어져 있는지 밀도를 계산해 혼자 동떨어진 값을 탐지"
    ]
    add_textbox_bullets(s5, 0.8, 1.5, 11.7, 5.5, bullets_s5, font_size=16)

    # Slide 6: 비지도 학습(Isolation Forest) 탐지 시각화
    s6 = prs.slides.add_slide(blank_layout)
    add_header(s6, "5. [1단계 실험 결과] Isolation Forest 이상 충격 탐지 분포", "정차 중 상·하차 충격(속도 0)과 주행 중 도로 요철 충격(고속)을 정확히 분리 (정확도 96.62%)")
    if os.path.exists('results/fig2_isolation_forest_scatter.png'):
        s6.shapes.add_picture('results/fig2_isolation_forest_scatter.png', Inches(0.6), Inches(1.4), width=Inches(7.6))
    bullets_s6 = [
        "■ 그래프 핵심 해석 포인트",
        "• 초록색 점: 안전한 정상 운송 구간 (4,747건)",
        "• 빨간색 삼각형: 모델이 찾아낸 위험 이상치 (198건)",
        "",
        "■ 발견된 2가지 사과 파손 위험 패턴",
        "1) 상·하차 적재 충격 (속도 = 0 km/h 부근)",
        "   - 트럭이 멈춰 있을 때 사과 상자를 던지거나",
        "     내려놓으며 발생한 강한 충격 (최대 6.4G)",
        "2) 도로 주행 충격 (속도 10~80 km/h 구간)",
        "   - 과속방지턱 미감속, 포트홀 통과 시 발생한",
        "     주행 충격 (최대 14.46G)",
        "",
        "■ 비지도 모델 비교 결과",
        "• Isolation Forest가 정확도 96.62%,",
        "  F1-Score 55.23%로 4개 비지도 모델 중 1위 달성"
    ]
    add_textbox_bullets(s6, 8.4, 1.5, 4.6, 5.5, bullets_s6, font_size=14)

    # Slide 7: 2단계 강의 연계 지도 학습 모델 및 GridSearchCV
    s7 = prs.slides.add_slide(blank_layout)
    add_header(s7, "6. [2단계] 강의 연계 예측 모델링 (3~6주차 수업 알고리즘 적용)", "수업에서 배운 Decision Tree, Random Forest(GridSearchCV), MLP 신경망 비교 실험")
    bullets_s7 = [
        "■ ① Decision Tree (의사결정나무 - 3~4주차 강의)",
        "  • 스무고개처럼 '최근 3초 평균 진동이 큰가?', '속도 변화가 심한가?' 질문을 던져 위험 여부를 분류",
        "  • 장점: 해석이 매우 직관적임 / 단점: 단일 나무 모델이라 과적합(Overfitting) 위험 존재",
        "",
        "■ ② Random Forest + GridSearchCV (랜덤 포레스트 - 4주차 핵심 실습)",
        "  • 수백 개의 의사결정나무를 모아 다수결 투표(Ensemble Bagging)로 예측하는 강력한 모델",
        "  • 수업 실습(RF_gridsearch.ipynb) 그대로 5-Fold 교차검증 GridSearchCV를 적용하여 최적 파라미터 탐색",
        "  • 도출된 최적 파라미터: n_estimators=200 (나무 200그루), max_depth=5, min_samples_split=2",
        "",
        "■ ③ MLP (다층 퍼셉트론 딥러닝 - 6주차 강의)",
        "  • 입력층 → 은닉층(64, 32 노드) → 출력층 구조와 역전파(Backpropagation) 학습을 통한 비선형 신경망 분류"
    ]
    add_textbox_bullets(s7, 0.8, 1.5, 11.7, 5.5, bullets_s7, font_size=16)

    # Slide 8: 모델 성능 비교 차트
    s8 = prs.slides.add_slide(blank_layout)
    add_header(s8, "7. 전체 실험 결과 비교: 비지도(1단계) & 지도 학습(2단계)", "Random Forest + GridSearchCV 모델이 정확도 97.74%, F1 67.44%, AUC 98.97%로 최고 성능 달성")
    if os.path.exists('results/fig3_model_comparison.png'):
        s8.shapes.add_picture('results/fig3_model_comparison.png', Inches(0.6), Inches(1.45), width=Inches(12.1))

    # Slide 9: 특성 중요도 (Feature Importance) 분석
    s9 = prs.slides.add_slide(blank_layout)
    add_header(s9, "8. 사과 충격 발생의 핵심 원인은? (Feature Importance)", "Random Forest 분석 결과: '연속 진동 추이(평균·변동성)'와 '직전 시점 충격'이 85% 이상 결정!")
    if os.path.exists('results/fig4_feature_importance.png'):
        s9.shapes.add_picture('results/fig4_feature_importance.png', Inches(0.5), Inches(1.5), width=Inches(7.6))
    bullets_s9 = [
        "■ 변수 중요도 TOP 3 (합계 85.3%)",
        "1위: 최근 3구간 평균 진동 (42.1%)",
        "2위: 최근 3구간 진동 변동성 (25.5%)",
        "3위: 직전 시점 충격량 (17.8%)",
        "",
        "■ 실무적 인사이트 (발표 핵심 강조점)",
        "• 단순 '현재 주행 속도(2.7%)' 자체보다,",
        "  불안정한 노면에 진입했을 때 나타나는",
        "  '연속적인 진동 흔들림(Rolling Mean/Std)'이",
        "  사과 파손 충격의 가장 강력한 전조 증상임!",
        "• 즉, 진동 변동성이 커지는 순간 운전자에게",
        "  감속 경고를 주면 사과 타박상을 예방 가능!"
    ]
    add_textbox_bullets(s9, 8.3, 1.5, 4.7, 5.5, bullets_s9, font_size=14)

    # Slide 10: 결론 및 기대 효과
    s10 = prs.slides.add_slide(blank_layout)
    add_header(s10, "9. 결론 및 스마트 신선 물류 기대 효과", "강의 이론(K-Means, Tree, RF+GridSearch, MLP)을 실제 IoT 물류 데이터에 성공적으로 구현")
    bullets_s10 = [
        "■ 연구 요약",
        "  1) 화물 트럭 IoT 센서 데이터(4,945건)에서 사과 상품성을 훼손하는 이상 충격(175건, 3.54%) 규명",
        "  2) [비지도 탐지] 라벨이 없는 환경에서 Isolation Forest가 정확도 96.62%로 상·하차 및 도로 충격 분리",
        "  3) [지도 예측] 강의 핵심 모델 비교 결과, GridSearchCV로 최적화한 Random Forest가 최고 종합 성능(Acc 97.74%, F1 67.44%) 입증",
        "",
        "■ 기대 효과 및 활용 방안",
        "  • 실시간 감속 알림: 주행 중 3초 진동 변동성이 급증할 때 트럭 기사에게 사전 경고하여 사과 멍 발생 예방",
        "  • 책임 소재 명확화: 상·하차 충격(속도=0)과 운행 중 충격(속도>0)을 구분하여 물류 품질 관리 고도화",
        "  • 스마트 콜드체인 등급제: 운송 완료 후 상자별 '누적 충격 위험 점수'를 계산해 출하 검수 효율화"
    ]
    add_textbox_bullets(s10, 0.8, 1.5, 11.7, 5.5, bullets_s10, font_size=17)

    out_path = "사과_운송_이상충격_예측_발표자료.pptx"
    prs.save(out_path)
    print(f"PPTX 생성 완료: {out_path}")

if __name__ == "__main__":
    create_ppt()
