"""
Decision Layer v1 - Prompt Builder

組裝 LLM Prompt，包含 Doctrine 條文摘要
"""

from typing import List

from jgod.decision.models import RawScoreItem


def build_decision_prompt(raw_item: RawScoreItem, doctrine_hits: List[any]) -> str:
    """建立 Decision Layer LLM Prompt
    
    Args:
        raw_item: Raw Score 項目
        doctrine_hits: Doctrine 查詢結果列表（DoctrineHit 類型）
    
    Returns:
        完整的 Prompt 字串
    """
    
    # System / Role 說明
    system_role = """你是 J-GOD Decision Layer 的仲裁引擎，任務是依照 Doctrine（交易聖經）修正量化分數。

你的職責：
1. 分析 Raw Score 是否符合 Doctrine 原則
2. 識別風險標籤（如：追高、過度集中、流動性風險）
3. 計算修正係數（correction_factor），用於調整 Raw Score
4. 提供清晰的調整理由

重要規則：
- correction_factor 範圍建議在 0.5 ~ 1.5 之間
- 1.0 = 不修改
- < 1.0 = 降分（風險考量）
- > 1.0 = 加分（需有強力 Doctrine 理由）
- 必須以 JSON 格式回傳結果

輸出格式要求：
{
  "correction_factor": <float>,
  "doctrine_flags": [
    {
      "code": "<flag_code>",
      "severity": "info|warning|critical",
      "message": "<short_message>",
      "doctrine_refs": ["<book_id>#<section_id>", ...]
    }
  ],
  "adjustment_reason": "<human_readable_explanation>"
}
"""
    
    # Input 概況
    input_section = f"""
=== 輸入資料 ===
股票代號: {raw_item.symbol}
股票名稱: {raw_item.name or 'N/A'}
日期: {raw_item.date}

Raw Score: {raw_item.raw_score:.4f}

策略分數:
"""
    
    for strategy, score in raw_item.strategy_scores.items():
        input_section += f"  - {strategy}: {score:.4f}\n"
    
    if raw_item.risk_metrics:
        input_section += "\n風險指標:\n"
        for metric, value in raw_item.risk_metrics.items():
            input_section += f"  - {metric}: {value:.4f}\n"
    
    if raw_item.context_tags:
        input_section += f"\n上下文標籤: {', '.join(raw_item.context_tags)}\n"
    
    # Doctrine 條文摘要
    doctrine_section = "\n=== Doctrine 聖經條文 ===\n"
    if doctrine_hits:
        for i, hit in enumerate(doctrine_hits, 1):
            doctrine_section += f"\n[{i}] 來源: {getattr(hit, 'book_id', 'unknown')}/{getattr(hit, 'section_id', 'unknown')}\n"
            
            summary = getattr(hit, 'summary', None)
            if summary:
                doctrine_section += f"摘要: {summary}\n"
            
            core_principles = getattr(hit, 'core_principles', [])
            if core_principles:
                doctrine_section += "核心原則:\n"
                for principle in core_principles:
                    doctrine_section += f"  - {principle}\n"
            
            risk_rules = getattr(hit, 'risk_rules', [])
            if risk_rules:
                doctrine_section += "風控規則:\n"
                for rule in risk_rules:
                    doctrine_section += f"  - {rule}\n"
            
            tags = getattr(hit, 'tags', [])
            if tags:
                doctrine_section += f"標籤: {', '.join(tags)}\n"
    else:
        doctrine_section += "\n（未找到相關 Doctrine 條文）\n"
    
    # 輸出要求
    output_section = """
=== 輸出要求 ===
請根據上述資料，分析並輸出：
1. correction_factor: 修正係數（建議範圍 0.5 ~ 1.5）
2. doctrine_flags: 風險標籤列表（如有違反或接近 Doctrine 紅線）
3. adjustment_reason: 調整理由（簡潔的中文說明）

請以 JSON 格式回傳。
"""
    
    return system_role + input_section + doctrine_section + output_section

