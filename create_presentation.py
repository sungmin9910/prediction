import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

def create_ppt():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

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
        p.font.size = Pt(24)
        p.font.bold = True
        p.font.color.rgb = WHITE
        p.font.name = '맑은 고딕'

        if subtitle_text:
            p2 = tf.add_paragraph()
            p2.text = subtitle_text
            p2.font.size = Pt(13)
            p2.font.color.rgb = RGBColor(200, 214, 229)
            p2.font.name = '맑은 고딕'

    def add_textbox_bullets(slide, left, top, width, height, items, font_size=15.5):
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
    p.text = "스마트 신선 물류 IoT 센서 기반\n누적 충격량(Cumulative Shock) 분석 및 사과 품질 상태 예측"
    p.font.size = Pt(35)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p.font.name = '맑은 고딕'
    p.space_after = Pt(24)

    p2 = tf1.add_paragraph()
    p2.text = "비지도 피로·이상 탐지(K-Means, Isolation Forest)와 지도 학습(Decision Tree, Random Forest, MLP) 비교 연구"
    p2.font.size = Pt(19.5)
    p2.font.color.rgb = RGBColor(255, 204, 102)
    p2.font.name = '맑은 고딕'
    p2.space_after = Pt(40)

    p3 = tf1.add_paragraph()
    p3.text = "• 실험 데이터: 화물 차량 IoT 트래커 주행 시계열 센서 데이터 (10개 운행 세션, 총 4,945건)\n• 예측 타깃: 누적 충격 피로도에 따른 사과 품질 3단계 상태 (Grade A 정상 / Grade B 미세타박 주의 / Grade C 파손 위험)"
    p3.font.size = Pt(15.5)
    p3.font.color.rgb = RGBColor(220, 225, 235)
    p3.font.name = '맑은 고딕'

    # Slide 2: 연구 배경 및 문제 정의
    s2 = prs.slides.add_slide(blank_layout)
    add_header(s2, "1. 연구 배경 및 문제 정의: 누적 충격량(Cumulative Shock)과 사과 품질", "단발성 임계 충격(Peak Impact)과 반복 진동에 의한 누적 피로 손상(Cumulative Fatigue Damage) 결합")
    bullets_s2 = [
        "■ 도메인 배경: 사과 운송 중 기계적 손상의 2가지 메커니즘",
        "  1) 순간 최대 충격 (Peak Impact): 상·하차 낙하 및 도로 포트홀 통과 시 1.8G 이상의 강한 충격으로 즉각적 세포벽 파괴 발생",
        "  2) 누적 진동 피로 (Cumulative Shock): 개별 진동이 임계치 미만이더라도 장시간 운송 중 초과 충격량이 누적되면",
        "     팔그렌-마이너 법칙(Palmgren-Miner's Rule)에 의해 과육 조직 피로가 축적되어 내부 갈변(타박상, Bruising) 유발",
        "",
        "■ 기존 물류 관제의 한계점 및 연구 필요성",
        "  • 단순 순간 가속도 임계치 알람만으로는 장시간 불량 노면 주행으로 인한 '누적 피로 손상'을 정량화할 수 없음",
        "  • 따라서 주행 세션별 누적 충격량과 환경 변수를 결합하여 실시간으로 사과의 품질 상태(등급)를 예측하는 모델이 필요함",
        "",
        "■ 연구 목표",
        "  1) [누적 충격 정량화] 10개 운행 세션(4,945건)의 누적 초과 충격량 산출 및 사과 품질 3단계 등급(Grade A / B / C) 정의",
        "  2) [비지도 & 지도 모델링] 4종 비지도 알고리즘과 3종 지도 학습 분류 모델을 통한 사과 품질 상태 예측 성능 검증"
    ]
    add_textbox_bullets(s2, 0.8, 1.45, 11.7, 5.6, bullets_s2, font_size=15.5)

    # Slide 3: 수집 데이터셋 및 누적 충격량 파생 변수 설계
    s3 = prs.slides.add_slide(blank_layout)
    add_header(s3, "2. 데이터셋 명세 및 누적 충격 파생 변수 설계 (Feature Engineering)", "화물 차량 IoT 트래커(Carrier-C6) 다변량 시계열 센서 데이터 (N = 4,945)")
    bullets_s3 = [
        "■ 누적 충격량(Cumulative Shock) 관련 핵심 파생 변수 정의",
        "  • 유효 초과 충격량 (Excess G): 평상시 기저 진동(1.15G)을 초과한 충격분 → ΔG_t = max(0, g_force_t - 1.15)",
        "  • 누적 초과 충격량 (cum_excess_g): 운행 시작부터 시점 t까지의 초과 충격 누적합 → Σ ΔG_i (최대 116.74G 기록)",
        "  • 단위 시간당 충격 축적 속도 (shock_rate): 경과 시간 대비 누적 충격 증가 기울기 (노면 불량도 지표)",
        "  • 단기 진동 추이 (g_force_roll_mean5, g_force_roll_std5) 및 온·습도 환경 변수 (temperature, humidity)",
        "",
        "■ 누적 충격 기반 사과 품질 상태 3단계 등급 정의 (전체 4,945건 분포)",
        "  • Grade A [정상/신선 상태, 2,781건 (56.2%)]: 누적 충격량 < 25G 및 손상지수 < 25 (과육 무결성 유지)",
        "  • Grade B [주의/미세타박 상태, 580건 (11.7%)]: 누적 충격량 25G ~ 65G 또는 일시 충격 발생 (조기 출하 및 선별 필요)",
        "  • Grade C [파손 위험 상태, 1,584건 (32.0%)]: 누적 충격량 ≥ 65G 또는 손상지수 ≥ 60 (심각한 타박상 및 상품성 상실 우려)"
    ]
    add_textbox_bullets(s3, 0.8, 1.45, 11.7, 5.6, bullets_s3, font_size=15)

    # Slide 4: 운행 세션별 누적 충격량 추이 시각화
    s4 = prs.slides.add_slide(blank_layout)
    add_header(s4, "3. 운행 세션별 시간에 따른 누적 충격량 추이 및 사과 상태 변화", "운행 시간(거리)보다 주행 노면 상태에 따라 누적 충격량이 최대 13배 차이 발생 (116.7G vs 8.8G)")
    if os.path.exists('results/fig1_shock_timeseries.png'):
        s4.shapes.add_picture('results/fig1_shock_timeseries.png', Inches(0.8), Inches(1.4), width=Inches(11.7))

    # Slide 5: 1단계 비지도 이상/피로 탐지 모델 정의
    s5 = prs.slides.add_slide(blank_layout)
    add_header(s5, "4. [1단계] 비지도 이상 및 피로 상태 탐지 모델 정의", "사전 라벨 없이 다변량 센서 공간의 군집 중심·분할 깊이·결정 경계·국소 밀도를 학습")
    bullets_s5 = [
        "■ ① K-Means Clustering (Centroid-based Partitioning)",
        "  • 정의: 클러스터 내 오차제곱합(WCSS)을 최소화하도록 K개의 중심점(Centroid)을 반복 갱신하여 주행 및 누적 피로 상태를 군집화 (K = 3)",
        "  • 특징: 누적 충격량 증가에 따라 상태가 단계적으로 전이되는 다변량 분포를 분할하는 데 적합함",
        "",
        "■ ② Isolation Forest (Tree-based Isolation Ensemble)",
        "  • 정의: 무작위 특성 및 분할 임계값을 기준으로 이진 탐색 트리(iTree)를 재귀적으로 구성하여 희소한 이상치를 짧은 경로에서 고립",
        "",
        "■ ③ One-Class SVM (Kernel Boundary-based Method)",
        "  • 정의: RBF 커널을 통해 입력 데이터를 고차원 특징 공간으로 사상한 후, 정상 상태 데이터를 감싸는 최적 초평면 경계를 학습",
        "",
        "■ ④ Local Outlier Factor (LOF, Density-based Method)",
        "  • 정의: k-최근접 이웃(k-NN) 기반 국소 도달 가능 밀도(Local Reachability Density)를 산출하여 주변 대비 저밀도 이상치 검출"
    ]
    add_textbox_bullets(s5, 0.8, 1.45, 11.7, 5.6, bullets_s5, font_size=15)

    # Slide 6: 누적 충격량 vs 순간 충격량 공간에서 사과 상태 분포 시각화
    s6 = prs.slides.add_slide(blank_layout)
    add_header(s6, "5. [1단계 실험 결과] 누적 충격량과 순간 충격량에 따른 사과 상태 분포", "K-Means가 누적 피로 군집을 정확도 88.51%로 분리하며, Isolation Forest는 고강도 스파이크 충격을 포착")
    if os.path.exists('results/fig2_isolation_forest_scatter.png'):
        s6.shapes.add_picture('results/fig2_isolation_forest_scatter.png', Inches(0.5), Inches(1.4), width=Inches(7.7))
    bullets_s6 = [
        "■ 누적 충격(X축) × 순간 충격(Y축) 상태 공간",
        "• 녹색 (Grade A): 정상/신선 상태 (2,781건)",
        "• 황색 (Grade B): 주의/미세타박 상태 (580건)",
        "• 적색 (Grade C): 파손 위험 상태 (1,584건)",
        "",
        "■ 비지도 모델 비교 분석 결과",
        "1) K-Means Clustering (Accuracy 88.51%, F1 83.77%)",
        "   - 누적 충격량이 축적됨에 따라 이동하는",
        "     파손 위험 상태(Grade C) 군집을 가장 정확히 분류",
        "2) Isolation Forest (Accuracy 75.87%, F1 64.92%)",
        "   - 누적 충격과 무관하게 돌발적으로 튀는",
        "     순간 고충격(1.8G~14.46G) 이상치를 집중 검출",
        "",
        "▶ 결론: 군집 기반(누적 피로)과 트리 고립 기반",
        "   (순간 충격)의 상호보완적 특성이 규명됨"
    ]
    add_textbox_bullets(s6, 8.35, 1.45, 4.65, 5.6, bullets_s6, font_size=13.5)

    # Slide 7: 2단계 지도 학습 사과 상태 예측 모델 정의
    s7 = prs.slides.add_slide(blank_layout)
    add_header(s7, "6. [2단계] 지도 학습 기반 사과 품질 상태(3등급) 예측 모델 설계", "직전 시점까지의 누적 충격 추이 및 주행 환경 변수로 향후 사과 품질 상태(Grade A/B/C)를 다중 분류 예측")
    bullets_s7 = [
        "■ ① Decision Tree Classifier (CART 알고리즘)",
        "  • 정의: 지니 불순도(Gini Impurity) 감소량을 극대화하는 방향으로 특징 공간을 재귀적 이진 분할하는 다중 분류 모델 (max_depth = 5)",
        "  • 특징: 누적 충격 임계 규칙의 해석 가능성이 높으나, 단일 트리 구조로 인해 복잡한 경계면에서 일반화 성능 한계 존재",
        "",
        "■ ② Random Forest & GridSearchCV (Bagging Ensemble)",
        "  • 정의: 부트스트랩 샘플링과 무작위 변수 선택을 통해 다수의 결정 트리를 병렬 학습·집계하여 분산을 감소시키는 앙상블 모델",
        "  • 최적화: 5-Fold 교차 검증 기반 GridSearchCV 수행 → 최적 파라미터 도출 (n_estimators = 100, max_depth = 14, min_samples_split = 2)",
        "",
        "■ ③ Multi-Layer Perceptron (MLPClassifier)",
        "  • 정의: 다층 은닉층(64, 32 노드), ReLU 활성화 함수 및 오차 역전파(Backpropagation)를 통해 다변량 센서 간 비선형 관계를 학습"
    ]
    add_textbox_bullets(s7, 0.8, 1.45, 11.7, 5.6, bullets_s7, font_size=15)

    # Slide 8: 모델 성능 비교 차트
    s8 = prs.slides.add_slide(blank_layout)
    add_header(s8, "7. 모델별 정량적 성능 비교 결과 (1단계 비지도 & 2단계 지도 학습)", "2단계 사과 상태 예측에서 Random Forest(98.63%)와 MLP(98.79%)가 매우 우수한 분류 성능 달성")
    if os.path.exists('results/fig3_model_comparison.png'):
        s8.shapes.add_picture('results/fig3_model_comparison.png', Inches(0.6), Inches(1.45), width=Inches(12.1))

    # Slide 9: 특성 중요도 (Feature Importance) 분석
    s9 = prs.slides.add_slide(blank_layout)
    add_header(s9, "8. 특성 중요도(Feature Importance) 기반 사과 상태 결정 요인 분석", "직전 누적 충격량(48.1%)과 충격 축적 속도(20.7%), 온·습도 환경(18.0%)이 사과 품질 상태를 결정")
    if os.path.exists('results/fig4_feature_importance.png'):
        s9.shapes.add_picture('results/fig4_feature_importance.png', Inches(0.5), Inches(1.5), width=Inches(7.6))
    bullets_s9 = [
        "■ 사과 품질 상태 예측 핵심 변수 기여도",
        "1위: 직전 시점 누적 충격량 (48.1%)",
        "2위: 시간당 충격 축적 속도 (20.7%)",
        "3위: 화물칸 습도(9.9%) 및 온도(8.1%) → 합 18.0%",
        "4위: 최근 5구간 평균 진동 및 변동성 → 합 9.6%",
        "",
        "■ 공학적 시사점 및 인사이트",
        "• 사과의 품질 저하는 현재까지 쌓인 '누적 피로도",
        "  (48.1%)'와 현재 노면에서 충격이 쌓이는 '축적 속도",
        "  (20.7%)'가 결합되어 약 69%의 영향력을 발휘함",
        "• 또한 온·습도 환경 변수(18.0%)가 결합되어",
        "  고온 환경에서의 누적 진동이 품질 저하를 가속화함"
    ]
    add_textbox_bullets(s9, 8.3, 1.5, 4.7, 5.5, bullets_s9, font_size=13.8)

    # Slide 10: 결론 및 기대 효과
    s10 = prs.slides.add_slide(blank_layout)
    add_header(s10, "9. 결론 및 스마트 신선 물류 적용 기대 효과", "누적 충격량 기반 실시간 사과 품질 등급 예측을 통한 농산물 유통 손실 최소화")
    bullets_s10 = [
        "■ 연구 결론 요약",
        "  1) 10개 운행 세션 분석 결과, 주행 시간이 길어도 안정 주행 시 누적 충격은 8.8G에 불과한 반면 불량 노면 주행 시 116.7G까지 급증함",
        "  2) [1단계 비지도 탐지] K-Means(Acc 88.51%)는 누적 피로 상태 군집화에, Isolation Forest(Acc 75.87%)는 돌발 고충격 검출에 강점을 보임",
        "  3) [2단계 지도 예측] 누적 충격 추이 및 환경 변수를 통해 향후 사과 상태(3등급)를 예측한 결과 Random Forest(98.63%)와 MLP(98.79%)가 최고 성능 달성",
        "",
        "■ 실무 적용 및 기대 효과",
        "  • 도착지 검수 및 유통 우선순위화: 운송 완료 시 트럭별 최종 사과 예측 등급(Grade A/B/C)에 따라 Grade B는 조기 출하, Grade C는 정밀 검수",
        "  • 실시간 경로 및 주행 제어: 단위 시간당 충격 축적 속도(shock_rate)가 급증하는 구간에서 운전자에게 감속 유도",
        "  • 객관적 품질 보증: 경험적 육안 검수를 넘어 IoT 센서 누적 데이터에 기반한 정량적 신선 농산물 품질 등급제 구현"
    ]
    add_textbox_bullets(s10, 0.8, 1.45, 11.7, 5.6, bullets_s10, font_size=15.5)

    out_path = "사과_운송_이상충격_예측_발표자료.pptx"
    prs.save(out_path)
    print(f"누적 충격량 기반 사과 상태 예측 PPTX 생성 완료: {out_path}")

if __name__ == "__main__":
    create_ppt()
