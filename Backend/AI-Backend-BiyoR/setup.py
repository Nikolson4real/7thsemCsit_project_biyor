"""
Quick start script for BiyoR AI Rules Engine
This script helps set up and test the backend.
"""

import sys
import subprocess
from pathlib import Path


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 9):
        print("[ERROR] Python 3.9+ required. Current version:", sys.version)
        return False
    print(f"[OK] Python version: {sys.version.split()[0]}")
    return True


def check_env_file():
    """Check if .env file exists."""
    env_file = Path(".env")
    if not env_file.exists():
        print("[ERROR] .env file not found!")
        print("   Please copy .env.example to .env and add your Google API key:")
        print("   cp .env.example .env")
        return False
    print("[OK] .env file found")
    return True


def check_directories():
    """Check and create necessary directories."""
    dirs = [
        Path("data/rulebooks"),
        Path("data/faiss_index"),
        Path("logs")
    ]
    
    for directory in dirs:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"[OK] Created directory: {directory}")
        else:
            print(f"[OK] Directory exists: {directory}")
    
    return True


def check_rulebooks():
    """Check if rulebooks exist."""
    rulebooks_dir = Path("data/rulebooks")
    rulebooks = list(rulebooks_dir.glob("**/*"))
    rulebooks = [r for r in rulebooks if r.is_file()]
    
    if not rulebooks:
        print("[WARNING] No rulebooks found in data/rulebooks/")
        print("   A sample rulebook has been created: Official_Dandi_Biyo_Rulebook_2024.md")
        return False
    
    print(f"[OK] Found {len(rulebooks)} rulebook file(s):")
    for rb in rulebooks[:5]:  # Show first 5
        print(f"   - {rb.name}")
    
    return True


def install_dependencies():
    """Install Python dependencies."""
    print("Installing dependencies from requirements.txt...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True
        )
        print("[OK] Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("[ERROR] Failed to install dependencies")
        return False


def main():
    """Main setup function."""
    print_header("BiyoR AI Rules Engine - Quick Start")
    
    # Check prerequisites
    print_header("1. Checking Prerequisites")
    if not check_python_version():
        return
    
    if not check_env_file():
        return
    
    # Setup directories
    print_header("2. Setting Up Directories")
    check_directories()
    
    # Check rulebooks
    print_header("3. Checking Rulebooks")
    has_rulebooks = check_rulebooks()
    
    # Install dependencies
    print_header("4. Installing Dependencies")
    answer = input("Install/update dependencies? (y/n): ").strip().lower()
    if answer == 'y':
        install_dependencies()
    
    # Final instructions
    print_header("Setup Complete!")
    
    if has_rulebooks:
        print("[OK] All checks passed!")
    else:
        print("[WARNING] Setup complete, but you need to add more rulebooks to data/rulebooks/")
    
    print("\nNext steps:")
    print("1. Start the server:")
    print("   uvicorn app.main:app --reload")
    print("\n2. Build the FAISS index (in another terminal):")
    print("   python -c \"import requests; print(requests.post('http://localhost:8000/api/v1/rules/reindex', json={'force_rebuild': True}).json())\"")
    print("\n3. View API docs:")
    print("   http://localhost:8000/api/v1/docs")
    print("\n4. Test a query:")
    print("   See README.md for example API calls")
    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
