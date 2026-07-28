"""
Feature Selection module for NIDS.
Filters constant, near-zero variance, duplicate, and highly correlated features.
Performs Mutual Information ranking and Recursive Feature Elimination (RFE) on sampled data.
"""
import logging
from typing import Any, Dict, List, Tuple
import pandas as pd
import numpy as np
from sklearn.feature_selection import mutual_info_classif, RFE
from sklearn.tree import DecisionTreeClassifier

from src.exceptions.custom_exceptions import DataPreprocessingError


class FeatureSelector:
    """
    OOP Feature Selector implementing multiple filtering and ranking stages.
    """

    def __init__(
        self,
        variance_threshold: float = 0.0001,
        correlation_threshold: float = 0.90,
        top_n_mi: int = 20,
        top_n_rfe: int = 20,
        random_state: int = 42
    ):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.variance_threshold = variance_threshold
        self.correlation_threshold = correlation_threshold
        self.top_n_mi = top_n_mi
        self.top_n_rfe = top_n_rfe
        self.random_state = random_state

        # Tracking state
        self.constant_cols: List[str] = []
        self.low_variance_cols: List[str] = []
        self.duplicate_cols: List[str] = []
        self.highly_correlated_cols: List[str] = []
        self.selected_features: List[str] = []
        
        # Reports logs
        self.mi_scores: Dict[str, float] = {}
        self.rfe_rankings: Dict[str, int] = {}
        self.removed_features: Dict[str, List[str]] = {}

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "FeatureSelector":
        """
        Fits the selectors on the training set to identify features to drop.
        """
        self.logger.info("Executing feature selection pipelines...")
        current_features = X.columns.tolist()
        
        # 1. Variance Filter (Constant & Near-Zero Variance)
        self.logger.debug("Running variance filters...")
        variances = X.var()
        
        # Constant columns (variance == 0)
        self.constant_cols = [col for col in current_features if variances[col] == 0.0]
        self.logger.info("Identified %d constant columns: %s", len(self.constant_cols), self.constant_cols)
        
        # Low variance columns
        self.low_variance_cols = [
            col for col in current_features 
            if col not in self.constant_cols and variances[col] < self.variance_threshold
        ]
        self.logger.info("Identified %d low-variance columns (< %s): %s", 
                         len(self.low_variance_cols), self.variance_threshold, self.low_variance_cols)
        
        # Apply variance filters
        to_drop_variance = self.constant_cols + self.low_variance_cols
        current_df = X.drop(columns=to_drop_variance)
        current_features = current_df.columns.tolist()

        # 2. Duplicate Feature Value Filter
        # To make it fast, sample rows, identify candidates, and verify on full DF
        self.logger.debug("Running duplicate feature checks...")
        dup_cols = []
        if len(current_features) > 1:
            sample_size = min(20000, len(current_df))
            sample_df = current_df.sample(n=sample_size, random_state=self.random_state)
            
            # Find duplicate columns on sample transpose
            dup_candidates = sample_df.T.duplicated()
            candidate_cols = dup_candidates[dup_candidates].index.tolist()
            
            # Verify candidate duplicate columns on full DF
            checked = set()
            for col in candidate_cols:
                # Find matching primary columns
                for col_orig in current_features:
                    if col_orig == col or col_orig in checked or col_orig in dup_cols:
                        continue
                    if (current_df[col] == current_df[col_orig]).all():
                        dup_cols.append(col)
                        checked.add(col)
                        break

        self.duplicate_cols = dup_cols
        self.logger.info("Identified %d duplicate columns: %s", len(self.duplicate_cols), self.duplicate_cols)
        current_df = current_df.drop(columns=self.duplicate_cols)
        current_features = current_df.columns.tolist()

        # 3. Highly Correlated Feature Filter
        self.logger.debug("Running correlation filtering...")
        corr_matrix = current_df.corr(method="pearson").abs()
        upper_tri = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
        
        to_drop_corr = []
        for col in upper_tri.columns:
            # Check if any feature correlates above threshold with col
            high_corrs = upper_tri[col][upper_tri[col] > self.correlation_threshold]
            if not high_corrs.empty:
                # We drop col. This is simple and deterministic.
                to_drop_corr.append(col)

        self.highly_correlated_cols = to_drop_corr
        self.logger.info("Identified %d highly correlated columns: %s", len(self.highly_correlated_cols), self.highly_correlated_cols)
        current_df = current_df.drop(columns=self.highly_correlated_cols)
        current_features = current_df.columns.tolist()

        # Save removed list for report
        self.removed_features = {
            "constant": self.constant_cols,
            "low_variance": self.low_variance_cols,
            "duplicate": self.duplicate_cols,
            "highly_correlated": self.highly_correlated_cols
        }

        # If we have no features left, raise error
        if not current_features:
            raise DataPreprocessingError("All features were eliminated by variance/correlation/duplicate filters!")

        # 4. Mutual Information Feature Ranking
        # Compute on representative sample to prevent OOM
        sample_size = min(50000, len(current_df))
        self.logger.info("Sampling %d records for Mutual Information and RFE calculations...", sample_size)
        sample_df = current_df.sample(n=sample_size, random_state=self.random_state)
        sample_y = y.loc[sample_df.index]

        self.logger.info("Calculating Mutual Information scores...")
        try:
            mi_vals = mutual_info_classif(sample_df, sample_y, random_state=self.random_state)
            self.mi_scores = dict(zip(current_features, mi_vals))
            # Sort descending by score
            sorted_mi = sorted(self.mi_scores.items(), key=lambda x: x[1], reverse=True)
            top_mi_features = [feat for feat, score in sorted_mi[:self.top_n_mi]]
            self.logger.info("Top %d Mutual Information features: %s", self.top_n_mi, top_mi_features)
        except Exception as e:
            self.logger.exception("Mutual Information calculation failed: %s", e)
            top_mi_features = current_features[:self.top_n_mi]

        # 5. Recursive Feature Elimination (RFE)
        # Run using a fast Decision Tree classifier on the sample subset
        self.logger.info("Running Recursive Feature Elimination (RFE) with DecisionTree estimator...")
        try:
            dt_estimator = DecisionTreeClassifier(max_depth=5, random_state=self.random_state)
            rfe = RFE(estimator=dt_estimator, n_features_to_select=self.top_n_rfe)
            rfe.fit(sample_df, sample_y)
            
            self.rfe_rankings = dict(zip(current_features, rfe.ranking_))
            
            # Selected features from RFE (ranking == 1)
            top_rfe_features = [feat for feat, rank in self.rfe_rankings.items() if rank == 1]
            self.logger.info("Top RFE features: %s", top_rfe_features)
        except Exception as e:
            self.logger.exception("RFE execution failed: %s", e)
            top_rfe_features = current_features[:self.top_n_rfe]

        # Final Selected Features are the combination of RFE selections (or intersection/union).
        # We will follow the RFE selection as the final selection, as RFE accounts for feature interactions.
        self.selected_features = top_rfe_features
        self.logger.info("Feature selection complete. Final selected feature count: %d", len(self.selected_features))
        
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Transforms features DataFrame by selecting only final selected features.
        """
        if not self.selected_features:
            raise DataPreprocessingError("FeatureSelector has not been fitted or no features were selected.")
        
        self.logger.info("Filtering DataFrame columns down to %d selected features...", len(self.selected_features))
        return X[self.selected_features].copy()

    def fit_transform(self, X: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
        """Fits and transforms features in one step."""
        return self.fit(X, y).transform(X)

    def get_selection_summary(self) -> pd.DataFrame:
        """
        Creates a DataFrame summarizing details of all features and selection results.
        """
        summary_records = []
        
        # Reconstruct all features that were ever evaluated
        all_features = set()
        for group in self.removed_features.values():
            all_features.update(group)
        all_features.update(self.selected_features)
        all_features.update(self.mi_scores.keys())

        for feat in all_features:
            status = "Selected" if feat in self.selected_features else "Dropped"
            
            # Find drop reason
            reason = "N/A"
            if feat in self.constant_cols:
                reason = "Constant feature (0 variance)"
            elif feat in self.low_variance_cols:
                reason = "Low variance"
            elif feat in self.duplicate_cols:
                reason = "Duplicate column contents"
            elif feat in self.highly_correlated_cols:
                reason = "Highly correlated"
            elif status == "Dropped":
                reason = "Eliminated by RFE ranking"

            mi_score = self.mi_scores.get(feat, 0.0)
            rfe_rank = self.rfe_rankings.get(feat, 999)

            summary_records.append({
                "feature": feat,
                "status": status,
                "reason": reason,
                "mi_score": mi_score,
                "rfe_rank": rfe_rank
            })

        # Sort: Selected features first, then by MI score descending
        df_summary = pd.DataFrame(summary_records)
        df_summary = df_summary.sort_values(by=["status", "mi_score"], ascending=[False, False])
        return df_summary
