"""Direct test of Groq API to debug the issue."""
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
print(f"API Key loaded: {api_key[:20]}..." if api_key else "No API key found")

if not api_key:
    print("ERROR: GROQ_API_KEY not found in .env")
    exit(1)

url = "https://api.groq.com/openai/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

payload = {
    "model": "llama-3.3-70b-versatile",
    "messages": [
        {
            "role": "user",
            "content": "Say 'working' if you can read this."
        }
    ],
    "temperature": 0.1,
    "max_tokens": 100
}

print("\nSending request to Groq API...")
print(f"URL: {url}")
print(f"Model: {payload['model']}")

try:
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        result = response.json()
        print("\n✓ SUCCESS!")
        print(f"Response: {json.dumps(result, indent=2)}")
        print(f"\nAI said: {result['choices'][0]['message']['content']}")
    else:
        print("\n✗ ERROR!")
        print(f"Response: {response.text}")
        
        # Try to parse error
        try:
            error_data = response.json()
            print(f"\nError details: {json.dumps(error_data, indent=2)}")
        except:
            pass
            
except requests.exceptions.RequestException as e:
    print(f"\n✗ Request failed: {e}")
except Exception as e:
    print(f"\n✗ Unexpected error: {e}")
