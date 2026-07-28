#!/usr/bin/env python
"""
Main pipeline execution script for NIDS Data Preprocessing, Feature Selection, and Scaling.
Applies stratified splits, encoding, feature selection, scaling, imbalance corrections,
saves outputs, and generates a preprocessing report markdown.
"""
import sys
import json
import logging
from pathlib import Path

# Add project root to system paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

from src.config.config import ConfigManager
from src.utils.logging import configure_logging, get_logger
from src.utils.utils import ensure_directory, get_absolute_path
from src.split_data import stratified_split
from src.preprocessing import PreprocessingPipeline


def main():
    # 1. Initialize configuration and logging
    config_manager = ConfigManager()
    config_manager.initialize()
    settings = config_manager.settings

    configure_logging(settings)
    logger = get_logger("NIDS.preprocessing_pipeline")

    logger.info("==================================================")
    logger.info("NIDS Preprocessing & Feature Selection Pipeline Run")
    logger.info("==================================================")

    # 2. Resolve Paths
    processed_dir = get_absolute_path(settings.paths.processed_data_dir)
    reports_dir = get_absolute_path("reports")

    ensure_directory(processed_dir)
    ensure_directory(reports_dir)

    merged_data_path = processed_dir / "merged_dataset.csv"
    if not merged_data_path.exists():
        logger.critical("Merged dataset not found at %s. Please run scripts/run_eda.py first.", merged_data_path)
        sys.exit(1)

    target_col = settings.data_preparation.target_column

    # 3. Load merged dataset
    logger.info("Loading merged dataset from: %s", merged_data_path)
    try:
        df = pd.read_csv(merged_data_path, low_memory=False)
        logger.info("Loaded dataset with shape: %s", df.shape)
        
        # Calculate memory footprint before preprocessing
        mem_before_mb = float(df.memory_usage(deep=True).sum() / (1024 * 1024))
        logger.info("Dataset memory footprint: %.2f MB", mem_before_mb)
    except Exception as e:
        logger.critical("Failed to load merged dataset: %s", e, exc_info=True)
        sys.exit(1)

    # 4. Resolve Target Column Case
    # Fallback to case-insensitive target column check
    target_candidates = [col for col in df.columns if col.lower() == target_col.lower()]
    if target_candidates:
        target_col = target_candidates[0]
        logger.info("Resolved target column name to: %s", target_col)
    else:
        logger.critical("Target column '%s' not found in dataset columns: %s", target_col, df.columns.tolist())
        sys.exit(1)

    # 5. Stratified Train/Test Split
    test_size = settings.preprocessing.test_size
    random_state = settings.preprocessing.random_state
    
    try:
        X_train, X_test, y_train, y_test = stratified_split(
            df=df,
            target_column=target_col,
            test_size=test_size,
            random_state=random_state,
            stratify=True
        )
    except Exception as e:
        logger.critical("Failed to split dataset: %s", e, exc_info=True)
        sys.exit(1)

    # Free up memory
    del df

    # 6. Fit and Transform Preprocessing Pipeline
    prep_config = {
        "scaling_method": settings.preprocessing.scaling_method,
        "variance_threshold": settings.preprocessing.variance_threshold,
        "correlation_threshold": settings.preprocessing.correlation_threshold,
        "top_n_mi": settings.preprocessing.top_n_mi,
        "top_n_rfe": settings.preprocessing.top_n_rfe,
        "balancing_method": settings.preprocessing.balancing_method,
        "random_state": settings.preprocessing.random_state
    }

    pipeline = PreprocessingPipeline(config=prep_config)
    try:
        # Fit on train, transform train and test
        X_train_trans, y_train_trans = pipeline.fit_transform(X_train, y_train)
        X_test_trans = pipeline.transform(X_test)
        y_test_trans = pipeline.transform_target(y_test)
    except Exception as e:
        logger.critical("Failed to run preprocessing transformations: %s", e, exc_info=True)
        sys.exit(1)

    # 7. Apply Resampling/Class Imbalance on Training Split
    try:
        X_train_bal, y_train_bal, balance_stats = pipeline.apply_resampling(X_train_trans, y_train_trans)
        
        # Calculate class weights for info (even if resampled)
        class_weights = pipeline.calculate_class_weights(y_train_trans)
    except Exception as e:
        logger.critical("Failed to apply class imbalance correction: %s", e, exc_info=True)
        sys.exit(1)

    # 8. Save Outputs
    try:
        logger.info("Saving transformed datasets to %s...", processed_dir)
        
        # Save CSV files
        X_train_bal.to_csv(processed_dir / "X_train.csv", index=False)
        X_test_trans.to_csv(processed_dir / "X_test.csv", index=False)
        y_train_bal.to_csv(processed_dir / "y_train.csv", index=False)
        y_test_trans.to_csv(processed_dir / "y_test.csv", index=False)
        
        # Save pipeline instance
        pipeline_file = processed_dir / "preprocessing_pipeline.joblib"
        pipeline.save(pipeline_file)

        # Save feature names list JSON
        feature_names_file = processed_dir / "feature_names.json"
        with open(feature_names_file, "w", encoding="utf-8") as f:
            json.dump(pipeline.final_features, f, indent=4)

        # Save selected features details CSV
        summary_df = pipeline.selector.get_selection_summary()
        summary_df.to_csv(processed_dir / "selected_features.csv", index=False)

        logger.info("Transformed outputs saved successfully.")
    except Exception as e:
        logger.critical("Failed to save preprocessing outputs: %s", e, exc_info=True)
        sys.exit(1)

    # 9. Memory Footprint Reduction Analysis
    mem_after_mb = float(
        (X_train_bal.memory_usage(deep=True).sum() +
         X_test_trans.memory_usage(deep=True).sum() +
         y_train_bal.memory_usage(deep=True) +
         y_test_trans.memory_usage(deep=True)) / (1024 * 1024)
    )
    mem_reduction_pct = ((mem_before_mb - mem_after_mb) / mem_before_mb) * 100
    logger.info("Transformed dataset memory footprint: %.2f MB", mem_after_mb)
    logger.info("Memory usage reduction: %.2f%%", mem_reduction_pct)

    # 10. Generate Preprocessing Markdown Report
    report_file = reports_dir / "preprocessing_report.md"
    logger.info("Generating Preprocessing Report: %s...", report_file)
    try:
        # Construct markdown content
        removed_summary = pipeline.selector.removed_features
        
        md_content = f"""# NIDS Preprocessing & Feature Selection Report

Report compiled dynamically on preprocessing pipeline telemetry.

---

## ⚙️ Pipeline Specifications
- **Scaling Method**: `{pipeline.scaling_method.upper()}`
- **Imbalance Method**: `{pipeline.balancing_method.upper()}`
- **Test Partition Size**: `{test_size * 100:.1f}%` (Stratified split)
- **Random Seed Reference**: `{random_state}`

---

## 🧹 Dataset Cleaning & Memory Profiling
- **Initial Merged Shape**: `{X_train.shape[0] + X_test.shape[0]:,} rows` × `{len(pipeline.original_features) + 1} columns`
- **Memory Footprint (Before)**: `{mem_before_mb:.2f} MB`
- **Memory Footprint (After)**: `{mem_after_mb:.2f} MB`
- **Memory Reduction**: **`{mem_reduction_pct:.2f}%`** (Major savings due to removal of uninformative/redundant features)

---

## 🏷️ Category Encoding Summary
- **Target Column Encoded**: `{target_col}`
- **String Labels Resolved**: `{list(pipeline.label_mapping.keys())}`
- **Encoded Mappings**: `{json.dumps(pipeline.label_mapping)}`
- **Feature Encoders Fitted**: `{len(pipeline.encoder.categorical_cols)} categorical column(s) OHE transformed`

---

## 📊 Feature Selection Auditing

### Dropped Features Summary
| Filtering Stage | Dropped Features Count | Dropped Column Names |
| :--- | :---: | :--- |
| **Constant Columns** | `{len(removed_summary['constant'])}` | `{', '.join(removed_summary['constant']) if removed_summary['constant'] else 'None'}` |
| **Near-Zero Variance** (Var < `{pipeline.var_threshold}`) | `{len(removed_summary['low_variance'])}` | `{', '.join(removed_summary['low_variance']) if removed_summary['low_variance'] else 'None'}` |
| **Duplicate Columns** | `{len(removed_summary['duplicate'])}` | `{', '.join(removed_summary['duplicate']) if removed_summary['duplicate'] else 'None'}` |
| **Multicollinearity** (Pearson r > `{pipeline.corr_threshold}`) | `{len(removed_summary['highly_correlated'])}` | `{', '.join(removed_summary['highly_correlated']) if removed_summary['highly_correlated'] else 'None'}` |

- **Total Features Evaluated**: `{len(pipeline.original_features)}`
- **Total Features Selected**: **`{len(pipeline.final_features)}`**
- **Selected Feature List**: `{', '.join(pipeline.final_features)}`

### Top Selected Features (Mutual Information Scores & RFE ranks)
The detailed list of all features and rank positions is exported to [selected_features.csv](file:///{str(processed_dir.resolve().as_posix())}/selected_features.csv).

---

## ⚖️ Class Imbalance & Resampling Statistics

- **Resampling Method Applied**: `{pipeline.balancing_method.upper()}`
- **SMOTE neighborhood reference**: `{balance_stats.get('method', 'N/A')}`

### Class Distributions Before vs. After Resampling
| Class Label | Encoded Index | Count (Before Balancing) | Count (After Balancing) |
| :--- | :---: | :---: | :---: |
"""
        # Append rows for each class label
        sorted_labels = sorted(pipeline.label_mapping.items(), key=lambda x: x[1])
        before_counts = balance_stats["before_balancing"]
        after_counts = balance_stats.get("after_balancing", before_counts)

        for label_name, label_idx in sorted_labels:
            before_val = before_counts.get(str(label_idx), before_counts.get(label_name, 0))
            after_val = after_counts.get(str(label_idx), after_counts.get(label_name, before_val))
            md_content += f"| **{label_name}** | `{label_idx}` | {before_val:,} | {after_val:,} |\n"

        md_content += f"""
### Computed Estimator Class Weights
(Calculated from training split proportions if model training uses weights instead of SMOTE resampling)
- `weights`: `{json.dumps(class_weights)}`

---
*Report generated automatically by NIDS Preprocessing Pipeline runner.*
"""

        with open(report_file, "w", encoding="utf-8") as f:
            f.write(md_content)
        logger.info("Preprocessing Report successfully saved at: %s", report_file)

    except Exception as e:
        logger.exception("Failed to generate Preprocessing Report: %s", e)

    logger.info("==================================================")
    logger.info("Preprocessing Pipeline Run Completed Successfully.")
    logger.info("Training Split: X_train.csv shape: %s", X_train_bal.shape)
    logger.info("Testing Split:  X_test.csv  shape: %s", X_test_trans.shape)
    logger.info("==================================================")


if __name__ == "__main__":
    main()
