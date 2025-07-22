// @flow
import React from 'react';
import { useAlertStatus } from '../hooks/useMonitoringData';

/**
 * Show whether the monitoring system is currently alerting.
 */

export function AlertStatusIndicator() {
  const alert = useAlertStatus(2);
  return (
    <div data-testid="alert-status" className="font-bold">
      {alert ? (
        <span className="text-red-600">ALERT</span>
      ) : (
        <span className="text-green-600">OK</span>
      )}
    </div>
  );
}
