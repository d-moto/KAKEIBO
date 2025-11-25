import google.generativeai as genai
from database import Database
import os

def list_models():
    db = Database()
    api_key = db.get_setting("gemini_api_key")
    
    if not api_key:
        print("No API Key found in database.")
        return

    print(f"Using API Key: {api_key[:5]}...{api_key[-5:]}")
    genai.configure(api_key=api_key)

    print("Listing available models...")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
    except Exception as e:
        print(f"Error listing models: {e}")

if __name__ == "__main__":
    list_models()
