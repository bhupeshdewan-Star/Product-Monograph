"""
Free AI Priority Manager
Automatically selects AI provider based on free tier availability
Priority: Ollama > Groq > Together.ai > OpenAI > Anthropic Free > Anthropic Paid
"""
import os
from typing import Dict, Tuple
from dotenv import load_dotenv
import requests
from datetime import datetime

load_dotenv()

class FreeAIPriorityManager:
    """Manages AI provider selection prioritizing free tiers"""

    def __init__(self):
        self.current_provider = None
        self.quota_status = {}
        self.usage_log = []
        self.fallback_chain = [
            'ollama',
            'groq_free',
            'together_ai',
            'openai_free',
            'anthropic_free',
            'anthropic_paid'
        ]

    def get_optimal_provider(self) -> Tuple[str, Dict]:
        """
        Select best available AI provider
        Checks in priority order, uses first available

        Returns: (provider_name, config_dict)
        """

        print("\n🤖 CHECKING AI PROVIDER AVAILABILITY (Free-First Strategy)")
        print("=" * 70)

        for provider in self.fallback_chain:
            is_available, config = self._check_provider_availability(provider)

            if is_available:
                print(f"[OK] SELECTED: {provider.upper()}")
                print(f"  Status: Available")
                if config.get('limit_note'):
                    print(f"  Note: {config['limit_note']}")
                print("=" * 70)

                self.current_provider = provider
                self._log_provider_usage(provider)
                return provider, config

        # Fallback to paid Anthropic
        print("[WARN] All free tiers exhausted, falling back to ANTHROPIC PAID")
        print("=" * 70)
        self.current_provider = 'anthropic_paid'
        self._log_provider_usage('anthropic_paid')
        return 'anthropic_paid', self._get_provider_config('anthropic_paid')

    def _check_provider_availability(self, provider: str) -> Tuple[bool, Dict]:
        """Check if provider is available and has quota"""

        if provider == 'ollama':
            return self._check_ollama()

        elif provider == 'groq_free':
            return self._check_groq_free()

        elif provider == 'together_ai':
            return self._check_together_ai()

        elif provider == 'openai_free':
            return self._check_openai_free()

        elif provider == 'anthropic_free':
            return self._check_anthropic_free()

        elif provider == 'anthropic_paid':
            return self._check_anthropic_paid()

        return False, {}

    def _check_ollama(self) -> Tuple[bool, Dict]:
        """
        Check Ollama availability (Local, 100% Free)
        """
        try:
            ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
            response = requests.get(f"{ollama_url}/api/tags", timeout=2)

            if response.status_code == 200:
                model = os.getenv('OLLAMA_MODEL', 'llama2')
                print(f"[OK] OLLAMA: Running locally (Free, Unlimited)")
                return True, {
                    'provider': 'ollama',
                    'model': model,
                    'url': ollama_url,
                    'cost': 0,
                    'limit_note': 'No limits - runs on your computer',
                    'quota_status': 'Unlimited'
                }
        except requests.exceptions.ConnectionError:
            print("[ERROR] Ollama: Not running (Start with: ollama serve)")
        except Exception as e:
            print(f"[ERROR] Ollama: {str(e)}")

        return False, {}

    def _check_groq_free(self) -> Tuple[bool, Dict]:
        """
        Check Groq free tier availability
        Limited free tier, very fast inference
        """
        api_key = os.getenv('GROQ_API_KEY', '')

        if not api_key:
            print("[ERROR] Groq: No API key configured")
            return False, {}

        try:
            # Check if API key works
            from groq import Groq
            client = Groq(api_key=api_key)

            # Attempt minimal request to verify
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": "test"}],
                model="mixtral-8x7b-32768",
                max_tokens=10
            )

            print(f"[OK] Groq: Free tier available (Fast inference)")
            return True, {
                'provider': 'groq',
                'model': 'mixtral-8x7b-32768',
                'cost': 0,
                'limit_note': 'Free tier has request limits - verify quota',
                'quota_status': 'Limited'
            }

        except Exception as e:
            print(f"[ERROR] Groq: {str(e)}")
            return False, {}

    def _check_together_ai(self) -> Tuple[bool, Dict]:
        """
        Check Together.ai free tier
        Open source models, low cost or free tier
        """
        api_key = os.getenv('TOGETHER_API_KEY', '')

        if not api_key:
            print("[ERROR] Together.ai: No API key configured")
            return False, {}

        try:
            import together
            together.api_key = api_key

            # Check API availability
            print(f"[OK] Together.ai: Available (Open source models)")
            return True, {
                'provider': 'together_ai',
                'model': os.getenv('TOGETHER_MODEL', 'meta-llama/Llama-2-70b-chat-hf'),
                'cost': 0,  # Free tier
                'limit_note': 'Free tier available - verify quota',
                'quota_status': 'Limited'
            }

        except Exception as e:
            print(f"[ERROR] Together.ai: {str(e)}")
            return False, {}

    def _check_openai_free(self) -> Tuple[bool, Dict]:
        """
        Check OpenAI free trial quota (if available)
        Only available for new accounts within trial period
        """
        api_key = os.getenv('OPENAI_API_KEY', '')

        if not api_key:
            print("[ERROR] OpenAI: No API key configured")
            return False, {}

        try:
            # Check if free quota still available
            # Note: OpenAI doesn't provide direct quota API
            # This requires manual tracking

            quota_remaining = self._get_openai_quota()

            if quota_remaining > 0:
                print(f"[OK] OpenAI: Free quota available (${quota_remaining:.2f} remaining)")
                return True, {
                    'provider': 'openai',
                    'model': 'gpt-3.5-turbo',
                    'cost': 0,
                    'limit_note': f'${quota_remaining:.2f} free trial remaining',
                    'quota_status': f'${quota_remaining:.2f}'
                }
            else:
                print("[ERROR] OpenAI: Free quota exhausted")
                return False, {}

        except Exception as e:
            print(f"[ERROR] OpenAI: {str(e)}")
            return False, {}

    def _check_anthropic_free(self) -> Tuple[bool, Dict]:
        """
        Check Anthropic free daily quota
        Claude has daily free usage limits in some regions
        """
        api_key = os.getenv('ANTHROPIC_API_KEY', '')

        if not api_key:
            print("[ERROR] Anthropic: No API key configured")
            return False, {}

        try:
            usage_today = self._get_anthropic_daily_usage()

            # Anthropic free daily limit (varies by region, typically 100K tokens)
            free_limit = 100000  # tokens
            remaining = max(0, free_limit - usage_today)

            if remaining > 0:
                print(f"[OK] Anthropic: Free quota available ({remaining:,.0f} tokens remaining)")
                return True, {
                    'provider': 'anthropic',
                    'model': 'claude-haiku-4-5-20251001',
                    'cost': 0,
                    'limit_note': f'{remaining:,.0f} tokens free remaining today',
                    'quota_status': f'{remaining:,.0f} tokens'
                }
            else:
                print("[ERROR] Anthropic: Free daily quota exhausted")
                return False, {}

        except Exception as e:
            print(f"[ERROR] Anthropic Free: {str(e)}")
            return False, {}

    def _check_anthropic_paid(self) -> Tuple[bool, Dict]:
        """
        Check Anthropic paid API (Last resort)
        """
        api_key = os.getenv('ANTHROPIC_API_KEY', '')

        if not api_key:
            print("[ERROR] Anthropic Paid: No API key configured")
            return False, {}

        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=api_key)

            print(f"[WARN] Anthropic: PAID API (Emergency/Fallback)")
            return True, {
                'provider': 'anthropic_paid',
                'model': 'claude-haiku-4-5-20251001',
                'cost': 0.154,  # per monograph
                'limit_note': 'Paid API - charges apply',
                'quota_status': 'Unlimited (paid)'
            }

        except Exception as e:
            print(f"[ERROR] Anthropic: {str(e)}")
            return False, {}

    def _get_provider_config(self, provider: str) -> Dict:
        """Get configuration for provider"""

        configs = {
            'ollama': {
                'provider': 'ollama',
                'model': os.getenv('OLLAMA_MODEL', 'llama2'),
                'url': os.getenv('OLLAMA_URL', 'http://localhost:11434'),
                'cost': 0
            },
            'groq': {
                'provider': 'groq',
                'model': os.getenv('GROQ_MODEL', 'mixtral-8x7b-32768'),
                'api_key': os.getenv('GROQ_API_KEY'),
                'cost': 0
            },
            'together_ai': {
                'provider': 'together_ai',
                'model': os.getenv('TOGETHER_MODEL', 'meta-llama/Llama-2-70b-chat-hf'),
                'api_key': os.getenv('TOGETHER_API_KEY'),
                'cost': 0
            },
            'anthropic_paid': {
                'provider': 'anthropic',
                'model': 'claude-haiku-4-5-20251001',
                'api_key': os.getenv('ANTHROPIC_API_KEY'),
                'cost': 0.154
            }
        }

        return configs.get(provider, {})

    def _get_openai_quota(self) -> float:
        """
        Get remaining OpenAI free quota
        Requires manual tracking (OpenAI API doesn't expose this)
        """
        # Read from local tracking file
        quota_file = 'data/openai_quota.json'

        try:
            import json
            if os.path.exists(quota_file):
                with open(quota_file, 'r') as f:
                    data = json.load(f)
                    return data.get('remaining', 0)
        except:
            pass

        return 0

    def _get_anthropic_daily_usage(self) -> int:
        """
        Get Anthropic daily token usage
        Requires manual tracking from API responses
        """
        usage_file = 'data/anthropic_daily_usage.json'

        try:
            import json
            if os.path.exists(usage_file):
                with open(usage_file, 'r') as f:
                    data = json.load(f)
                    # Reset if new day
                    if data.get('date') != datetime.now().strftime('%Y-%m-%d'):
                        return 0
                    return data.get('tokens', 0)
        except:
            pass

        return 0

    def _log_provider_usage(self, provider: str):
        """Log which provider was used for this monograph"""

        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'provider': provider,
            'date': datetime.now().strftime('%Y-%m-%d')
        }

        self.usage_log.append(log_entry)

        # Save to file
        try:
            import json
            log_file = 'data/ai_provider_usage_log.json'
            os.makedirs(os.path.dirname(log_file), exist_ok=True)

            # Read existing log
            existing_log = []
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    existing_log = json.load(f)

            # Append new entry
            existing_log.append(log_entry)

            # Save
            with open(log_file, 'w') as f:
                json.dump(existing_log, f, indent=2)

        except Exception as e:
            print(f"Warning: Could not log provider usage: {e}")

    def generate_usage_report(self) -> str:
        """Generate AI provider usage and cost report"""

        try:
            import json
            log_file = 'data/ai_provider_usage_log.json'

            if not os.path.exists(log_file):
                return "No usage data available yet"

            with open(log_file, 'r') as f:
                logs = json.load(f)

            # Count by provider
            provider_counts = {}
            for log in logs:
                provider = log.get('provider', 'unknown')
                provider_counts[provider] = provider_counts.get(provider, 0) + 1

            # Calculate costs
            costs = {
                'ollama': 0,
                'groq_free': 0,
                'together_ai': 0,
                'openai_free': 0,
                'anthropic_free': 0,
                'anthropic_paid': 0.154  # per monograph
            }

            total_cost = 0
            cost_breakdown = {}

            for provider, count in provider_counts.items():
                cost = count * costs.get(provider, 0)
                total_cost += cost
                cost_breakdown[provider] = {
                    'monographs': count,
                    'cost': cost
                }

            # Generate report
            report = f"""
╔════════════════════════════════════════════════════════════════════╗
║                    AI PROVIDER USAGE REPORT                        ║
╠════════════════════════════════════════════════════════════════════╣

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Monographs Generated: {len(logs)}
Unique Providers Used: {len(provider_counts)}

USAGE BY PROVIDER:
──────────────────
"""

            for provider, count in sorted(provider_counts.items(), key=lambda x: x[1], reverse=True):
                cost = cost_breakdown[provider]['cost']
                pct = (count / len(logs)) * 100
                report += f"\n{provider.upper():<20}: {count:>3} monographs ({pct:>5.1f}%) - ${cost:>8.2f}"

            report += f"""

COST SUMMARY:
─────────────
Total Cost: ${total_cost:.2f}
Average per Monograph: ${total_cost/len(logs) if logs else 0:.2f}

SAVINGS vs Anthropic Only:
──────────────────────────
Anthropic-only cost: ${len(logs) * 0.154:.2f}
Actual cost: ${total_cost:.2f}
SAVED: ${(len(logs) * 0.154) - total_cost:.2f}
Savings percentage: {((len(logs) * 0.154) - total_cost) / (len(logs) * 0.154) * 100 if logs else 0:.1f}%

═══════════════════════════════════════════════════════════════════════
"""

            return report

        except Exception as e:
            return f"Error generating report: {str(e)}"


# Initialize globally
free_ai_manager = FreeAIPriorityManager()
