# NIDS Hyperparameter Optimization Report

Report compiled dynamically on parameter search cross-validation and benchmark improvement deltas.

---

## ⚙️ Search Configuration
- **Optimization Strategy**: `RANDOMIZED SEARCH`
- **Cross-Validation Scheme**: `StratifiedKFold (5-Fold CV)`
- **Search Iteration Limit**: `5 parameter sets`
- **Stratified Training Sample Size**: `50,000 records` (used for parameter evaluation to prevent memory issues)
- **Refitting Dataset**: **FULL Training Partition** (`2,017,889 records`)

---

## 📈 Performance Improvement Profile
Comparison of classification metrics on test partition.

| Model / Estimator | Original F1 | Optimized F1 | F1 Delta | Original Recall | Optimized Recall | Original FPR | Optimized FPR |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **random_forest** | 0.80422 | 0.87927 | **+0.07505** | 0.93117 | 0.93378 | 0.00060 | 0.00019 |
| **extra_trees** | 0.56144 | 0.90053 | **+0.33909** | 0.89433 | 0.91314 | 0.00721 | 0.00013 |
| **catboost** | 0.53847 | 0.65825 | **+0.11978** | 0.93373 | 0.93056 | 0.00401 | 0.00108 |


---

## ⏱️ Training Duration & Compute Profiling
Comparison of fitting execution times on the full training dataset.

| Model / Estimator | Original Fit Time | Optimized Fit Time | Multiplier (Opt/Orig) |
| :--- | :---: | :---: | :---: |
| **random_forest** | `31.06 s` | `17.60 s` | `0.6x` |
| **extra_trees** | `17.68 s` | `19.32 s` | `1.1x` |
| **catboost** | `129.55 s` | `416.11 s` | `3.2x` |


---

## 🛠️ Hyperparameter Value Comparison
Detailed view of changed hyperparameters after tuning.

### Random Forest Parameter Details
| Parameter Key Name | Original Config Value | Optimized Search Value |
| :--- | :---: | :---: |
| **n_estimators** | `30` | `10` |
| **min_samples_split** | `5` | `5` |
| **min_samples_leaf** | `1` | `2` |
| **max_depth** | `15` | `None` |
| **bootstrap** | `True` | `False` |

### Extra Trees Parameter Details
| Parameter Key Name | Original Config Value | Optimized Search Value |
| :--- | :---: | :---: |
| **n_estimators** | `30` | `30` |
| **min_samples_leaf** | `1` | `1` |
| **max_depth** | `15` | `None` |
| **criterion** | `gini` | `gini` |

### Catboost Parameter Details
| Parameter Key Name | Original Config Value | Optimized Search Value |
| :--- | :---: | :---: |
| **learning_rate** | `0.1` | `0.1` |
| **l2_leaf_reg** | `N/A` | `3` |
| **iterations** | `50` | `100` |
| **depth** | `6` | `8` |
| **border_count** | `N/A` | `128` |



---
*Report generated automatically by NIDS Hyperparameter Optimization pipeline runner.*
