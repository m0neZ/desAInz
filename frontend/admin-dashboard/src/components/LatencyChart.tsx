// @flow
import React, { useState } from 'react';
import dynamic from 'next/dynamic';
import { useLatencyData } from '../hooks/useMonitoringData';

const Line = dynamic(
  async () => {
    const [chartJs, chart] = await Promise.all([
      import('chart.js'),
      import('react-chartjs-2'),
    ]);
    const {
      Chart: ChartJS,
      LineElement,
      PointElement,
      CategoryScale,
      LinearScale,
      Tooltip,
      Legend,
    } = chartJs;
    ChartJS.register(
      LineElement,
      PointElement,
      CategoryScale,
      LinearScale,
      Tooltip,
      Legend
    );
    return chart.Line;
  },
  { ssr: false }
);

export const LatencyChart = React.memo(function LatencyChart() {
  const [range, setRange] = useState('24h');
  const { data } = useLatencyData(range);

  const chartData = {
    labels: data?.map((d) => d.timestamp) ?? [],
    datasets: [
      {
        label: 'latency',
        data: data?.map((d) => d.value) ?? [],
        borderColor: '#82ca9d',
      },
    ],
  };

  return (
    <div>
      <label htmlFor="latency-range" className="mr-2">
        Range:
      </label>
      <select
        id="latency-range"
        aria-label="Latency range"
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
        data-testid="latency-chart"
      />
    </div>
  );
});
