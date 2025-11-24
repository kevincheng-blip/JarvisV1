"""
決策引擎：彙整多 AI 意見並產生最終決策
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import statistics

from .ai_council import AIOpinion, run_war_room


@dataclass
class Consensus:
    """共識結果"""
    direction: str  # "buy", "sell", "hold"
    confidence: float  # 0.0-1.0
    reasoning: str
    supporting_opinions: List[str]
    opposing_opinions: List[str]
    timestamp: datetime


class DecisionEngine:
    """
    決策引擎
    
    功能：
    - 彙整多個 AI 的意見
    - 產生共識決策
    - 計算信心度
    """
    
    def __init__(self):
        """初始化決策引擎"""
        pass
    
    def generate_consensus(
        self,
        opinions: List[AIOpinion],
    ) -> Consensus:
        """
        從多個 AI 意見產生共識
        
        Args:
            opinions: AI 意見列表
        
        Returns:
            共識結果
        """
        if not opinions:
            return Consensus(
                direction="hold",
                confidence=0.0,
                reasoning="沒有足夠的意見",
                supporting_opinions=[],
                opposing_opinions=[],
                timestamp=datetime.now(),
            )
        
        # 統計方向
        directions = []
        confidences = []
        buy_count = 0
        sell_count = 0
        hold_count = 0
        
        for opinion in opinions:
            stance = opinion.stance.lower()
            if "多" in stance or "buy" in stance.lower():
                directions.append("buy")
                buy_count += 1
            elif "空" in stance or "sell" in stance.lower():
                directions.append("sell")
                sell_count += 1
            else:
                directions.append("hold")
                hold_count += 1
            
            confidences.append(opinion.confidence)
        
        # 決定主要方向
        if buy_count > sell_count and buy_count > hold_count:
            direction = "buy"
        elif sell_count > buy_count and sell_count > hold_count:
            direction = "sell"
        else:
            direction = "hold"
        
        # 計算平均信心度
        avg_confidence = statistics.mean(confidences) if confidences else 0.0
        
        # 計算一致性（相同方向的意見比例）
        same_direction_count = sum(1 for d in directions if d == direction)
        consistency = same_direction_count / len(directions) if directions else 0.0
        
        # 最終信心度 = 平均信心度 * 一致性
        final_confidence = avg_confidence * consistency
        
        # 收集支持意見
        supporting_opinions = [
            f"{op.display_name}: {op.content[:50]}..."
            for op in opinions
            if (direction == "buy" and ("多" in op.stance or "buy" in op.stance.lower())) or
               (direction == "sell" and ("空" in op.stance or "sell" in op.stance.lower())) or
               (direction == "hold" and op.stance == "中性")
        ]
        
        # 收集反對意見
        opposing_opinions = [
            f"{op.display_name}: {op.content[:50]}..."
            for op in opinions
            if op not in [o for o in opinions if o.display_name in [s.split(":")[0] for s in supporting_opinions]]
        ]
        
        # 產生推理說明
        reasoning = f"""
        共識方向：{direction}
        支持意見：{len(supporting_opinions)}/{len(opinions)}
        平均信心度：{avg_confidence:.2f}
        一致性：{consistency:.2f}
        """.strip()
        
        return Consensus(
            direction=direction,
            confidence=final_confidence,
            reasoning=reasoning,
            supporting_opinions=supporting_opinions,
            opposing_opinions=opposing_opinions,
            timestamp=datetime.now(),
        )
    
    def make_decision(
        self,
        question: str,
        stock_id: Optional[str] = None,
        jg_state: Optional[Dict[str, Any]] = None,
        selected_providers: Optional[List[str]] = None,
    ) -> Consensus:
        """
        做出決策（整合戰情室和共識產生）
        
        Args:
            question: 問題
            stock_id: 股票代號
            jg_state: J-GOD 狀態
            selected_providers: 選擇的 AI 提供者
        
        Returns:
            共識決策
        """
        # 執行戰情室
        opinions_dict, summary = run_war_room(
            question=question,
            stock_id=stock_id,
            jg_state=jg_state,
            selected_providers=selected_providers,
        )
        
        # 轉換為 AIOpinion 物件
        opinions = [
            AIOpinion(
                role_id=op.get("role_id", ""),
                display_name=op.get("display_name", ""),
                provider=op.get("provider", ""),
                content=op.get("content", ""),
                stance=op.get("stance", "中性"),
                confidence=op.get("confidence", 0.5),
            )
            for op in opinions_dict
        ]
        
        # 產生共識
        consensus = self.generate_consensus(opinions)
        
        return consensus

