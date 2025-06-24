"""Configuration management for Video Services API."""

import os
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class Config:
    """Configuration settings for the Video Services API client."""
    
    # API Settings
    base_url: str = "http://localhost:8000"
    timeout: float = 60.0
    
    # Authentication
    username: Optional[str] = None
    password: Optional[str] = None
    
    # File paths
    default_output_dir: str = "."
    
    @property
    def auth(self) -> Optional[Tuple[str, str]]:
        """Return auth tuple if both username and password are set."""
        if self.username and self.password:
            return (self.username, self.password)
        return None
    
    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> "Config":
        """
        Load configuration from environment variables and optional .env file.
        
        Args:
            env_file: Path to .env file (defaults to .env in current directory)
        """
        # Load .env file if it exists
        if env_file is None:
            env_file = ".env"
        
        env_path = Path(env_file)
        if env_path.exists():
            load_dotenv(env_path)
        
        return cls(
            base_url=os.getenv("VIDEO_API_BASE_URL", "http://localhost:8000"),
            timeout=float(os.getenv("VIDEO_API_TIMEOUT", "60.0")),
            username=os.getenv("VIDEO_API_USERNAME"),
            password=os.getenv("VIDEO_API_PASSWORD"),
            default_output_dir=os.getenv("VIDEO_API_OUTPUT_DIR", "."),
        )


def load_dotenv(env_path: Path) -> None:
    """
    Simple .env file loader without external dependencies.
    
    Args:
        env_path: Path to the .env file
    """
    if not env_path.exists():
        return
    
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Parse KEY=VALUE format
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                # Set environment variable
                os.environ[key] = value