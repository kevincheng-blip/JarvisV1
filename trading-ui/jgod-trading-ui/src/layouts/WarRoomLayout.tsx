/**
 * WarRoomLayout Component
 * 
 * War Room 三層配置 Layout
 * 
 * Anomaly Layer (25%) | Macro Layer (50%) | Micro Layer (25%)
 */

import { ReactNode } from 'react';

interface WarRoomLayoutProps {
  anomalyLayer: ReactNode;
  macroLayer: ReactNode;
  microLayer: ReactNode;
}

export function WarRoomLayout({ anomalyLayer, macroLayer, microLayer }: WarRoomLayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-4">
      <div className="max-w-[1920px] mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            J-GOD War Room
          </h1>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            行動決策中心 · Macro / Micro / Anomaly Layer
          </p>
        </div>

        {/* Three-Layer Layout */}
        <div className="grid grid-cols-12 gap-4">
          {/* Anomaly Layer - 25% (3 columns) */}
          <div className="col-span-12 lg:col-span-3 space-y-4">
            {anomalyLayer}
          </div>

          {/* Macro Layer - 50% (6 columns) */}
          <div className="col-span-12 lg:col-span-6 space-y-4">
            {macroLayer}
          </div>

          {/* Micro Layer - 25% (3 columns) */}
          <div className="col-span-12 lg:col-span-3 space-y-4">
            {microLayer}
          </div>
        </div>
      </div>
    </div>
  );
}

