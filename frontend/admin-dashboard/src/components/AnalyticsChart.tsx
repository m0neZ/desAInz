import React, { useState } from 'react';
import {
  Line,
  LineChart,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
} from 'recharts';
import { useAnalyticsData } from '../hooks/useMonitoringData';

export function AnalyticsChart() {
  const [range, setRange] = useState('24h');
  const data = useAnalyticsData(range);

  return (
    <div>
      <label htmlFor="analytics-range" className="mr-2">
        Range:
      </label>
      <select
        id="analytics-range"
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
        data-testid="analytics-chart"
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="timestamp" />
        <YAxis />
        <Tooltip />
        <Line type="monotone" dataKey="value" stroke="#8884d8" />
      </LineChart>
    </div>
  );
}
