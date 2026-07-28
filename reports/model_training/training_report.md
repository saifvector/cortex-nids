# NIDS Machine Learning Model Training Report

Report compiled dynamically on model fitting telemetry and classification benchmarks.

---

## 🏆 Best Performing Model
- **Algorithm Selected**: `LIGHTGBM`
- **F1 Score (Macro)**: `0.81964`
- **Recall (Macro)**: `0.95367`
- **False Positive Rate**: `0.00016`
- **Model Storage Reference**: `models/best_model.joblib`

---

## 📊 Model Ranking Summary
Ranked descending by **F1 Score**, then **Recall**, then ascending **False Positive Rate**.

| Algorithm / Classifier | F1 Score (Macro) | Recall (Macro) | False Positive Rate | Accuracy | Precision |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **lightgbm** | 0.81964 | 0.95367 | 0.00016 | 0.99771 | 0.79315 |
| **random_forest** | 0.80422 | 0.93117 | 0.00060 | 0.99138 | 0.80690 |
| **xgboost** | 0.75663 | 0.93521 | 0.00039 | 0.99437 | 0.71516 |
| **decision_tree** | 0.74523 | 0.93477 | 0.00179 | 0.97374 | 0.72265 |
| **extra_trees** | 0.56144 | 0.89433 | 0.00721 | 0.91000 | 0.58270 |
| **catboost** | 0.53847 | 0.93373 | 0.00401 | 0.94112 | 0.49114 |
| **logistic_regression** | 0.27948 | 0.81967 | 0.02603 | 0.61604 | 0.25134 |


---

## ⏱️ Training Duration & System Profiling
Summary of compute times and memory footprint differentials during training.

| Algorithm / Classifier | Training Duration | Prediction Latency | Memory Consumption |
| :--- | :---: | :---: | :---: |
| **lightgbm** | `42.642 s` | `2.911 s` | `6.93 MB` |
| **random_forest** | `31.056 s` | `0.724 s` | `6.45 MB` |
| **xgboost** | `74.986 s` | `0.912 s` | `124.94 MB` |
| **decision_tree** | `30.374 s` | `0.088 s` | `0.26 MB` |
| **extra_trees** | `17.683 s` | `0.859 s` | `1.66 MB` |
| **catboost** | `129.550 s` | `0.243 s` | `1621.30 MB` |
| **logistic_regression** | `91.088 s` | `0.083 s` | `103.10 MB` |


- **Total Execution Time**: `443.60 seconds`

---

## 🌲 Tree-based Classifier Feature Importances
Top 10 relative feature variable importances mapped dynamically across fitted tree estimators.

### Decision Tree Feature Importance
| Rank | Feature Variable Name | Weight Score |
| :---: | :--- | :---: |
| 1 | **Destination Port** | `0.292590` |
| 2 | **Bwd Packet Length Max** | `0.188579` |
| 3 | **Init_Win_bytes_backward** | `0.139469` |
| 4 | **Flow IAT Std** | `0.087377` |
| 5 | **Fwd Packet Length Max** | `0.081376` |
| 6 | **min_seg_size_forward** | `0.050116` |
| 7 | **Bwd Packets/s** | `0.035975` |
| 8 | **Fwd IAT Min** | `0.029716` |
| 9 | **Flow Bytes/s** | `0.027143` |
| 10 | **Active Mean** | `0.024674` |

### Random Forest Feature Importance
| Rank | Feature Variable Name | Weight Score |
| :---: | :--- | :---: |
| 1 | **Destination Port** | `0.129887` |
| 2 | **Bwd Packet Length Max** | `0.096455` |
| 3 | **Init_Win_bytes_backward** | `0.092631` |
| 4 | **Fwd Packet Length Max** | `0.081531` |
| 5 | **Flow IAT Std** | `0.072483` |
| 6 | **Bwd Header Length** | `0.070827` |
| 7 | **Total Length of Fwd Packets** | `0.059212` |
| 8 | **Fwd Header Length** | `0.057759` |
| 9 | **Init_Win_bytes_forward** | `0.054778` |
| 10 | **min_seg_size_forward** | `0.049953` |

### Extra Trees Feature Importance
| Rank | Feature Variable Name | Weight Score |
| :---: | :--- | :---: |
| 1 | **Bwd Packet Length Max** | `0.179915` |
| 2 | **Flow IAT Std** | `0.102665` |
| 3 | **Init_Win_bytes_backward** | `0.095992` |
| 4 | **min_seg_size_forward** | `0.088115` |
| 5 | **Destination Port** | `0.081421` |
| 6 | **Fwd Packet Length Max** | `0.074033` |
| 7 | **PSH Flag Count** | `0.065533` |
| 8 | **Init_Win_bytes_forward** | `0.058334` |
| 9 | **Fwd IAT Min** | `0.040399` |
| 10 | **Idle Std** | `0.030414` |

### Xgboost Feature Importance
| Rank | Feature Variable Name | Weight Score |
| :---: | :--- | :---: |
| 1 | **Destination Port** | `0.123918` |
| 2 | **Bwd Packet Length Max** | `0.087299` |
| 3 | **Active Mean** | `0.086394` |
| 4 | **PSH Flag Count** | `0.084628` |
| 5 | **min_seg_size_forward** | `0.075027` |
| 6 | **Bwd Packets/s** | `0.063775` |
| 7 | **Init_Win_bytes_backward** | `0.057424` |
| 8 | **Flow Bytes/s** | `0.051638` |
| 9 | **Bwd Header Length** | `0.047517` |
| 10 | **act_data_pkt_fwd** | `0.041403` |

### Lightgbm Feature Importance
| Rank | Feature Variable Name | Weight Score |
| :---: | :--- | :---: |
| 1 | **Init_Win_bytes_backward** | `2740.000000` |
| 2 | **Fwd IAT Min** | `2489.000000` |
| 3 | **Init_Win_bytes_forward** | `2378.000000` |
| 4 | **Bwd Packets/s** | `2147.000000` |
| 5 | **Destination Port** | `2039.000000` |
| 6 | **Flow IAT Std** | `1787.000000` |
| 7 | **Flow Bytes/s** | `1415.000000` |
| 8 | **Bwd Packet Length Max** | `1297.000000` |
| 9 | **Fwd Header Length** | `1225.000000` |
| 10 | **Total Length of Fwd Packets** | `1196.000000` |

### Catboost Feature Importance
| Rank | Feature Variable Name | Weight Score |
| :---: | :--- | :---: |
| 1 | **Destination Port** | `13.993134` |
| 2 | **min_seg_size_forward** | `10.396419` |
| 3 | **Init_Win_bytes_backward** | `9.481520` |
| 4 | **Flow Bytes/s** | `8.326132` |
| 5 | **Bwd Packet Length Max** | `7.322319` |
| 6 | **Bwd Packets/s** | `7.164577` |
| 7 | **Init_Win_bytes_forward** | `6.250566` |
| 8 | **Total Length of Fwd Packets** | `6.155367` |
| 9 | **PSH Flag Count** | `5.423542` |
| 10 | **Bwd Header Length** | `5.033673` |



---

## ⚙️ Environment & Package Versions
- **Operating System**: `Windows (10)`
- **Python Version**: `3.11.9`
- **Scikit-Learn Version**: `1.5.1`
- **XGBoost Version**: `2.1.0`
- **LightGBM Version**: `4.5.0`
- **CatBoost Version**: `1.2.5`

---
*Report generated automatically by NIDS Model Training pipeline runner.*
