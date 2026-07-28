"""
Visualization module for NIDS.
Plots and saves histograms, boxplots, density plots, class distributions,
missing value heatmaps, and Pearson/Spearman correlation matrices inside reports/eda/.
Also encodes plots to base64 for direct HTML embedding.
"""
import base64
import io
import logging
from pathlib import Path
from typing import List, Optional, Union
import matplotlib
# Use Agg backend for non-interactive execution
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns

from src.utils.utils import ensure_directory


class Visualizer:
    """
    OOP Visualizer class to generate, style, and save charts to disk.
    All files are output to reports/eda/ as PNG.
    """

    def __init__(self, output_dir: Optional[Union[str, Path]] = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        if output_dir is None:
            from src.config.constants import PROJECT_ROOT
            self.output_dir = PROJECT_ROOT / "reports" / "eda"
        else:
            self.output_dir = Path(output_dir)

        ensure_directory(self.output_dir)
        self._apply_style()

    def _apply_style(self) -> None:
        """Configures matplotlib and seaborn visualization settings."""
        sns.set_theme(style="whitegrid", context="paper")
        plt.rcParams.update({
            "font.family": "sans-serif",
            "font.size": 10,
            "axes.labelsize": 11,
            "axes.titlesize": 13,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "figure.titlesize": 14,
            "savefig.bbox": "tight",
            "savefig.dpi": 150,
        })
        self.palette = sns.color_palette("muted")

    def _fig_to_base64(self, fig: plt.Figure) -> str:
        """Converts a matplotlib figure to a Base64-encoded string."""
        buf = io.BytesIO()
        fig.savefig(buf, format="png")
        buf.seek(0)
        img_bytes = buf.read()
        buf.close()
        return base64.b64encode(img_bytes).decode("utf-8")

    def save_and_close(self, fig: plt.Figure, filename: str) -> str:
        """
        Saves figure to disk, encodes to base64, and closes it.
        """
        dest_path = self.output_dir / filename
        ensure_directory(dest_path.parent)
        fig.savefig(dest_path)
        self.logger.debug("Saved chart to: %s", dest_path)
        
        b64_str = self._fig_to_base64(fig)
        plt.close(fig)
        return b64_str

    def plot_class_distribution(self, y: pd.Series, filename: str = "class_distribution.png") -> str:
        """
        Plots a bar chart of class frequencies.
        """
        self.logger.info("Plotting class distribution...")
        counts = y.value_counts()
        percentages = y.value_counts(normalize=True) * 100

        fig, ax = plt.subplots(figsize=(8, 5))
        
        # Color mapping (benign vs attack)
        colors = [self.palette[0] if str(idx).lower() == "benign" else self.palette[1] for idx in counts.index]
        if len(colors) < len(counts):
            colors = sns.color_palette("coolwarm", len(counts))

        bars = sns.barplot(x=counts.index, y=counts.values, ax=ax, palette=colors, hue=counts.index, legend=False)
        
        # Annotate percentages
        for bar, pct in zip(bars.patches, percentages):
            height = bar.get_height()
            ax.annotate(
                f"{int(height):,}\n({pct:.2f}%)",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center", 
                va="bottom", 
                fontsize=9,
                weight="bold"
            )

        ax.set_title("NIDS Dataset Class Distribution", weight="bold", pad=15)
        ax.set_xlabel("Traffic Label", weight="bold")
        ax.set_ylabel("Records Count", weight="bold")
        ax.set_ylim(0, max(counts.values) * 1.15)
        
        ax.get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
        plt.xticks(rotation=20, ha="right")

        return self.save_and_close(fig, filename)

    def plot_correlation_heatmap(
        self, 
        corr_matrix: pd.DataFrame, 
        method_name: str = "Pearson", 
        top_n: int = 12, 
        filename: str = "correlation_heatmap.png"
    ) -> str:
        """
        Plots a correlation heatmap for the top N features by variance.
        """
        self.logger.info("Plotting %s correlation heatmap for top %d features...", method_name, top_n)
        
        # Check size of correlation matrix
        if corr_matrix.empty:
            fig, ax = plt.subplots(figsize=(5, 5))
            ax.text(0.5, 0.5, "No Numeric Columns Available", ha="center", va="center")
            return self.save_and_close(fig, filename)

        # Slice matrix to top N elements
        top_features = corr_matrix.index[:top_n].tolist()
        corr_sliced = corr_matrix.loc[top_features, top_features]

        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(
            corr_sliced,
            annot=True,
            cmap="coolwarm",
            fmt=".2f",
            linewidths=0.5,
            ax=ax,
            cbar_kws={"shrink": 0.8},
            vmin=-1,
            vmax=1
        )
        
        ax.set_title(f"{method_name} Correlation Heatmap (Top {top_n} Features by Variance)", weight="bold", pad=15)
        plt.xticks(rotation=45, ha="right")
        plt.yticks(rotation=0)

        return self.save_and_close(fig, filename)

    def plot_histograms(self, df: pd.DataFrame, features: List[str], filename: str = "histograms.png") -> str:
        """
        Plots grid distribution histograms for key features.
        """
        self.logger.info("Plotting histograms for: %s", features)
        num_features = len(features)
        if num_features == 0:
            fig, ax = plt.subplots()
            return self.save_and_close(fig, filename)

        cols = 3
        rows = (num_features + cols - 1) // cols
        
        fig, axes = plt.subplots(rows, cols, figsize=(14, 3 * rows), squeeze=False)
        axes = axes.flatten()

        for idx, feat in enumerate(features):
            if feat in df.columns:
                sns.histplot(
                    data=df, 
                    x=feat, 
                    kde=False, 
                    ax=axes[idx], 
                    color=self.palette[0],
                    bins=30
                )
                axes[idx].set_title(f"Histogram of {feat}", fontsize=10, weight="semibold")
                axes[idx].set_xlabel("")
                axes[idx].ticklabel_format(style="scientific", scilimits=(-3, 4), axis="x")
            else:
                axes[idx].text(0.5, 0.5, f"Feature '{feat}'\nnot found", ha="center", va="center")

        for i in range(num_features, len(axes)):
            axes[i].set_visible(False)

        fig.suptitle("Feature Histograms", weight="bold", y=1.02)
        fig.tight_layout()

        return self.save_and_close(fig, filename)

    def plot_boxplots(self, df: pd.DataFrame, features: List[str], filename: str = "boxplots.png") -> str:
        """
        Plots grid box plots for outlier analysis.
        """
        self.logger.info("Plotting boxplots for: %s", features)
        num_features = len(features)
        if num_features == 0:
            fig, ax = plt.subplots()
            return self.save_and_close(fig, filename)

        cols = 3
        rows = (num_features + cols - 1) // cols
        
        fig, axes = plt.subplots(rows, cols, figsize=(14, 3 * rows), squeeze=False)
        axes = axes.flatten()

        for idx, feat in enumerate(features):
            if feat in df.columns:
                sns.boxplot(
                    data=df, 
                    y=feat, 
                    ax=axes[idx], 
                    color=self.palette[2],
                    width=0.4
                )
                axes[idx].set_title(f"Outliers in {feat}", fontsize=10, weight="semibold")
                axes[idx].set_ylabel("")
                axes[idx].ticklabel_format(style="scientific", scilimits=(-3, 4), axis="y")
            else:
                axes[idx].text(0.5, 0.5, f"Feature '{feat}'\nnot found", ha="center", va="center")

        for i in range(num_features, len(axes)):
            axes[i].set_visible(False)

        fig.suptitle("Outlier Boxplots", weight="bold", y=1.02)
        fig.tight_layout()

        return self.save_and_close(fig, filename)

    def plot_density_plots(self, df: pd.DataFrame, features: List[str], filename: str = "density_plots.png") -> str:
        """
        Plots grid Kernel Density Estimate (KDE) curves.
        """
        self.logger.info("Plotting density plots for: %s", features)
        num_features = len(features)
        if num_features == 0:
            fig, ax = plt.subplots()
            return self.save_and_close(fig, filename)

        cols = 3
        rows = (num_features + cols - 1) // cols
        
        fig, axes = plt.subplots(rows, cols, figsize=(14, 3 * rows), squeeze=False)
        axes = axes.flatten()

        for idx, feat in enumerate(features):
            if feat in df.columns:
                # Catch singular matrix warning if variance is zero
                try:
                    sns.kdeplot(
                        data=df, 
                        x=feat, 
                        fill=True,
                        ax=axes[idx], 
                        color=self.palette[3]
                    )
                except Exception:
                    # Fallback to histogram if KDE fails (e.g. singular matrix)
                    sns.histplot(
                        data=df,
                        x=feat,
                        kde=False,
                        ax=axes[idx],
                        color=self.palette[3]
                    )
                axes[idx].set_title(f"Density Plot of {feat}", fontsize=10, weight="semibold")
                axes[idx].set_xlabel("")
                axes[idx].set_ylabel("Density")
                axes[idx].ticklabel_format(style="scientific", scilimits=(-3, 4), axis="x")
            else:
                axes[idx].text(0.5, 0.5, f"Feature '{feat}'\nnot found", ha="center", va="center")

        for i in range(num_features, len(axes)):
            axes[i].set_visible(False)

        fig.suptitle("Feature Density Plots", weight="bold", y=1.02)
        fig.tight_layout()

        return self.save_and_close(fig, filename)

    def plot_feature_distributions(
        self, 
        df: pd.DataFrame, 
        features: List[str], 
        target_col: str, 
        filename: str = "feature_distributions_split.png"
    ) -> str:
        """
        Plots KDE/density curves comparing features split by Benign vs Malicious label.
        """
        self.logger.info("Plotting split feature distributions for: %s", features)
        num_features = len(features)
        if num_features == 0 or target_col not in df.columns:
            fig, ax = plt.subplots()
            return self.save_and_close(fig, filename)

        cols = 2
        rows = (num_features + cols - 1) // cols
        
        fig, axes = plt.subplots(rows, cols, figsize=(14, 4 * rows), squeeze=False)
        axes = axes.flatten()

        # Simplify targets for binary label representation
        plot_df = df.copy()
        plot_df["Traffic Type"] = plot_df[target_col].apply(
            lambda x: "Benign" if str(x).lower() == "benign" or x == 0 else "Malicious / Intrusion"
        )

        for idx, feat in enumerate(features):
            if feat in plot_df.columns:
                try:
                    sns.kdeplot(
                        data=plot_df,
                        x=feat,
                        hue="Traffic Type",
                        fill=True,
                        common_norm=False,
                        palette={"Benign": self.palette[0], "Malicious / Intrusion": self.palette[1]},
                        alpha=0.4,
                        linewidth=1.5,
                        ax=axes[idx]
                    )
                except Exception:
                    # Fallback to histogram split if KDE fails
                    sns.histplot(
                        data=plot_df,
                        x=feat,
                        hue="Traffic Type",
                        multiple="dodge",
                        palette={"Benign": self.palette[0], "Malicious / Intrusion": self.palette[1]},
                        ax=axes[idx]
                    )
                axes[idx].set_title(f"{feat} - Benign vs. Malicious", fontsize=10, weight="semibold")
                axes[idx].set_xlabel("")
                axes[idx].set_ylabel("Density")
                axes[idx].ticklabel_format(style="scientific", scilimits=(-3, 4), axis="x")
            else:
                axes[idx].text(0.5, 0.5, f"Feature '{feat}'\nnot found", ha="center", va="center")

        for i in range(num_features, len(axes)):
            axes[i].set_visible(False)

        fig.suptitle("Feature Distributions Split: Benign vs Malicious", weight="bold", y=1.02)
        fig.tight_layout()

        return self.save_and_close(fig, filename)

    def plot_missing_value_heatmap(self, df: pd.DataFrame, filename: str = "missing_values_heatmap.png") -> str:
        """
        Plots a missingness matrix heatmap.
        For large datasets, samples 10,000 rows to prevent execution freezes.
        """
        self.logger.info("Plotting missing value heatmap...")
        num_rows = df.shape[0]
        
        # Sample if dataset is massive to keep matplotlib fast
        sample_size = min(10000, num_rows)
        sample_df = df.sample(n=sample_size, random_state=42) if num_rows > sample_size else df

        # We only plot columns that have at least some missing values,
        # or a subset of top features if everything is clean.
        null_counts = sample_df.isnull().sum()
        cols_to_plot = null_counts[null_counts > 0].index.tolist()
        
        # If no missing values are present, select the top 15 columns to draw a clean blank heatmap
        if not cols_to_plot:
            cols_to_plot = list(sample_df.columns[:15])
            title_suffix = " (No Missing Values Detected)"
        else:
            title_suffix = ""

        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Draw heatmap of boolean null mask
        sns.heatmap(
            sample_df[cols_to_plot].isnull(),
            cbar=False,
            cmap="binary",
            yticklabels=False,
            ax=ax
        )
        
        ax.set_title(f"Missing Values Heatmap{title_suffix}", weight="bold", pad=15)
        ax.set_xlabel("Columns / Features")
        ax.set_ylabel(f"Sample Records (n={sample_size})")
        plt.xticks(rotation=45, ha="right")

        return self.save_and_close(fig, filename)
