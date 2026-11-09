# 🍎 스마트 신선 물류 IoT 센서 기반 누적 충격량(Cumulative Shock) 분석 및 사과 품질 상태 예측 프로젝트

본 저장소는 화물 트럭 IoT 트래커(`carrier-c6`)에서 수집된 실제 주행 센서 데이터(10개 운행 세션, 총 4,945건)를 바탕으로, **운송 중 축적되는 누적 충격량(Cumulative Shock)에 따라 사과의 품질 상태를 3단계(Grade A 정상 / Grade B 미세타박 주의 / Grade C 파손 위험)로 정량화**하고, **비지도 학습(K-Means, Isolation Forest 등) 및 지도 학습(Decision Tree, Random Forest + GridSearchCV, MLP) 모델로 사과 상태를 탐지·예측**한 프로젝트입니다.

---

## 📁 주요 산출물 및 파일 구성

| 파일 / 폴더명 | 설명 |
| :--- | :--- |
| **[`사과_운송_1단계_비지도학습_발표자료.pptx`](./사과_운송_1단계_비지도학습_발표자료.pptx)** | **[이번 발표용: 1단계 비지도 학습 전담 PPT (총 10장)]** `K-Means`, `Isolation Forest`, `One-Class SVM`, `LOF` 4개 모델별 개별 분석 슬라이드 및 전용 그래프(`stage1_*.png` 5종) 삽입 |
| **[`1단계_발표대본_및_가이드.md`](./1단계_발표대본_및_가이드.md)** | **[이번 발표용: 1단계 전용 대본]** `사과_운송_1단계_비지도학습_발표자료.pptx` 슬라이드 1~10번과 1:1 매칭되는 발표 대본 |
| **[`사과_운송_이상충격_예측_발표자료.pptx`](./사과_운송_이상충격_예측_발표자료.pptx)** | **[다음 발표용: 1단계+2단계 통합 최종 PPT (총 10장)]** 2단계 지도 학습(`Decision Tree`, `Random Forest + GridSearchCV`, `MLP`) 및 특성 중요도까지 포함된 전체 버전 |
| **[`발표대본_및_쉬운해설_가이드.md`](./발표대본_및_쉬운해설_가이드.md)** | **[다음 발표용: 1+2단계 통합 대본]** `사과_운송_이상충격_예측_발표자료.pptx`와 1:1 매칭되는 발표 대본 |
| **[`발표전_완벽공부_기초부터_마스터_가이드.md`](./발표전_완벽공부_기초부터_마스터_가이드.md)** | **기초 지식이 전혀 없어도 15분 만에 물리·머신러닝·수식·차트·예상 Q&A를 마스터하는 완벽 독학서** |
| [`analyze_apple_shock.py`](./analyze_apple_shock.py) | 누적 충격량 산출, 사과 상태 3등급 정의, 비지도/지도 학습 실험 및 차트 생성 스크립트 |
| [`create_stage1_presentation.py`](./create_stage1_presentation.py) | 1단계 비지도 학습 모델별 상세 그래프 5종(`results/stage1_*.png`) 및 1단계 전용 PPT 자동 생성 스크립트 |
| [`create_presentation.py`](./create_presentation.py) | 1+2단계 통합 발표 자료(`.pptx`) 자동 생성 스크립트 |
| [`results/`](./results/) | 실험 결과 요약 JSON(`experiment_summary.json`), 1단계 전용 그래프 5종 및 통합 그래프 4종 |

---

## 📊 핵심 실험 결과 요약 (총 4,945건, 10개 운행 세션)

### 0. 누적 충격량에 따른 사과 품질 3단계 상태 분포 (학술 논문 및 USDA 사과 등급 표준 기반)
* **학술적 근거**:
  * **Van Zeebroeck et al. (2007, *Postharvest Biology and Technology*) & Acıcan et al. (2007, *Biosystems Engineering*)**: 정지 중력(`1.0G`) 대비 탄성 한계 이내의 기저 진동(`+0.15G` $\rightarrow$ 총 가속도 `1.15G`) 초과 충격 적분 및 단발성 세포벽 항복 임계치(`+0.8G` $\rightarrow$ 총 가속도 `1.8G`) 적용
  * **Lu & Zhou (2009, *Trans. CSAE*)**: Palmgren-Miner 선형 누적 피로 손상 이론($D = \sum n_i / N_i$) 기반 과실 수송 진동 누적 손상 지수(`ADI`, 0~100%) 산출
  * **미국 농무부 사과 등급 표준 (USDA Standards for Grades of Apples)**: 타박상 허용 직경 기준에 따른 3단계 상품성 등급 매핑
* 🟢 **Grade A (정상/신선, `USDA Extra Fancy` 상당)**: **2,781건 (56.24%)** — 누적 초과 충격량 `< 25G` 및 피로 손상지수 `< 25%` (타박상 직경 `< 12.7mm` 무결점 수준)
* 🟡 **Grade B (주의/미세타박, `USDA Fancy / No. 1` 상당)**: **580건 (11.73%)** — 누적 초과 충격량 `25G ~ 65G` 또는 손상지수 `25% ~ 60%` 또는 순간충격 `≥ 1.8G` (타박상 직경 `12.7 ~ 15.9mm` 경미 손상 수준)
* 🔴 **Grade C (파손 위험, `USDA Culled` 등급 외 상당)**: **1,584건 (32.03%)** — 누적 초과 충격량 `≥ 65G` 또는 피로 손상지수 `≥ 60%` (타박상 직경 `> 15.9mm` 상품성 상실 우려 수준)

### 1단계: 비지도 학습 기반 이상 충격 및 누적 피로 상태 탐지
| 모델명 | 정확도 (Accuracy) | 정밀도 (Precision) | 재현율 (Recall) | F1-Score | 특성 및 역할 |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **K-Means Clustering** | **88.51%** | **81.44%** | **86.24%** | **83.77%** | **누적 피로 상태 군집 분리 1위 (K=3)** |
| **Isolation Forest** | **75.87%** | **64.90%** | **64.94%** | **64.92%** | **돌발 순간 스파이크 충격(1.8G~14.46G) 검출 특화** |
| One-Class SVM | 67.00% | 52.00% | 52.00% | 52.00% | 비선형 경계 기반 |
| Local Outlier Factor (LOF) | 56.18% | 36.27% | 36.29% | 36.28% | 국소 밀도 기반 |

### 2단계: 지도 학습 기반 향후 사과 품질 상태(3등급) 예측 모델 비교
| 모델명 | 분류 정확도 (Accuracy) | Macro F1-Score | ROC-AUC | 최적 파라미터 / 구조 |
| :--- | :---: | :---: | :---: | :--- |
| Decision Tree | 97.41% | 95.34% | 97.93% | `max_depth=5` |
| **Random Forest + GridSearchCV** | **98.63%** | **97.52%** | **99.61%** | **`n_estimators=100, max_depth=14, min_samples_split=2`** |
| **MLP (Multi-Layer Perceptron)** | **98.79%** | **97.83%** | **99.62%** | **`hidden_layer_sizes=(64, 32)`** |

### 3단계: Random Forest 특성 중요도 (Feature Importance)
1. **직전 시점 누적 충격량 (`prev_cum_g_lag5`)**: **48.10%**
2. **시간당 충격 축적 속도 (`shock_rate`)**: **20.74%**
3. **화물칸 습도 (`humidity`)**: **9.94%**
4. **화물칸 온도 (`temperature`)**: **8.06%**
5. **최근 5구간 평균 진동 (`g_force_roll_mean5`)**: **7.07%**
6. 최근 5구간 진동 변동성 (`g_force_roll_std5`): 2.56%
7. 트럭 주행 속도 (`speed`): 2.55%
8. 순간 속도 변화율 (`speed_diff`): 0.98%
