# 物流 IoT 및 화물 차량 주행 센서 데이터 분석 & 예측 프로젝트

본 저장소는 차량/화물 IoT 트래커(Carrier 디바이스)에서 수집된 시계열 주행 센서 데이터를 바탕으로 탐색적 데이터 분석(EDA) 및 다양한 머신러닝 예측 모델을 수행하기 위한 프로젝트입니다.

---

## 1. 데이터 개요
* **수집 기간**: 2026-10-02 ~ 2026-10-20
* **총 데이터 건수**: 4,945건 (10개 세션 CSV 파일)
* **수집 대상 디바이스**: `carrier-c6-01`, `carrier-c6-02`, `carrier-c6-04`
* **주요 피처(Features)**:
  * `timestamp`: 수집 일시 (초 단위 시계열)
  * `temperature`: 화물칸/차량 온도 (°C)
  * `humidity`: 화물칸/차량 습도 (%)
  * `lux`: 조도 (Lux, 도어 개폐 감지)
  * `g_force`: 가속도 및 충격량 (G-force, 충격/급가감속 감지)
  * `speed`: 차량 주행 속도 (km/h)
  * `lat`, `lng`: GPS 위경도 좌표 (주행 경로/이동 거리 추적)
  * `status`: 상태 이벤트 (대기, 주행, 충격 발생, GPS 수신 상태 등)
  * `run_id`: 개별 주행 세션 식별자

---

## 2. 예측 모델링 및 분석 주제
1. **화물칸 온·습도 시계열 예측 (Time-Series Regression)**
   - 모델: LSTM, GRU, LightGBM (Lag Features), Prophet
2. **이상 충격 및 급가감속/사고 위험 감지 (Anomaly & Classification)**
   - 모델: Isolation Forest, Random Forest, XGBoost
3. **화물칸 비인가 개폐(Door Open) 감지**
   - 모델: 조도(lux) 기반 임계치 및 로지스틱 회귀
4. **ETA (도착 예정 시간) 및 잔여 주행 시간 예측**
   - 모델: CatBoost, XGBoost, MLP Regression
