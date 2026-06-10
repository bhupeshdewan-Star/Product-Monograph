"""
Cost Analytics Dashboard
Tracks AI provider costs, free tier usage, and savings
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List
from collections import defaultdict

class CostAnalyticsDashboard:
    """Tracks and analyzes costs across all monograph generations"""

    def __init__(self):
        self.data_dir = "data/analytics"
        os.makedirs(self.data_dir, exist_ok=True)
        self.usage_log_file = os.path.join(self.data_dir, "cost_log.json")
        self.quota_file = os.path.join(self.data_dir, "quota_tracking.json")

    def log_monograph_generation(self, molecule_name: str, provider: str,
                                 tokens_used: int, cost: float):
        """Log a monograph generation event"""

        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'molecule_name': molecule_name,
            'provider': provider,
            'tokens_used': tokens_used,
            'cost': cost
        }

        # Read existing log
        existing_log = []
        if os.path.exists(self.usage_log_file):
            try:
                with open(self.usage_log_file, 'r') as f:
                    existing_log = json.load(f)
            except:
                existing_log = []

        # Append new entry
        existing_log.append(log_entry)

        # Save
        try:
            with open(self.usage_log_file, 'w') as f:
                json.dump(existing_log, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not log cost: {e}")

    def get_daily_summary(self, date: str = None) -> Dict:
        """
        Get cost summary for a specific date

        Args:
            date: YYYY-MM-DD format, defaults to today
        """

        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        summary = {
            'date': date,
            'total_monographs': 0,
            'total_tokens': 0,
            'total_cost': 0.0,
            'by_provider': defaultdict(lambda: {'count': 0, 'cost': 0.0, 'tokens': 0}),
            'molecules': []
        }

        # Read log
        if not os.path.exists(self.usage_log_file):
            return summary

        try:
            with open(self.usage_log_file, 'r') as f:
                logs = json.load(f)
        except:
            return summary

        # Filter by date
        for log in logs:
            if log.get('date') == date:
                summary['total_monographs'] += 1
                summary['total_tokens'] += log.get('tokens_used', 0)
                summary['total_cost'] += log.get('cost', 0)
                summary['molecules'].append(log.get('molecule_name', 'Unknown'))

                provider = log.get('provider', 'unknown')
                summary['by_provider'][provider]['count'] += 1
                summary['by_provider'][provider]['cost'] += log.get('cost', 0)
                summary['by_provider'][provider]['tokens'] += log.get('tokens_used', 0)

        return summary

    def get_monthly_summary(self, year: int = None, month: int = None) -> Dict:
        """Get cost summary for a specific month"""

        if year is None or month is None:
            now = datetime.now()
            year, month = now.year, now.month

        summary = {
            'period': f"{year}-{month:02d}",
            'total_monographs': 0,
            'total_tokens': 0,
            'total_cost': 0.0,
            'by_provider': defaultdict(lambda: {'count': 0, 'cost': 0.0}),
            'daily_breakdown': defaultdict(lambda: {'count': 0, 'cost': 0.0}),
            'top_molecules': defaultdict(int)
        }

        # Read log
        if not os.path.exists(self.usage_log_file):
            return summary

        try:
            with open(self.usage_log_file, 'r') as f:
                logs = json.load(f)
        except:
            return summary

        # Filter by month
        for log in logs:
            log_date = log.get('date', '')
            if log_date.startswith(f"{year}-{month:02d}"):
                summary['total_monographs'] += 1
                summary['total_tokens'] += log.get('tokens_used', 0)
                summary['total_cost'] += log.get('cost', 0)

                provider = log.get('provider', 'unknown')
                summary['by_provider'][provider]['count'] += 1
                summary['by_provider'][provider]['cost'] += log.get('cost', 0)

                day = log_date[-2:]
                summary['daily_breakdown'][day]['count'] += 1
                summary['daily_breakdown'][day]['cost'] += log.get('cost', 0)

                molecule = log.get('molecule_name', 'Unknown')
                summary['top_molecules'][molecule] += 1

        return summary

    def get_yearly_summary(self, year: int = None) -> Dict:
        """Get cost summary for a specific year"""

        if year is None:
            year = datetime.now().year

        summary = {
            'year': year,
            'total_monographs': 0,
            'total_tokens': 0,
            'total_cost': 0.0,
            'by_provider': defaultdict(lambda: {'count': 0, 'cost': 0.0}),
            'by_month': defaultdict(lambda: {'count': 0, 'cost': 0.0}),
            'free_monographs': 0,
            'paid_monographs': 0
        }

        # Read log
        if not os.path.exists(self.usage_log_file):
            return summary

        try:
            with open(self.usage_log_file, 'r') as f:
                logs = json.load(f)
        except:
            return summary

        # Filter by year
        for log in logs:
            log_date = log.get('date', '')
            if log_date.startswith(str(year)):
                summary['total_monographs'] += 1
                summary['total_tokens'] += log.get('tokens_used', 0)
                cost = log.get('cost', 0)
                summary['total_cost'] += cost

                if cost == 0:
                    summary['free_monographs'] += 1
                else:
                    summary['paid_monographs'] += 1

                provider = log.get('provider', 'unknown')
                summary['by_provider'][provider]['count'] += 1
                summary['by_provider'][provider]['cost'] += cost

                month = log_date[5:7]
                summary['by_month'][month]['count'] += 1
                summary['by_month'][month]['cost'] += cost

        return summary

    def generate_daily_report(self) -> str:
        """Generate today's cost report"""

        summary = self.get_daily_summary()

        report = f"""
╔════════════════════════════════════════════════════════════════════╗
║                     DAILY COST REPORT                              ║
╠════════════════════════════════════════════════════════════════════╣

Date: {summary['date']}

SUMMARY:
────────
Monographs Generated: {summary['total_monographs']}
Total Tokens Used: {summary['total_tokens']:,}
Total Cost: ${summary['total_cost']:.2f}
Average Cost per Monograph: ${summary['total_cost']/summary['total_monographs'] if summary['total_monographs'] > 0 else 0:.2f}

BY PROVIDER:
────────────
"""

        for provider, data in sorted(summary['by_provider'].items(),
                                    key=lambda x: x[1]['cost'], reverse=True):
            report += f"\n{provider.upper():<20}: {data['count']:>3} monographs | {data['tokens']:>7,} tokens | ${data['cost']:>8.2f}"

        report += f"""

MOLECULES GENERATED:
──────────────────"""

        for molecule in summary['molecules']:
            report += f"\n  • {molecule}"

        report += f"""

SAVINGS vs Anthropic-Only:
─────────────────────────
If using Anthropic: ${summary['total_monographs'] * 0.154:.2f}
Actual cost: ${summary['total_cost']:.2f}
SAVED: ${(summary['total_monographs'] * 0.154) - summary['total_cost']:.2f}

═══════════════════════════════════════════════════════════════════════
"""

        return report

    def generate_monthly_report(self, year: int = None, month: int = None) -> str:
        """Generate monthly cost report"""

        if year is None or month is None:
            now = datetime.now()
            year, month = now.year, now.month

        summary = self.get_monthly_summary(year, month)

        report = f"""
╔════════════════════════════════════════════════════════════════════╗
║                   MONTHLY COST REPORT                              ║
╠════════════════════════════════════════════════════════════════════╣

Period: {summary['period']}

SUMMARY:
────────
Total Monographs: {summary['total_monographs']}
Total Tokens: {summary['total_tokens']:,}
Total Cost: ${summary['total_cost']:.2f}
Average per Monograph: ${summary['total_cost']/summary['total_monographs'] if summary['total_monographs'] > 0 else 0:.2f}

BY PROVIDER:
────────────
"""

        free_count = 0
        for provider, data in sorted(summary['by_provider'].items(),
                                    key=lambda x: x[1]['cost'], reverse=True):
            report += f"\n{provider.upper():<20}: {data['count']:>3} monographs | ${data['cost']:>8.2f}"
            if data['cost'] == 0:
                free_count += data['count']

        report += f"""

USAGE EFFICIENCY:
─────────────────
Free Tier Usage: {free_count} monographs ({free_count*100//summary['total_monographs'] if summary['total_monographs'] > 0 else 0}%)
Paid Usage: {summary['total_monographs'] - free_count} monographs ({(summary['total_monographs']-free_count)*100//summary['total_monographs'] if summary['total_monographs'] > 0 else 0}%)

COMPARISON:
──────────
Anthropic-Only Cost: ${summary['total_monographs'] * 0.154:.2f}
Actual Cost: ${summary['total_cost']:.2f}
TOTAL SAVED: ${(summary['total_monographs'] * 0.154) - summary['total_cost']:.2f}
Savings Rate: {((summary['total_monographs'] * 0.154) - summary['total_cost']) / (summary['total_monographs'] * 0.154) * 100 if summary['total_monographs'] > 0 else 0:.1f}%

═══════════════════════════════════════════════════════════════════════
"""

        return report

    def generate_yearly_report(self, year: int = None) -> str:
        """Generate yearly cost report"""

        if year is None:
            year = datetime.now().year

        summary = self.get_yearly_summary(year)

        report = f"""
╔════════════════════════════════════════════════════════════════════╗
║                   YEARLY COST REPORT                               ║
╠════════════════════════════════════════════════════════════════════╣

Year: {summary['year']}

SUMMARY:
────────
Total Monographs: {summary['total_monographs']}
Total Tokens: {summary['total_tokens']:,}
Total Cost: ${summary['total_cost']:.2f}
Average per Monograph: ${summary['total_cost']/summary['total_monographs'] if summary['total_monographs'] > 0 else 0:.2f}

FREE vs PAID:
──────────────
Free Monographs: {summary['free_monographs']} ({summary['free_monographs']*100//summary['total_monographs'] if summary['total_monographs'] > 0 else 0}%)
Paid Monographs: {summary['paid_monographs']} ({summary['paid_monographs']*100//summary['total_monographs'] if summary['total_monographs'] > 0 else 0}%)

BY PROVIDER:
────────────
"""

        for provider, data in sorted(summary['by_provider'].items(),
                                    key=lambda x: x[1]['cost'], reverse=True):
            pct = (data['count'] / summary['total_monographs'] * 100) if summary['total_monographs'] > 0 else 0
            report += f"\n{provider.upper():<20}: {data['count']:>3} monographs ({pct:>5.1f}%) | ${data['cost']:>10.2f}"

        report += f"""

COMPARISON:
──────────
Anthropic-Only Cost: ${summary['total_monographs'] * 0.154:.2f}
Actual Cost: ${summary['total_cost']:.2f}
TOTAL SAVED: ${(summary['total_monographs'] * 0.154) - summary['total_cost']:.2f}
Savings Rate: {((summary['total_monographs'] * 0.154) - summary['total_cost']) / (summary['total_monographs'] * 0.154) * 100 if summary['total_monographs'] > 0 else 0:.1f}%

COST PROJECTION:
───────────────
If using Anthropic only for 5 monographs/day:
  Daily: ${5 * 0.154:.2f} | Monthly: ${5 * 0.154 * 30:.2f} | Yearly: ${5 * 0.154 * 365:.2f}

With Free-First Strategy:
  Daily: ${summary['total_cost'] / (summary['total_monographs'] / 5) if summary['total_monographs'] > 0 else 0:.2f}
  Monthly: ${(summary['total_cost'] / summary['total_monographs'] * 5 * 30) if summary['total_monographs'] > 0 else 0:.2f}
  Yearly: ${(summary['total_cost'] / summary['total_monographs'] * 5 * 365) if summary['total_monographs'] > 0 else 0:.2f}

═══════════════════════════════════════════════════════════════════════
"""

        return report

    def print_dashboard(self):
        """Print current dashboard to console"""

        print("\n" + "=" * 80)
        print("COST ANALYTICS DASHBOARD")
        print("=" * 80)

        print("\n" + self.generate_daily_report())
        print("\n" + self.generate_monthly_report())
        print("\n" + self.generate_yearly_report())


# Initialize globally
cost_analytics = CostAnalyticsDashboard()
