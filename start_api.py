"""
HLAS Insurance API Startup Script

This script starts the FastAPI server for the HLAS Insurance Agent System.
"""

import uvicorn
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Start the API server"""
    print("🚀 Starting HLAS Insurance Agent API...")
    print("=" * 50)
    
    # Validate configuration
    try:
        from config import Config
        Config.validate()
        print("✅ Configuration validation passed")
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        print("Please check your .env file and ensure all required variables are set.")
        return
    
    print(f"📡 API will be available at: http://localhost:8000")
    print(f"📚 API Documentation: http://localhost:8000/docs")
    print(f"🔍 Alternative Docs: http://localhost:8000/redoc")
    print(f"❤️  Health Check: http://localhost:8000/health")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Start the server (disable reload to avoid WatchFiles issues)
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disabled to prevent file watcher issues
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()
