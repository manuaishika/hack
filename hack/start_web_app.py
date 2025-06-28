"""
start_web_app.py
startup script for the enhanced code analyzer web application
"""

import subprocess
import sys
import os
import time
import webbrowser
from pathlib import Path

def check_dependencies():
    """check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        print("✅ fastapi and uvicorn are available")
    except ImportError:
        print("❌ fastapi or uvicorn not found. installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn"])
    
    try:
        import enhanced_analyzer
        print("✅ enhanced analyzer module is available")
    except ImportError:
        print("❌ enhanced analyzer module not found")
        return False
    
    return True

def start_backend():
    """start the fastapi backend server"""
    print("🚀 starting fastapi backend server...")
    backend_dir = Path(__file__).parent / "backend"
    os.chdir(backend_dir)
    
    try:
        subprocess.Popen([
            sys.executable, "-m", "uvicorn", "main:app", 
            "--host", "0.0.0.0", "--port", "8000", "--reload"
        ])
        print("✅ backend server started on http://localhost:8000")
        return True
    except Exception as e:
        print(f"❌ failed to start backend: {e}")
        return False

def setup_frontend():
    """setup and start the react frontend"""
    frontend_dir = Path(__file__).parent / "frontend"
    
    if not frontend_dir.exists():
        print("❌ frontend directory not found")
        return False
    
    os.chdir(frontend_dir)
    
    # check if node_modules exists
    if not (frontend_dir / "node_modules").exists():
        print("📦 installing frontend dependencies...")
        try:
            subprocess.check_call(["npm", "install"])
            print("✅ frontend dependencies installed")
        except Exception as e:
            print(f"❌ failed to install frontend dependencies: {e}")
            return False
    
    print("🚀 starting react frontend...")
    try:
        subprocess.Popen(["npm", "start"])
        print("✅ frontend started on http://localhost:3000")
        return True
    except Exception as e:
        print(f"❌ failed to start frontend: {e}")
        return False

def main():
    """main startup function"""
    print("=" * 60)
    print("enhanced code analyzer web application")
    print("=" * 60)
    
    # check dependencies
    if not check_dependencies():
        print("❌ dependency check failed")
        return
    
    # start backend
    if not start_backend():
        print("❌ backend startup failed")
        return
    
    # wait a moment for backend to start
    time.sleep(2)
    
    # setup and start frontend
    if not setup_frontend():
        print("❌ frontend startup failed")
        return
    
    # wait a moment for frontend to start
    time.sleep(5)
    
    print("\n" + "=" * 60)
    print("🎉 web application is ready!")
    print("=" * 60)
    print("backend api: http://localhost:8000")
    print("frontend app: http://localhost:3000")
    print("api docs: http://localhost:8000/docs")
    print("\nopening frontend in browser...")
    
    # open frontend in browser
    try:
        webbrowser.open("http://localhost:3000")
    except:
        print("could not open browser automatically")
    
    print("\npress ctrl+c to stop the servers")
    
    try:
        # keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 shutting down servers...")
        print("✅ servers stopped")

if __name__ == "__main__":
    main() 