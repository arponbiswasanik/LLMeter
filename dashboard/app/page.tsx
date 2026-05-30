"use client";

import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

const API_BASE = "http://127.0.0.1:8000";

interface AnomalyStats {
  window_size: number;
  mean_latency_ms: number;
  error_rate: number;
  total_requests: number;
}

interface RecoveryStatus {
  status: string;
  active_model: string;
  using_fallback: boolean;
  reason: string;
  total_incidents: number;
  incident_log: { incident_id: number; reason: string; action: string }[];
}

interface Event {
  request_id: string;
  timestamp: string;
  prompt: string;
  response: string;
  model: string;
  latency_ms: string;
  fallback_used: string;
  flagged: string;
  flag_reason: string;
}

interface DriftStatus {
  drift_detected: boolean;
  reason: string;
  p_value: number | null;
  reference_mean: number;
  current_mean: number;
}

export default function Dashboard() {
  const [anomaly, setAnomaly] = useState<AnomalyStats | null>(null);
  const [recovery, setRecovery] = useState<RecoveryStatus | null>(null);
  const [events, setEvents] = useState<Event[]>([]);
  const [drift, setDrift] = useState<DriftStatus | null>(null);
  const [latencyHistory, setLatencyHistory] = useState<{ time: string; latency: number }[]>([]);

  const fetchData = async () => {
    const [a, r, e, d] = await Promise.all([
      fetch(`${API_BASE}/anomalies`).then((res) => res.json()),
      fetch(`${API_BASE}/recovery`).then((res) => res.json()),
      fetch(`${API_BASE}/events`).then((res) => res.json()),
      fetch(`${API_BASE}/drift`).then((res) => res.json()),
    ]);
    setAnomaly(a);
    setRecovery(r);
    setEvents(e.recent_events || []);
    setDrift(d);

    const history = (e.recent_events || [])
      .slice(0, 20)
      .reverse()
      .map((ev: Event) => ({
        time: new Date(parseFloat(ev.timestamp) * 1000).toLocaleTimeString(),
        latency: parseFloat(ev.latency_ms),
      }));
    setLatencyHistory(history);
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6">
      <h1 className="text-3xl font-bold mb-2">LLMeter Dashboard</h1>
      <p className="text-gray-400 mb-8">Real-time LLM monitoring & anomaly detection</p>

      {/* Status Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard label="Total Requests" value={anomaly?.total_requests ?? 0} />
        <StatCard label="Mean Latency" value={`${anomaly?.mean_latency_ms ?? 0}ms`} />
        <StatCard label="Error Rate" value={`${((anomaly?.error_rate ?? 0) * 100).toFixed(1)}%`} />
        <StatCard
          label="System Status"
          value={recovery?.status ?? "—"}
          highlight={recovery?.status === "healthy" ? "green" : "red"}
        />
      </div>

      {/* Active Model */}
      <div className="bg-gray-900 rounded-xl p-4 mb-8">
        <p className="text-gray-400 text-sm mb-1">Active Model</p>
        <p className="text-xl font-semibold">{recovery?.active_model ?? "—"}</p>
        {recovery?.using_fallback && (
          <p className="text-yellow-400 text-sm mt-1">⚠️ Using fallback — {recovery.reason}</p>
        )}
      </div>

      {/* Latency Chart */}
      <div className="bg-gray-900 rounded-xl p-4 mb-8">
        <h2 className="text-lg font-semibold mb-4">Latency History</h2>
        {latencyHistory.length > 0 ? (
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={latencyHistory}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="time" stroke="#9CA3AF" tick={{ fontSize: 11 }} />
              <YAxis stroke="#9CA3AF" tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={{ backgroundColor: "#1F2937", border: "none" }} />
              <Line type="monotone" dataKey="latency" stroke="#6366F1" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <p className="text-gray-500 text-sm">No data yet — send some requests first.</p>
        )}
      </div>

      {/* Drift Detection */}
      <div className="bg-gray-900 rounded-xl p-4 mb-8">
        <h2 className="text-lg font-semibold mb-4">Output Drift Detection</h2>
        <div className="flex gap-4">
          <div className="flex-1 bg-gray-800 rounded-lg p-3">
            <p className="text-gray-400 text-sm">Status</p>
            <p className={`text-xl font-bold ${drift?.drift_detected ? "text-red-400" : "text-green-400"}`}>
              {drift?.drift_detected ? "⚠️ Drift Detected" : "✅ Stable"}
            </p>
          </div>
          <div className="flex-1 bg-gray-800 rounded-lg p-3">
            <p className="text-gray-400 text-sm">Reference Mean</p>
            <p className="text-xl font-bold">{drift?.reference_mean ?? 0} words</p>
          </div>
          <div className="flex-1 bg-gray-800 rounded-lg p-3">
            <p className="text-gray-400 text-sm">Current Mean</p>
            <p className="text-xl font-bold">{drift?.current_mean ?? 0} words</p>
          </div>
          <div className="flex-1 bg-gray-800 rounded-lg p-3">
            <p className="text-gray-400 text-sm">P-Value</p>
            <p className="text-xl font-bold">{drift?.p_value ?? "—"}</p>
          </div>
        </div>
        <p className="text-gray-500 text-sm mt-2">{drift?.reason}</p>
      </div>

      {/* Incident Log */}
      <div className="bg-gray-900 rounded-xl p-4 mb-8">
        <h2 className="text-lg font-semibold mb-4">
          Incident Log ({recovery?.total_incidents ?? 0})
        </h2>
        {recovery?.incident_log.length ? (
          <div className="space-y-2">
            {recovery.incident_log.map((inc) => (
              <div key={inc.incident_id} className="bg-gray-800 rounded-lg p-3">
                <p className="text-red-400 text-sm font-medium">#{inc.incident_id} — {inc.reason}</p>
                <p className="text-gray-400 text-xs mt-1">→ {inc.action}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-sm">No incidents recorded.</p>
        )}
      </div>

      {/* Recent Events */}
      <div className="bg-gray-900 rounded-xl p-4">
        <h2 className="text-lg font-semibold mb-4">Recent Events</h2>
        <div className="space-y-2">
          {events.slice(0, 10).map((ev) => (
            <div key={ev.request_id} className="bg-gray-800 rounded-lg p-3">
              <div className="flex justify-between items-center mb-1">
                <span className="text-xs text-gray-400">{ev.model}</span>
                <span className="text-xs text-gray-400">{ev.latency_ms}ms</span>
                {ev.flagged === "True" && (
                  <span className="text-xs text-red-400">🚨 Flagged</span>
                )}
              </div>
              <p className="text-sm text-gray-300 truncate">Q: {ev.prompt}</p>
              <p className="text-sm text-gray-500 truncate">A: {ev.response}</p>
            </div>
          ))}
          {events.length === 0 && (
            <p className="text-gray-500 text-sm">No events yet.</p>
          )}
        </div>
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  highlight,
}: {
  label: string;
  value: string | number;
  highlight?: "green" | "red";
}) {
  const color =
    highlight === "green"
      ? "text-green-400"
      : highlight === "red"
      ? "text-red-400"
      : "text-white";

  return (
    <div className="bg-gray-900 rounded-xl p-4">
      <p className="text-gray-400 text-sm mb-1">{label}</p>
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
    </div>
  );
}