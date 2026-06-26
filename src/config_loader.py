"""
config_loader.py
Load configuration from settings.yaml and .env
"""
import os
import yaml
from pathlib import Path
from dotenv import load_dotenv


def load_settings(path: str = "config/settings.yaml") -> dict:
    """Load settings from YAML file"""
    config_path = Path(__file__).parent.parent / path
    if not config_path.exists():
        raise FileNotFoundError(f"❌ Settings file not found: {path}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_env(path: str = "config/.env"):
    """Load environment variables"""
    env_path = Path(__file__).parent.parent / path
    if env_path.exists():
        load_dotenv(env_path)
        return True
    return False


def get_env(key: str, default: str = None) -> str:
    """Get environment variable with fallback"""
    return os.getenv(key, default)


def validate_config():
    """Validate that all required config exists"""
    required_env = [
        "GROQ_API_KEY",
    ]
    
    missing = []
    for key in required_env:
        if not os.getenv(key):
            missing.append(key)
    
    if missing:
        print(f"⚠️ Missing environment variables: {', '.join(missing)}")
        print("   Add them to config/.env file")
        return False
    
    return True


# Load on import
load_env()
