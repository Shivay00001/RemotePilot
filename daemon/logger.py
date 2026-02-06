import logging
import json
import os
from datetime import datetime
from typing import Dict, Any

class AuditLogger:
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.log_file = os.path.join(log_dir, "audit.log")
        
        # Setup specific logger
        self.logger = logging.getLogger("RemotePilotAudit")
        self.logger.setLevel(logging.INFO)
        
        handler = logging.FileHandler(self.log_file)
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)

    def log_event(self, event_type: str, details: Dict[str, Any]):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            "details": details
        }
        self.logger.info(json.dumps(entry))
        print(f"[Audit] {event_type}: {str(details)[:100]}...")

audit_logger = AuditLogger()
