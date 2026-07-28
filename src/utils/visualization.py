"""
Visualization module for the Network Intrusion Detection System (NIDS).
Provides methods to plot class imbalance, feature distributions, outlier boxplots, and correlation heatmaps.
Saves plots to disk and encodes them to Base64 for HTML report embedding.
"""
import base64
import io
import logging
from pathlib import Path
from typing import List, Optional

import matplotlib
# Use Agg backend to avoid showing plot windows during background execution
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.utils.utils import ensure_directory


class Visualizer:
    """
    OOP Visualizer class responsible for generating, styling, and saving NIDS data plots.
    """

    def __init__(self, output_dir: Optional[Path] = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        # Configure output folder (default to reports/figures inside workspace)
        if output_dir is None:
            from src.config.constants import PROJECT_ROOT
            self.output_dir = PROJECT_ROOT / "reports" / "figures"
        else:
            self.output_dir = Path(output_dir)
        
        ensure_directory(self.output_dir)
        self._apply_style()

    def _apply_style(self) -> None:
        """Applies a consistent, premium visual design style for all plots."""
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
        Saves a figure to disk, encodes it to base64, and closes the plot to free memory.
        """
        dest_path = self.output_dir / filename
        ensure_directory(dest_path.parent)
        fig.savefig(dest_path)
        self.logger.debug("Saved plot: %s", dest_path)
        
        b64_str = self._fig_to_base64(fig)
        plt.close(fig)
        return b64_str

    def plot_class_distribution(self, y: pd.Series, filename: str = "class_distribution.png") -> str:
        """
        Plots a bar chart showing class distribution and frequency.
        """
        self.logger.info("Plotting class distribution...")
        counts = y.value_counts()
        percentages = y.value_counts(normalize=True) * 100

        fig, ax = plt.subplots(figsize=(8, 5))
        
        # Determine bar colors
        colors = [self.palette[0] if str(idx).lower() == "benign" else self.palette[1] for idx in counts.index]
        if len(colors) < len(counts):
            colors = sns.color_palette("coolwarm", len(counts))

        bars = sns.barplot(x=counts.index, y=counts.values, ax=ax, palette=colors, hue=counts.index, legend=False)
        
        # Add labels on top of the bars
        for bar, pct in zip(bars.patches, percentages):
            height = bar.get_height()
            ax.annotate(
                f"{int(height):,}\n({pct:.2f}%)",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),  # 3 points vertical offset
                textcoords="offset points",
                ha="center", 
                va="bottom", 
                fontsize=9,
                weight="bold"
            )

        ax.set_title("NIDS Dataset Class Distribution", weight="bold", pad=15)
        ax.set_xlabel("Traffic Label", weight="bold")
        ax.set_ylabel("Records Count", weight="bold")
        # Add padding to top of y-axis for labels
        ax.set_ylim(0, max(counts.values) * 1.15)
        
        # Format y-axis numbers with commas
        ax.get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
        plt.xticks(rotation=20, ha="right")

        return self.save_and_close(fig, filename)

    def plot_correlation_matrix(self, df: pd.DataFrame, top_n: int = 15, filename: str = "correlation_matrix.png") -> str:
        """
        Plots a correlation heatmap of the top_n numerical features with the highest variance.
        Avoids drawing a massive, unreadable matrix of 80+ columns.
        """
        self.logger.info("Plotting correlation matrix of top %d features...", top_n)
        
        # Filter numerical features
        num_df = df.select_dtypes(include=["number"])
        if num_df.empty:
            self.logger.warning("No numeric columns found for correlation matrix.")
            fig, ax = plt.subplots(figsize=(5, 5))
            ax.text(0.5, 0.5, "No Numeric Columns Available", ha="center", va="center")
            return self.save_and_close(fig, filename)

        # Select top_n features by variance
        variances = num_df.var()
        top_features = variances.nlargest(top_n).index.tolist()
        
        # Calculate correlation matrix
        corr_matrix = num_df[top_features].corr()

        # Create plot
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(
            corr_matrix,
            annot=True,
            cmap="coolwarm",
            fmt=".2f",
            linewidths=0.5,
            ax=ax,
            cbar_kws={"shrink": 0.8},
            vmin=-1,
            vmax=1
        )
        
        ax.set_title(f"Correlation Heatmap (Top {top_n} Features by Variance)", weight="bold", pad=15)
        plt.xticks(rotation=45, ha="right")
        plt.yticks(rotation=0)

        return self.save_and_close(fig, filename)

    def plot_histograms(self, df: pd.DataFrame, features: List[str], filename: str = "histograms.png") -> str:
        """
        Plots histograms/density curves for selected features in a grid.
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
                    kde=True, 
                    ax=axes[idx], 
                    color=self.palette[0],
                    bins=30,
                    stat="density"
                )
                axes[idx].set_title(f"Distribution of {feat}", fontsize=11, weight="semibold")
                axes[idx].set_xlabel("")
                axes[idx].set_ylabel("Density")
                # Format scientific notations on x-axis if values are very large
                axes[idx].ticklabel_format(style="scientific", scilimits=(-3, 4), axis="x")
            else:
                axes[idx].text(0.5, 0.5, f"Feature '{feat}'\nnot found", ha="center", va="center")

        # Hide any unused axes in the grid
        for i in range(num_features, len(axes)):
            axes[i].set_visible(False)

        fig.suptitle("Feature Distributions (Histograms & KDE)", weight="bold", y=1.02)
        fig.tight_layout()

        return self.save_and_close(fig, filename)

    def plot_boxplots(self, df: pd.DataFrame, features: List[str], filename: str = "boxplots.png") -> str:
        """
        Plots box plots for selected features in a grid to analyze outliers.
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
                axes[idx].set_title(f"Outliers in {feat}", fontsize=11, weight="semibold")
                axes[idx].set_ylabel("")
                axes[idx].ticklabel_format(style="scientific", scilimits=(-3, 4), axis="y")
            else:
                axes[idx].text(0.5, 0.5, f"Feature '{feat}'\nnot found", ha="center", va="center")

        # Hide unused axes
        for i in range(num_features, len(axes)):
            axes[i].set_visible(False)

        fig.suptitle("Feature Outlier Analysis (Boxplots)", weight="bold", y=1.02)
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
        Plots histograms/KDE curves comparing features between Benign and Malicious traffic.
        """
        self.logger.info("Plotting split feature distributions split by label for: %s", features)
        num_features = len(features)
        if num_features == 0 or target_col not in df.columns:
            fig, ax = plt.subplots()
            return self.save_and_close(fig, filename)

        cols = 2
        rows = (num_features + cols - 1) // cols
        
        fig, axes = plt.subplots(rows, cols, figsize=(14, 4 * rows), squeeze=False)
        axes = axes.flatten()

        # Simplify targets for binary visualization (Benign vs Attack)
        plot_df = df.copy()
        plot_df["Traffic Type"] = plot_df[target_col].apply(
            lambda x: "Benign" if str(x).lower() == "benign" or x == 0 else "Malicious / Intrusion"
        )

        for idx, feat in enumerate(features):
            if feat in plot_df.columns:
                # Plot overlayed KDE
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
                axes[idx].set_title(f"{feat} - Benign vs. Malicious Distribution", fontsize=11, weight="semibold")
                axes[idx].set_xlabel("")
                axes[idx].set_ylabel("Density")
                axes[idx].ticklabel_format(style="scientific", scilimits=(-3, 4), axis="x")
            else:
                axes[idx].text(0.5, 0.5, f"Feature '{feat}'\nnot found", ha="center", va="center")

        # Hide unused axes
        for i in range(num_features, len(axes)):
            axes[i].set_visible(False)

        fig.suptitle("Feature Distributions Split: Benign vs Malicious Traffic", weight="bold", y=1.02)
        fig.tight_layout()

        return self.save_and_close(fig, filename)
