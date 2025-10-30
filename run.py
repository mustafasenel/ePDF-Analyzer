"""
Run script for ePDF Analyzer API
"""

import uvicorn
from config.settings import settings

if __name__ == "__main__":
    print(f"🚀 Starting {settings.API_TITLE} v{settings.API_VERSION}")
    print(f"📍 Server will run at: http://{settings.API_HOST}:{settings.API_PORT}")
    print(f"📚 API docs at: http://{settings.API_HOST}:{settings.API_PORT}/docs")
    print(f"🔧 Debug mode: {settings.DEBUG}")
    print("\n")
    
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning"
    )

