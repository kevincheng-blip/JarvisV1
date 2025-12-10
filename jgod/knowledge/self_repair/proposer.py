"""Repair Proposer

Generates fix proposals for consistency issues found during scanning.
"""

import logging
import uuid
from typing import List, Optional, Protocol

from jgod.knowledge.self_repair.models import (
    ConsistencyIssue,
    DoctrineSection,
    FixProposal,
    IssueType,
)

logger = logging.getLogger(__name__)


class LLMProvider(Protocol):
    """Protocol for LLM provider"""
    def ask(self, system_prompt: str, user_prompt: str) -> str:
        ...


class RepairProposer:
    """Generates fix proposals for consistency issues"""
    
    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        """
        Initialize proposer
        
        Args:
            llm_provider: LLM provider for generating proposals
        """
        self.llm_provider = llm_provider
    
    def generate_proposals(
        self,
        issues: List[ConsistencyIssue],
        doctrine_sections: List[DoctrineSection],
    ) -> List[FixProposal]:
        """
        Generate fix proposals for each issue.
        
        Args:
            issues: List of consistency issues
            doctrine_sections: Full list of Doctrine sections for context
        
        Returns:
            List of FixProposal objects
        """
        logger.info(f"Generating proposals for {len(issues)} issues")
        
        proposals = []
        
        for issue in issues:
            proposal = self._generate_proposal_for_issue(issue, doctrine_sections)
            if proposal:
                proposals.append(proposal)
        
        logger.info(f"Generated {len(proposals)} proposals")
        return proposals
    
    def _generate_proposal_for_issue(
        self,
        issue: ConsistencyIssue,
        all_sections: List[DoctrineSection],
    ) -> Optional[FixProposal]:
        """Generate a proposal for a specific issue"""
        
        if not self.llm_provider:
            logger.warning("LLM provider not available, cannot generate proposal")
            return None
        
        # Get relevant sections
        relevant_sections = []
        for ref in issue.doctrine_refs:
            # Find section by reference (format: "B01#S12")
            for section in all_sections:
                section_ref = f"{section.source}#{section.section_id}" if section.source and section.section_id else section.id
                if section_ref == ref or section.id == ref:
                    relevant_sections.append(section)
                    break
        
        if not relevant_sections:
            logger.warning(f"Could not find sections for refs: {issue.doctrine_refs}")
            return None
        
        # Generate proposal based on issue type
        if issue.issue_type == IssueType.CONFLICT:
            return self._propose_conflict_fix(issue, relevant_sections)
        elif issue.issue_type == IssueType.AMBIGUOUS:
            return self._propose_ambiguity_fix(issue, relevant_sections)
        elif issue.issue_type == IssueType.GAP:
            return self._propose_gap_fix(issue, relevant_sections)
        elif issue.issue_type == IssueType.DUPLICATE:
            return self._propose_duplicate_fix(issue, relevant_sections)
        else:
            return None
    
    def _propose_conflict_fix(
        self,
        issue: ConsistencyIssue,
        sections: List[DoctrineSection],
    ) -> Optional[FixProposal]:
        """Propose fix for conflict"""
        system_prompt = """你是一個交易規則專家。當發現兩條規則存在衝突時，你需要提出一個統一的修正方案。

請提供：
1. 修正後的統一規則文字（proposed_text）
2. 修正理由（justification）
3. 影響說明（impact）

回覆格式（必須嚴格遵守）：
PROPOSED_TEXT:
[修正後的規則文字，應整合兩者優點，消除矛盾]

JUSTIFICATION:
[為什麼這樣修正，如何解決衝突]

IMPACT:
[這個修正會帶來什麼影響，例如：risk-reduction, rule-clarity, consistency-improvement]
"""
        
        sections_text = "\n\n".join([
            f"條文 {i+1} ({s.source}#{s.section_id}):\n{s.text[:500]}"
            for i, s in enumerate(sections)
        ])
        
        user_prompt = f"""以下規則存在衝突：

{issue.description}

衝突的條文：
{sections_text}

請提出修正方案。"""
        
        try:
            response = self.llm_provider.ask(system_prompt, user_prompt)
            
            # Parse response
            proposed_text = ""
            justification = ""
            impact = ""
            
            current_section = None
            for line in response.split("\n"):
                line = line.strip()
                if line.startswith("PROPOSED_TEXT:"):
                    current_section = "text"
                    proposed_text = line.replace("PROPOSED_TEXT:", "").strip()
                elif line.startswith("JUSTIFICATION:"):
                    current_section = "justification"
                    justification = line.replace("JUSTIFICATION:", "").strip()
                elif line.startswith("IMPACT:"):
                    current_section = "impact"
                    impact = line.replace("IMPACT:", "").strip()
                elif current_section == "text":
                    proposed_text += "\n" + line
                elif current_section == "justification":
                    justification += "\n" + line
                elif current_section == "impact":
                    impact += "\n" + line
            
            if proposed_text:
                return FixProposal(
                    id=str(uuid.uuid4()),
                    issue_id=issue.id,
                    proposed_text=proposed_text.strip(),
                    justification=justification.strip() or "LLM 建議的修正方案",
                    impact=impact.strip() or "rule-clarity",
                )
        except Exception as e:
            logger.error(f"Failed to generate conflict fix proposal: {e}")
        
        return None
    
    def _propose_ambiguity_fix(
        self,
        issue: ConsistencyIssue,
        sections: List[DoctrineSection],
    ) -> Optional[FixProposal]:
        """Propose fix for ambiguity"""
        system_prompt = """你是一個交易規則專家。當發現規則定義模糊時，你需要提出更具體、可操作的版本。

請提供更清晰的規則文字，包含：
- 具體的操作條件
- 明確的數值標準（如果適用）
- 清晰的判斷流程

回覆格式（必須嚴格遵守）：
PROPOSED_TEXT:
[更具體、可操作的規則文字]

JUSTIFICATION:
[為什麼這樣修正，如何提升清晰度]

IMPACT:
[這個修正會帶來什麼影響]
"""
        
        section = sections[0]
        user_prompt = f"""以下規則定義模糊：

{issue.description}

原始條文：
{section.source}#{section.section_id}:
{section.text[:500]}

請提出更具體的版本。"""
        
        try:
            response = self.llm_provider.ask(system_prompt, user_prompt)
            
            # Parse response (same format as conflict fix)
            proposed_text = ""
            justification = ""
            impact = ""
            
            current_section = None
            for line in response.split("\n"):
                line = line.strip()
                if line.startswith("PROPOSED_TEXT:"):
                    current_section = "text"
                    proposed_text = line.replace("PROPOSED_TEXT:", "").strip()
                elif line.startswith("JUSTIFICATION:"):
                    current_section = "justification"
                    justification = line.replace("JUSTIFICATION:", "").strip()
                elif line.startswith("IMPACT:"):
                    current_section = "impact"
                    impact = line.replace("IMPACT:", "").strip()
                elif current_section == "text":
                    proposed_text += "\n" + line
                elif current_section == "justification":
                    justification += "\n" + line
                elif current_section == "impact":
                    impact += "\n" + line
            
            if proposed_text:
                return FixProposal(
                    id=str(uuid.uuid4()),
                    issue_id=issue.id,
                    proposed_text=proposed_text.strip(),
                    justification=justification.strip() or "提升規則清晰度",
                    impact=impact.strip() or "rule-clarity",
                )
        except Exception as e:
            logger.error(f"Failed to generate ambiguity fix proposal: {e}")
        
        return None
    
    def _propose_gap_fix(
        self,
        issue: ConsistencyIssue,
        sections: List[DoctrineSection],
    ) -> Optional[FixProposal]:
        """Propose fix for missing rules"""
        system_prompt = """你是一個交易規則專家。當發現規則缺少操作條款時，你需要補強缺失的部分。

請提供新增的規則條款，應包含：
- 具體的操作步驟
- 必要的判斷條件
- 例外情況處理

回覆格式（必須嚴格遵守）：
PROPOSED_TEXT:
[新增的規則條款文字]

JUSTIFICATION:
[為什麼需要補強這個部分]

IMPACT:
[這個修正會帶來什麼影響]
"""
        
        section = sections[0]
        user_prompt = f"""以下規則缺少操作條款：

{issue.description}

原始條文：
{section.source}#{section.section_id}:
{section.text[:500]}

請提出補強的條款。"""
        
        try:
            response = self.llm_provider.ask(system_prompt, user_prompt)
            
            # Parse response
            proposed_text = ""
            justification = ""
            impact = ""
            
            current_section = None
            for line in response.split("\n"):
                line = line.strip()
                if line.startswith("PROPOSED_TEXT:"):
                    current_section = "text"
                    proposed_text = line.replace("PROPOSED_TEXT:", "").strip()
                elif line.startswith("JUSTIFICATION:"):
                    current_section = "justification"
                    justification = line.replace("JUSTIFICATION:", "").strip()
                elif line.startswith("IMPACT:"):
                    current_section = "impact"
                    impact = line.replace("IMPACT:", "").strip()
                elif current_section == "text":
                    proposed_text += "\n" + line
                elif current_section == "justification":
                    justification += "\n" + line
                elif current_section == "impact":
                    impact += "\n" + line
            
            if proposed_text:
                return FixProposal(
                    id=str(uuid.uuid4()),
                    issue_id=issue.id,
                    proposed_text=proposed_text.strip(),
                    justification=justification.strip() or "補強缺失的操作條款",
                    impact=impact.strip() or "completeness",
                )
        except Exception as e:
            logger.error(f"Failed to generate gap fix proposal: {e}")
        
        return None
    
    def _propose_duplicate_fix(
        self,
        issue: ConsistencyIssue,
        sections: List[DoctrineSection],
    ) -> Optional[FixProposal]:
        """Propose fix for duplicates (suggest removal/merge)"""
        # For duplicates, suggest keeping the most complete version or merging
        if len(sections) > 1:
            # Find the longest/most complete section
            best_section = max(sections, key=lambda s: len(s.text))
            
            return FixProposal(
                id=str(uuid.uuid4()),
                issue_id=issue.id,
                proposed_text=f"建議保留：{best_section.source}#{best_section.section_id}\n建議刪除重複條文：{', '.join([f'{s.source}#{s.section_id}' for s in sections if s != best_section])}",
                justification="發現重複條文，建議保留最完整的版本，刪除其他重複項",
                impact="consistency-improvement",
            )
        
        return None

