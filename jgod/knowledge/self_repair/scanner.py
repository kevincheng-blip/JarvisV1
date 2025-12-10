"""Self-Repair Scanner

Scans Doctrine sections for consistency issues using LLM comparison and static analysis.
"""

import logging
import uuid
from typing import List, Optional, Protocol

from jgod.knowledge.self_repair.models import (
    DoctrineSection,
    ConsistencyIssue,
    IssueType,
    IssueSeverity,
)

logger = logging.getLogger(__name__)


class LLMProvider(Protocol):
    """Protocol for LLM provider"""
    def ask(self, system_prompt: str, user_prompt: str) -> str:
        ...


class SelfRepairScanner:
    """Scans Doctrine sections for consistency issues"""
    
    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        """
        Initialize scanner
        
        Args:
            llm_provider: LLM provider for comparison (optional, can use static analysis only)
        """
        self.llm_provider = llm_provider
    
    def scan_doctrine(
        self,
        doctrine_sections: List[DoctrineSection],
        use_llm: bool = True,
    ) -> List[ConsistencyIssue]:
        """
        Scan Doctrine sections for consistency issues.
        
        Args:
            doctrine_sections: List of Doctrine sections to scan
            use_llm: Whether to use LLM for advanced comparison (default: True)
        
        Returns:
            List of ConsistencyIssue objects
        """
        logger.info(f"Scanning {len(doctrine_sections)} Doctrine sections for consistency issues")
        
        issues = []
        
        # Step 1: Static analysis for duplicates
        issues.extend(self._scan_duplicates(doctrine_sections))
        
        # Step 2: LLM-based comparison for conflicts and ambiguities
        if use_llm and self.llm_provider:
            issues.extend(self._scan_with_llm(doctrine_sections))
        else:
            logger.warning("LLM provider not available, skipping advanced analysis")
        
        logger.info(f"Found {len(issues)} consistency issues")
        return issues
    
    def _scan_duplicates(self, sections: List[DoctrineSection]) -> List[ConsistencyIssue]:
        """Static analysis: Find duplicate sections"""
        issues = []
        
        # Group sections by normalized text (simple hash-based)
        text_to_sections = {}
        for section in sections:
            # Normalize text (remove extra whitespace, lower case for comparison)
            normalized = " ".join(section.text.split()).lower()
            if normalized not in text_to_sections:
                text_to_sections[normalized] = []
            text_to_sections[normalized].append(section)
        
        # Check for duplicates
        for normalized_text, section_list in text_to_sections.items():
            if len(section_list) > 1:
                # Found duplicates
                refs = [f"{s.source}#{s.section_id}" if s.source and s.section_id else s.id for s in section_list]
                issue = ConsistencyIssue(
                    id=str(uuid.uuid4()),
                    issue_type=IssueType.DUPLICATE,
                    doctrine_refs=refs,
                    description=f"發現重複的條文內容（{len(section_list)} 處）：{', '.join(refs[:3])}",
                    severity=IssueSeverity.MEDIUM,
                    context={"normalized_text": normalized_text[:100]},
                )
                issues.append(issue)
        
        return issues
    
    def _scan_with_llm(self, sections: List[DoctrineSection]) -> List[ConsistencyIssue]:
        """Use LLM to find conflicts, ambiguities, and gaps"""
        issues = []
        
        if not self.llm_provider:
            return issues
        
        # Compare pairs of sections for conflicts
        for i, section1 in enumerate(sections):
            for section2 in sections[i+1:]:
                # Skip if same source (usually not conflicting within same book)
                if section1.source == section2.source:
                    continue
                
                conflict_issue = self._check_conflict_with_llm(section1, section2)
                if conflict_issue:
                    issues.append(conflict_issue)
                
                # Check for ambiguities in individual sections
                if i == 0:  # Only check once per section
                    ambiguous_issue = self._check_ambiguity_with_llm(section2)
                    if ambiguous_issue:
                        issues.append(ambiguous_issue)
        
        # Check first section for ambiguity too
        if sections:
            ambiguous_issue = self._check_ambiguity_with_llm(sections[0])
            if ambiguous_issue:
                issues.append(ambiguous_issue)
        
        return issues
    
    def _check_conflict_with_llm(
        self,
        section1: DoctrineSection,
        section2: DoctrineSection,
    ) -> Optional[ConsistencyIssue]:
        """Use LLM to check if two sections conflict"""
        if not self.llm_provider:
            return None
        
        system_prompt = """你是一個交易規則分析專家。請比較兩段 Doctrine 條文，判斷是否存在邏輯矛盾或衝突。

回覆格式必須嚴格遵守：
- 如果沒有衝突，回覆：NO_CONFLICT
- 如果有衝突，回覆：CONFLICT: [簡短描述衝突內容]
"""
        
        user_prompt = f"""請比較以下兩段條文：

條文 1 ({section1.source}#{section1.section_id}):
{section1.text[:500]}

條文 2 ({section2.source}#{section2.section_id}):
{section2.text[:500]}

請判斷是否存在邏輯矛盾。"""
        
        try:
            response = self.llm_provider.ask(system_prompt, user_prompt)
            response = response.strip().upper()
            
            if response.startswith("CONFLICT:"):
                description = response.replace("CONFLICT:", "").strip()
                return ConsistencyIssue(
                    id=str(uuid.uuid4()),
                    issue_type=IssueType.CONFLICT,
                    doctrine_refs=[f"{section1.source}#{section1.section_id}", f"{section2.source}#{section2.section_id}"],
                    description=f"規則衝突：{description}",
                    severity=IssueSeverity.HIGH,
                    context={"section1": section1.id, "section2": section2.id},
                )
        except Exception as e:
            logger.warning(f"LLM conflict check failed: {e}")
        
        return None
    
    def _check_ambiguity_with_llm(self, section: DoctrineSection) -> Optional[ConsistencyIssue]:
        """Use LLM to check if a section is ambiguous"""
        if not self.llm_provider:
            return None
        
        system_prompt = """你是一個交易規則分析專家。請評估一段 Doctrine 條文是否清晰、具體、可操作。

回覆格式必須嚴格遵守：
- 如果清晰具體，回覆：CLEAR
- 如果模糊或不具體，回覆：AMBIGUOUS: [簡短描述模糊之處]
- 如果缺少操作細節，回覆：GAP: [簡短描述缺少什麼]
"""
        
        user_prompt = f"""請評估以下條文：

{section.source}#{section.section_id}:
{section.text[:500]}

請判斷是否清晰、具體、可操作。"""
        
        try:
            response = self.llm_provider.ask(system_prompt, user_prompt)
            response = response.strip().upper()
            
            if response.startswith("AMBIGUOUS:"):
                description = response.replace("AMBIGUOUS:", "").strip()
                return ConsistencyIssue(
                    id=str(uuid.uuid4()),
                    issue_type=IssueType.AMBIGUOUS,
                    doctrine_refs=[f"{section.source}#{section.section_id}"],
                    description=f"定義模糊：{description}",
                    severity=IssueSeverity.MEDIUM,
                    context={"section": section.id},
                )
            elif response.startswith("GAP:"):
                description = response.replace("GAP:", "").strip()
                return ConsistencyIssue(
                    id=str(uuid.uuid4()),
                    issue_type=IssueType.GAP,
                    doctrine_refs=[f"{section.source}#{section.section_id}"],
                    description=f"缺少操作條款：{description}",
                    severity=IssueSeverity.HIGH,
                    context={"section": section.id},
                )
        except Exception as e:
            logger.warning(f"LLM ambiguity check failed: {e}")
        
        return None

