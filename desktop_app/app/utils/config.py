"""
Configuration Manager

Manages application configuration stored in JSON file.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages application configuration"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager

        Args:
            config_path: Path to config file (default: AppData/RecoveryAssistant/config.json)
        """

        if not config_path:
            # Default to AppData
            appdata = Path.home() / "AppData" / "Roaming" / "RecoveryAssistant"
            appdata.mkdir(parents=True, exist_ok=True)
            config_path = str(appdata / "config.json")

        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""

        if not Path(self.config_path).exists():
            # Create default config
            default_config = self._get_default_config()
            self._save_config(default_config)
            return default_config

        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Configuration loaded from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return self._get_default_config()

    def _save_config(self, config: Dict[str, Any]):
        """Save configuration to file"""

        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=4)
            logger.info("Configuration saved")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""

        documents = Path.home() / "Documents" / "RecoveryAssistant"
        documents.mkdir(parents=True, exist_ok=True)

        return {
            "version": "1.0.0",
            "first_run": True,
            "database": {
                "path": str(documents / "receivables.db"),
                "backup_enabled": True,
                "backup_frequency_days": 7,
                "last_backup": None
            },
            "integrations": {
                "xero": {
                    "enabled": False,
                    "client_id": "",
                    "client_secret": "",
                    "connected": False,
                    "auto_sync": False,
                    "sync_interval_hours": 24
                },
                "quickbooks": {
                    "enabled": False,
                    "connected": False
                },
                "outlook": {
                    "enabled": True,
                    "test_connection_on_startup": True
                },
                "stripe": {
                    "enabled": False,
                    "api_key": "",
                    "webhook_secret": ""
                },
                "openai": {
                    "api_key": "",
                    "model": "gpt-4-turbo-preview",
                    "enabled": True
                }
            },
            "workflows": {
                "enabled": True,
                "auto_run_interval_minutes": 30,
                "schedules": {
                    "0-30": {
                        "reminder_frequency_days": 7,
                        "tone": "friendly"
                    },
                    "31-60": {
                        "reminder_frequency_days": 3,
                        "tone": "professional"
                    },
                    "61-90": {
                        "reminder_frequency_days": 1,
                        "tone": "firm"
                    },
                    "90+": {
                        "reminder_frequency_days": 1,
                        "tone": "urgent",
                        "auto_escalate": True
                    }
                },
                "payment_plan_threshold": 10000.0,
                "escalation_enabled": True
            },
            "communication": {
                "default_channel": "email",
                "rate_limit_per_hour": 50,
                "delay_between_emails_seconds": 5,
                "include_payment_link": True
            },
            "ui": {
                "theme": "light",
                "start_with_windows": False,
                "minimize_to_tray": True,
                "show_notifications": True
            },
            "logging": {
                "level": "INFO",
                "max_file_size_mb": 10,
                "backup_count": 5
            }
        }

    def is_configured(self) -> bool:
        """Check if application is configured"""

        return not self.config.get("first_run", True)

    def mark_configured(self):
        """Mark application as configured"""

        self.config["first_run"] = False
        self._save_config(self.config)

    def get(self, key_path: str, default=None) -> Any:
        """
        Get configuration value by key path

        Args:
            key_path: Dot-separated path (e.g., "integrations.xero.enabled")
            default: Default value if key not found

        Returns:
            Configuration value
        """

        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, key_path: str, value: Any):
        """
        Set configuration value by key path

        Args:
            key_path: Dot-separated path
            value: Value to set
        """

        keys = key_path.split('.')
        config = self.config

        # Navigate to parent
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        # Set value
        config[keys[-1]] = value

        # Save config
        self._save_config(self.config)

    def update_config(self, updates: Dict[str, Any]):
        """
        Update multiple configuration values

        Args:
            updates: Dict of configuration updates
        """

        def deep_update(base_dict, update_dict):
            for key, value in update_dict.items():
                if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
                    deep_update(base_dict[key], value)
                else:
                    base_dict[key] = value

        deep_update(self.config, updates)
        self._save_config(self.config)

    def get_database_path(self) -> str:
        """Get database file path"""

        return self.get("database.path")

    def get_openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key"""

        return self.get("integrations.openai.api_key")

    def get_stripe_api_key(self) -> Optional[str]:
        """Get Stripe API key"""

        return self.get("integrations.stripe.api_key")

    def get_xero_credentials(self) -> Dict[str, str]:
        """Get Xero credentials"""

        return {
            "client_id": self.get("integrations.xero.client_id", ""),
            "client_secret": self.get("integrations.xero.client_secret", "")
        }
