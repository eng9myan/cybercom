# -*- coding: utf-8 -*-
import hashlib
from typing import List, Dict, Any

class CryptoAudit:
    """Cryptographic chain integrity validator for database audit logs."""
    
    @staticmethod
    def hash_log_block(prev_hash: str, user_email: str, action: str, model: str, timestamp: str) -> str:
        """Compute SHA-256 block hash for an audit log record."""
        payload = f"{prev_hash}|{user_email}|{action}|{model}|{timestamp}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @classmethod
    def verify_chain(cls, logs: List[Dict[str, Any]]) -> bool:
        """
        Verify the integrity of a sequential list of audit log blocks.
        Each log dict should contain: 'prev_hash', 'current_hash', 'user_email', 'action', 'model', 'created_at'
        """
        current_prev_hash = "GENESIS_HASH"
        for log in sorted(logs, key=lambda x: x.get("id", 0)):
            # Check link to previous
            if log.get("prev_hash") != current_prev_hash:
                return False
                
            # Recompute block hash
            recomputed = cls.hash_log_block(
                prev_hash=log.get("prev_hash", ""),
                user_email=log.get("user_email", ""),
                action=log.get("action", ""),
                model=log.get("model", ""),
                timestamp=str(log.get("created_at", ""))
            )
            
            if log.get("current_hash") != recomputed:
                return False
                
            current_prev_hash = log.get("current_hash")
        return True
