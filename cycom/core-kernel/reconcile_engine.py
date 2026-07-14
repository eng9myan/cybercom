# -*- coding: utf-8 -*-
from typing import List, Dict, Any

class ReconcileEngine:
    """AI-Powered Bank Reconciliation Matcher using Jaccard Similarity and variance thresholds."""
    
    @staticmethod
    def _jaccard_similarity(str1: str, str2: str) -> float:
        """Calculate word-based Jaccard similarity coefficient."""
        words1 = set(str(str1).lower().split())
        words2 = set(str(str2).lower().split())
        if not words1 and not words2:
            return 1.0
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        return len(intersection) / len(union)

    @classmethod
    def match_statement_lines(
        cls, 
        bank_lines: List[Dict[str, Any]], 
        open_invoices: List[Dict[str, Any]], 
        min_similarity: float = 0.4
    ) -> List[Dict[str, Any]]:
        """
        Map bank transaction lines to open invoices.
        Outputs best match candidate with match score.
        """
        matches = []
        for line in bank_lines:
            line_amt = float(line.get("amount") or 0.0)
            line_desc = str(line.get("description") or "")
            
            best_match = None
            highest_score = 0.0
            
            for inv in open_invoices:
                inv_amt = float(inv.get("amount_total") or 0.0)
                inv_partner = str(inv.get("partner_name") or "")
                inv_num = str(inv.get("number") or "")
                
                # Check price exact match or variance
                amt_match = abs(line_amt - inv_amt) < 0.01
                
                # Check text similarity with partner name & invoice number
                sim_partner = cls._jaccard_similarity(line_desc, inv_partner)
                sim_num = cls._jaccard_similarity(line_desc, inv_num)
                text_sim = max(sim_partner, sim_num)
                
                # Calculate combined score
                score = (0.6 if amt_match else 0.0) + (0.4 * text_sim)
                
                if score > highest_score:
                    highest_score = score
                    best_match = inv
                    
            if best_match and highest_score >= min_similarity:
                matches.append({
                    "statement_line_id": line.get("id"),
                    "invoice_id": best_match.get("id"),
                    "invoice_number": best_match.get("number"),
                    "partner_name": best_match.get("partner_name"),
                    "amount": line_amt,
                    "confidence_score": highest_score,
                    "status": "matched" if highest_score >= 0.8 else "suggested"
                })
            else:
                matches.append({
                    "statement_line_id": line.get("id"),
                    "invoice_id": None,
                    "amount": line_amt,
                    "confidence_score": 0.0,
                    "status": "unmatched"
                })
                
        return matches
