import React, { useState } from 'react';
import {
  Line,
  LineChart,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
} from 'recharts';
import { useLatencyData } from '../hooks/useMonitoringData';

export function LatencyChart() {
  const [range, setRange] = useState('24h');
  const data = useLatencyData(range);

  return (
    <div>
      <label htmlFor="latency-range" className="mr-2">
        Range:
      </label>
      <select
        id="latency-range"
        onChange={(e) => setRange(e.target.value)}
        value={range}
      >
        <option value="24h">24h</option>
        <option value="7d">7d</option>
        <option value="30d">30d</option>
      </select>
      <LineChart
        width={400}
        height={200}
        data={data}
        data-testid="latency-chart"
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="timestamp" />
        <YAxis />
        <Tooltip />
        <Line type="monotone" dataKey="value" stroke="#82ca9d" />
      </LineChart>
    </div>
  );
}
