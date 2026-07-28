# NIDS Preprocessing & Feature Selection Report

Report compiled dynamically on preprocessing pipeline telemetry.

---

## ⚙️ Pipeline Specifications
- **Scaling Method**: `STANDARD`
- **Imbalance Method**: `NONE`
- **Test Partition Size**: `20.0%` (Stratified split)
- **Random Seed Reference**: `42`

---

## 🧹 Dataset Cleaning & Memory Profiling
- **Initial Merged Shape**: `2,522,362 rows` × `79 columns`
- **Memory Footprint (Before)**: `1653.17 MB`
- **Memory Footprint (After)**: `507.11 MB`
- **Memory Reduction**: **`69.32%`** (Major savings due to removal of uninformative/redundant features)

---

## 🏷️ Category Encoding Summary
- **Target Column Encoded**: `Label`
- **String Labels Resolved**: `['BENIGN', 'Bot', 'DDoS', 'DoS GoldenEye', 'DoS Hulk', 'DoS Slowhttptest', 'DoS slowloris', 'FTP-Patator', 'Heartbleed', 'Infiltration', 'PortScan', 'SSH-Patator', 'Web Attack � Brute Force', 'Web Attack � Sql Injection', 'Web Attack � XSS']`
- **Encoded Mappings**: `{"BENIGN": 0, "Bot": 1, "DDoS": 2, "DoS GoldenEye": 3, "DoS Hulk": 4, "DoS Slowhttptest": 5, "DoS slowloris": 6, "FTP-Patator": 7, "Heartbleed": 8, "Infiltration": 9, "PortScan": 10, "SSH-Patator": 11, "Web Attack \ufffd Brute Force": 12, "Web Attack \ufffd Sql Injection": 13, "Web Attack \ufffd XSS": 14}`
- **Feature Encoders Fitted**: `0 categorical column(s) OHE transformed`

---

## 📊 Feature Selection Auditing

### Dropped Features Summary
| Filtering Stage | Dropped Features Count | Dropped Column Names |
| :--- | :---: | :--- |
| **Constant Columns** | `8` | `Bwd PSH Flags, Bwd URG Flags, Fwd Avg Bytes/Bulk, Fwd Avg Packets/Bulk, Fwd Avg Bulk Rate, Bwd Avg Bytes/Bulk, Bwd Avg Packets/Bulk, Bwd Avg Bulk Rate` |
| **Near-Zero Variance** (Var < `0.0001`) | `2` | `Fwd URG Flags, CWE Flag Count` |
| **Duplicate Columns** | `4` | `SYN Flag Count, Fwd Header Length.1, Subflow Fwd Packets, Subflow Bwd Packets` |
| **Multicollinearity** (Pearson r > `0.9`) | `26` | `Total Backward Packets, Total Length of Bwd Packets, Fwd Packet Length Std, Bwd Packet Length Mean, Bwd Packet Length Std, Flow IAT Max, Fwd IAT Total, Fwd IAT Mean, Fwd IAT Std, Fwd IAT Max, Bwd IAT Min, Fwd Packets/s, Max Packet Length, Packet Length Mean, Packet Length Std, Packet Length Variance, ECE Flag Count, Average Packet Size, Avg Fwd Segment Size, Avg Bwd Segment Size, Subflow Fwd Bytes, Subflow Bwd Bytes, Active Min, Idle Mean, Idle Max, Idle Min` |

- **Total Features Evaluated**: `78`
- **Total Features Selected**: **`20`**
- **Selected Feature List**: `Destination Port, Total Length of Fwd Packets, Fwd Packet Length Max, Bwd Packet Length Max, Flow Bytes/s, Flow IAT Std, Fwd IAT Min, Fwd Header Length, Bwd Header Length, Bwd Packets/s, FIN Flag Count, PSH Flag Count, Init_Win_bytes_forward, Init_Win_bytes_backward, act_data_pkt_fwd, min_seg_size_forward, Active Mean, Active Std, Active Max, Idle Std`

### Top Selected Features (Mutual Information Scores & RFE ranks)
The detailed list of all features and rank positions is exported to [selected_features.csv](file:///C:/Users/saifu/Desktop/Network Intrusion Detection/data/processed/selected_features.csv).

---

## ⚖️ Class Imbalance & Resampling Statistics

- **Resampling Method Applied**: `NONE`
- **SMOTE neighborhood reference**: `none`

### Class Distributions Before vs. After Resampling
| Class Label | Encoded Index | Count (Before Balancing) | Count (After Balancing) |
| :--- | :---: | :---: | :---: |
| **BENIGN** | `0` | 1,677,187 | 1,677,187 |
| **Bot** | `1` | 1,562 | 1,562 |
| **DDoS** | `2` | 102,413 | 102,413 |
| **DoS GoldenEye** | `3` | 8,229 | 8,229 |
| **DoS Hulk** | `4` | 138,279 | 138,279 |
| **DoS Slowhttptest** | `5` | 4,182 | 4,182 |
| **DoS slowloris** | `6` | 4,308 | 4,308 |
| **FTP-Patator** | `7` | 4,746 | 4,746 |
| **Heartbleed** | `8` | 9 | 9 |
| **Infiltration** | `9` | 29 | 29 |
| **PortScan** | `10` | 72,655 | 72,655 |
| **SSH-Patator** | `11` | 2,575 | 2,575 |
| **Web Attack � Brute Force** | `12` | 1,176 | 1,176 |
| **Web Attack � Sql Injection** | `13` | 17 | 17 |
| **Web Attack � XSS** | `14` | 522 | 522 |

### Computed Estimator Class Weights
(Calculated from training split proportions if model training uses weights instead of SMOTE resampling)
- `weights`: `{"0": 0.08020926308952629, "1": 86.12415706359369, "2": 1.3135630567733914, "3": 16.347786284279174, "4": 0.9728587372871754, "5": 32.16784632552208, "6": 31.22700402352213, "7": 28.34511869644613, "8": 14947.325925925927, "9": 4638.8252873563215, "10": 1.8515715825935357, "11": 52.24308090614887, "12": 114.39280045351474, "13": 7913.290196078431, "14": 257.7125159642401}`

---
*Report generated automatically by NIDS Preprocessing Pipeline runner.*
