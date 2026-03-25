"""Entry point for running the API server with python -m src.api."""
import uvicorn
from src.utils.logger import print_startup_banner

if __name__ == "__main__":
    # Print startup banner
    print_startup_banner()
    
    # Start server
    uvicorn.run(
        "src.api:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )

