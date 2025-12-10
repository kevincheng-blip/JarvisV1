"""Decision AB Test Storage

Stores and loads AB test results from JSONL files.
"""

import json
import logging
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional

from jgod.decision_ab.models import DecisionAbResult, DecisionABTestReport

logger = logging.getLogger(__name__)


class AbResultStorage:
    """Storage for AB test results (JSONL-based)"""
    
    def __init__(self, path: str = "data/decision_ab/decision_ab_results_v1.jsonl"):
        """
        Initialize storage
        
        Args:
            path: Path to JSONL file for storing results
        """
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"AbResultStorage initialized with path: {self.path}")
    
    def save(self, result: DecisionAbResult) -> None:
        """Save an AB test result to JSONL file
        
        Args:
            result: DecisionAbResult to save
        """
        # Convert to dict (Pydantic model serializes dates/datetimes properly)
        result_dict = result.model_dump(mode='json')
        
        # Append to JSONL file
        with open(self.path, 'a', encoding='utf-8') as f:
            json.dump(result_dict, f, ensure_ascii=False)
            f.write('\n')
        
        logger.info(f"Saved AB test result: {result.experiment_id}")
    
    def load_recent(self, limit: int = 20) -> List[DecisionAbResult]:
        """Load recent AB test results
        
        Args:
            limit: Maximum number of results to return
        
        Returns:
            List of DecisionAbResult, sorted by created_at (newest first)
        """
        if not self.path.exists():
            logger.info(f"Storage file does not exist: {self.path}")
            return []
        
        results = []
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        result_dict = json.loads(line)
                        # Parse dates/datetimes
                        result_dict['created_at'] = datetime.fromisoformat(result_dict['created_at'])
                        result_dict['raw_only']['start_date'] = datetime.fromisoformat(
                            result_dict['raw_only']['start_date']
                        ).date()
                        result_dict['raw_only']['end_date'] = datetime.fromisoformat(
                            result_dict['raw_only']['end_date']
                        ).date()
                        result_dict['decision_on']['start_date'] = datetime.fromisoformat(
                            result_dict['decision_on']['start_date']
                        ).date()
                        result_dict['decision_on']['end_date'] = datetime.fromisoformat(
                            result_dict['decision_on']['end_date']
                        ).date()
                        
                        result = DecisionAbResult(**result_dict)
                        results.append(result)
                    except Exception as e:
                        logger.warning(f"Failed to parse line {line_num} in {self.path}: {e}")
                        continue
            
            # Sort by created_at (newest first)
            results.sort(key=lambda x: x.created_at, reverse=True)
            
            # Apply limit
            results = results[:limit]
            
            logger.info(f"Loaded {len(results)} AB test results from {self.path}")
        
        except Exception as e:
            logger.error(f"Error loading AB test results: {e}", exc_info=True)
        
        return results
    
    def load_by_experiment_id(self, experiment_id: str) -> Optional[DecisionAbResult]:
        """Load a specific AB test result by experiment_id
        
        Args:
            experiment_id: Experiment identifier
        
        Returns:
            DecisionAbResult if found, None otherwise
        """
        if not self.path.exists():
            return None
        
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        result_dict = json.loads(line)
                        if result_dict.get('experiment_id') == experiment_id:
                            # Parse dates/datetimes
                            result_dict['created_at'] = datetime.fromisoformat(result_dict['created_at'])
                            result_dict['raw_only']['start_date'] = datetime.fromisoformat(
                                result_dict['raw_only']['start_date']
                            ).date()
                            result_dict['raw_only']['end_date'] = datetime.fromisoformat(
                                result_dict['raw_only']['end_date']
                            ).date()
                            result_dict['decision_on']['start_date'] = datetime.fromisoformat(
                                result_dict['decision_on']['start_date']
                            ).date()
                            result_dict['decision_on']['end_date'] = datetime.fromisoformat(
                                result_dict['decision_on']['end_date']
                            ).date()
                            
                            return DecisionAbResult(**result_dict)
                    except Exception as e:
                        logger.warning(f"Failed to parse line in {self.path}: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"Error loading AB test result for {experiment_id}: {e}", exc_info=True)
        
        return None


class DecisionAbStorageV1:
    """Storage for Decision AB Test Reports (V1 vs V2)"""
    
    def __init__(self, path: str = "data/decision_ab/decision_ab_reports_v2.jsonl"):
        """
        Initialize storage
        
        Args:
            path: Path to JSONL file for storing reports
        """
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"DecisionAbStorageV1 initialized with path: {self.path}")
    
    def save_decision_report(self, report: DecisionABTestReport) -> None:
        """Save a Decision AB Test report to JSONL file
        
        Args:
            report: DecisionABTestReport to save
        """
        # Convert to dict (Pydantic model serializes dates/datetimes properly)
        report_dict = report.model_dump(mode='json')
        
        # Append to JSONL file
        with open(self.path, 'a', encoding='utf-8') as f:
            json.dump(report_dict, f, ensure_ascii=False)
            f.write('\n')
        
        logger.info(f"Saved Decision AB Test report: {report.experiment_id}")
    
    def load_recent_decision_reports(self, limit: int = 20) -> List[DecisionABTestReport]:
        """Load recent Decision AB Test reports
        
        Args:
            limit: Maximum number of reports to return
        
        Returns:
            List of DecisionABTestReport, sorted by created_at (newest first)
        """
        if not self.path.exists():
            logger.info(f"Storage file does not exist: {self.path}")
            return []
        
        reports = []
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        report_dict = json.loads(line)
                        # Parse datetime
                        report_dict['created_at'] = datetime.fromisoformat(report_dict['created_at'])
                        
                        # Parse dates in config if they exist
                        if 'config' in report_dict:
                            if 'start_date' in report_dict['config']:
                                report_dict['config']['start_date'] = datetime.fromisoformat(
                                    report_dict['config']['start_date']
                                ).date()
                            if 'end_date' in report_dict['config']:
                                report_dict['config']['end_date'] = datetime.fromisoformat(
                                    report_dict['config']['end_date']
                                ).date()
                        
                        report = DecisionABTestReport(**report_dict)
                        reports.append(report)
                    except Exception as e:
                        logger.warning(f"Failed to parse line {line_num} in {self.path}: {e}")
                        continue
            
            # Sort by created_at (newest first)
            reports.sort(key=lambda x: x.created_at, reverse=True)
            
            # Apply limit
            reports = reports[:limit]
            
            logger.info(f"Loaded {len(reports)} Decision AB Test reports from {self.path}")
        
        except Exception as e:
            logger.error(f"Error loading Decision AB Test reports: {e}", exc_info=True)
        
        return reports
    
    def load_decision_report(self, experiment_id: str) -> Optional[DecisionABTestReport]:
        """Load a specific Decision AB Test report by experiment_id
        
        Args:
            experiment_id: Experiment identifier
        
        Returns:
            DecisionABTestReport if found, None otherwise
        """
        if not self.path.exists():
            return None
        
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        report_dict = json.loads(line)
                        if report_dict.get('experiment_id') == experiment_id:
                            # Parse datetime
                            report_dict['created_at'] = datetime.fromisoformat(report_dict['created_at'])
                            
                            # Parse dates in config if they exist
                            if 'config' in report_dict:
                                if 'start_date' in report_dict['config']:
                                    report_dict['config']['start_date'] = datetime.fromisoformat(
                                        report_dict['config']['start_date']
                                    ).date()
                                if 'end_date' in report_dict['config']:
                                    report_dict['config']['end_date'] = datetime.fromisoformat(
                                        report_dict['config']['end_date']
                                    ).date()
                            
                            return DecisionABTestReport(**report_dict)
                    except Exception as e:
                        logger.warning(f"Failed to parse line in {self.path}: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"Error loading Decision AB Test report for {experiment_id}: {e}", exc_info=True)
        
        return None

