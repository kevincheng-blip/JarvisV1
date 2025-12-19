"""
Prophecy Archive Writer (JSONL + immutable_hash).
"""
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from jgod.oracle.schemas import Prophecy, ForecastHorizon, DecisionFootprint


def generate_prophecy_id(
    as_of_date: str, 
    symbol: str, 
    oracle_core_version: str = "or-os.v1",
    toolset_version: str = "stub",
    doctrine_version: str = "stub"
) -> str:
    """
    Generate deterministic prophecy_id (SHA256 64 hex).
    
    Args:
        as_of_date: YYYY-MM-DD
        symbol: Stock symbol
        oracle_core_version: Oracle core version (default: "or-os.v1")
        toolset_version: Toolset version (default: "stub")
        doctrine_version: Doctrine version (default: "stub")
        
    Returns:
        SHA256 hash hex string (64 chars)
    """
    content = f"{as_of_date}|{symbol}|{oracle_core_version}|{toolset_version}|{doctrine_version}"
    return hashlib.sha256(content.encode()).hexdigest()


def compute_immutable_hash(prophecy_dict: Dict) -> str:
    """
    Compute SHA256 hash of canonical JSON representation.
    
    Args:
        prophecy_dict: Prophecy as dict (without immutable_hash)
        
    Returns:
        SHA256 hex string (64 chars)
    """
    # Remove immutable_hash if present
    clean_dict = {k: v for k, v in prophecy_dict.items() if k != "immutable_hash"}
    
    # Canonical JSON (sorted keys, no whitespace)
    canonical_json = json.dumps(clean_dict, sort_keys=True, separators=(',', ':'))
    
    return hashlib.sha256(canonical_json.encode()).hexdigest()


def write_prophecy_archive(prophecies: List[Prophecy], output_path: Path) -> None:
    """
    Write prophecies to JSONL file.
    
    Args:
        prophecies: List of Prophecy objects
        output_path: Output file path
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for prophecy in prophecies:
            # Convert to dict and ensure immutable_hash is computed
            prophecy_dict = prophecy.model_dump()
            if not prophecy_dict.get("immutable_hash"):
                prophecy_dict["immutable_hash"] = compute_immutable_hash(prophecy_dict)
            
            f.write(json.dumps(prophecy_dict, ensure_ascii=False) + '\n')


def load_prophecy_archive(archive_path: Path) -> List[Prophecy]:
    """
    Load prophecies from JSONL file (with backward compat).
    
    Args:
        archive_path: Path to JSONL file
        
    Returns:
        List of Prophecy objects
    """
    prophecies = []
    with open(archive_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            prophecy_dict = json.loads(line)
            # Use from_dict for backward compat
            prophecies.append(Prophecy.from_dict(prophecy_dict))
    return prophecies
