import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report
import joblib
import os

def train_skyguard_models():
    data_path = os.path.join("data", "aws_synthetic_telemetry.csv")
    if not os.path.exists(data_path):
        data_path = "aws_synthetic_telemetry.csv"
        
    df = pd.read_csv(data_path)
    
    # 1. Strict Inputs Only
    features = ['temperature_c', 'humidity_percent', 'pressure_hpa']
    
    df[features] = df[features].fillna(df[features].rolling(window=3, min_periods=1).mean())
    df[features] = df[features].bfill()
    
    X = df[features]
    y_true = df['is_anomaly']

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 2. Train Isolation Forest
    iso_forest = IsolationForest(n_estimators=100, contamination=0.03, random_state=42)
    iso_forest.fit(X_scaled)
    
    iso_preds = iso_forest.predict(X_scaled)
    iso_preds_binary = np.where(iso_preds == -1, 1, 0)
    print(classification_report(y_true, iso_preds_binary, zero_division=0))

    # 3. Train Random Forest Regressor (Contextual Baseline for Corrected Values)
    X_rf = df[['humidity_percent', 'pressure_hpa']]
    y_rf = df['temperature_c']
    
    rf_regressor = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
    rf_regressor.fit(X_rf, y_rf)

    # 4. Save Models
    os.makedirs("ml_models", exist_ok=True)
    joblib.dump(scaler, os.path.join("ml_models", "scaler.pkl"))
    joblib.dump(iso_forest, os.path.join("ml_models", "iso_forest.pkl"))
    joblib.dump(rf_regressor, os.path.join("ml_models", "rf_regressor.pkl"))
    print("Pipeline training complete. Models saved.")

if __name__ == "__main__":
    train_skyguard_models()