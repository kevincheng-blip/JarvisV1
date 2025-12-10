/**
 * War Room Page
 * 
 * J-GOD War Room 主頁面
 * 
 * 整合三層架構的所有 Widget
 */

import { WarRoomLayout } from '../layouts/WarRoomLayout';

// Macro Layer Widgets
import { PolicyHealthV2 } from '../components/war-room/macro/PolicyHealthV2';
import { AggregateRisk } from '../components/war-room/macro/AggregateRisk';
import { EquityCurve } from '../components/war-room/macro/EquityCurve';
import { FinalOrders } from '../components/war-room/macro/FinalOrders';
import { ExposureHeatmap } from '../components/war-room/macro/ExposureHeatmap';
import { DecisionEffectCard } from '../components/war-room/macro/DecisionEffectCard';

// Micro Layer Widgets
import { TopLongPanel } from '../components/war-room/micro/TopLongPanel';
import { TopShortPanel } from '../components/war-room/micro/TopShortPanel';
import { SignalConflictMap } from '../components/war-room/micro/SignalConflictMap';
import { MicrostructureFactors } from '../components/war-room/micro/MicrostructureFactors';
import { SRankRankingCard } from '../components/war-room/micro/SRankRankingCard';

// Anomaly Layer Widgets
import { ErrorReplayPanel } from '../components/war-room/anomaly/ErrorReplayPanel';
import { DoctrineAlertPanel } from '../components/war-room/anomaly/DoctrineAlertPanel';
import { PositionHealthPanel } from '../components/war-room/anomaly/PositionHealthPanel';
import { SentimentGauge } from '../components/war-room/anomaly/SentimentGauge';
import { SystemLogStream } from '../components/war-room/anomaly/SystemLogStream';
import { KnowledgeGovernancePanel } from '../components/war-room/anomaly/KnowledgeGovernancePanel';

export function WarRoomPage() {
  return (
    <WarRoomLayout
            anomalyLayer={
              <>
                <KnowledgeGovernancePanel />
                <ErrorReplayPanel />
                <DoctrineAlertPanel />
                <PositionHealthPanel />
                <SentimentGauge />
                <SystemLogStream />
              </>
            }
      macroLayer={
        <>
          <PolicyHealthV2 />
          <DecisionEffectCard />
          <AggregateRisk />
          <EquityCurve />
          <ExposureHeatmap />
          <FinalOrders />
        </>
      }
      microLayer={
        <>
          <SRankRankingCard />
          <TopLongPanel />
          <TopShortPanel />
          <SignalConflictMap />
          <MicrostructureFactors />
        </>
      }
    />
  );
}

