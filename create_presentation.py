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

    def add_textbox_bullets(slide, left, top, width, height, items, font_size=14.2, space_after=4.5):
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
        """슬라이드 하단에 모델/변수/용어의 정의를 작고 깔끔하게 정리해 두는 박스입니다."""
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
        p0.font.size = Pt(11.0)
        p0.font.bold = True
        p0.font.color.rgb = GLOSSARY_TITLE
        p0.font.name = '맑은 고딕'
        p0.space_after = Pt(2)

        for term, desc in glossary_items:
            p = tf.add_paragraph()
            p.space_after = Pt(1.2)
            run_term = p.add_run()
            run_term.text = f"• {term}: "
            run_term.font.size = Pt(10.3)
            run_term.font.bold = True
            run_term.font.color.rgb = NAVY
            run_term.font.name = '맑은 고딕'

            run_desc = p.add_run()
            run_desc.text = desc
            run_desc.font.size = Pt(10.3)
            run_desc.font.bold = False
            run_desc.font.color.rgb = DARK_GRAY
            run_desc.font.name = '맑은 고딕'

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
        "■ 학술적 배경: 사과 운송 중 기계적 손상의 2가지 메커니즘 (선행 연구 기반)",
        "  1) 순간 최대 충격 (Peak Impact): 상·하차 낙하 및 포트홀 통과 시 총 가속도 1.8G(순수 동적 가속도 +0.8G) 이상의 충격이 가해지면",
        "     사과 유세포(Parenchyma cell)가 즉각 항복·파괴됨 (Van Zeebroeck et al., 2007; Acıcan et al., 2007)",
        "  2) 누적 진동 피로 (Cumulative Shock): 개별 진동이 1.8G 미만이더라도 장시간 운송 중 기저 진동(1.15G) 초과 충격이 반복 누적되면,",
        "     팔그렌-마이너 기반 과실 피로 손상 모델(Lu & Zhou, 2009)에 의해 과육 세포벽 피로도(D)가 축적되어 내부 갈변(타박상) 유발",
        "",
        "■ 기존 물류 관제의 한계점 및 연구 목표",
        "  • 단순 순간 충격 알람만으로는 장시간 불량 노면 주행으로 인한 '누적 피로 손상(D = Σ n_i / N_i)'을 정량화할 수 없음",
        "  • 선행 논문 임계치와 미국 농무부(USDA) 사과 타박상 등급 표준을 결합해 사과 품질 3단계(Grade A/B/C)를 정량화하고 AI로 예측함"
    ]
    add_textbox_bullets(s2, 0.8, 1.28, 11.7, 4.55, bullets_s2, font_size=14.0, space_after=4.2)
    add_glossary_footer(s2, "📌 핵심 참고문헌(논문) 및 물리 법칙 정의", [
        ("Lu & Zhou (2009) 과실 누적 피로 모델", "금속 피로 법칙인 Palmgren-Miner 법칙(D = Σ n_i/N_i)을 과실 수송 진동에 적용하여, 미세 진동 누적에 따른 타박상 면적 증가를 규명한 논문"),
        ("Van Zeebroeck et al. (2007) & Acıcan et al. (2007)", "Postharvest Biol. Technol. 및 Biosystems Eng. 게재 논문으로, 사과 수송 시 동적 가속도 임계치(+0.15G~+0.8G)와 세포벽 파괴 메커니즘을 규명함")
    ])

    # Slide 3: 데이터셋 기초 분석 및 학술/국제 표준 기반 사과 품질 3단계 분류 결과
    s3 = prs.slides.add_slide(blank_layout)
    add_header(s3, "2. 학술 논문·USDA 표준 기반 사과 등급 기준 및 데이터 분석 결과", "선행 논문 임계치(1.15G/1.8G)와 USDA 사과 타박상 등급 기준을 매핑한 10개 운행 세션(N = 4,945) 분석")
    bullets_s3 = [
        "■ 10개 주행 세션(4,945건) 센서 데이터 기초 분석 결과",
        "  • 순간 충격량(g_force): 평상시 평균 1.14G이나, 포트홀·상하차 충격으로 논문상 세포 파괴 임계치(≥1.8G)가 총 175건(최대 14.46G) 발생함",
        "  • 누적 초과 충격량(cum_excess_g): 안정 주행 세션(truck04, 1,518스텝)은 최종 8.8G에 그친 반면, 불량 노면 세션(truck02, 504스텝)은",
        "    116.74G까지 누적되어 도로 상태에 따라 누적 충격량이 최대 13.3배 차이를 보임",
        "",
        "■ USDA 사과 등급 표준 및 Lu & Zhou(2009) 피로 손상도(D) 기반 3단계 상태 분류 결과",
        "  • Grade A [정상/신선 (USDA Extra Fancy 상당) → 2,781건 (56.24%)]: 피로 손상지수 < 25% & 누적 충격 < 25G (타박상 직경 < 12.7mm 무결점)",
        "  • Grade B [미세타박 주의 (USDA Fancy / No.1 상당) → 580건 (11.73%)]: 손상지수 25~60% 또는 누적 25~65G (타박상 12.7~15.9mm, 조기출하 대상)",
        "  • Grade C [파손 위험 (USDA Culled 등급 외 상당) → 1,584건 (32.03%)]: 손상지수 ≥ 60% 또는 누적 ≥ 65G (타박상 > 15.9mm 심각한 갈변 위험)"
    ]
    add_textbox_bullets(s3, 0.8, 1.28, 11.7, 4.55, bullets_s3, font_size=13.8, space_after=4.2)
    add_glossary_footer(s3, "📌 논문 기반 임계치(1.15G / 1.8G) 및 USDA 등급 매핑 정의", [
        ("기저 진동(1.15G) 및 순간 임계 충격(1.8G) 근거", "정지 중력(1.0G) 상태에서 탄성 한계 이내의 무해 진동(+0.15G → 1.15G)을 초과한 충격만 적분하며, 단발성 세포 항복 임계치는 +0.8G(총 1.8G)를 적용함"),
        ("USDA 사과 타박상 등급 표준 (Agricultural Marketing Service)", "미국 농무부 표준은 타박상 직경·깊이에 따라 Extra Fancy(직경 <12.7mm), Fancy/No.1(12.7~15.9mm), Culled(>15.9mm 상품성 상실)로 등급을 구분함")
    ])

    # Slide 4: 운행 세션별 누적 충격량 추이 시각화
    s4 = prs.slides.add_slide(blank_layout)
    add_header(s4, "3. 운행 세션별 시간에 따른 누적 충격량 추이 및 사과 상태 변화", "운행 시간(거리)보다 주행 노면 상태에 따라 누적 충격량이 최대 13.3배 차이 발생 (116.7G vs 8.8G)")
    if os.path.exists('results/fig1_shock_timeseries.png'):
        s4.shapes.add_picture('results/fig1_shock_timeseries.png', Inches(2.35), Inches(1.25), height=Inches(4.55))
    add_glossary_footer(s4, "📌 시계열 차트 주요 지표 및 축 정의", [
        ("운행 경과 스텝 (Time Steps, 가로축)", "IoT 센서가 5초 주기로 데이터를 1회 측정·기록하는 시간 단위로, 가로축이 길수록 장시간(장거리) 주행한 트럭 세션을 의미함"),
        ("곡선 기울기(충격 축적 속도)와 배경 등급 구간", "선이 가파를수록(빨간선 truck02) 짧은 시간 내 불량 노면에서 진동이 집중 누적됨을 뜻하며, 배경 색상은 누적 25G(주의)·65G(위험) 등급 전환 기준선임")
    ])

    # Slide 5: 1단계 비지도 모델 적용 실험 결과 (정의는 하단 박스에 작게 배치, 본문은 실험 결과 중심!)
    s5 = prs.slides.add_slide(blank_layout)
    add_header(s5, "4. [1단계 실험 결과] 비지도 학습 모델 4종 적용 및 탐지 성능 분석", "사전 라벨 없이 센서 데이터만으로 파손 위험 구간(Grade C) 및 고충격 이상 상태를 탐지한 결과 비교")
    bullets_s5 = [
        "■ ① K-Means Clustering (K = 3) 적용 결과 → [탐지 성능 1위] 정확도 88.51% | 정밀도 81.44% | 재현율 86.24% | F1 83.77%",
        "  • 주행 시간이 흐르며 누적 충격량이 증가함에 따라 사과 상태가 3단계(정상→주의→위험) 영역으로 뚜렷하게 이동하기 때문에,",
        "    3개 중심점(Centroid)으로 상태 공간을 분할한 K-Means가 파손 위험(Grade C) 군집을 86.24%의 높은 재현율로 가장 정확히 포착함",
        "",
        "■ ② Isolation Forest (n_estimators = 200) 적용 결과 → [탐지 성능 2위] 정확도 75.87% | 정밀도 64.90% | 재현율 64.94% | F1 64.92%",
        "  • 연속적인 누적 피로 군집 전체를 묶는 정확도는 K-Means보다 낮았으나, 누적 충격량과 무관하게 포트홀·낙하로 인해",
        "    순간적으로 치솟는 1.8G ~ 14.46G 돌발 스파이크 충격(175건)을 짧은 트리 경로에서 집중 검출하는 데 강점을 보임",
        "",
        "■ ③ One-Class SVM (정확도 67.00%, F1 52.00%) 및 ④ LOF (정확도 56.18%, F1 36.28%) 적용 한계 분석",
        "  • One-Class SVM은 정상(Grade A)에서 주의·위험으로 서서히 전이되는 연속적 누적 피로 경계면에서 오분류가 다수 발생함",
        "  • LOF는 파손 위험 구간(Grade C, 1,584건) 데이터들이 서로 촘촘히 밀집해 있어 이를 '정상 고밀도 구간'으로 오인하며 탐지율이 크게 하락함"
    ]
    add_textbox_bullets(s5, 0.8, 1.28, 11.7, 4.55, bullets_s5, font_size=13.8, space_after=4)
    add_glossary_footer(s5, "📌 [참고] 1단계 비지도 학습 모델 4종 핵심 알고리즘 정의", [
        ("K-Means & Isolation Forest 정의", "K-Means는 군집 내 오차제곱합(WCSS)을 최소화하도록 K개 중심점으로 데이터를 묶는 군집화 기법이며, Isolation Forest는 무작위 이진 분할 트리(iTree)로 희소 이상치를 고립시키는 기법임"),
        ("One-Class SVM & LOF 정의", "One-Class SVM은 RBF 커널 고차원 공간에서 정상 데이터 경계(초평면)를 학습하는 기법이며, LOF는 k-최근접 이웃과의 국소 밀도(LRD)를 비교해 저밀도 외톨이를 찾는 기법임")
    ])

    # Slide 6: 정리된 누적 충격량 vs 순간 충격량 산점도 시각화 및 해석
    s6 = prs.slides.add_slide(blank_layout)
    add_header(s6, "5. [1단계 시각화] 누적 충격량과 순간 충격량에 따른 사과 상태 분포", "K-Means 중심점(★)은 가로축 누적 피로 단계를 분리하고, Isolation Forest(○/▲)는 세로축 돌발 스파이크를 포착")
    if os.path.exists('results/fig2_isolation_forest_scatter.png'):
        s6.shapes.add_picture('results/fig2_isolation_forest_scatter.png', Inches(0.50), Inches(1.26), height=Inches(4.55))
    bullets_s6 = [
        "■ 상태 공간(X: 누적 충격, Y: 순간 충격) 핵심 패턴",
        "• 녹색 구간(Grade A): 누적 < 25G 정상 (2,781건)",
        "• 황색 구간(Grade B): 누적 25~65G 주의 (580건)",
        "• 적색 구간(Grade C): 누적 ≥ 65G 위험 (1,584건)",
        "",
        "■ 그래프에서 확인된 두 모델의 상호보완적 역할",
        "1) K-Means 군집 중심점 (노란 별표 ★ 3곳)",
        "   - 가로축(누적 충격량) 증가에 따라 3개 중심점이",
        "     나란히 배치되어 누적 피로 등급을 88.5%로 분리",
        "2) Isolation Forest 고충격 포착 (남색 원 ○ / 삼각형 ▲)",
        "   - 가로축 위치와 상관없이 1.8G 임계선 위로 튀는",
        "     돌발 순간 충격(최대 14.46G)을 빠짐없이 검출",
        "",
        "▶ 실무 시사점: 누적 피로 관제(K-Means)와 실시간",
        "   낙하·포트홀 경보(Isolation Forest) 결합이 최적임"
    ]
    add_textbox_bullets(s6, 8.55, 1.28, 4.35, 4.55, bullets_s6, font_size=12.8, space_after=3.2)
    add_glossary_footer(s6, "📌 차트 마커 표기 및 평가 지표 정의", [
        ("군집 중심점 (★ Centroid) & 극단 스파이크 (▲)", "★은 K-Means가 찾은 3개 그룹의 평균 중심 좌표이며, ▲은 차트 가독성을 위해 상단(3.55G)에 모아 표시한 3.8G~14.46G 초강력 낙하·포트홀 충격(9건)임"),
        ("Accuracy (정확도) & F1-Score 정의", "Accuracy는 전체 4,945건 중 실제 위험 여부를 맞힌 비율이며, F1-Score는 정밀도(오경보 방지)와 재현율(위험 상태 놓침 방지)의 조화평균 지표임")
    ])

    # Slide 7: 2단계 지도 학습 모델 적용 실험 결과 (정의는 하단 박스에 작게 배치, 본문은 실험 결과 중심!)
    s7 = prs.slides.add_slide(blank_layout)
    add_header(s7, "6. [2단계 실험 결과] 지도 학습 모델 3종을 통한 향후 사과 등급 예측", "직전 시점(t-5) 누적 충격 추이 및 온·습도 변수(8종)로 미래(t+10) 사과 품질 3등급을 예측한 실험 결과")
    bullets_s7 = [
        "■ ① Decision Tree (max_depth = 5) 적용 결과 → 분류 정확도 97.41% | Macro F1 95.34% | ROC-AUC 97.93%",
        "  • 직전 누적 충격량과 충격 축적 속도의 임계 규칙만으로 97.41%의 높은 베이스라인 정확도를 달성했으나,",
        "    단일 트리의 수직/수평 분할 한계로 인해 샘플 수가 적은 Grade B(주의 등급, 11.7%) 전이 경계면에서 일부 오분류(2.59%)가 발생함",
        "",
        "■ ② Random Forest + GridSearchCV 적용 결과 → 분류 정확도 98.63% | Macro F1 97.52% | ROC-AUC 99.61%",
        "  • 5-Fold 교차 검증으로 최적 파라미터(n_estimators=100, max_depth=14, min_samples_split=2)를 적용한 결과,",
        "    단일 결정 트리 대비 오분류율을 47% 감소(2.59% → 1.37%)시키며 온·습도와 진동 변동성이 결합된 복합 경계를 정교하게 분류함",
        "",
        "■ ③ Multi-Layer Perceptron (MLP, 은닉층 64-32) 적용 결과 → [예측 1위] 분류 정확도 98.79% | Macro F1 97.83% | ROC-AUC 99.62%",
        "  • 스케일링된 8개 다변량 센서 변수 간의 연속적·비선형적 상호작용을 학습하여 전체 모델 중 최고 예측 성능(정확도 98.79%)을 기록함"
    ]
    add_textbox_bullets(s7, 0.8, 1.28, 11.7, 4.55, bullets_s7, font_size=13.8, space_after=4.2)
    add_glossary_footer(s7, "📌 [참고] 2단계 지도 학습 모델 3종 및 최적화 기법 정의", [
        ("Decision Tree & Random Forest 정의", "Decision Tree는 지니 불순도(혼잡도)가 가장 크게 감소하는 기준으로 데이터를 이진 분할하는 트리 모델이며, Random Forest는 부트스트랩 샘플로 다수의 트리를 병렬 학습·투표(배깅)하는 앙상블 모델임"),
        ("5-Fold GridSearchCV & MLP 신경망 정의", "GridSearchCV는 데이터를 5등분 교차 검증해 최적 하이퍼파라미터 조합을 찾는 기법이며, MLP는 다층 은닉층과 ReLU 활성화 함수·오차 역전파를 통해 비선형 관계를 학습하는 인공신경망임")
    ])

    # Slide 8: 모델 성능 비교 차트
    s8 = prs.slides.add_slide(blank_layout)
    add_header(s8, "7. 전체 모델 정량적 성능 종합 비교 (1단계 비지도 & 2단계 지도 학습)", "1단계 비지도 군집화에서는 K-Means(88.51%), 2단계 상태 예측에서는 Random Forest(98.63%)·MLP(98.79%)가 최고 성능 달성")
    if os.path.exists('results/fig3_model_comparison.png'):
        s8.shapes.add_picture('results/fig3_model_comparison.png', Inches(1.45), Inches(1.26), height=Inches(4.52))
    add_glossary_footer(s8, "📌 다중 분류 평가 지표 (Macro F1 & ROC-AUC) 정의", [
        ("Macro F1-Score (매크로 F1 점수)", "등급별 데이터 개수 차이(Grade A 56%, B 12%, C 32%)에 상관없이 소수 등급인 Grade B까지 동등한 비중(1:1:1)으로 평균 내어 모델을 엄격히 평가한 지표"),
        ("ROC-AUC (Area Under the ROC Curve)", "모델이 3개 사과 등급을 얼마나 확실한 확률 차이로 구분해 내는지를 나타내는 종합 변별력 지표로, 100%(1.0)에 가까울수록 완벽한 분류 성능을 뜻함")
    ])

    # Slide 9: 특성 중요도 (Feature Importance) 분석
    s9 = prs.slides.add_slide(blank_layout)
    add_header(s9, "8. 특성 중요도(Feature Importance) 기반 사과 상태 결정 요인 분석", "직전 누적 충격량(48.1%)과 충격 축적 속도(20.7%), 온·습도 환경(18.0%)이 향후 사과 품질 상태를 결정")
    if os.path.exists('results/fig4_feature_importance.png'):
        s9.shapes.add_picture('results/fig4_feature_importance.png', Inches(0.55), Inches(1.34), height=Inches(4.25))
    bullets_s9 = [
        "■ 사과 품질 상태 예측 핵심 변수 기여도 결과",
        "1위: 직전 시점 누적 충격량 (48.10%)",
        "2위: 시간당 충격 축적 속도 (20.74%)",
        "3위: 화물칸 습도(9.94%) 및 온도(8.06%) → 합 18.00%",
        "4위: 최근 5구간 평균 진동 및 변동성 → 합 9.63%",
        "5위: 주행 속도(2.55%) 및 순간 가감속(0.98%) → 합 3.53%",
        "",
        "■ 실험 결과에 따른 공학적 인사이트",
        "• 향후 사과의 품질은 현재까지 쌓인 '누적 피로도(48.1%)'와",
        "  현재 노면의 '충격 축적 속도(20.7%)'가 68.8%를 좌우함",
        "• 단순 차량 속도(3.5%)보다 화물칸 온·습도(18.0%)가",
        "  5배 이상 중요하여 냉장·방진 통합 관제의 필요성 입증"
    ]
    add_textbox_bullets(s9, 8.40, 1.32, 4.50, 4.50, bullets_s9, font_size=13.0, space_after=3.8)
    add_glossary_footer(s9, "📌 특성 중요도 산출 원리 및 시차 변수(Lag) 설계 정의", [
        ("특성 중요도 (Feature Importance) 정의", "Random Forest 내 100개의 결정 트리가 사과 등급을 분할할 때, 각 센서 변수가 지니 불순도를 감소시키는 데 기여한 총량을 100% 비중으로 환산한 지표"),
        ("시차 변수 (prev_cum_g_lag5) 및 데이터 누수 방지", "정답을 미리 보고 예측하는 오류(Data Leakage)를 차단하기 위해, 과거 시점(t-5)까지의 누적 충격 추이만으로 미래 시점(t+10)의 사과 등급을 예측하도록 분리한 변수")
    ])

    # Slide 10: 결론 및 기대 효과
    s10 = prs.slides.add_slide(blank_layout)
    add_header(s10, "9. 결론 및 스마트 신선 물류 적용 기대 효과", "누적 충격량 기반 실시간 사과 품질 등급 예측을 통한 농산물 유통 손실 최소화")
    bullets_s10 = [
        "■ 연구 결론 요약",
        "  1) 10개 운행 세션 분석 결과, 주행 시간이 길어도 안정 주행 시 누적 충격은 8.8G에 불과한 반면 불량 노면 주행 시 116.7G까지 급증함",
        "  2) [1단계 비지도 탐지 결과] K-Means(Acc 88.51%)는 누적 피로 상태 군집화에, Isolation Forest(Acc 75.87%)는 돌발 고충격 검출에 강점을 보임",
        "  3) [2단계 지도 예측 결과] 누적 충격 추이 및 환경 변수로 향후 사과 상태(3등급)를 예측한 결과 Random Forest(98.63%)와 MLP(98.79%)가 최고 성능 달성",
        "",
        "■ 실무 적용 및 기대 효과",
        "  • 도착지 검수 및 유통 우선순위화: 운송 완료 시 트럭별 최종 사과 예측 등급(Grade A/B/C)에 따라 Grade B는 조기 출하, Grade C는 정밀 검수",
        "  • 실시간 경로 및 주행 제어: 단위 시간당 충격 축적 속도(shock_rate)가 급증하는 구간에서 운전자에게 실시간 감속 유도",
        "  • 객관적 품질 보증: 경험적 육안 검수를 넘어 IoT 센서 누적 데이터에 기반한 정량적 신선 농산물 품질 등급제 구현"
    ]
    add_textbox_bullets(s10, 0.8, 1.28, 11.7, 4.55, bullets_s10, font_size=14.2, space_after=4)
    add_glossary_footer(s10, "📌 스마트 신선 물류 실무 용어 정의", [
        ("선제적 품질 관제 (Predictive Quality Control)", "도착 후 상자를 열어 사후 확인하는 방식에서 벗어나, 운송 중 실시간 IoT 누적 데이터와 AI 예측을 통해 파손 위험을 사전에 감지·대응하는 스마트 물류 기술"),
        ("FEFO (First-Expired, First-Out) 출하 전략", "단순 선입선출(FIFO)이 아니라, 누적 충격으로 인해 미세타박 주의(Grade B) 판정을 받아 잔여 상품 수명이 짧아진 화물부터 우선 유통·판매하여 폐기 손실을 줄이는 기법")
    ])

    out_path = "사과_운송_이상충격_예측_발표자료.pptx"
    prs.save(out_path)
    print(f"누적 충격량 기반 사과 상태 예측 PPTX 생성 완료: {out_path}")

if __name__ == "__main__":
    create_ppt()
