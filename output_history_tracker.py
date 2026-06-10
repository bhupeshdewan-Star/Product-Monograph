"""
Output History Tracker
Tracks all generated monographs with metadata and history
"""
import json
import os
from datetime import datetime
from typing import Dict, List

class OutputHistoryTracker:
    """Tracks all monograph outputs with detailed metadata"""

    def __init__(self):
        self.history_dir = "data/generation_history"
        self.history_file = os.path.join(self.history_dir, "monograph_history.json")
        os.makedirs(self.history_dir, exist_ok=True)

    def log_generation(self, monograph_data: Dict) -> str:
        """Log a monograph generation"""

        entry = {
            'timestamp': datetime.now().isoformat(),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'time': datetime.now().strftime('%H:%M:%S'),
            'molecule_name': monograph_data.get('molecule_name', 'Unknown'),
            'sections_generated': len(monograph_data.get('sections', {})),
            'total_articles': monograph_data.get('total_articles', 0),
            'compliance_score': monograph_data.get('compliance_score', 0),
            'total_tokens_used': monograph_data.get('total_tokens_used', 0),
            'estimated_cost': monograph_data.get('estimated_cost', 0),
            'ai_provider': monograph_data.get('ai_provider', 'Unknown'),
            'output_files': {
                'pdf': monograph_data.get('pdf_path', ''),
                'word': monograph_data.get('word_path', ''),
                'json': monograph_data.get('json_path', ''),
            },
            'references_count': monograph_data.get('references_count', 0),
            'hcp_specialty': monograph_data.get('hcp_specialty', 'General'),
            'generation_time_seconds': monograph_data.get('generation_time', 0),
            'markdown_cleaned': monograph_data.get('markdown_cleaned', False),
            'tables_formatted': monograph_data.get('tables_formatted', False),
            'validation_status': monograph_data.get('validation_status', 'Unknown'),
        }

        # Read existing history
        history = []
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    history = json.load(f)
            except:
                history = []

        # Append new entry
        history.append(entry)

        # Save
        try:
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save history: {e}")

        return entry

    def get_generation_history(self, limit: int = 100) -> List[Dict]:
        """Get generation history"""
        if not os.path.exists(self.history_file):
            return []

        try:
            with open(self.history_file, 'r') as f:
                history = json.load(f)
                return history[-limit:]  # Return last N entries
        except:
            return []

    def get_daily_summary(self, date: str = None) -> Dict:
        """Get today's generation summary"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        history = self.get_generation_history(limit=10000)

        summary = {
            'date': date,
            'total_monographs': 0,
            'total_articles': 0,
            'total_tokens': 0,
            'total_cost': 0.0,
            'average_compliance': 0.0,
            'by_provider': {},
            'by_specialty': {},
            'molecules': []
        }

        daily_entries = [h for h in history if h.get('date') == date]

        if not daily_entries:
            return summary

        summary['total_monographs'] = len(daily_entries)
        summary['total_articles'] = sum(e.get('total_articles', 0) for e in daily_entries)
        summary['total_tokens'] = sum(e.get('total_tokens_used', 0) for e in daily_entries)
        summary['total_cost'] = sum(e.get('estimated_cost', 0) for e in daily_entries)
        summary['average_compliance'] = sum(e.get('compliance_score', 0) for e in daily_entries) / len(daily_entries)

        for entry in daily_entries:
            # Provider breakdown
            provider = entry.get('ai_provider', 'Unknown')
            if provider not in summary['by_provider']:
                summary['by_provider'][provider] = {'count': 0, 'cost': 0}
            summary['by_provider'][provider]['count'] += 1
            summary['by_provider'][provider]['cost'] += entry.get('estimated_cost', 0)

            # Specialty breakdown
            specialty = entry.get('hcp_specialty', 'General')
            if specialty not in summary['by_specialty']:
                summary['by_specialty'][specialty] = 0
            summary['by_specialty'][specialty] += 1

            # Molecule list
            summary['molecules'].append(entry.get('molecule_name', 'Unknown'))

        return summary

    def generate_history_report(self, days: int = 30) -> str:
        """Generate detailed history report"""
        history = self.get_generation_history(limit=10000)

        # Filter last N days
        cutoff_date = datetime.now()
        from datetime import timedelta
        cutoff_date = cutoff_date - timedelta(days=days)

        recent_history = [
            h for h in history
            if datetime.fromisoformat(h['timestamp']) >= cutoff_date
        ]

        # Calculate statistics
        total_monographs = len(recent_history)
        total_articles = sum(h.get('total_articles', 0) for h in recent_history)
        total_tokens = sum(h.get('total_tokens_used', 0) for h in recent_history)
        total_cost = sum(h.get('estimated_cost', 0) for h in recent_history)

        if total_monographs == 0:
            return f"No monographs generated in the last {days} days"

        report = f"""
╔════════════════════════════════════════════════════════════════════╗
║               MONOGRAPH GENERATION HISTORY REPORT                  ║
╠════════════════════════════════════════════════════════════════════╣

Period: Last {days} days
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SUMMARY:
────────
Total Monographs Generated: {total_monographs}
Total Articles Used: {total_articles:,}
Total Tokens Consumed: {total_tokens:,}
Total Cost: ${total_cost:.2f}
Average Cost per Monograph: ${total_cost/total_monographs if total_monographs > 0 else 0:.2f}

QUALITY METRICS:
────────────────
Average Compliance Score: {sum(h.get('compliance_score', 0) for h in recent_history) / total_monographs:.1f}%
Markdown Cleaned: {sum(1 for h in recent_history if h.get('markdown_cleaned'))}/{total_monographs}
Tables Formatted: {sum(1 for h in recent_history if h.get('tables_formatted'))}/{total_monographs}

BY AI PROVIDER:
───────────────
"""

        provider_stats = {}
        for entry in recent_history:
            provider = entry.get('ai_provider', 'Unknown')
            if provider not in provider_stats:
                provider_stats[provider] = {'count': 0, 'cost': 0}
            provider_stats[provider]['count'] += 1
            provider_stats[provider]['cost'] += entry.get('estimated_cost', 0)

        for provider, stats in sorted(provider_stats.items(), key=lambda x: x[1]['cost'], reverse=True):
            report += f"\n{provider:<20}: {stats['count']:>3} monographs | ${stats['cost']:>8.2f}"

        report += """

BY HCP SPECIALTY:
─────────────────
"""

        specialty_stats = {}
        for entry in recent_history:
            specialty = entry.get('hcp_specialty', 'General')
            if specialty not in specialty_stats:
                specialty_stats[specialty] = 0
            specialty_stats[specialty] += 1

        for specialty, count in sorted(specialty_stats.items(), key=lambda x: x[1], reverse=True):
            report += f"\n{specialty:<30}: {count:>3} monographs"

        report += """

TOP MOLECULES:
──────────────
"""

        molecule_stats = {}
        for entry in recent_history:
            molecule = entry.get('molecule_name', 'Unknown')
            if molecule not in molecule_stats:
                molecule_stats[molecule] = 0
            molecule_stats[molecule] += 1

        for molecule, count in sorted(molecule_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
            report += f"\n{molecule:<30}: {count:>3} times"

        report += """

RECENT GENERATIONS:
───────────────────
"""

        for entry in recent_history[-10:]:  # Last 10
            report += f"\n{entry['timestamp']:<25} | {entry['molecule_name']:<20} | {entry['compliance_score']:>5.1f}% | ${entry['estimated_cost']:>8.2f}"

        report += """

═══════════════════════════════════════════════════════════════════════
"""

        return report

    def export_history_csv(self, filename: str = None) -> str:
        """Export history as CSV"""
        if filename is None:
            filename = os.path.join(self.history_dir, f"history_{datetime.now().strftime('%Y%m%d')}.csv")

        history = self.get_generation_history(limit=10000)

        if not history:
            return "No history to export"

        # Build CSV
        csv_lines = []

        # Header
        csv_lines.append("Timestamp,Molecule,Sections,Articles,Compliance%,Tokens,Cost,Provider,Specialty,Generation_Time_Sec")

        # Data
        for entry in history:
            csv_lines.append(
                f"{entry.get('timestamp', '')},"
                f"{entry.get('molecule_name', '')},"
                f"{entry.get('sections_generated', 0)},"
                f"{entry.get('total_articles', 0)},"
                f"{entry.get('compliance_score', 0):.1f},"
                f"{entry.get('total_tokens_used', 0)},"
                f"{entry.get('estimated_cost', 0):.2f},"
                f"{entry.get('ai_provider', '')},"
                f"{entry.get('hcp_specialty', '')},"
                f"{entry.get('generation_time_seconds', 0)}"
            )

        csv_content = '\n'.join(csv_lines)

        # Save
        try:
            with open(filename, 'w') as f:
                f.write(csv_content)
            return filename
        except Exception as e:
            return f"Error: {str(e)}"


# Initialize globally
output_history = OutputHistoryTracker()
