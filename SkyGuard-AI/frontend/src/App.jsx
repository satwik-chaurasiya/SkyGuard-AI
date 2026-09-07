import { useState, useEffect, useRef } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { AlertTriangle, CheckCircle, Thermometer, Droplets, Gauge, Activity, ShieldAlert } from 'lucide-react';
import './App.css';

export default function App() {
  const [telemetry, setTelemetry] = useState([]);
  const [status, setStatus] = useState("Connecting...");
  const [latest, setLatest] = useState(null);
  const timeRef = useRef(0);

  useEffect(() => {
    fetch('http://127.0.0.1:8000/status')
      .then(res => res.json())
      .then(data => setStatus(data.status))
      .catch(() => setStatus("Backend Offline"));
  }, []);

  useEffect(() => {
    const interval = setInterval(async () => {
      timeRef.current += 1;
      
      const isSpike = Math.random() > 0.9;
      
      const payload = {
        station_id: "AWS-NOIDA-01",
        temperature_c: 25 + (Math.sin(timeRef.current) * 2) + (isSpike ? 15 : 0),
        humidity_percent: 60 + (Math.random() * 5),
        pressure_hpa: 1012 + (Math.random() * 2)
      };

      try {
        const response = await fetch('http://127.0.0.1:8000/ingest', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        
        const prediction = await response.json();
        const newPoint = {
          time: new Date().toLocaleTimeString('en-US', { hour12: false }),
          temperature: parseFloat(payload.temperature_c.toFixed(2)),
          isAnomaly: prediction.is_anomaly
        };

        setLatest({ ...payload, prediction });
        setTelemetry(prev => [...prev.slice(-19), newPoint]); 
      } catch (error) {
        console.error("Connection failed", error);
      }
    }, 2500);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="dashboard-container">
      <div className="header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <Activity size={32} color="#3b82f6" />
          <h1 style={{ margin: 0 }}>SkyGuard AI Console</h1>
        </div>
        <div className={`status-badge ${status.includes('Offline') ? 'status-offline' : 'status-online'}`}>
          {status.includes('Offline') ? <AlertTriangle size={16} /> : <CheckCircle size={16} />}
          {status}
        </div>
      </div>

      {latest && latest.prediction.is_anomaly && (
        <div className="card" style={{ background: '#7f1d1d', borderColor: '#ef4444', marginBottom: '2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <h3 style={{ margin: '0 0 0.5rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <ShieldAlert color="#fca5a5" /> Corrupted Telemetry Blocked
              </h3>
              <p style={{ margin: 0, color: '#fecaca', marginBottom: '0.5rem' }}>
                {latest.prediction.anomaly_details.spike_detected ? "Hardware voltage spike isolated." : "Contextual environmental drift flagged."}
              </p>
              <div style={{ display: 'flex', gap: '1rem', fontSize: '0.875rem', color: '#f87171' }}>
                <span><strong>SHAP Root Cause:</strong> {latest.prediction.root_cause}</span>
                <span><strong>Corrected Estimate:</strong> {latest.prediction.anomaly_details.expected_temperature}°C</span>
              </div>
            </div>
            <div style={{ background: '#991b1b', padding: '0.5rem 1rem', borderRadius: '8px', textAlign: 'center' }}>
              <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#fca5a5', fontWeight: 'bold' }}>Severity</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#fff' }}>
                {latest.prediction.severity_score}%
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="grid">
        <div className="card">
          <div className="card-header"><Thermometer size={20} /> Temperature</div>
          <div className={`card-value ${latest?.prediction?.is_anomaly ? 'anomaly' : ''}`}>
            {latest ? latest.temperature_c.toFixed(1) : '--'}°C
          </div>
        </div>
        <div className="card">
          <div className="card-header"><Droplets size={20} /> Humidity</div>
          <div className="card-value">{latest ? latest.humidity_percent.toFixed(1) : '--'}%</div>
        </div>
        <div className="card">
          <div className="card-header"><Gauge size={20} /> Pressure</div>
          <div className="card-value">{latest ? latest.pressure_hpa.toFixed(1) : '--'} hPa</div>
        </div>
      </div>

      <div className="chart-container">
        <h3 style={{ marginTop: 0, color: '#94a3b8' }}>Live Temperature Telemetry Feed</h3>
        <ResponsiveContainer width="100%" height="90%">
          <LineChart data={telemetry}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="time" stroke="#94a3b8" />
            <YAxis stroke="#94a3b8" domain={['dataMin - 5', 'dataMax + 5']} />
            <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155' }} />
            <Line 
              type="monotone" 
              dataKey="temperature" 
              stroke="#3b82f6" 
              strokeWidth={2}
              isAnimationActive={false}
              dot={(props) => {
                const { cx, cy, payload, key } = props;
                if (payload.isAnomaly) {
                  return <circle key={key} cx={cx} cy={cy} r={6} fill="#ef4444" stroke="#7f1d1d" strokeWidth={2} />;
                }
                return <circle key={key} cx={cx} cy={cy} r={3} fill="#3b82f6" />;
              }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}