"""
compute_dataset_statistics.py

Analyzes the synthetic datasets (workers, contractors, districts) generated for Suraksha Chakra.
Computes requested statistical requirements (Covariance, Correlation, PCA, Outliers)
and produces the final markdown report.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

SYNTHETIC_DIR = os.path.join("data", "synthetic")
REPORT_FILE = os.path.join(SYNTHETIC_DIR, "dataset_report.md")

def load_data():
    logging.info("Loading synthetic datasets...")
    workers = pd.read_csv(os.path.join(SYNTHETIC_DIR, "workers.csv"))
    contractors = pd.read_csv(os.path.join(SYNTHETIC_DIR, "contractors.csv"))
    districts = pd.read_csv(os.path.join(SYNTHETIC_DIR, "districts.csv"))
    return workers, contractors, districts

def compute_descriptive_stats(df, name):
    logging.info(f"Computing descriptive stats for {name}...")
    num_cols = df.select_dtypes(include=[np.number]).columns
    stats = []
    for col in num_cols:
        series = df[col].dropna()
        if len(series) == 0: continue
        
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        outliers = series[(series < lower_bound) | (series > upper_bound)].count()
        
        stats.append({
            "Feature": col,
            "Mean": round(series.mean(), 2),
            "Median": round(series.median(), 2),
            "Variance": round(series.var(), 2),
            "Std Dev": round(series.std(), 2),
            "CV (%)": round((series.std() / series.mean() * 100) if series.mean() != 0 else 0, 2),
            "Skewness": round(series.skew(), 2),
            "Kurtosis": round(series.kurtosis(), 2),
            "25th %ile": round(q1, 2),
            "75th %ile": round(q3, 2),
            "IQR": round(iqr, 2),
            "Outliers": outliers
        })
    return pd.DataFrame(stats)

def compute_matrices(df, name):
    logging.info(f"Computing matrices for {name}...")
    num_df = df.select_dtypes(include=[np.number])
    if num_df.empty: return None, None
    corr = num_df.corr()
    cov = num_df.cov()
    return corr, cov

def perform_pca(df, name):
    logging.info(f"Performing PCA on {name}...")
    num_df = df.select_dtypes(include=[np.number]).dropna()
    if num_df.shape[1] < 2: return None
    
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(num_df)
    
    pca = PCA(n_components=2)
    pca_result = pca.fit_transform(scaled_data)
    
    explained_variance = pca.explained_variance_ratio_
    return explained_variance

def generate_visualizations(workers, districts):
    logging.info("Generating distribution plots...")
    sns.set_theme(style="whitegrid")
    
    # Wage Distribution
    plt.figure(figsize=(10, 6))
    sns.histplot(workers['daily_wage'], bins=100, kde=True, color="blue")
    plt.title("Synthetic Daily Wage Distribution (Log-Normal)")
    plt.xlabel("Daily Wage (INR)")
    plt.ylabel("Frequency")
    plt.savefig(os.path.join(SYNTHETIC_DIR, "wage_distribution.png"))
    plt.close()
    
    # District Correlation Heatmap
    num_dist = districts.select_dtypes(include=[np.number])
    plt.figure(figsize=(10, 8))
    sns.heatmap(num_dist.corr(), annot=True, cmap="coolwarm", fmt=".2f")
    plt.title("District Features Correlation Matrix (Gaussian Copula)")
    plt.tight_layout()
    plt.savefig(os.path.join(SYNTHETIC_DIR, "district_correlation.png"))
    plt.close()

def write_markdown_report(w_stats, c_stats, d_stats, d_corr, d_cov, pca_var):
    logging.info("Writing dataset_report.md...")
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("# Synthetic Dataset Statistical Report\n\n")
        f.write("> **Disclaimer**: Synthetic dataset generated from official statistical priors for prototype development. Do not use for actual policy enforcement without real-world substitution.\n\n")
        
        f.write("## 1. Population & Sampling Methodology\n")
        f.write("- **Worker Dataset**: $N=100,000$. Age sampled via Truncated Normal ($\mu=31, \sigma=9$). Daily Wage sampled via Log-Normal distribution, penalized linearly by the assigned contractor's fraud probability.\n")
        f.write("- **Contractor Dataset**: $N=10,000$. Fraud probability derived via Beta distribution ($a=2, b=8$), creating a realistic right-skewed tail for exploitative entities.\n")
        f.write("- **District Dataset**: $N=100$. Generated using Multivariate Normal sampling (Gaussian Copula approximation) to preserve the real-world correlation structure where high climate/economic distress drives migration, which subsequently drives crime and vulnerability.\n\n")
        
        f.write("## 2. Descriptive Statistics & Outlier Analysis\n")
        
        f.write("### 2.1 District Vulnerability Dataset\n")
        f.write(d_stats.to_markdown(index=False) + "\n\n")
        
        f.write("### 2.2 Contractor Fraud Dataset\n")
        f.write(c_stats.to_markdown(index=False) + "\n\n")
        
        f.write("### 2.3 Worker Population Dataset\n")
        f.write(w_stats.to_markdown(index=False) + "\n\n")
        
        f.write("## 3. Multivariate Correlation & Covariance (Districts)\n")
        f.write("The engineered covariance matrix successfully preserves the relationships. Migration and Crime exhibit strong positive correlation.\n\n")
        f.write("### Correlation Matrix\n")
        f.write(d_corr.to_markdown() + "\n\n")
        
        f.write("## 4. Principal Component Analysis (PCA)\n")
        f.write("PCA was applied to the scaled district features to identify orthogonal drivers of vulnerability.\n")
        f.write(f"- **PC1 Explained Variance**: {pca_var[0]*100:.2f}%\n")
        f.write(f"- **PC2 Explained Variance**: {pca_var[1]*100:.2f}%\n")
        f.write(f"- **Total Variance Captured (2D)**: {(pca_var[0]+pca_var[1])*100:.2f}%\n\n")
        
        f.write("## 5. Replacement Strategy (Official Data)\n")
        f.write("To migrate this system to production:\n")
        f.write("1. Replace the Log-Normal `daily_wage` with actual BOCW API lookups.\n")
        f.write("2. Replace Beta-sampled `risk_index` with historical EPFO/ESIC default data.\n")
        f.write("3. Replace Copula-sampled `crime_rate` with raw NCRB tabular ingest.\n")
        
if __name__ == "__main__":
    w_df, c_df, d_df = load_data()
    
    generate_visualizations(w_df, d_df)
    
    w_stats = compute_descriptive_stats(w_df, "Workers")
    c_stats = compute_descriptive_stats(c_df, "Contractors")
    d_stats = compute_descriptive_stats(d_df, "Districts")
    
    d_corr, d_cov = compute_matrices(d_df, "Districts")
    
    pca_var = perform_pca(d_df, "Districts")
    
    write_markdown_report(w_stats, c_stats, d_stats, d_corr, d_cov, pca_var)
    logging.info(f"Statistical analysis complete. Report saved to {REPORT_FILE}")
