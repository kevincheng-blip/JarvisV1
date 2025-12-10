"""J-GOD Doctrine Service V2

Doctrine Management Console (DMC) - Knowledge governance and review system.
"""

from .models import (
    DoctrineSectionV2,
    SectionRevision,
    SectionStatus,
    ChangeType,
)
from .service import DoctrineServiceV2
from .version_storage import VersionStorage

__all__ = [
    "DoctrineSectionV2",
    "SectionRevision",
    "SectionStatus",
    "ChangeType",
    "DoctrineServiceV2",
    "VersionStorage",
]

