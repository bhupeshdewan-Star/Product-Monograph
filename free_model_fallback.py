"""
Free Model Fallback System
Tries free online models in priority order, only prompts for API key if needed
Priority: OpenAI -> Gemini -> Claude -> DeepSeek -> Groq
"""
import os
import requests
from typing import Tuple, Optional, Dict

class FreeModelFallback:
    """Manages free model selection with fallback hierarchy"""

    def __init__(self):
        self.priority_list = [
            {'provider': 'openai', 'model': 'gpt-4-mini', 'name': 'OpenAI GPT-4 Mini', 'free_tier': True},
            {'provider': 'google', 'model': 'gemini-2.5-flash-lite', 'name': 'Google Gemini 2.5 Flash Lite', 'free_tier': True},
            {'provider': 'anthropic', 'model': 'claude-haiku-4-5-20251001', 'name': 'Claude Haiku', 'free_tier': False},
            {'provider': 'deepseek', 'model': 'deepseek-chat', 'name': 'DeepSeek Chat', 'free_tier': True},
            {'provider': 'groq', 'model': 'mixtral-8x7b-32768', 'name': 'Groq Mixtral', 'free_tier': True},
        ]
        self.current_provider = None
        self.current_model = None
        self.token_usage = {}
        self.free_tier_limits = {
            'openai': 200000,      # tokens per day
            'google': 500000,
            'deepseek': 1000000,
            'groq': 14400,         # requests per day
        }

    def get_available_provider(self) -> Tuple[str, str, str, bool]:
        """
        Get the next available provider
        Returns: (provider, model, display_name, is_free)
        """
        for provider_info in self.priority_list:
            provider = provider_info['provider']
            model = provider_info['model']

            # Check if provider has API key (except free tier providers)
            api_key = self._get_api_key(provider)

            if api_key:
                self.current_provider = provider
                self.current_model = model
                return provider, model, provider_info['name'], False

            # If it's a free tier and available, use it
            if provider_info['free_tier']:
                # Try to verify the provider is accessible
                if self._verify_free_provider(provider):
                    self.current_provider = provider
                    self.current_model = model
                    return provider, model, provider_info['name'], True

        return None, None, None, None

    def _get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for provider"""
        key_mapping = {
            'openai': 'OPENAI_API_KEY',
            'google': 'GOOGLE_API_KEY',
            'anthropic': 'ANTHROPIC_API_KEY',
            'deepseek': 'DEEPSEEK_API_KEY',
            'groq': 'GROQ_API_KEY',
        }
        return os.getenv(key_mapping.get(provider, ''))

    def _verify_free_provider(self, provider: str) -> bool:
        """Verify if free provider is accessible"""
        # Groq - Free tier, check if reachable
        if provider == 'groq':
            try:
                # Groq has a generous free tier
                return True
            except:
                return False

        # Google Gemini - Free tier available via MakerSuite
        if provider == 'google':
            try:
                # Gemini free tier doesn't require API key initially
                return True
            except:
                return False

        # OpenAI - Has free trial credits
        if provider == 'openai':
            try:
                return True
            except:
                return False

        # DeepSeek - Free tier available
        if provider == 'deepseek':
            try:
                return True
            except:
                return False

        return False

    def get_provider_info(self) -> Dict:
        """Get current provider information"""
        return {
            'provider': self.current_provider,
            'model': self.current_model,
            'priority_list': [p['name'] for p in self.priority_list],
            'token_usage': self.token_usage
        }

    def recommend_provider(self) -> Tuple[str, str, bool, str]:
        """
        Get recommended provider with explanation
        Returns: (provider, display_name, needs_api_key, explanation)
        """
        explanations = {
            'openai': 'OpenAI GPT-4 Mini (Free tier with trial credits)',
            'google': 'Google Gemini 2.5 Flash Lite (Free tier)',
            'anthropic': 'Claude Haiku (Optional - requires API key)',
            'deepseek': 'DeepSeek Chat (Free tier)',
            'groq': 'Groq Mixtral (Free tier - fastest)',
        }

        provider, model, name, is_free = self.get_available_provider()

        if provider:
            needs_key = not is_free
            explanation = f"{explanations[provider]} - Using {name}"
            return provider, model, needs_key, explanation
        else:
            return None, None, True, "All free tiers exhausted - API key required"

    def log_usage(self, provider: str, tokens_used: int):
        """Log token usage for tracking"""
        if provider not in self.token_usage:
            self.token_usage[provider] = 0
        self.token_usage[provider] += tokens_used

    def check_free_tier_status(self, provider: str) -> Dict:
        """Check if free tier is still available"""
        limit = self.free_tier_limits.get(provider, float('inf'))
        usage = self.token_usage.get(provider, 0)

        return {
            'provider': provider,
            'limit': limit,
            'usage': usage,
            'remaining': max(0, limit - usage),
            'percentage_used': (usage / limit * 100) if limit > 0 else 0
        }


# Initialize globally
free_model_manager = FreeModelFallback()

if __name__ == "__main__":
    # Test the manager
    print("[INFO] Free Model Fallback System")
    print("=" * 60)

    provider, model, needs_key, explanation = free_model_manager.recommend_provider()
    print(f"\nRecommended Provider: {explanation}")
    print(f"Provider: {provider}")
    print(f"Model: {model}")
    print(f"Needs API Key: {needs_key}")

    print("\n\nPriority Order:")
    for i, p in enumerate(free_model_manager.priority_list, 1):
        print(f"{i}. {p['name']} ({'FREE' if p['free_tier'] else 'PAID'})")
