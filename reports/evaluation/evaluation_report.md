# NIDS Model Evaluation Report

Comprehensive evaluation of optimized classifiers on the CICIDS2017 test partition.

---

## 📋 Dataset Summary
- **Train Partition**: `2,017,889` rows × `20` features
- **Test Partition**: `504,473` rows × `20` features

---

## 🏆 Recommended Model
> **`extra_trees`** — selected based on highest macro F1, high recall, and lowest FPR.

---

## 📊 Category Leaders
| Category | Best Model |
| :--- | :---: |
| **Best Accuracy** | `extra_trees` |
| **Best Recall** | `lightgbm` |
| **Best Precision** | `extra_trees` |
| **Best F1** | `extra_trees` |
| **Lowest FPR** | `extra_trees` |
| **Lowest Prediction Time** | `random_forest` |
| **Best ROC-AUC** | `lightgbm` |
| **Best MCC** | `extra_trees` |

---

## 📈 Full Metric Comparison (Ranked)
| **Model** | **Accuracy** | **Balanced Accuracy** | **Precision (Macro)** | **Precision (Weighted)** | **Recall (Macro)** | **Recall (Weighted)** | **F1 Score (Macro)** | **F1 Score (Weighted)** | **ROC-AUC (OvR)** | **PR-AUC** | **Matthews Correlation Coefficient** | **Cohen's Kappa** | **False Positive Rate** | **False Negative Rate** | **Specificity** | **Sensitivity** | **Prediction Time (s)** |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **extra_trees** | 0.99870 | 0.91314 | 0.90358 | 0.99879 | 0.91314 | 0.99870 | 0.90053 | 0.99873 | 0.99944 | 0.93697 | 0.99570 | 0.99569 | 0.00013 | 0.08686 | 0.99987 | 0.91314 | 0.89706 |
| **random_forest** | 0.99755 | 0.93378 | 0.86573 | 0.99856 | 0.93378 | 0.99755 | 0.87927 | 0.99798 | 0.99939 | 0.92581 | 0.99191 | 0.99189 | 0.00019 | 0.06622 | 0.99981 | 0.93378 | 0.25652 |
| **lightgbm** | 0.99771 | 0.95367 | 0.79315 | 0.99833 | 0.95367 | 0.99771 | 0.81964 | 0.99792 | 0.99991 | 0.93325 | 0.99244 | 0.99243 | 0.00016 | 0.04633 | 0.99984 | 0.95367 | 3.04994 |
| **xgboost** | 0.99437 | 0.93521 | 0.71516 | 0.99681 | 0.93521 | 0.99437 | 0.75663 | 0.99535 | 0.99988 | 0.89841 | 0.98166 | 0.98152 | 0.00039 | 0.06479 | 0.99961 | 0.93521 | 0.94365 |
| **catboost** | 0.98411 | 0.93056 | 0.61556 | 0.99483 | 0.93056 | 0.98411 | 0.65825 | 0.98887 | 0.99950 | 0.86446 | 0.95040 | 0.94921 | 0.00108 | 0.06944 | 0.99892 | 0.93056 | 0.29487 |


---

## 🔍 Per-Model Strengths & Weaknesses

### extra_trees
**Strengths:**
- Best Accuracy
- Best Precision
- Best F1
- Lowest FPR
- Best MCC
- High intrusion recall (≥ 90%)
- Very low false positive rate (≤ 0.1%)
- Fast inference (< 1 s on full test set)

**Weaknesses:**
- —

### random_forest
**Strengths:**
- Lowest Prediction Time
- High intrusion recall (≥ 90%)
- Very low false positive rate (≤ 0.1%)
- Fast inference (< 1 s on full test set)

**Weaknesses:**
- —

### lightgbm
**Strengths:**
- Best Recall
- Best ROC-AUC
- High intrusion recall (≥ 90%)
- Very low false positive rate (≤ 0.1%)

**Weaknesses:**
- —

### xgboost
**Strengths:**
- High intrusion recall (≥ 90%)
- Very low false positive rate (≤ 0.1%)
- Fast inference (< 1 s on full test set)

**Weaknesses:**
- —

### catboost
**Strengths:**
- High intrusion recall (≥ 90%)
- Fast inference (< 1 s on full test set)

**Weaknesses:**
- Below-par macro F1 (< 0.70)


---

## 📄 Classification Report — extra_trees (Recommended Model)
| Model       | Class                      |   precision |   recall |   f1-score |       support |
|:------------|:---------------------------|------------:|---------:|-----------:|--------------:|
| extra_trees | BENIGN                     |    0.999847 | 0.999056 |   0.999451 | 419297        |
| extra_trees | Bot                        |    0.73374  | 0.923274 |   0.817667 |    391        |
| extra_trees | DDoS                       |    0.99957  | 0.999688 |   0.999629 |  25603        |
| extra_trees | DoS GoldenEye              |    0.995148 | 0.997083 |   0.996115 |   2057        |
| extra_trees | DoS Hulk                   |    0.997805 | 0.999508 |   0.998656 |  34570        |
| extra_trees | DoS Slowhttptest           |    0.987631 | 0.992352 |   0.989986 |   1046        |
| extra_trees | DoS Slowloris              |    0.997209 | 0.995357 |   0.996283 |   1077        |
| extra_trees | FTP-Patator                |    0.999158 | 0.999158 |   0.999158 |   1187        |
| extra_trees | Heartbleed                 |    1        | 1        |   1        |      2        |
| extra_trees | Infiltration               |    1        | 0.571429 |   0.727273 |      7        |
| extra_trees | PortScan                   |    0.990013 | 0.998734 |   0.994354 |  18164        |
| extra_trees | SSH-Patator                |    1        | 1        |   1        |    644        |
| extra_trees | Web Attack – Brute Force   |    0.769841 | 0.659864 |   0.710623 |    294        |
| extra_trees | Web Attack – SQL Injection |    0.666667 | 1        |   0.8      |      4        |
| extra_trees | Web Attack – XSS           |    0.417143 | 0.561538 |   0.478689 |    130        |
| extra_trees | accuracy                   |    0.998704 | 0.998704 |   0.998704 |      0.998704 |
| extra_trees | macro avg                  |    0.903585 | 0.913136 |   0.900525 | 504473        |
| extra_trees | weighted avg               |    0.998795 | 0.998704 |   0.998733 | 504473        |

---

## 📂 Plots Generated
All figures are saved in `reports/evaluation/plots/`.

| Plot | Description |
| :--- | :--- |
| `*_confusion_matrix.png` | Raw confusion matrix per model |
| `*_normalized_confusion_matrix.png` | Row-normalized confusion matrix per model |
| `roc_curve.png` | Macro-average OvR ROC curves (all models) |
| `precision_recall_curve.png` | Macro-average PR curves (all models) |
| `*_feature_importance.png` | Top-20 feature importances per model |
| `*_learning_curve.png` | Training vs. validation F1 score (learning curve) |
| `*_validation_curve.png` | Hyperparameter sensitivity curve |
| `calibration_curve.png` | Probability calibration comparison |
| `model_comparison.png` | Side-by-side metric comparison bar chart |

---
*Report generated automatically by NIDS Model Evaluation pipeline.*
