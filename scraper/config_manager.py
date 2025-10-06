import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any

class ConfigManager:
    def __init__(self, config_path: str = "config.json"):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        try:
            if not self.config_path.exists():
                self.logger.error(f"Config file not found: {self.config_path}")
                raise FileNotFoundError(f"Config file not found: {self.config_path}")
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self._validate_config(config)
            self.logger.info("Config loaded successfully")
            return config
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in config file: {e}", exc_info=True)
            raise
        except Exception as e:
            self.logger.error(f"Error loading config: {e}", exc_info=True)
            raise
    
    def _validate_config(self, config: Dict[str, Any]):
        try:
            required_fields = ['base_url', 'downloads_dir', 'timeout', 'pages_per_parse']
            
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"Missing required field: {field}")
            
            if not isinstance(config['base_url'], str):
                raise ValueError("base_url must be a string")
            
            if not isinstance(config['downloads_dir'], str):
                raise ValueError("downloads_dir must be a string")
            
            if not isinstance(config['timeout'], (int, float)) or config['timeout'] <= 0:
                raise ValueError("timeout must be a positive number")
            
            if not isinstance(config['pages_per_parse'], int) or config['pages_per_parse'] <= 0:
                raise ValueError("pages_per_parse must be a positive integer")
            
        except Exception as e:
            self.logger.error(f"Config validation failed: {e}", exc_info=True)
            raise
    
    def get_base_url(self) -> str:
        return self.config['base_url']
    
    def get_downloads_dir(self) -> str:
        return self.config['downloads_dir']
    
    def get_timeout(self) -> int:
        return int(self.config['timeout'])
    
    def get_pages_per_parse(self) -> int:
        return int(self.config['pages_per_parse'])
    
    def get_all(self) -> Dict[str, Any]:
        return self.config.copy()