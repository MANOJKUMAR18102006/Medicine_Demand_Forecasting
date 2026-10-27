"""
Generate interactive Jupyter notebook for Exploratory Data Analysis.
"""

import json
import os

notebook_cells = [
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "# 📊 Medicine Demand Forecasting - Exploratory Data Analysis (EDA)\n",
            "\n",
            "This notebook provides a comprehensive investigation of historical medicine demand,\n",
            "seasonality patterns, weather sensitivities, inventory dynamics, and demand spikes."
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "import os\n",
            "import pandas as pd\n",
            "import numpy as np\n",
            "import matplotlib.pyplot as plt\n",
            "import seaborn as sns\n",
            "import plotly.express as px\n",
            "import plotly.graph_objects as go\n",
            "\n",
            "sns.set_theme(style='whitegrid')\n",
            "plt.rcParams['figure.figsize'] = (12, 6)\n",
            "\n",
            "# Load cleaned dataset\n",
            "DATA_PATH = os.path.join('..', 'dataset', 'cleaned_medicine_demand.csv')\n",
            "df = pd.read_csv(DATA_PATH)\n",
            "df['Date'] = pd.to_datetime(df['Date'])\n",
            "print(f'Dataset Loaded: {df.shape[0]:,} rows, {df.shape[1]} columns')\n",
            "df.head()"
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 1. Overall Demand Distribution & Statistics"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "num_cols = ['Quantity_Sold', 'Stock_Level', 'Unit_Price', 'Temperature', 'Rainfall']\n",
            "df[num_cols].describe().round(2)"
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 2. Top Medicines by Total Demand"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "med_agg = df.groupby(['Medicine', 'Medicine_Category']).agg(\n",
            "    Total_Demand=('Quantity_Sold', 'sum'),\n",
            "    Avg_Daily=('Quantity_Sold', 'mean'),\n",
            "    Std_Dev=('Quantity_Sold', 'std'),\n",
            "    Max_Spike=('Quantity_Sold', 'max'),\n",
            "    Outlier_Days=('Is_Demand_Outlier', 'sum')\n",
            ").sort_values(by='Total_Demand', ascending=False).reset_index()\n",
            "\n",
            "plt.figure(figsize=(12, 5))\n",
            "sns.barplot(data=med_agg, x='Medicine', y='Avg_Daily', hue='Medicine', palette='mako', legend=False)\n",
            "plt.title('Average Daily Demand per Medicine')\n",
            "plt.xticks(rotation=45, ha='right')\n",
            "plt.tight_layout()\n",
            "plt.show()\n",
            "med_agg"
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 3. Daily Aggregate Timeline & Moving Average"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "daily = df.groupby('Date')['Quantity_Sold'].sum().reset_index()\n",
            "daily['MA30'] = daily['Quantity_Sold'].rolling(30, center=True).mean()\n",
            "\n",
            "plt.figure(figsize=(14, 5))\n",
            "plt.plot(daily['Date'], daily['Quantity_Sold'], color='#94a3b8', alpha=0.5, label='Daily Total')\n",
            "plt.plot(daily['Date'], daily['MA30'], color='#0284c7', linewidth=2.2, label='30-Day Moving Average')\n",
            "plt.title('3-Year Aggregate Daily Medicine Consumption')\n",
            "plt.xlabel('Date')\n",
            "plt.ylabel('Units Sold')\n",
            "plt.legend()\n",
            "plt.tight_layout()\n",
            "plt.show()"
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 4. Seasonal and Day-of-Week Patterns"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "fig, axes = plt.subplots(1, 2, figsize=(14, 5))\n",
            "\n",
            "dow_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']\n",
            "sns.barplot(data=df, x='Day_of_Week', y='Quantity_Sold', order=dow_order, ax=axes[0], color='#0d9488', errorbar=None)\n",
            "axes[0].set_title('Average Demand by Day of Week')\n",
            "axes[0].tick_params(axis='x', rotation=30)\n",
            "\n",
            "season_order = ['Winter', 'Spring', 'Summer', 'Monsoon', 'Autumn']\n",
            "sns.barplot(data=df, x='Season', y='Quantity_Sold', order=season_order, ax=axes[1], color='#6366f1', errorbar=None)\n",
            "axes[1].set_title('Average Demand by Season')\n",
            "\n",
            "plt.tight_layout()\n",
            "plt.show()"
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 5. Weather Correlates & Heatmap"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "corr = df[['Quantity_Sold', 'Stock_Level', 'Unit_Price', 'Temperature', 'Rainfall', 'Is_Weekend', 'Is_Holiday']].corr()\n",
            "plt.figure(figsize=(8, 6))\n",
            "sns.heatmap(corr, annot=True, fmt='.2f', cmap='coolwarm', vmin=-0.5, vmax=0.5, square=True)\n",
            "plt.title('Correlation Matrix')\n",
            "plt.tight_layout()\n",
            "plt.show()"
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 6. Inventory Dynamics: Stock Level vs Quantity Sold"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "sample = df[df['Medicine'] == 'Paracetamol'].sort_values('Date').head(90)\n",
            "plt.figure(figsize=(12, 5))\n",
            "plt.plot(sample['Date'], sample['Stock_Level'], label='Stock Level', color='#10b981', linewidth=2)\n",
            "plt.plot(sample['Date'], sample['Quantity_Sold'], label='Daily Demand', color='#ef4444', linestyle='--')\n",
            "plt.title('Paracetamol: Stock Level vs Daily Demand (90 Days)')\n",
            "plt.xlabel('Date')\n",
            "plt.ylabel('Units')\n",
            "plt.legend()\n",
            "plt.tight_layout()\n",
            "plt.show()"
        ]
    }
]

notebook_json = {
    "cells": notebook_cells,
    "metadata": {
        "language_info": {
            "name": "python",
            "version": "3.11"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 4
}

out_nb_path = os.path.join("notebooks", "01_eda_and_data_understanding.ipynb")
with open(out_nb_path, "w", encoding="utf-8") as f:
    json.dump(notebook_json, f, indent=2)
print("Notebook generated successfully at", out_nb_path)
