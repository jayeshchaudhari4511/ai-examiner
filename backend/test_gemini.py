import google.generativeai as genai
from config import Config
import time

print("Testing Gemini API...")
print(f"API Key configured: {'Yes' if Config.GEMINI_API_KEY else 'No'}")
if Config.GEMINI_API_KEY:
    print(f"API Key (first 10 chars): {Config.GEMINI_API_KEY[:10]}...")

if not Config.GEMINI_API_KEY:
    print("ERROR: No API key configured!")
    exit(1)

# Configure Gemini
genai.configure(api_key=Config.GEMINI_API_KEY)

# Test simple text generation with timeout
print("\n=== Testing Gemini 1.5 Flash ===")
try:
    print("Creating model...")
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    print("Generating content (with 30 second timeout)...")
    start_time = time.time()
    
    response = model.generate_content(
        "Say 'Hello! I am working.' in one sentence.",
        request_options={'timeout': 30}
    )
    
    elapsed = time.time() - start_time
    print(f"✓ SUCCESS in {elapsed:.2f} seconds")
    print(f"Response: {response.text}")
    
except Exception as e:
    print(f"✗ FAILED: {str(e)}")
    print(f"\nFull error: {repr(e)}")

print("\n=== Test Complete ===")

