"""Test if Claude API is working"""
import os
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

api_key = os.getenv('ANTHROPIC_API_KEY')

print("=" * 60)
print("Testing Claude API")
print("=" * 60)

if not api_key:
    print("[ERROR] No API key found in .env")
    print("Please add: ANTHROPIC_API_KEY=sk-ant-xxxxx to .env")
    exit()

print(f"[OK] API key found: {api_key[:20]}...")

try:
    client = Anthropic(api_key=api_key)
    print("[OK] Anthropic client created")

    # Test simple message
    print("\nSending test message to Claude...")
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=100,
        messages=[
            {"role": "user", "content": "Say 'Hello! Claude is working!' in exactly those words."}
        ]
    )

    response_text = message.content[0].text
    print(f"[OK] Claude response: {response_text}")

    if "Hello! Claude is working!" in response_text:
        print("\n[OK][OK][OK] SUCCESS! Claude API is working correctly!")
    else:
        print(f"\n[WARN] Claude responded but with unexpected text: {response_text}")

except Exception as e:
    print(f"[ERROR] Error: {e}")
    print("\nThis error tells us what's wrong with the API call.")
    print("Share this error message with me!")

print("=" * 60)
