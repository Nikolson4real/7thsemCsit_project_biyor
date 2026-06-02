"""
List all available Gemini models from Google AI Studio.
Run this to find the correct model names for your API key.
"""

import google.generativeai as genai
from dotenv import load_dotenv
import os

# Load API key
load_dotenv()
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

print("=" * 80)
print("Available Gemini Models")
print("=" * 80)

try:
    models = genai.list_models()
    
    # Filter for generative models
    generative_models = [
        m for m in models 
        if 'generateContent' in m.supported_generation_methods
    ]
    
    if not generative_models:
        print("No generative models found!")
        print("   Check if your API key is valid and has access to Gemini models.")
    else:
        print(f"\nFound {len(generative_models)} generative models:\n")
        
        for i, model in enumerate(generative_models, 1):
            print(f"{i}. Model Name: {model.name}")
            print(f"   Display Name: {model.display_name}")
            print(f"   Description: {model.description[:100]}...")
            print(f"   Supported Methods: {', '.join(model.supported_generation_methods)}")
            print()
        
        print("=" * 80)
        print("Use the 'Model Name' values in your .env file")
        print("=" * 80)
        
        # Suggest best models
        print("\nRecommended Configuration:\n")
        
        # Find latest flash models
        flash_models = [m for m in generative_models if 'flash' in m.name.lower()]
        pro_models = [m for m in generative_models if 'pro' in m.name.lower()]
        
        if flash_models:
            print(f"Primary (Fast): {flash_models[0].name}")
        if len(flash_models) > 1:
            print(f"Fallback (Faster): {flash_models[1].name}")
        elif pro_models:
            print(f"Fallback (Quality): {pro_models[0].name}")

except Exception as e:
    print(f"Error: {str(e)}")
    print("\nTroubleshooting:")
    print("1. Check if GOOGLE_API_KEY is set in .env file")
    print("2. Verify your API key is valid at: https://aistudio.google.com/app/apikey")
    print("3. Ensure you have access to Gemini models")
