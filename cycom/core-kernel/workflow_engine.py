# -*- coding: utf-8 -*-
from typing import Dict, Any, List

class WorkflowEngine:
    """Low-Code Rule Trigger & Workflow Engine."""
    
    @staticmethod
    def evaluate_rule(rule: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """
        Evaluate if context matches rule criteria.
        Rule format: {field, operator, value}
        operators: '>', '<', '==', 'contains'
        """
        field = rule.get("field")
        op = rule.get("operator")
        rule_val = rule.get("value")
        
        if field not in context:
            return False
            
        ctx_val = context[field]
        
        try:
            if op == ">":
                return float(ctx_val) > float(rule_val)
            elif op == "<":
                return float(ctx_val) < float(rule_val)
            elif op == "==":
                return str(ctx_val) == str(rule_val)
            elif op == "contains":
                return str(rule_val) in str(ctx_val)
        except (ValueError, TypeError):
            pass
        return False

    @staticmethod
    def run_actions(actions: List[Dict[str, Any]], record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute actions on record mutation.
        Action format: {action_type, target_field, value}
        """
        updated = dict(record)
        for act in actions:
            act_type = act.get("action_type")
            field = act.get("target_field")
            val = act.get("value")
            
            if act_type == "set_field":
                updated[field] = val
        return updated
