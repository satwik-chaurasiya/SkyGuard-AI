import joblib
import pandas as pd
import numpy as np
import os
import shap
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="SkyGuard AI - AWS Telemetry Anomaly Detection")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, "ml_models")

scaler = joblib.load(os.path.join(MODEL_DIR, "scaler.pkl"))
iso_forest = joblib.load(os.path.join(MODEL_DIR, "iso_forest.pkl"))
rf_regressor = joblib.load(os.path.join(MODEL_DIR, "rf_regressor.pkl"))

# Initialize SHAP explainer for Explainable AI (XAI)
explainer = shap.TreeExplainer(iso_forest)
feature_names = ['Temperature', 'Humidity', 'Pressure']

# Strict inputs: No Wind Speed
class TelemetryData(BaseModel):
    station_id: str
    temperature_c: float
    humidity_percent: float
    pressure_hpa: float

@app.post("/ingest")
async def ingest_telemetry(data: TelemetryData):
    features_df = pd.DataFrame([{
        'temperature_c': data.temperature_c,
        'humidity_percent': data.humidity_percent,
        'pressure_hpa': data.pressure_hpa
    }])
    
    scaled_features = scaler.transform(features_df)
    
    # 1. Unsupervised Anomaly Detection & Severity Score
    iso_pred = iso_forest.predict(scaled_features)[0]
    anomaly_score_raw = iso_forest.decision_function(scaled_features)[0]
    
    is_spike_anomaly = bool(iso_pred == -1)
    
    # Map raw decision threshold to a 0-100% confidence/severity score
    severity_score = 0.0
    if is_spike_anomaly:
        severity_score = min(100.0, round(abs(anomaly_score_raw) * 200 + 70, 1))
    
    # 2. Contextual Drift & Corrected Estimation
    rf_features = features_df[['humidity_percent', 'pressure_hpa']]
    expected_temp = rf_regressor.predict(rf_features)[0]
    temp_diff = abs(expected_temp - data.temperature_c)
    
    is_drift_anomaly = bool(temp_diff > 5.0)
    is_anomaly = is_spike_anomaly or is_drift_anomaly
    
    if is_drift_anomaly and not is_spike_anomaly:
        severity_score = min(100.0, round((temp_diff / 15.0) * 100 + 60, 1))
    
    # 3. Explainable AI: Identify the Root Cause
    root_cause = "None"
    if is_anomaly:
        shap_values = explainer.shap_values(scaled_features)
        # Find which sensor deviated the most from the normal baseline
        max_idx = np.argmax(np.abs(shap_values[0]))
        root_cause = feature_names[max_idx]
        
        # Override for contextual drift
        if is_drift_anomaly and not is_spike_anomaly:
            root_cause = "Temperature vs. Baseline Drift"

    return {
        "station_id": data.station_id,
        "is_anomaly": is_anomaly,
        "severity_score": severity_score,
        "root_cause": root_cause,
        "anomaly_details": {
            "spike_detected": is_spike_anomaly,
            "drift_detected": is_drift_anomaly,
            "expected_temperature": round(expected_temp, 2), # Corrected Data Estimation
            "deviation": round(temp_diff, 2)
        }
    }

@app.get("/status")
async def get_status():
    return {"status": "Engine Running", "models_loaded": True, "shap_enabled": True}