"""
A11Y (Accessibility) Checker Agent
Checks website accessibility against WCAG 2.1 AA standards
"""
import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, List
from datetime import datetime
import json


class A11YChecker:
    """Check website accessibility compliance against WCAG 2.1 AA standards"""

    def __init__(self, wcag_level: str = "AA"):
        self.wcag_level = wcag_level
        self.checked_url = None
        self.html_content = None
        self.issues = []
        self.score = 100

    def check_url(self, url: str) -> Dict:
        """Check a live website for accessibility issues"""
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            self.checked_url = url
            self.html_content = response.text
            return self._analyze_html()
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def check_html(self, html_code: str) -> Dict:
        """Check HTML code for accessibility issues"""
        try:
            self.html_content = html_code
            self.checked_url = "html_input"
            return self._analyze_html()
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _analyze_html(self) -> Dict:
        """Analyze HTML content for accessibility issues"""
        self.issues = []
        self.score = 100
        soup = BeautifulSoup(self.html_content, 'html.parser')
        
        self._check_page_structure(soup)
        self._check_images(soup)
        self._check_forms(soup)
        self._check_keyboard_navigation(soup)
        self._check_aria_attributes(soup)
        self._check_semantic_html(soup)
        self._check_link_text(soup)
        self._check_heading_hierarchy(soup)

        return self.generate_report()

    def _check_page_structure(self, soup: BeautifulSoup):
        """Check page structure (title, language)"""
        title = soup.find('title')
        if not title or not title.string:
            self._add_issue("A11Y-001", "structure", "critical",
                          "Missing page title", "<title>", "Add page title", "2.4.2")

        html_tag = soup.find('html')
        if not html_tag or not html_tag.get('lang'):
            self._add_issue("A11Y-002", "structure", "major",
                          "Missing language declaration", "<html>", "Add lang attribute", "3.1.1")

    def _check_images(self, soup: BeautifulSoup):
        """Check images have alt text"""
        images = soup.find_all('img')
        for i, img in enumerate(images):
            if not img.get('alt'):
                self._add_issue(f"A11Y-IMG-{i}", "images", "major",
                              f"Missing alt text", "<img>", "Add alt attribute", "1.1.1")

    def _check_forms(self, soup: BeautifulSoup):
        """Check form accessibility"""
        inputs = soup.find_all(['input', 'textarea', 'select'])
        for i, inp in enumerate(inputs):
            inp_id = inp.get('id')
            if inp_id:
                label = soup.find('label', {'for': inp_id})
                if not label:
                    self._add_issue(f"A11Y-FORM-{i}", "forms", "major",
                                  f"Form input missing label", "<label>", "Add label", "1.3.1")

    def _check_keyboard_navigation(self, soup: BeautifulSoup):
        """Check keyboard navigation"""
        clickable_divs = soup.find_all('div', attrs={'onclick': True})
        for div in clickable_divs:
            if not div.get('tabindex'):
                self._add_issue("A11Y-KBD", "keyboard", "major",
                              "Clickable div not keyboard accessible", "<div>", "Add tabindex", "2.1.1")

    def _check_aria_attributes(self, soup: BeautifulSoup):
        """Check ARIA attributes"""
        hidden_interactive = soup.find_all(
            lambda tag: tag.get('aria-hidden') == 'true' and tag.name in ['button', 'a']
        )
        if hidden_interactive:
            self._add_issue("A11Y-ARIA", "aria", "critical",
                          "Hidden interactive element", "<element>", "Remove aria-hidden", "1.3.1")

    def _check_semantic_html(self, soup: BeautifulSoup):
        """Check semantic HTML"""
        if not soup.find('header') and not soup.find('nav'):
            self._add_issue("A11Y-SEM", "semantic", "minor",
                          "Missing semantic structure", "Page", "Use semantic HTML", "1.3.1")

    def _check_link_text(self, soup: BeautifulSoup):
        """Check link text quality"""
        links = soup.find_all('a')
        for i, link in enumerate(links):
            text = link.get_text(strip=True)
            if not text:
                self._add_issue(f"A11Y-LINK-{i}", "links", "major",
                              "Link with no text", "<a>", "Add link text", "2.4.4")

    def _check_heading_hierarchy(self, soup: BeautifulSoup):
        """Check heading hierarchy"""
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        h1s = [h for h in headings if h.name == 'h1']
        
        if not h1s:
            self._add_issue("A11Y-H1", "headings", "major",
                          "No H1 heading", "Page", "Add H1 heading", "1.3.1")

    def _add_issue(self, issue_id: str, category: str, severity: str,
                   issue: str, element: str, fix: str, wcag: str):
        """Add issue and update score"""
        self.issues.append({
            "id": issue_id,
            "category": category,
            "severity": severity,
            "issue": issue,
            "element": element,
            "fix": fix,
            "wcag": wcag
        })
        
        if severity == "critical":
            self.score -= 10
        elif severity == "major":
            self.score -= 5
        else:
            self.score -= 2
        
        self.score = max(0, self.score)

    def generate_report(self) -> Dict:
        """Generate JSON report"""
        critical = len([i for i in self.issues if i['severity'] == 'critical'])
        major = len([i for i in self.issues if i['severity'] == 'major'])
        minor = len([i for i in self.issues if i['severity'] == 'minor'])
        
        status = "fail" if critical > 0 else "warning" if major > 0 else "pass"
        
        return {
            "status": status,
            "score": self.score,
            "wcagLevel": self.wcag_level,
            "checkedUrl": self.checked_url,
            "checkedDate": datetime.now().isoformat(),
            "issues": self.issues,
            "summary": f"{critical} critical, {major} major, {minor} minor",
            "totals": {"critical": critical, "major": major, "minor": minor, "total": len(self.issues)}
        }


a11y_checker = A11YChecker()
