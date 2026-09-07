import pandas as pd
import numpy as np
import os

def generate_synthetic_aws_data(days=365):
    hours = days * 24
    time_idx = pd.date_range(start="2024-01-01", periods=hours, freq="h")
    
    daily_cycle = np.sin(2 * np.pi * time_idx.hour / 24)
    yearly_cycle = np.sin(2 * np.pi * time_idx.dayofyear / 365)
    
    temperature = 20 + 5 * daily_cycle + 10 * yearly_cycle + np.random.normal(0, 1, hours)
    humidity = 60 - 15 * daily_cycle + np.random.normal(0, 3, hours) 
    pressure = 1013 + np.random.normal(0, 2, hours)
    
    df = pd.DataFrame({
        'timestamp': time_idx,
        'temperature_c': temperature,
        'humidity_percent': np.clip(humidity, 0, 100),
        'pressure_hpa': pressure,
        'is_anomaly': 0,
        'anomaly_type': 'none'
    })
    
    np.random.seed(42)
    n_anomalies = int(hours * 0.03) 
    
    valid_indices = df.index[:-24]
    anomaly_starts = np.random.choice(valid_indices, n_anomalies, replace=False)
    
    for idx in anomaly_starts:
        if df.at[idx, 'is_anomaly'] == 1:
            continue
            
        anomaly_class = np.random.choice(['spike', 'freeze', 'drift', 'null'])
        
        if anomaly_class == 'spike':
            df.at[idx, 'temperature_c'] += np.random.choice([1, -1]) * np.random.uniform(15, 30)
            df.at[idx, 'is_anomaly'] = 1
            df.at[idx, 'anomaly_type'] = 'spike'
            
        elif anomaly_class == 'freeze':
            frozen_val = df.at[idx, 'humidity_percent']
            df.loc[idx:idx+5, 'humidity_percent'] = frozen_val
            df.loc[idx:idx+5, 'is_anomaly'] = 1
            df.loc[idx:idx+5, 'anomaly_type'] = 'freeze'
            
        elif anomaly_class == 'drift':
            drift_values = np.linspace(0.5, 10, 24)
            df.loc[idx:idx+23, 'pressure_hpa'] += drift_values
            df.loc[idx:idx+23, 'is_anomaly'] = 1
            df.loc[idx:idx+23, 'anomaly_type'] = 'drift'
            
        elif anomaly_class == 'null':
            df.at[idx, 'temperature_c'] = np.nan
            df.at[idx, 'is_anomaly'] = 1
            df.at[idx, 'anomaly_type'] = 'null'

    return df

if __name__ == "__main__":
    print("Generating telemetry (Strict Inputs: Temp, Humidity, Pressure)...")
    telemetry_df = generate_synthetic_aws_data(days=365)
    
    os.makedirs("data", exist_ok=True)
    telemetry_df.to_csv("data/aws_synthetic_telemetry.csv", index=False)
    print("Dataset saved to 'data/aws_synthetic_telemetry.csv'.")