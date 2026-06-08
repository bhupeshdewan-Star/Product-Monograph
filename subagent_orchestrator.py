"""Sub-Agent Orchestrator - Unified interface for A11Y Checker and Auditor"""
from a11y_checker import A11YChecker
from auditor_agent_builder import AuditorAgentBuilder
from typing import Dict, List, Optional
import json
from datetime import datetime

class SubAgentOrchestrator:
    """Orchestrate A11Y Checker and Auditor agents"""
    
    def __init__(self):
        self.a11y_checker = A11YChecker()
        self.auditor_builder = AuditorAgentBuilder()
        self.audit_cache = {}
        self.operation_history = []
    
    def run_a11y_check(self, url: str) -> Dict:
        """Run WCAG 2.1 AA accessibility check"""
        try:
            report = self.a11y_checker.check_url(url)
            self._log_operation("a11y_check", url, "success")
            return report
        except Exception as e:
            self._log_operation("a11y_check", url, "failed", str(e))
            return {"status": "error", "message": str(e)}
    
    def run_a11y_check_html(self, html: str) -> Dict:
        """Check HTML code for accessibility"""
        try:
            report = self.a11y_checker.check_html(html)
            self._log_operation("a11y_check_html", "html_input", "success")
            return report
        except Exception as e:
            self._log_operation("a11y_check_html", "html_input", "failed", str(e))
            return {"status": "error", "message": str(e)}
    
    def create_auditor(self, checklist_url: str):
        """Create audit agent from checklist URL"""
        try:
            criteria, agent = self.auditor_builder.build_from_url(checklist_url)
            agent_id = f"auditor_{len(self.audit_cache)}"
            self.audit_cache[agent_id] = {"agent": agent, "url": checklist_url}
            self._log_operation("create_auditor", checklist_url, "success")
            return agent_id
        except Exception as e:
            self._log_operation("create_auditor", checklist_url, "failed", str(e))
            return None
    
    def run_audit(self, auditor_id: str, target: str) -> Dict:
        """Run specific audit"""
        if auditor_id not in self.audit_cache:
            return {"status": "error", "message": f"Auditor {auditor_id} not found"}
        
        try:
            agent = self.audit_cache[auditor_id]["agent"]
            report = agent.run_audit(target)
            self._log_operation("run_audit", target, "success")
            return report
        except Exception as e:
            self._log_operation("run_audit", target, "failed", str(e))
            return {"status": "error", "message": str(e)}
    
    def run_chained_audits(self, target: str, run_a11y: bool = True, 
                          auditor_ids: List[str] = None) -> Dict:
        """Run A11Y + custom audits in sequence"""
        results = {}
        
        if run_a11y:
            results["a11y"] = self.run_a11y_check(target)
        
        if auditor_ids:
            results["audits"] = {}
            for auditor_id in auditor_ids:
                results["audits"][auditor_id] = self.run_audit(auditor_id, target)
        
        self._log_operation("chained_audits", target, "success")
        
        return {
            "combined_report": results,
            "overall_score": self._calculate_overall_score(results),
            "timestamp": datetime.now().isoformat()
        }
    
    def _calculate_overall_score(self, results: Dict) -> float:
        """Calculate overall score from all audits"""
        scores = []
        
        if "a11y" in results and "score" in results["a11y"]:
            scores.append(results["a11y"]["score"])
        
        if "audits" in results:
            for audit in results["audits"].values():
                if "audit_report" in audit and "overall_score" in audit["audit_report"]:
                    scores.append(audit["audit_report"]["overall_score"])
        
        return sum(scores) / len(scores) if scores else 0
    
    def _log_operation(self, operation: str, target: str, status: str, error: str = ""):
        """Log operation to history"""
        self.operation_history.append({
            "operation": operation,
            "target": target,
            "status": status,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_operation_history(self) -> List[Dict]:
        """Get operation history"""
        return self.operation_history
    
    def export_summary(self) -> Dict:
        """Export orchestrator state"""
        return {
            "cached_auditors": len(self.audit_cache),
            "operations": len(self.operation_history),
            "last_operation": self.operation_history[-1] if self.operation_history else None
        }

orchestrator = SubAgentOrchestrator()
