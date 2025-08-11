import os
from pathlib import Path

class AppConfig:
    """Hauptkonfiguration der Anwendung"""

    # App Metadaten
    APP_NAME = "ARC"
    VERSION = "1.0.1"
    DESCRIPTION = "Anwendung für nahtlose Auftragsprozesse. Eine intelligente Erweiterung zum bestehenden System."

    # Gmail Konfiguration
    GMAIL_IMAP_SERVER = "imap.gmail.com"
    GMAIL_IMAP_PORT = 993

    # Sucheinstellungen
    DEFAULT_SEARCH_DAYS = 30
    MAX_SEARCH_DAYS = 365
    DEFAULT_MAX_EMAILS = 100
    MAX_EMAILS_LIMIT = 500

    # UI Konfiguration
    THEME_OPTIONS = ["light", "dark", "auto"]
    DEFAULT_THEME = "dark"

    # Pfade
    PROJECT_ROOT = Path(__file__).parent
    ASSETS_DIR = PROJECT_ROOT / "assets"
    DATA_DIR = PROJECT_ROOT / "data"

    # Performance
    EMAIL_BATCH_SIZE = 10
    PROGRESS_UPDATE_INTERVAL = 5