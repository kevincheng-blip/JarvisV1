"""J-GOD Knowledge Brain v2 – Self-Repair Engine

Provides self-consistency scanning, repair proposal generation, and safe update
capabilities for Doctrine knowledge base.
"""

from .models import (
    DoctrineSection,
    ConsistencyIssue,
    FixProposal,
    RepairReport,
)
from .scanner import SelfRepairScanner
from .proposer import RepairProposer
from .evaluator import ProposalEvaluator
from .patcher import SafePatcher
from .storage import RepairReportStorage

__all__ = [
    "DoctrineSection",
    "ConsistencyIssue",
    "FixProposal",
    "RepairReport",
    "SelfRepairScanner",
    "RepairProposer",
    "ProposalEvaluator",
    "SafePatcher",
    "RepairReportStorage",
]

