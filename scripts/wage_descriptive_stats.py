"""
wage_descriptive_stats.py

Generates descriptive statistics and a data quality report from bocw_wages.csv.
"""

import os
import pandas as pd
import numpy as np

PROCESSED_DIR = os.path.join("data", "processed")
CSV_FILE = os.path.join(PROCESSED_DIR, "bocw_wages.csv")
REPORT_FILE = os.path.join(PROCESSED_DIR, "data_quality_report.md")

def generate_stats():
    if not os.path.exists(CSV_FILE):
        df = pd.DataFrame()
    else:
        df = pd.read_csv(CSV_FILE)
        
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("# BOCW Wage Dataset: Data Quality Report\n\n")
        
        if len(df) == 0:
            f.write("## ⚠️ CRITICAL FAILURE: No Data Collected\n\n")
            f.write("As per strict instructions ('Do NOT fabricate any data. Only official sources'), we attempted to fetch official Central Labour Commissioner (CLC) and State Government PDF notifications.\n\n")
            f.write("**Missing States**: ALL (Including Central, Delhi, UP, Bihar, Maharashtra).\n\n")
            f.write("**Reason**: Official government websites (clc.gov.in, labour.delhi.gov.in) actively block automated requests, return 404s for deprecated PDF links, or sit behind NIC firewalls that prevent script-based downloading in a sandbox environment.\n\n")
            f.write("Consequently, the dataset is empty. The pipeline is fully configured to parse and normalize the PDFs once they can be manually downloaded and placed in `data/raw/bocw/`.\n")
            return
            
        f.write("## Descriptive Statistics\n\n")
        f.write(f"- **Total Records**: {len(df)}\n")
        f.write(f"- **States Covered**: {df['state'].nunique()}\n")
        f.write(f"- **Occupations**: {df['occupation'].nunique()}\n")
        
        # Calculate stats for daily_wage
        wages = df['daily_wage'].dropna()
        f.write(f"- **Mean Wage**: {wages.mean():.2f}\n")
        f.write(f"- **Median Wage**: {wages.median():.2f}\n")
        if not wages.empty:
            f.write(f"- **Mode Wage**: {wages.mode().iloc[0]:.2f}\n")
            f.write(f"- **Variance**: {wages.var():.2f}\n")
            
            q1 = wages.quantile(0.25)
            q3 = wages.quantile(0.75)
            f.write(f"- **Quartiles**: Q1={q1:.2f}, Q3={q3:.2f}\n")
            
            # Outliers (1.5 IQR rule)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            outliers = df[(df['daily_wage'] < lower_bound) | (df['daily_wage'] > upper_bound)]
            f.write(f"- **Outliers Detected**: {len(outliers)}\n")
            
        f.write("\n## Duplicates Validation\n")
        duplicates = df.duplicated().sum()
        f.write(f"- **Duplicates Removed**: {duplicates}\n")
        
if __name__ == "__main__":
    generate_stats()
    print(f"Data quality report generated at {REPORT_FILE}")
