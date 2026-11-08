# 🍎 스마트 신선 물류(사과 운송) IoT 센서 기반 이상 충격 탐지 및 예측 프로젝트

본 저장소는 화물 트럭 IoT 트래커(`carrier-c6`)에서 수집된 실제 주행 센서 데이터(4,945건)를 바탕으로, **사과 운송 중 과육 타박상(멍)을 유발하는 이상 충격을 비지도 학습으로 탐지**하고, **지도 학습 머신러닝·딥러닝 모델(Decision Tree, Random Forest + GridSearchCV, MLP)로 예측 및 비교 분석**한 프로젝트입니다.

---

## 📁 주요 산출물 및 파일 구성

| 파일 / 폴더명 | 설명 |
| :--- | :--- |
| **[`사과_운송_이상충격_예측_발표자료.pptx`](./사과_운송_이상충격_예측_발표자료.pptx)** | **최종 발표용 파워포인트 슬라이드 (총 10장, 고해상도 차트 4종 삽입 완료)** |
| **[`발표대본_및_쉬운해설_가이드.md`](./발표대본_및_쉬운해설_가이드.md)** | **초보자용 3분 핵심 용어 해설 + 슬라이드별 1:1 발표 대본 + 예상 질문 Q&A** |
| [`analyze_apple_shock.py`](./analyze_apple_shock.py) | 데이터 전처리, 비지도/지도 학습 모델 실험 및 결과 차트 생성 파이썬 스크립트 |
| [`create_presentation.py`](./create_presentation.py) | `python-pptx` 기반 발표 자료(`.pptx`) 자동 생성 스크립트 |
| [`results/`](./results/) | 실험 결과 요약 JSON(`experiment_summary.json`) 및 고해상도 시각화 그래프 4종 |
| [`lecture/`](./lecture/) | 참고 자료 및 실습 주피터 노트북 레퍼런스 |

---

## 📊 핵심 실험 결과 요약 (총 4,945건, 위험 충격 175건 / 3.54%)

### 1단계: 비지도 학습 기반 이상 충격 탐지 (Unsupervised Anomaly Detection)
| 모델명 | 정확도 (Accuracy) | 정밀도 (Precision) | 재현율 (Recall) | F1-Score | 비고 |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Isolation Forest** | **96.62%** | **52.02%** | **58.86%** | **55.23%** | **비지도 모델 중 종합 1위** |
| One-Class SVM | 91.10% | 18.23% | 43.43% | 25.68% | 비선형 경계 기반 |
| Local Outlier Factor (LOF) | 92.94% | 6.06% | 6.86% | 6.43% | 국소 밀도 기반 |
| K-Means Clustering | 96.48% | 52.63% | 5.71% | 10.31% | K=3 군집화 |

### 2단계: 지도 학습 예측 모델 비교 (Supervised Prediction)
| 모델명 | 정확도 (Accuracy) | F1-Score | ROC-AUC | 최적 파라미터 / 구조 |
| :--- | :---: | :---: | :---: | :--- |
| Decision Tree | 97.41% | 60.98% | 95.55% | `max_depth=5` |
| **Random Forest + GridSearchCV** | **97.74%** | **67.44%** | **98.97%** | **`n_estimators=200, max_depth=5, min_samples_split=2`** |
| MLP (Multi-Layer Perceptron) | 97.41% | 64.44% | 99.13% | `hidden_layer_sizes=(64, 32)` |

### 3단계: Random Forest 특성 중요도 (Feature Importance)
1. **최근 3구간 평균 진동 (`g_force_roll_mean3`)**: **42.07%**
2. **최근 3구간 진동 변동성 (`g_force_roll_std3`)**: **25.48%**
3. **직전 시점 충격량 (`g_force_prev1`)**: **17.78%**
4. 화물칸 습도 (`humidity`): 4.48%
5. 화물칸 온도 (`temperature`): 4.26%
6. 순간 속도 변화량 (`speed_diff`): 3.25%
7. 트럭 주행 속도 (`speed`): 2.67%
