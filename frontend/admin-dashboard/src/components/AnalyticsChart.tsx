import React, { useState } from 'react';
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { useAnalyticsData } from '../hooks/useMonitoringData';

ChartJS.register(
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend
);

export function AnalyticsChart() {
  const [range, setRange] = useState('24h');
  const { data } = useAnalyticsData(range);

  const chartData = {
    labels: data?.map((d) => d.timestamp) ?? [],
    datasets: [
      {
        label: 'value',
        data: data?.map((d) => d.value) ?? [],
        borderColor: '#8884d8',
      },
    ],
  };

  return (
    <div>
      <label htmlFor="analytics-range" className="mr-2">
        Range:
      </label>
      <select
        id="analytics-range"
        aria-label="Analytics range"
        onChange={(e) => setRange(e.target.value)}
        value={range}
      >
        <option value="24h">24h</option>
        <option value="7d">7d</option>
        <option value="30d">30d</option>
      </select>
      <Line
        options={{ responsive: true }}
        data={chartData}
        data-testid="analytics-chart"
      />
    </div>
  );
}
