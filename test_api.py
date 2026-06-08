"""Quick test to debug API calls"""
import os
from dotenv import load_dotenv

load_dotenv()

# Test 1: Check API key
print("=" * 60)
print("TEST 1: API Key Check")
print("=" * 60)
api_key = os.getenv('ANTHROPIC_API_KEY')
if api_key:
    print(f"[OK] API key found: {api_key[:20]}...")
else:
    print("[ERROR] No API key in .env")

# Test 2: Check internet to PubMed
print("\n" + "=" * 60)
print("TEST 2: PubMed Connection")
print("=" * 60)
try:
    import requests
    response = requests.get('https://pubmed.ncbi.nlm.nih.gov/', timeout=5)
    print(f"[OK] PubMed reachable: {response.status_code}")
except Exception as e:
    print(f"[ERROR] PubMed error: {e}")

# Test 3: Check internet to FDA
print("\n" + "=" * 60)
print("TEST 3: FDA API Connection")
print("=" * 60)
try:
    import requests
    response = requests.get('https://api.fda.gov/drug/label.json', timeout=5)
    print(f"[OK] FDA reachable: {response.status_code}")
except Exception as e:
    print(f"[ERROR] FDA error: {e}")

# Test 4: Check internet to Anthropic
print("\n" + "=" * 60)
print("TEST 4: Anthropic API Connection")
print("=" * 60)
try:
    from anthropic import Anthropic
    client = Anthropic(api_key=api_key)
    print("[OK] Anthropic client initialized")
except Exception as e:
    print(f"[ERROR] Anthropic error: {e}")

# Test 5: Try to fetch from PubMed
print("\n" + "=" * 60)
print("TEST 5: PubMed Search")
print("=" * 60)
try:
    import requests
    url = 'https://pubmed.ncbi.nlm.nih.gov/api/search/?term=Metformin&format=json'
    response = requests.get(url, timeout=10)
    if response.status_code == 200:
        data = response.json()
        print(f"[OK] Search successful")
        print(f"  Articles found: {data.get('count', 0)}")
    else:
        print(f"[ERROR] Search failed: {response.status_code}")
except Exception as e:
    print(f"[ERROR] Error: {e}")

print("\n" + "=" * 60)
print("All tests complete!")
print("=" * 60)
