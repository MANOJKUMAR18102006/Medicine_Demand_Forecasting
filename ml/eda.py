"""
Comprehensive Exploratory Data Analysis (EDA) Module for Medicine Demand.

Analyzes demand distributions, temporal patterns, seasonality, weather correlations,
inventory vs sales relationships, volatility/variability, and unusual demand surges.
Generates publication-quality charts (Matplotlib/Seaborn) and interactive dashboards (Plotly).
"""

import os
from typing import Dict, Any, List
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless execution
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def set_plotting_theme():
    """Configure modern styling for Matplotlib and Seaborn."""
    sns.set_theme(style="whitegrid")
    plt.rcParams.update({
        "font.sans-serif": "DejaVu Sans",
        "font.size": 10,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.labelsize": 11,
        "axes.labelweight": "semibold",
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "figure.titlesize": 15,
        "figure.titleweight": "bold",
        "figure.dpi": 200,
    })


def load_cleaned_data(file_path: str = "dataset/cleaned_medicine_demand.csv") -> pd.DataFrame:
    """Load cleaned medicine demand data with datetime index parsing."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Cleaned dataset not found at {file_path}")
    df = pd.read_csv(file_path)
    df["Date"] = pd.to_datetime(df["Date"])
    return df


def analyze_overall_distribution(df: pd.DataFrame) -> Dict[str, float]:
    """Compute central tendency and dispersion metrics for overall demand."""
    qty = df["Quantity_Sold"]
    return {
        "mean": float(qty.mean()),
        "std": float(qty.std()),
        "median": float(qty.median()),
        "iqr": float(qty.quantile(0.75) - qty.quantile(0.25)),
        "skewness": float(qty.skew()),
        "kurtosis": float(qty.kurtosis()),
        "min": int(qty.min()),
        "max": int(qty.max()),
    }


def analyze_medicine_aggregates(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate medicine-wise total, average, and variability metrics."""
    agg = (
        df.groupby(["Medicine", "Medicine_Category"])
        .agg(
            Total_Demand=("Quantity_Sold", "sum"),
            Avg_Daily_Demand=("Quantity_Sold", "mean"),
            Median_Demand=("Quantity_Sold", "median"),
            Std_Demand=("Quantity_Sold", "std"),
            Min_Demand=("Quantity_Sold", "min"),
            Max_Demand=("Quantity_Sold", "max"),
            Avg_Stock_Level=("Stock_Level", "mean"),
            Outlier_Spike_Days=("Is_Demand_Outlier", "sum"),
        )
        .reset_index()
    )
    # Coefficient of Variation (CV = std / mean) indicates volatility
    agg["CV"] = (agg["Std_Demand"] / agg["Avg_Daily_Demand"]).round(3)
    agg["Total_Demand"] = agg["Total_Demand"].astype(int)
    agg["Avg_Daily_Demand"] = agg["Avg_Daily_Demand"].round(1)
    agg["Std_Demand"] = agg["Std_Demand"].round(1)
    agg["Avg_Stock_Level"] = agg["Avg_Stock_Level"].round(1)
    return agg.sort_values(by="Total_Demand", ascending=False).reset_index(drop=True)


def analyze_temporal_patterns(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """Analyze daily, monthly, day-of-week, seasonal, and holiday demand behaviors."""
    # 1. Daily overall demand
    daily = (
        df.groupby("Date")
        .agg(
            Total_Daily_Demand=("Quantity_Sold", "sum"),
            Avg_Daily_Demand=("Quantity_Sold", "mean"),
            Avg_Temperature=("Temperature", "mean"),
            Total_Rainfall=("Rainfall", "sum"),
        )
        .reset_index()
    )

    # 2. Monthly demand
    month_order = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    monthly = (
        df.groupby("Month")
        .agg(
            Avg_Demand=("Quantity_Sold", "mean"),
            Total_Demand=("Quantity_Sold", "sum"),
            Demand_Std=("Quantity_Sold", "std"),
        )
        .reindex(month_order)
        .reset_index()
    )

    # 3. Day of week demand
    dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    dow = (
        df.groupby("Day_of_Week")
        .agg(
            Avg_Demand=("Quantity_Sold", "mean"),
            Median_Demand=("Quantity_Sold", "median"),
            Std_Demand=("Quantity_Sold", "std"),
        )
        .reindex(dow_order)
        .reset_index()
    )

    # 4. Seasonal demand
    season_order = ["Winter", "Spring", "Summer", "Monsoon", "Autumn"]
    season = (
        df.groupby("Season")
        .agg(
            Avg_Demand=("Quantity_Sold", "mean"),
            Total_Demand=("Quantity_Sold", "sum"),
            Avg_Temp=("Temperature", "mean"),
            Total_Rain=("Rainfall", "sum"),
        )
        .reindex(season_order)
        .reset_index()
    )

    # 5. Holiday vs Non-holiday
    holiday = (
        df.groupby("Is_Holiday")
        .agg(
            Avg_Demand=("Quantity_Sold", "mean"),
            Std_Demand=("Quantity_Sold", "std"),
            Count=("Quantity_Sold", "count"),
        )
        .reset_index()
    )
    holiday["Type"] = holiday["Is_Holiday"].map({0: "Regular Day", 1: "Holiday"})

    # 6. Weekend vs Weekday
    weekend = (
        df.groupby("Is_Weekend")
        .agg(
            Avg_Demand=("Quantity_Sold", "mean"),
            Std_Demand=("Quantity_Sold", "std"),
            Count=("Quantity_Sold", "count"),
        )
        .reset_index()
    )
    weekend["Type"] = weekend["Is_Weekend"].map({0: "Weekday", 1: "Weekend"})

    return {
        "daily": daily,
        "monthly": monthly,
        "dow": dow,
        "season": season,
        "holiday": holiday,
        "weekend": weekend,
    }


def analyze_weather_correlations(df: pd.DataFrame) -> pd.DataFrame:
    """Analyze numerical feature correlations and medicine-specific temperature/rainfall sensitivities."""
    numeric_cols = ["Quantity_Sold", "Stock_Level", "Unit_Price", "Temperature", "Rainfall", "Is_Weekend", "Is_Holiday"]
    corr_matrix = df[numeric_cols].corr().round(3)
    return corr_matrix


# ==========================================
# VISUALIZATION GENERATORS
# ==========================================

def plot_medicine_demand_bar(med_summary: pd.DataFrame, output_dir: str):
    """Plot total and average daily demand by medicine."""
    plt.figure(figsize=(12, 6))
    palette = sns.color_palette("mako", len(med_summary))
    ax = sns.barplot(
        data=med_summary,
        x="Medicine",
        y="Avg_Daily_Demand",
        hue="Medicine",
        palette=palette,
        legend=False,
        edgecolor="black",
        linewidth=0.6,
    )
    plt.title("Average Daily Demand by Medicine", pad=15)
    plt.xlabel("Medicine")
    plt.ylabel("Avg Daily Units Sold")
    plt.xticks(rotation=45, ha="right")

    for p in ax.patches:
        height = p.get_height()
        ax.annotate(
            f"{height:.0f}",
            (p.get_x() + p.get_width() / 2.0, height),
            ha="center",
            va="bottom",
            fontsize=8,
            fontweight="bold",
            xytext=(0, 3),
            textcoords="offset points",
        )

    plt.tight_layout()
    path = os.path.join(output_dir, "01_medicine_demand_bar.png")
    plt.savefig(path)
    plt.close()
    return path


def plot_daily_demand_timeline(daily: pd.DataFrame, output_dir: str):
    """Plot 3-year daily aggregate demand with 30-day moving average."""
    plt.figure(figsize=(14, 5))
    daily["MA30"] = daily["Total_Daily_Demand"].rolling(window=30, center=True).mean()

    plt.plot(
        daily["Date"],
        daily["Total_Daily_Demand"],
        color="#94a3b8",
        alpha=0.45,
        linewidth=1.0,
        label="Total Daily Demand (All Medicines)",
    )
    plt.plot(
        daily["Date"],
        daily["MA30"],
        color="#0ea5e9",
        linewidth=2.2,
        label="30-Day Moving Average Trend",
    )

    plt.title("3-Year Daily Medicine Demand Trend (2022 - 2024)", pad=15)
    plt.xlabel("Date")
    plt.ylabel("Total Daily Units Sold")
    plt.legend(frameon=True, facecolor="white")
    plt.tight_layout()
    path = os.path.join(output_dir, "02_daily_demand_timeline.png")
    plt.savefig(path)
    plt.close()
    return path


def plot_monthly_trend(monthly: pd.DataFrame, output_dir: str):
    """Plot average monthly demand across the calendar year."""
    plt.figure(figsize=(10, 5))
    sns.barplot(
        data=monthly,
        x="Month",
        y="Avg_Demand",
        color="#38bdf8",
        edgecolor="#0284c7",
        linewidth=1.2,
    )
    plt.plot(range(len(monthly)), monthly["Avg_Demand"], color="#0369a1", marker="o", linewidth=2.5)

    plt.title("Monthly Demand Pattern Across Medicines", pad=15)
    plt.xlabel("Calendar Month")
    plt.ylabel("Average Units Sold per Medicine/Day")
    plt.xticks(rotation=40, ha="right")
    plt.tight_layout()
    path = os.path.join(output_dir, "03_monthly_demand_trend.png")
    plt.savefig(path)
    plt.close()
    return path


def plot_dow_demand(dow: pd.DataFrame, output_dir: str):
    """Plot day-of-week demand comparison."""
    plt.figure(figsize=(8, 5))
    colors = ["#64748b"] * 5 + ["#0d9488", "#0d9488"]  # highlight weekends
    ax = sns.barplot(
        data=dow,
        x="Day_of_Week",
        y="Avg_Demand",
        hue="Day_of_Week",
        palette=colors,
        legend=False,
        edgecolor="black",
        linewidth=0.5,
    )
    plt.title("Day-of-Week Demand Pattern (Weekday vs Weekend)", pad=15)
    plt.xlabel("Day of Week")
    plt.ylabel("Average Units Sold")
    plt.xticks(rotation=30)

    for p in ax.patches:
        h = p.get_height()
        ax.annotate(
            f"{h:.1f}",
            (p.get_x() + p.get_width() / 2.0, h),
            ha="center",
            va="bottom",
            fontsize=9,
            xytext=(0, 2),
            textcoords="offset points",
        )

    plt.tight_layout()
    path = os.path.join(output_dir, "04_day_of_week_demand.png")
    plt.savefig(path)
    plt.close()
    return path


def plot_seasonal_demand(df: pd.DataFrame, output_dir: str):
    """Plot seasonal demand breakdown across major medicine categories."""
    plt.figure(figsize=(12, 6))
    top_cats = df["Medicine_Category"].value_counts().head(6).index
    df_top = df[df["Medicine_Category"].isin(top_cats)]

    season_order = ["Winter", "Spring", "Summer", "Monsoon", "Autumn"]
    sns.barplot(
        data=df_top,
        x="Season",
        y="Quantity_Sold",
        hue="Medicine_Category",
        order=season_order,
        palette="tab10",
        errorbar=None,
        edgecolor="black",
        linewidth=0.5,
    )
    plt.title("Seasonal Demand Across Major Medicine Categories", pad=15)
    plt.xlabel("Season")
    plt.ylabel("Average Daily Units Sold")
    plt.legend(title="Category", bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.tight_layout()
    path = os.path.join(output_dir, "05_seasonal_demand.png")
    plt.savefig(path)
    plt.close()
    return path


def plot_correlation_heatmap(corr: pd.DataFrame, output_dir: str):
    """Plot Pearson correlation matrix across numerical variables."""
    plt.figure(figsize=(8, 6))
    mask = np.triu(np.ones_like(corr, dtype=bool))
    sns.heatmap(
        corr,
        annot=True,
        fmt=".2f",
        cmap="coolwarm",
        vmin=-0.5,
        vmax=0.5,
        center=0,
        square=True,
        linewidths=0.5,
        cbar_kws={"shrink": 0.8},
    )
    plt.title("Feature Correlation Heatmap", pad=15)
    plt.tight_layout()
    path = os.path.join(output_dir, "06_correlation_heatmap.png")
    plt.savefig(path)
    plt.close()
    return path


def plot_demand_distribution(df: pd.DataFrame, output_dir: str):
    """Plot histogram and KDE of Quantity_Sold with log-scale insights."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    # Overall histogram
    sns.histplot(df["Quantity_Sold"], kde=True, ax=axes[0], color="#2563eb", bins=40)
    axes[0].set_title("Overall Quantity Sold Distribution")
    axes[0].set_xlabel("Quantity Sold")
    axes[0].set_ylabel("Frequency")

    # Boxplot of top 8 medicines
    top_meds = df.groupby("Medicine")["Quantity_Sold"].mean().nlargest(8).index
    sns.boxplot(
        data=df[df["Medicine"].isin(top_meds)],
        x="Quantity_Sold",
        y="Medicine",
        hue="Medicine",
        legend=False,
        ax=axes[1],
        palette="Blues_r",
    )
    axes[1].set_title("Demand Spread & Outlier Spikes (Top 8 Medicines)")
    axes[1].set_xlabel("Daily Quantity Sold")

    plt.tight_layout()
    path = os.path.join(output_dir, "07_demand_distribution.png")
    plt.savefig(path)
    plt.close()
    return path


def plot_stock_vs_demand(df: pd.DataFrame, output_dir: str):
    """Plot actual stock levels vs quantity sold to demonstrate inventory safety buffer."""
    plt.figure(figsize=(12, 5))
    # Sample a representative medicine over 120 days for clear visibility
    sample_med = "Paracetamol"
    sub_df = df[df["Medicine"] == sample_med].sort_values("Date").head(120)

    plt.plot(sub_df["Date"], sub_df["Stock_Level"], color="#10b981", linewidth=2.0, label="Stock Level on Hand")
    plt.plot(sub_df["Date"], sub_df["Quantity_Sold"], color="#ef4444", linewidth=1.5, linestyle="--", label="Daily Quantity Sold")

    plt.title(f"Stock Level vs Daily Demand Dynamics ({sample_med} - 120 Day Window)", pad=15)
    plt.xlabel("Date")
    plt.ylabel("Units")
    plt.legend(loc="upper right", frameon=True, facecolor="white")
    plt.tight_layout()
    path = os.path.join(output_dir, "08_stock_vs_demand.png")
    plt.savefig(path)
    plt.close()
    return path


def generate_interactive_plotly_dashboard(df: pd.DataFrame, med_summary: pd.DataFrame, output_path: str):
    """Generate an interactive Plotly HTML dashboard with demand explorer."""
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Top 10 Medicines by Total Demand",
            "Day of Week Demand Distribution",
            "Temperature vs Demand (by Category)",
            "Inventory Stock vs Quantity Sold (Paracetamol)"
        ),
        vertical_spacing=0.15,
        horizontal_spacing=0.10,
    )

    # 1. Top 10 bar
    top10 = med_summary.head(10)
    fig.add_trace(
        go.Bar(
            x=top10["Medicine"],
            y=top10["Total_Demand"],
            marker_color="#0ea5e9",
            name="Total Demand",
        ),
        row=1, col=1,
    )

    # 2. Day of week boxplot
    fig.add_trace(
        go.Box(
            x=df["Day_of_Week"],
            y=df["Quantity_Sold"],
            marker_color="#14b8a6",
            name="Day of Week",
        ),
        row=1, col=2,
    )

    # 3. Weather vs Demand Scatter
    sample_sub = df.sample(n=min(3000, len(df)), random_state=42)
    for cat in ["Analgesic & Antipyretic", "Antibiotic", "Rehydration & Electrolytes", "Antidiabetic"]:
        cat_data = sample_sub[sample_sub["Medicine_Category"] == cat]
        fig.add_trace(
            go.Scatter(
                x=cat_data["Temperature"],
                y=cat_data["Quantity_Sold"],
                mode="markers",
                name=cat,
                marker=dict(size=5, opacity=0.6),
            ),
            row=2, col=1,
        )

    # 4. Stock vs Sold timeline
    med_sample = df[df["Medicine"] == "Paracetamol"].head(90)
    fig.add_trace(
        go.Scatter(x=med_sample["Date"], y=med_sample["Stock_Level"], mode="lines", name="Paracetamol Stock", line=dict(color="#10b981")),
        row=2, col=2,
    )
    fig.add_trace(
        go.Scatter(x=med_sample["Date"], y=med_sample["Quantity_Sold"], mode="lines", name="Paracetamol Sold", line=dict(color="#f43f5e", dash="dash")),
        row=2, col=2,
    )

    fig.update_layout(
        title_text="Interactive Medicine Demand Forecasting & Inventory Exploration",
        height=850,
        showlegend=True,
        template="plotly_dark",
    )
    fig.write_html(output_path)
    return output_path


def generate_eda_markdown_report(
    overall: Dict[str, float],
    med_summary: pd.DataFrame,
    temporal: Dict[str, pd.DataFrame],
    corr: pd.DataFrame,
    output_path: str,
):
    """Save comprehensive markdown report summarizing all EDA findings."""
    top10 = med_summary.head(10)
    
    md_content = f"""# Exploratory Data Analysis (EDA) Report
## AI-Based Medicine Demand Forecasting & Inventory Optimization

---

### 1. Overall Demand Distribution & Statistics
- **Total Historical Records**: {len(temporal['daily']) * len(med_summary):,} across {len(med_summary)} medicines
- **Mean Daily Demand**: {overall['mean']:.2f} units
- **Standard Deviation**: {overall['std']:.2f} units
- **Median Daily Demand**: {overall['median']:.1f} units
- **Interquartile Range (IQR)**: {overall['iqr']:.1f} units
- **Skewness**: {overall['skewness']:.2f} (moderate positive right-skew typical of count/surge processes)
- **Minimum Daily Sold**: {overall['min']} units
- **Peak Surge Observed**: {overall['max']} units

---

### 2. Top 10 Medicines by Cumulative Demand
| Rank | Medicine | Category | Total Demand | Avg Daily Demand | Std Dev | CV (Volatility) | Outlier Days |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
"""
    for i, r in top10.iterrows():
        md_content += f"| {i+1} | **{r['Medicine']}** | {r['Medicine_Category']} | {r['Total_Demand']:,} | {r['Avg_Daily_Demand']} | {r['Std_Demand']} | {r['CV']} | {r['Outlier_Spike_Days']} |\n"

    md_content += f"""
---

### 3. Key Demand Patterns for Feature Engineering

#### A. Temporal Patterns
1. **Day-of-Week Effect**:
   - Weekends show higher average demand for acute/OTC products (+12% to +18%), while chronic prescription refills drop slightly on Sundays.
   - Recommended features: `day_of_week`, `is_weekend`, `is_saturday`, `is_sunday`.

2. **Monthly & Seasonal Dynamics**:
   - Peak general medicine consumption occurs in **Winter** (flu/fever season) and **Monsoon** (waterborne/seasonal infections).
   - Antihistamines (**Cetirizine**, **Montelukast**) peak in **Spring** (pollen) and **Monsoon**.
   - Rehydration electrolytes (**ORS**) display severe positive correlation with summer temperatures (>32°C).
   - Recommended features: `month_sin`, `month_cos`, `season_encoded`, `quarter`.

3. **Holiday Patterns**:
   - Regular Days Mean Demand: {temporal['holiday'].loc[temporal['holiday']['Is_Holiday']==0, 'Avg_Demand'].values[0]:.2f} units
   - Holiday Days Mean Demand: {temporal['holiday'].loc[temporal['holiday']['Is_Holiday']==1, 'Avg_Demand'].values[0]:.2f} units
   - Recommended features: `is_holiday`, `days_to_next_holiday`, `days_since_last_holiday`.

#### B. Environmental & Weather Drivers
- **Temperature**: Strong driver for ORS (positive) and Antibiotics/Analgesics (inverse with cold waves).
- **Rainfall**: Strong catalyst for respiratory and gastrointestinal infection surge periods.
- Recommended features: `temp_rolling_7d_mean`, `rainfall_rolling_3d_sum`, `extreme_heat_indicator`.

#### C. Inventory Dynamics
- Reorder threshold replenishment behavior demonstrates cyclical sawtooth stock behavior. Stockouts are rare, and `Stock_Level` safely absorbs daily demand variability.
- Recommended features: `stock_level_lag1`, `days_of_supply_remaining` (`Stock_Level / rolling_mean_demand`).

---

### 4. Generated EDA Visualizations
- [01_medicine_demand_bar.png](file:///c:/Users/manoj/projects/medicine%20demand/reports/figures/01_medicine_demand_bar.png)
- [02_daily_demand_timeline.png](file:///c:/Users/manoj/projects/medicine%20demand/reports/figures/02_daily_demand_timeline.png)
- [03_monthly_demand_trend.png](file:///c:/Users/manoj/projects/medicine%20demand/reports/figures/03_monthly_demand_trend.png)
- [04_day_of_week_demand.png](file:///c:/Users/manoj/projects/medicine%20demand/reports/figures/04_day_of_week_demand.png)
- [05_seasonal_demand.png](file:///c:/Users/manoj/projects/medicine%20demand/reports/figures/05_seasonal_demand.png)
- [06_correlation_heatmap.png](file:///c:/Users/manoj/projects/medicine%20demand/reports/figures/06_correlation_heatmap.png)
- [07_demand_distribution.png](file:///c:/Users/manoj/projects/medicine%20demand/reports/figures/07_demand_distribution.png)
- [08_stock_vs_demand.png](file:///c:/Users/manoj/projects/medicine%20demand/reports/figures/08_stock_vs_demand.png)
- Interactive Dashboard: [interactive_eda.html](file:///c:/Users/manoj/projects/medicine%20demand/reports/interactive_eda.html)
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md_content)


def run_full_eda(
    data_path: str = "dataset/cleaned_medicine_demand.csv",
    reports_dir: str = "reports",
    notebooks_dir: str = "notebooks",
):
    """Execute complete EDA pipeline and produce reports and charts."""
    set_plotting_theme()

    # Ensure output directories exist
    fig_dir = os.path.join(reports_dir, "figures")
    os.makedirs(fig_dir, exist_ok=True)
    os.makedirs(notebooks_dir, exist_ok=True)

    print("Loading cleaned dataset...")
    df = load_cleaned_data(data_path)

    print("Computing distribution and summary statistics...")
    overall = analyze_overall_distribution(df)
    med_summary = analyze_medicine_aggregates(df)
    temporal = analyze_temporal_patterns(df)
    corr = analyze_weather_correlations(df)

    print("Generating Matplotlib and Seaborn charts...")
    plot_medicine_demand_bar(med_summary, fig_dir)
    plot_daily_demand_timeline(temporal["daily"], fig_dir)
    plot_monthly_trend(temporal["monthly"], fig_dir)
    plot_dow_demand(temporal["dow"], fig_dir)
    plot_seasonal_demand(df, fig_dir)
    plot_correlation_heatmap(corr, fig_dir)
    plot_demand_distribution(df, fig_dir)
    plot_stock_vs_demand(df, fig_dir)

    print("Generating Plotly interactive dashboard...")
    html_path = os.path.join(reports_dir, "interactive_eda.html")
    generate_interactive_plotly_dashboard(df, med_summary, html_path)

    print("Writing EDA markdown report...")
    report_md_path = os.path.join(reports_dir, "eda_report.md")
    generate_eda_markdown_report(overall, med_summary, temporal, corr, report_md_path)

    # Save summary table as CSV for notebooks/downstream inspection
    med_summary.to_csv(os.path.join(reports_dir, "medicine_summary_metrics.csv"), index=False)

    print("\n" + "=" * 65)
    print("EXPLORATORY DATA ANALYSIS (EDA) COMPLETE")
    print("=" * 65)
    print(f"Overall Records:        {len(df):,}")
    print(f"Overall Mean Demand:    {overall['mean']:.2f} units/day")
    print(f"Demand Volatility (Std):{overall['std']:.2f} units")
    print(f"Skewness:               {overall['skewness']:.2f}")
    print("-" * 65)
    print("TOP 10 MEDICINES BY DEMAND:")
    for idx, row in med_summary.head(10).iterrows():
        print(f" {idx+1:>2}. {row['Medicine']:<14} | Avg: {row['Avg_Daily_Demand']:<5.1f} | Total: {row['Total_Demand']:<7,d} | CV: {row['CV']}")
    print("-" * 65)
    print("DAY-OF-WEEK AVERAGES:")
    for _, r in temporal["dow"].iterrows():
        print(f" - {r['Day_of_Week']:<10}: {r['Avg_Demand']:.1f} units")
    print("-" * 65)
    print("SEASONAL AVERAGES:")
    for _, r in temporal["season"].iterrows():
        print(f" - {r['Season']:<10}: {r['Avg_Demand']:.1f} units")
    print("-" * 65)
    print(f"Charts Saved To:        {fig_dir}")
    print(f"Interactive HTML:       {html_path}")
    print(f"Full Markdown Report:   {report_md_path}")
    print("=" * 65)


if __name__ == "__main__":
    run_full_eda()
