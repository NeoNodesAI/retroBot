"""Structured logging configuration."""
import logging
import sys
from config.settings import settings


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for terminal output."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    def format(self, record):
        # Add color to level name
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{self.BOLD}{record.levelname}{self.RESET}"
        
        # Format timestamp
        record.asctime = self.formatTime(record, '%H:%M:%S')
        
        # Custom format with emojis
        if 'Fetching' in record.msg or 'crypto' in record.msg.lower():
            emoji = '💰'
        elif 'Router' in record.msg:
            emoji = '🔀'
        elif 'response' in record.msg.lower():
            emoji = '✅'
        elif 'API' in record.msg or 'Starting' in record.msg:
            emoji = '🚀'
        elif 'error' in record.msg.lower() or 'Error' in record.msg:
            emoji = '❌'
        elif 'Getting model' in record.msg:
            emoji = '🤖'
        elif 'compiled' in record.msg.lower():
            emoji = '⚙️'
        else:
            emoji = '📝'
        
        record.emoji = emoji
        
        return super().format(record)


# Create custom formatter
formatter = ColoredFormatter(
    '%(emoji)s  [%(asctime)s] %(levelname)s - %(message)s'
)

# Configure handler
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    handlers=[handler]
)

logger = logging.getLogger(settings.agent_name)

# Startup banner
def print_startup_banner():
    """Print ASCII art banner on startup."""
    banner = f"""
{ColoredFormatter.COLORS['INFO']}{ColoredFormatter.BOLD}
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║    ██████╗ ███████╗████████╗██████╗  ██████╗ ██████╗    ║
║    ██╔══██╗██╔════╝╚══██╔══╝██╔══██╗██╔═══██╗██╔══██╗   ║
║    ██████╔╝█████╗     ██║   ██████╔╝██║   ██║██████╔╝   ║
║    ██╔══██╗██╔══╝     ██║   ██╔══██╗██║   ██║██╔══██╗   ║
║    ██║  ██║███████╗   ██║   ██║  ██║╚██████╔╝██████╔╝   ║
║    ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═════╝    ║
║                                                          ║
║           🤖 AI Agent with Real-Time Crypto Data         ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
{ColoredFormatter.RESET}

🚀 retroBot v{settings.agent_version}
🧠 Model: {settings.default_model}
⚡ Provider: {settings.llm_provider.upper()}
🌐 Server: http://0.0.0.0:8000
🔗 Web UI: http://0.0.0.0:8000/ui
📊 Health: http://0.0.0.0:8000/health

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    print(banner)

