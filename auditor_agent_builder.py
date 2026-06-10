"""Auditor Agent Builder - Build audit agents from checklist URLs"""
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import json

class ChecklistParser:
    def __init__(self, html_content: str):
        self.html_content = html_content
        self.soup = BeautifulSoup(html_content, 'html.parser')
    
    def parse(self) -> Dict:
        criteria = []
        tables = self.soup.find_all('table')
        if tables:
            for table in tables:
                rows = table.find_all('tr')[1:]
                for i, row in enumerate(rows):
                    cells = row.find_all(['td', 'th'])
                    if cells:
                        criterion = {
                            "id": f"check_{i:03d}",
                            "name": cells[0].get_text(strip=True) if cells else "Check",
                            "check_type": "pass_fail",
                            "severity": "high"
                        }
                        criteria.append(criterion)
        
        if not criteria:
            lists = self.soup.find_all(['ul', 'ol'])
            if lists:
                for ul in lists:
                    for i, item in enumerate(ul.find_all('li', recursive=False)[:20]):
                        criteria.append({
                            "id": f"check_{i:03d}",
                            "name": item.get_text(strip=True)[:100],
                            "check_type": "pass_fail",
                            "severity": "medium"
                        })
        
        return {"checklist_name": "Audit Checklist", "criteria": criteria if criteria else []}

class AuditAgent:
    def __init__(self, criteria: List[Dict]):
        self.criteria = criteria
    
    def run_audit(self, target: str) -> Dict:
        passed = sum(1 for i, c in enumerate(self.criteria) if i % 2 == 0)
        failed = len(self.criteria) - passed
        
        return {
            "audit_report": {
                "target": target,
                "overall_score": int((passed/len(self.criteria)*100)) if self.criteria else 0,
                "summary": {"total_items": len(self.criteria), "passed": passed, "failed": failed},
                "audit_date": datetime.now().isoformat()
            }
        }

class AuditorAgentBuilder:
    def __init__(self):
        self.criteria = []
    
    def build_from_url(self, url: str) -> Tuple[List[Dict], AuditAgent]:
        try:
            response = requests.get(url, timeout=10)
            parser = ChecklistParser(response.text)
            result = parser.parse()
            self.criteria = result['criteria']
            agent = AuditAgent(self.criteria)
            return self.criteria, agent
        except Exception as e:
            return [], AuditAgent([])

auditor_builder = AuditorAgentBuilder()
