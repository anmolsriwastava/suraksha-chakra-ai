import pandas as pd
import numpy as np
import json
import joblib
import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from pathlib import Path

np.random.seed(42)

DISTRICTS = [
    # UP
    ("Lucknow", "UP", "lower", "lower"), ("Noida", "UP", "very low", "very low"),
    ("Gorakhpur", "UP", "high", "high"), ("Azamgarh", "UP", "high", "very high"),
    ("Ballia", "UP", "high", "high"), ("Varanasi", "UP", "moderate", "high"),
    ("Agra", "UP", "moderate", "moderate"), ("Kanpur", "UP", "moderate", "moderate"),
    ("Ghazipur", "UP", "high", "high"), ("Deoria", "UP", "high", "high"),
    ("Mau", "UP", "high", "high"), ("Jaunpur", "UP", "high", "high"),
    ("Pratapgarh", "UP", "high", "high"), ("Mirzapur", "UP", "moderate", "moderate"),
    ("Sonbhadra", "UP", "moderate", "moderate"), ("Chandauli", "UP", "moderate", "moderate"),
    ("Gonda", "UP", "high", "moderate"), ("Basti", "UP", "high", "moderate"),
    ("Bahraich", "UP", "high", "moderate"), ("Siddharthnagar", "UP", "high", "high"),
    ("Maharajganj", "UP", "high", "high"), ("Sant Kabir Nagar", "UP", "high", "moderate"),
    ("Kushinagar", "UP", "high", "high"), ("Shravasti", "UP", "high", "high"),
    ("Balrampur", "UP", "high", "high"),
    # Bihar
    ("Patna", "Bihar", "lower", "lower"), ("Gaya", "Bihar", "lower", "moderate"),
    ("Darbhanga", "Bihar", "high", "high"), ("Sitamarhi", "Bihar", "high", "high"),
    ("Supaul", "Bihar", "high", "high"), ("Kishanganj", "Bihar", "high", "high"),
    ("Muzaffarpur", "Bihar", "high", "high"), ("Purnia", "Bihar", "high", "high"),
    ("Samastipur", "Bihar", "high", "high"), ("Madhubani", "Bihar", "high", "high"),
    ("Saharsa", "Bihar", "high", "high"), ("Madhepura", "Bihar", "high", "high"),
    ("Araria", "Bihar", "high", "high"), ("Katihar", "Bihar", "high", "high"),
    ("Khagaria", "Bihar", "high", "high"), ("Begusarai", "Bihar", "moderate", "moderate"),
    ("Bhagalpur", "Bihar", "moderate", "moderate"), ("Munger", "Bihar", "moderate", "moderate"),
    ("Banka", "Bihar", "moderate", "moderate"), ("Jamui", "Bihar", "moderate", "moderate"),
    ("Nawada", "Bihar", "moderate", "high"), ("Aurangabad", "Bihar", "moderate", "moderate"),
    ("Rohtas", "Bihar", "lower", "moderate"), ("Bhojpur", "Bihar", "lower", "moderate"),
    ("Buxar", "Bihar", "lower", "moderate"), ("Saran", "Bihar", "moderate", "high"),
    ("Siwan", "Bihar", "moderate", "high"), ("Gopalganj", "Bihar", "moderate", "high"),
    ("Vaishali", "Bihar", "moderate", "moderate"), ("West Champaran", "Bihar", "high", "high"),
    ("East Champaran", "Bihar", "high", "high"), ("Sheohar", "Bihar", "high", "high")
]

def get_base_metrics(vuln_level):
    if vuln_level == "very low":
        return {"crime": (1.0, 0.1), "migration": (10, 5), "flood": (10, 5)}
    elif vuln_level == "lower":
        return {"crime": (1.1, 0.2), "migration": (20, 5), "flood": (20, 10)}
    elif vuln_level == "moderate":
        return {"crime": (1.3, 0.3), "migration": (35, 10), "flood": (40, 15)}
    elif vuln_level == "high":
        return {"crime": (1.8, 0.4), "migration": (55, 15), "flood": (70, 15)}
    elif vuln_level == "very high":
        return {"crime": (2.2, 0.5), "migration": (70, 15), "flood": (85, 10)}
    return {"crime": (1.0, 0.1), "migration": (10, 5), "flood": (10, 5)}

def generate_data():
    data = []
    # To get statistical significance, we'll generate 1000 synthetic samples based on the 57 distinct profiles
    for _ in range(20):
        for d, s, f_level, m_level in DISTRICTS:
            f_metrics = get_base_metrics(f_level)
            m_metrics = get_base_metrics(m_level)
            
            crime_ratio = max(1.0, np.random.normal(f_metrics["crime"][0], f_metrics["crime"][1]))
            migration_rate = max(0, min(100, np.random.normal(m_metrics["migration"][0], m_metrics["migration"][1])))
            flood_severity = max(0, min(100, np.random.normal(f_metrics["flood"][0], f_metrics["flood"][1])))
            
            logit = -6.0 + 1.5 * crime_ratio + 0.05 * migration_rate + 0.03 * flood_severity
            prob = 1 / (1 + np.exp(-logit))
            risk_label = 1 if np.random.rand() < prob else 0
            
            data.append({
                "district": d,
                "state": s,
                "post_disaster_crime_ratio": crime_ratio,
                "outmigration_rate_pct": migration_rate,
                "flood_severity": flood_severity,
                "risk_label": risk_label
            })
        
    df = pd.DataFrame(data)
    
    # Save CSVs (aggregated to mean for district level file)
    district_df = df.groupby(["district", "state"]).mean().reset_index()
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    district_df[["district", "state", "post_disaster_crime_ratio"]].to_csv("data/raw/ncrb_district_crime.csv", index=False)
    district_df[["district", "state", "outmigration_rate_pct"]].to_csv("data/raw/district_migration.csv", index=False)
    
    return df

def train_model(df):
    features = ["post_disaster_crime_ratio", "outmigration_rate_pct", "flood_severity"]
    X = df[features]
    y = df["risk_label"]
    
    model = LogisticRegression(class_weight="balanced")
    model.fit(X, y)
    
    y_pred = model.predict(X)
    y_prob = model.predict_proba(X)[:, 1]
    
    print("--- Model Training Complete ---")
    print(f"Accuracy: {accuracy_score(y, y_pred):.3f}")
    print(f"Precision: {precision_score(y, y_pred):.3f}")
    print(f"Recall: {recall_score(y, y_pred):.3f}")
    print(f"F1 Score: {f1_score(y, y_pred):.3f}")
    print(f"ROC-AUC: {roc_auc_score(y, y_prob):.3f}")
    
    print(f'sklearn version: {sklearn.__version__}')
    print(f'Model trained successfully, coefficients: {model.coef_}')
    
    Path("data").mkdir(exist_ok=True)
    joblib.dump(model, "data/vulnerability_model.pkl")
    print("Saved model to data/vulnerability_model.pkl")

if __name__ == "__main__":
    df = generate_data()
    train_model(df)
