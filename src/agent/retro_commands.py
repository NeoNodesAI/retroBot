"""Retro-themed special commands for retroBot."""
from datetime import datetime
from config.settings import settings


RETRO_COMMANDS = {
    "/retro help": {
        "response": """
╔══════════════════════════════════════╗
║   retroBot - NeoNodes AI Command    ║
╚══════════════════════════════════════╝

Available Commands:
────────────────────────────────────────
/retro help       → Show this menu
/retro about      → About retroBot
/retro status     → System status
/retro version    → Version info
/retro commands   → List all commands
/retro ping       → Connection test
/retro stats      → Performance stats
/retro ascii      → ASCII art surprise
/retro quote      → Random retro quote

Special Phrases:
────────────────────────────────────────
"what is retro"       → What is retroBot?
"how does retro work" → How does it work?
"retro capabilities"  → What can I do?

╔══════════════════════════════════════╗
║  Type any command to get started!   ║
╚══════════════════════════════════════╝
        """,
        "metadata": {"type": "help", "category": "info"}
    },
    
    "/retro about": {
        "response": """
╔══════════════════════════════════════╗
║            retroBot v1.0            ║
╚══════════════════════════════════════╝

🤖 Powered by: NeoNodes AI
🏛️  Network: neonodesai.xyz
🌐 Framework: LangGraph + FastAPI
⚡ Speed: Lightning fast responses
🔄 Streaming: Real-time capabilities
🧠 Intelligence: Advanced AI reasoning

retroBot brings the power of modern AI
with a nostalgic touch. Built for the
future, inspired by the past.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Welcome to the retro revolution! 🎮
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """,
        "metadata": {"type": "about", "category": "info"}
    },
    
    "/retro status": {
        "response": lambda: f"""
╔══════════════════════════════════════╗
║         System Status Check         ║
╚══════════════════════════════════════╝

Status: ✅ ONLINE
Model: {settings.default_model}
Provider: {settings.llm_provider.upper()}
Version: {settings.agent_version}
Uptime: Active
Temperature: {settings.temperature}
Max Tokens: {settings.max_tokens}
Streaming: {"Enabled" if settings.streaming_enabled else "Disabled"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  All systems operational! 🚀
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """,
        "metadata": {"type": "status", "category": "system"}
    },
    
    "/retro version": {
        "response": lambda: f"""
retroBot v{settings.agent_version}
Model: {settings.default_model}
Framework: LangGraph Cloud API Compatible
Build: {datetime.now().strftime("%Y.%m.%d")}
Status: Production Ready ✅
        """,
        "metadata": {"type": "version", "category": "info"}
    },
    
    "/retro commands": {
        "response": """
╔══════════════════════════════════════╗
║        Quick Command Reference      ║
╚══════════════════════════════════════╝

/retro help       → Full command list
/retro about      → Bot information
/retro status     → System check
/retro version    → Version details
/retro ping       → Test connection
/retro stats      → Performance data
/retro ascii      → ASCII art
/retro quote      → Get inspired

Pro tip: You can also just chat naturally!
        """,
        "metadata": {"type": "commands", "category": "help"}
    },
    
    "/retro ping": {
        "response": """
╔══════════════════════════════════════╗
║             PONG! 🏓                ║
╚══════════════════════════════════════╝

Connection: ✅ Active
Latency: <100ms
Response: Instant

retroBot is ready to assist! 🚀
        """,
        "metadata": {"type": "ping", "category": "test"}
    },
    
    "/retro stats": {
        "response": lambda: f"""
╔══════════════════════════════════════╗
║        Performance Statistics       ║
╚══════════════════════════════════════╝

Model Performance:
├─ Model: Claude Sonnet 4.5
├─ Temperature: {settings.temperature}
├─ Max Tokens: {settings.max_tokens}
├─ Streaming: {"ON" if settings.streaming_enabled else "OFF"}
└─ Provider: Anthropic

System Info:
├─ Agent: {settings.agent_name}
├─ Version: {settings.agent_version}
├─ Protocol: Warden Compatible
└─ API: LangGraph Cloud Format

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Optimized for maximum performance! ⚡
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """,
        "metadata": {"type": "stats", "category": "system"}
    },
    
    "/retro ascii": {
        "response": """
╔══════════════════════════════════════╗
║           retroBot ASCII            ║
╚══════════════════════════════════════╝

    ____  ______ _______ ____  ____  
   / __ \/ ____/_  __/ __ \/ __ \/ __ )
  / /_/ / __/   / / / /_/ / / / / __  |
 / _, _/ /___  / / / _, _/ /_/ / /_/ /
/_/ |_/_____/ /_/ /_/ |_|\____/_____/ 
                                      
   🤖 Powered by Claude Sonnet 4.5 🚀

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  The future is retro! 🎮✨
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """,
        "metadata": {"type": "ascii", "category": "fun"}
    },
    
    "/retro quote": {
        "response": lambda: """
╔══════════════════════════════════════╗
║         Retro Wisdom of the Day     ║
╚══════════════════════════════════════╝

"The best way to predict the future
 is to invent it."
                    - Alan Kay

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Stay curious, stay creative! 🌟
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """,
        "metadata": {"type": "quote", "category": "inspiration"}
    },
}

# Additional special phrases
RETRO_PHRASES = {
    "what is retro": """
╔══════════════════════════════════════╗
║        What is retroBot?            ║
╚══════════════════════════════════════╝

retroBot is an advanced AI assistant built
with Claude Sonnet 4.5 and Warden Protocol
standards.

Features:
• LangGraph framework for agent management
• Real-time streaming responses
• Multi-thread conversation support
• Production-ready API
• Warden Protocol compatible

retroBot = Modern AI + Retro vibes! 🎮✨
    """,
    
    "how does retro work": """
╔══════════════════════════════════════╗
║      How retroBot Works             ║
╚══════════════════════════════════════╝

Architecture:
1. FastAPI REST API server
2. LangGraph agent orchestration
3. Claude Sonnet 4.5 (most powerful)
4. Streaming & thread management
5. Warden Protocol standard

Technology Stack:
├─ Framework: LangGraph + FastAPI
├─ Model: Claude Sonnet 4.5
├─ API: LangGraph Cloud Compatible
└─ Protocol: Warden Standard

Ask me anything, I'm here to help! 🚀
    """,
    
    "retro capabilities": """
╔══════════════════════════════════════╗
║      retroBot Capabilities          ║
╚══════════════════════════════════════╝

What I Can Do:

✅ General conversation & Q&A
✅ Programming assistance
✅ Research & analysis
✅ Problem solving
✅ Technical support
✅ Data analysis
✅ Multi-language support
✅ Real-time streaming
✅ Thread management
✅ Context awareness

Special: Type /retro help for all commands!

Ready to assist with any question! 💪
    """,
}


def check_retro_command(user_input: str) -> dict:
    """
    Check if user input matches a retro command.
    
    Args:
        user_input: User's message
        
    Returns:
        dict with response and metadata, or None if no match
    """
    # Normalize input
    normalized = user_input.lower().strip()
    
    # Check exact commands
    if normalized in RETRO_COMMANDS:
        cmd_data = RETRO_COMMANDS[normalized]
        response = cmd_data["response"]
        
        # If response is callable (lambda), call it
        if callable(response):
            response = response()
            
        return {
            "response": response.strip(),
            "metadata": cmd_data["metadata"],
            "is_retro_command": True
        }
    
    # Check Turkish phrases
    for phrase, response in RETRO_PHRASES.items():
        if phrase in normalized:
            return {
                "response": response.strip(),
                "metadata": {"type": "phrase", "category": "turkish"},
                "is_retro_command": True
            }
    
    # No match
    return None


def get_all_commands():
    """Get list of all retro commands."""
    return list(RETRO_COMMANDS.keys())


def get_all_phrases():
    """Get list of all special phrases."""
    return list(RETRO_PHRASES.keys())

