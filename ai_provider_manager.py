"""
AI Provider Manager
Supports multiple AI platforms: Anthropic, OpenRouter, Ollama, local models
"""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class AIProviderManager:
    """Manages multiple AI provider integrations"""

    SUPPORTED_PROVIDERS = {
        'anthropic': 'Anthropic API (Claude)',
        'openrouter': 'OpenRouter (Multiple models: Claude, GPT, LLaMA, Mistral, etc.)',
        'ollama': 'Ollama (Local models: LLaMA, Mistral, etc.)',
        'together': 'Together.ai (Open source models)',
        'replicate': 'Replicate (Multiple models)',
        'groq': 'Groq API (Fast inference)',
    }

    def __init__(self):
        self.provider = os.getenv('AI_PROVIDER', 'anthropic').lower()
        self.model = self._get_model()
        self.client = self._initialize_client()

    def _get_model(self) -> str:
        """Get model based on provider"""
        provider_models = {
            'anthropic': os.getenv('ANTHROPIC_MODEL', 'claude-haiku-4-5-20251001'),
            'openrouter': os.getenv('OPENROUTER_MODEL', 'anthropic/claude-3-haiku'),
            'ollama': os.getenv('OLLAMA_MODEL', 'llama2'),
            'together': os.getenv('TOGETHER_MODEL', 'meta-llama/Llama-2-70b-chat-hf'),
            'replicate': os.getenv('REPLICATE_MODEL', 'meta/llama-2-70b-chat'),
            'groq': os.getenv('GROQ_MODEL', 'mixtral-8x7b-32768'),
        }
        return provider_models.get(self.provider, 'claude-haiku-4-5-20251001')

    def _initialize_client(self):
        """Initialize client based on provider"""
        if self.provider == 'anthropic':
            return self._init_anthropic()
        elif self.provider == 'openrouter':
            return self._init_openrouter()
        elif self.provider == 'ollama':
            return self._init_ollama()
        elif self.provider == 'together':
            return self._init_together()
        elif self.provider == 'groq':
            return self._init_groq()
        else:
            return self._init_anthropic()  # Default to Anthropic

    def _init_anthropic(self):
        """Initialize Anthropic client"""
        try:
            from anthropic import Anthropic
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                print("[WARN] Warning: ANTHROPIC_API_KEY not set")
            return Anthropic(api_key=api_key)
        except ImportError:
            print("Error: anthropic package not installed. Install with: pip install anthropic")
            return None

    def _init_openrouter(self):
        """Initialize OpenRouter client (uses OpenAI-compatible API)"""
        try:
            import openai
            api_key = os.getenv('OPENROUTER_API_KEY')
            if not api_key:
                print("[WARN] Warning: OPENROUTER_API_KEY not set")
                print("Get one at: https://openrouter.ai/")

            openai.api_key = api_key
            openai.api_base = "https://openrouter.ai/api/v1"
            return openai
        except ImportError:
            print("Error: openai package not installed. Install with: pip install openai")
            return None

    def _init_ollama(self):
        """Initialize Ollama (local models)"""
        try:
            import requests
            ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
            # Test connection
            try:
                requests.get(f"{ollama_url}/api/tags", timeout=5)
                print(f"[OK] Connected to Ollama at {ollama_url}")
            except:
                print(f"[WARN] Warning: Cannot reach Ollama at {ollama_url}")
                print("Start Ollama with: ollama serve")
            return ollama_url
        except ImportError:
            print("Error: requests package not installed")
            return None

    def _init_together(self):
        """Initialize Together.ai client"""
        try:
            import together
            api_key = os.getenv('TOGETHER_API_KEY')
            if not api_key:
                print("[WARN] Warning: TOGETHER_API_KEY not set")
                print("Get one at: https://together.ai/")
            together.api_key = api_key
            return together
        except ImportError:
            print("Error: together package not installed. Install with: pip install together")
            return None

    def _init_groq(self):
        """Initialize Groq client"""
        try:
            from groq import Groq
            api_key = os.getenv('GROQ_API_KEY')
            if not api_key:
                print("[WARN] Warning: GROQ_API_KEY not set")
                print("Get one at: https://console.groq.com/")
            return Groq(api_key=api_key)
        except ImportError:
            print("Error: groq package not installed. Install with: pip install groq")
            return None

    def generate_text(self, prompt: str, max_tokens: int = 2000) -> str:
        """Generate text using configured provider"""

        if self.provider == 'anthropic':
            return self._generate_anthropic(prompt, max_tokens)
        elif self.provider == 'openrouter':
            return self._generate_openrouter(prompt, max_tokens)
        elif self.provider == 'ollama':
            return self._generate_ollama(prompt, max_tokens)
        elif self.provider == 'groq':
            return self._generate_groq(prompt, max_tokens)
        else:
            return self._generate_anthropic(prompt, max_tokens)

    def _generate_anthropic(self, prompt: str, max_tokens: int) -> str:
        """Generate using Anthropic API"""
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
        except Exception as e:
            print(f"Error with Anthropic: {e}")
            return ""

    def _generate_openrouter(self, prompt: str, max_tokens: int) -> str:
        """Generate using OpenRouter (OpenAI-compatible)"""
        try:
            import openai
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.3,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error with OpenRouter: {e}")
            return ""

    def _generate_ollama(self, prompt: str, max_tokens: int) -> str:
        """Generate using Ollama (local models)"""
        try:
            import requests
            response = requests.post(
                f"{self.client}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": 0.3
                    }
                }
            )
            if response.status_code == 200:
                return response.json()['response']
            else:
                print(f"Ollama error: {response.status_code}")
                return ""
        except Exception as e:
            print(f"Error with Ollama: {e}")
            return ""

    def _generate_groq(self, prompt: str, max_tokens: int) -> str:
        """Generate using Groq API"""
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                max_tokens=max_tokens,
                temperature=0.3,
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            print(f"Error with Groq: {e}")
            return ""

    def get_provider_info(self) -> str:
        """Get current provider information"""
        return f"""
╔════════════════════════════════════════════════╗
║           AI PROVIDER CONFIGURATION             ║
╠════════════════════════════════════════════════╣
║ Current Provider: {self.provider.upper():<34}║
║ Model: {self.model:<42}║
╠════════════════════════════════════════════════╣
║           AVAILABLE PROVIDERS                  ║
╚════════════════════════════════════════════════╝

1. ANTHROPIC (Default)
   - Model: claude-haiku-4-5-20251001
   - Cost: ~$0.80/$4 per 1M tokens
   - Setup: ANTHROPIC_API_KEY

2. OPENROUTER (Recommended - Cheapest)
   - Models: Claude, GPT, LLaMA, Mistral, Qwen, etc.
   - Cost: $0.15-2 per 1M tokens (varies by model)
   - Setup: OPENROUTER_API_KEY
   - Website: https://openrouter.ai/

3. OLLAMA (Local - Free)
   - Models: LLaMA, Mistral, Neurberus (run locally)
   - Cost: $0 (runs on your machine)
   - Setup: Install Ollama, run 'ollama serve'
   - Website: https://ollama.ai/

4. TOGETHER.AI
   - Models: Open source models (LLaMA, Mistral, etc.)
   - Cost: ~$0.90 per 1M tokens
   - Setup: TOGETHER_API_KEY
   - Website: https://together.ai/

5. GROQ (Fast)
   - Models: Mixtral, LLaMA
   - Cost: Free tier available
   - Setup: GROQ_API_KEY
   - Website: https://console.groq.com/

═════════════════════════════════════════════════

CONFIGURATION (.env file):

# Option 1: Use Anthropic (Default)
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Option 2: Use OpenRouter (Cheapest)
AI_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-xxxxx
OPENROUTER_MODEL=anthropic/claude-3-haiku

# Option 3: Use Ollama (Local, Free)
AI_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Option 4: Use Groq (Fast)
AI_PROVIDER=groq
GROQ_API_KEY=xxxxx
GROQ_MODEL=mixtral-8x7b-32768
"""

# Initialize globally
ai_provider = AIProviderManager()
