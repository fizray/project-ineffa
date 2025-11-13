"""
Logging System Component
Handles attendance logging to CSV/JSONL files and optional snapshot management
"""

import csv
import json
import os
import time
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
import cv2
import numpy as np

@dataclass
class AttendanceRecord:
    """Data class for attendance records"""
    timestamp_iso: str
    user_id: str
    user_name: str
    matched_score: float
    liveness_passed: bool
    snapshot_path: str
    note: str
    face_detected: bool
    detection_confidence: float
    processing_time_ms: float

class AttendanceLogger:
    def __init__(self, log_path: str = "attendance.csv", 
                 snapshot_dir: str = "snapshots",
                 save_snapshot_threshold: float = 0.75,
                 auto_snapshot_unknown: bool = True):
        """
        Initialize attendance logger
        
        Args:
            log_path: Path to attendance log file
            snapshot_dir: Directory for snapshot storage
            save_snapshot_threshold: Minimum score to save snapshot
            auto_snapshot_unknown: Save snapshots for unknown faces
        """
        self.log_path = log_path
        self.snapshot_dir = snapshot_dir
        self.save_snapshot_threshold = save_snapshot_threshold
        self.auto_snapshot_unknown = auto_snapshot_unknown
        
        # Ensure snapshot directory exists
        os.makedirs(snapshot_dir, exist_ok=True)
        
        # Initialize CSV file with headers
        self._init_csv_file()
    
    def _init_csv_file(self):
        """Initialize CSV file with proper headers"""
        try:
            if not os.path.exists(self.log_path):
                with open(self.log_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        'timestamp_iso', 'user_id', 'user_name', 'matched_score',
                        'liveness_passed', 'snapshot_path', 'note', 'face_detected',
                        'detection_confidence', 'processing_time_ms'
                    ])
        except Exception as e:
            print(f"Failed to initialize CSV file: {e}")
    
    def _generate_snapshot_filename(self, user_id: str, timestamp: str) -> str:
        """Generate snapshot filename"""
        if user_id:
            filename = f"snap_{user_id}_{timestamp.replace(':', '-').replace('T', '_')}.jpg"
        else:
            filename = f"unknown_{timestamp.replace(':', '-').replace('T', '_')}.jpg"
        
        return os.path.join(self.snapshot_dir, filename)
    
    def save_snapshot(self, frame: np.ndarray, user_id: str, timestamp: str) -> Optional[str]:
        """
        Save frame snapshot to file
        
        Args:
            frame: Frame to save
            user_id: User ID (empty for unknown)
            timestamp: Timestamp string
            
        Returns:
            Path to saved snapshot or None if save failed
        """
        try:
            snapshot_path = self._generate_snapshot_filename(user_id, timestamp)
            
            # Save with some compression
            success = cv2.imwrite(snapshot_path, frame, 
                                [cv2.IMWRITE_JPEG_QUALITY, 85])
            
            return snapshot_path if success else None
            
        except Exception as e:
            print(f"Failed to save snapshot: {e}")
            return None
    
    def log_attendance(self, record: AttendanceRecord) -> bool:
        """
        Log attendance record to CSV file
        
        Args:
            record: AttendanceRecord to log
            
        Returns:
            True if logging successful
        """
        try:
            # Save snapshot if needed
            snapshot_path = ""
            should_save_snapshot = (
                (record.user_id and record.matched_score >= self.save_snapshot_threshold) or
                (not record.user_id and self.auto_snapshot_unknown and record.face_detected)
            )
            
            if should_save_snapshot and hasattr(record, '_frame_data'):
                # This would be set externally for actual frames
                pass  # In real implementation, frame would be passed separately
            
            # Update record with snapshot path
            if snapshot_path:
                record.snapshot_path = snapshot_path
            
            # Append to CSV
            with open(self.log_path, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    record.timestamp_iso,
                    record.user_id,
                    record.user_name,
                    f"{record.matched_score:.3f}",
                    str(record.liveness_passed),
                    record.snapshot_path,
                    record.note,
                    str(record.face_detected),
                    f"{record.detection_confidence:.3f}",
                    f"{record.processing_time_ms:.1f}"
                ])
            
            return True
            
        except Exception as e:
            print(f"Failed to log attendance: {e}")
            return False
    
    def log_attendance_with_frame(self, frame: np.ndarray, user_id: str, user_name: str,
                                matched_score: float, liveness_passed: bool,
                                note: str = "auto", face_detected: bool = True,
                                detection_confidence: float = 0.0,
                                processing_time_ms: float = 0.0) -> bool:
        """
        Log attendance with frame snapshot (convenience method)
        
        Args:
            frame: Frame to save as snapshot
            user_id: User ID (empty for unknown)
            user_name: User name
            matched_score: Match confidence score
            liveness_passed: Whether liveness check passed
            note: Additional note
            face_detected: Whether face was detected
            detection_confidence: Face detection confidence
            processing_time_ms: Processing time in milliseconds
            
        Returns:
            True if logging successful
        """
        timestamp = datetime.now().isoformat()
        
        # Save snapshot
        snapshot_path = ""
        should_save_snapshot = (
            (user_id and matched_score >= self.save_snapshot_threshold) or
            (not user_id and self.auto_snapshot_unknown and face_detected)
        )
        
        if should_save_snapshot:
            snapshot_path = self.save_snapshot(frame, user_id, timestamp)
        
        # Create record
        record = AttendanceRecord(
            timestamp_iso=timestamp,
            user_id=user_id,
            user_name=user_name,
            matched_score=matched_score,
            liveness_passed=liveness_passed,
            snapshot_path=snapshot_path,
            note=note,
            face_detected=face_detected,
            detection_confidence=detection_confidence,
            processing_time_ms=processing_time_ms
        )
        
        return self.log_attendance(record)
    
    def get_recent_logs(self, limit: int = 10) -> List[AttendanceRecord]:
        """
        Get recent attendance logs
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of recent attendance records
        """
        records = []
        try:
            with open(self.log_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    record = AttendanceRecord(
                        timestamp_iso=row['timestamp_iso'],
                        user_id=row['user_id'],
                        user_name=row['user_name'],
                        matched_score=float(row['matched_score']),
                        liveness_passed=row['liveness_passed'].lower() == 'true',
                        snapshot_path=row['snapshot_path'],
                        note=row['note'],
                        face_detected=row['face_detected'].lower() == 'true',
                        detection_confidence=float(row['detection_confidence']),
                        processing_time_ms=float(row['processing_time_ms'])
                    )
                    records.append(record)
                
                # Return most recent records
                return records[-limit:] if limit > 0 else records
                
        except Exception as e:
            print(f"Failed to read logs: {e}")
            return []
    
    def get_logs_by_user(self, user_id: str) -> List[AttendanceRecord]:
        """
        Get all logs for a specific user
        
        Args:
            user_id: User ID to filter by
            
        Returns:
            List of attendance records for the user
        """
        try:
            with open(self.log_path, 'r') as f:
                reader = csv.DictReader(f)
                user_records = []
                
                for row in reader:
                    if row['user_id'] == user_id:
                        record = AttendanceRecord(
                            timestamp_iso=row['timestamp_iso'],
                            user_id=row['user_id'],
                            user_name=row['user_name'],
                            matched_score=float(row['matched_score']),
                            liveness_passed=row['liveness_passed'].lower() == 'true',
                            snapshot_path=row['snapshot_path'],
                            note=row['note'],
                            face_detected=row['face_detected'].lower() == 'true',
                            detection_confidence=float(row['detection_confidence']),
                            processing_time_ms=float(row['processing_time_ms'])
                        )
                        user_records.append(record)
                
                return user_records
                
        except Exception as e:
            print(f"Failed to get user logs: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get attendance statistics
        
        Returns:
            Dictionary with attendance statistics
        """
        try:
            if not os.path.exists(self.log_path):
                return {
                    "total_records": 0,
                    "unique_users": 0,
                    "success_rate": 0.0,
                    "average_score": 0.0,
                    "liveness_pass_rate": 0.0
                }
            
            with open(self.log_path, 'r') as f:
                reader = csv.DictReader(f)
                records = list(reader)
            
            if not records:
                return {
                    "total_records": 0,
                    "unique_users": 0,
                    "success_rate": 0.0,
                    "average_score": 0.0,
                    "liveness_pass_rate": 0.0
                }
            
            # Calculate statistics
            total_records = len(records)
            unique_users = len(set(r['user_id'] for r in records if r['user_id']))
            
            successful_matches = sum(1 for r in records if r['user_id'])
            success_rate = successful_matches / total_records if total_records > 0 else 0.0
            
            avg_score = np.mean([float(r['matched_score']) for r in records])
            
            liveness_passed = sum(1 for r in records if r['liveness_passed'].lower() == 'true')
            liveness_rate = liveness_passed / total_records if total_records > 0 else 0.0
            
            return {
                "total_records": total_records,
                "unique_users": unique_users,
                "success_rate": success_rate,
                "average_score": avg_score,
                "liveness_pass_rate": liveness_rate
            }
            
        except Exception as e:
            print(f"Failed to get statistics: {e}")
            return {}

class JSONLLogger:
    """Alternative logger using JSONL format"""
    
    def __init__(self, log_path: str = "attendance.jsonl"):
        self.log_path = log_path
    
    def log_record(self, record: AttendanceRecord):
        """Log a single record to JSONL file"""
        try:
            with open(self.log_path, 'a') as f:
                f.write(json.dumps(asdict(record)) + '\n')
        except Exception as e:
            print(f"Failed to log JSONL record: {e}")
    
    def read_records(self) -> List[AttendanceRecord]:
        """Read all records from JSONL file"""
        records = []
        try:
            with open(self.log_path, 'r') as f:
                for line in f:
                    data = json.loads(line.strip())
                    record = AttendanceRecord(**data)
                    records.append(record)
        except Exception as e:
            print(f"Failed to read JSONL records: {e}")
        
        return records

# Test function
if __name__ == "__main__":
    # Test attendance logger
    logger = AttendanceLogger("test_attendance.csv", "test_snapshots")
    
    # Test logging
    record = AttendanceRecord(
        timestamp_iso=datetime.now().isoformat(),
        user_id="user_001",
        user_name="Test User",
        matched_score=0.85,
        liveness_passed=True,
        snapshot_path="test_snapshots/snap_user_001.jpg",
        note="auto",
        face_detected=True,
        detection_confidence=0.95,
        processing_time_ms=150.5
    )
    
    success = logger.log_attendance(record)
    print(f"Logging test: {'Success' if success else 'Failed'}")
    
    # Test statistics
    stats = logger.get_statistics()
    print(f"Statistics: {stats}")
    
    # Clean up test files
    for file in ["test_attendance.csv", "test_snapshots"]:
        if os.path.exists(file):
            if os.path.isfile(file):
                os.remove(file)
            else:
                import shutil
                shutil.rmtree(file)