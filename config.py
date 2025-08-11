"""
Konfigurationsdatei für Gmail Cancellation Tracker
"""

import os
from pathlib import Path

class AppConfig:
    """Hauptkonfiguration der Anwendung"""
    
    # App Metadaten
    APP_NAME = "Gmail Cancellation Tracker"
    VERSION = "2.0.0"
    DESCRIPTION = "Moderne Anwendung zum Durchsuchen von Gmail nach Stornierungsanfragen"
    
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

class UIConfig:
    """UI-spezifische Konfiguration"""
    
    # Farben für Dark Theme
    DARK_COLORS = {
        'primary': '#00f5ff',
        'secondary': '#1e293b',
        'success': '#10b981',
        'warning': '#f59e0b',
        'error': '#ef4444',
        'background': '#0f172a',
        'surface': '#1e293b',
        'text': '#f8fafc'
    }
    
    # Farben für Light Theme
    LIGHT_COLORS = {
        'primary': '#0ea5e9',
        'secondary': '#64748b',
        'success': '#059669',
        'warning': '#d97706',
        'error': '#dc2626',
        'background': '#ffffff',
        'surface': '#f8fafc',
        'text': '#1e293b'
    }
    
    # Icons
    ICONS = {
        'search': '🔍',
        'email': '📧',
        'success': '✅',
        'warning': '⚠️',
        'error': '❌',
        'info': 'ℹ️',
        'settings': '⚙️',
        'download': '📥',
        'upload': '📤',
        'refresh': '🔄',
        'delete': '🗑️',
        'edit': '✏️',
        'view': '👁️',
        'filter': '🔽',
        'sort': '↕️',
        'calendar': '📅',
        'chart': '📊',
        'user': '👤',
        'lock': '🔒',
        'unlock': '🔓'
    }
    
    # CSS Klassen
    CSS_CLASSES = {
        'card': 'custom-card',
        'metric': 'custom-metric',
        'button': 'custom-button',
        'input': 'custom-input',
        'table': 'custom-table'
    }

class EmailConfig:
    """E-Mail Analyse Konfiguration"""
    
    # Stornierungsschlüsselwörter (Deutsch)
    CANCELLATION_KEYWORDS_DE = [
        'stornierung', 'stornieren', 'storno',
        'rückgabe', 'zurückgeben', 'zurücksenden',
        'erstattung', 'rückerstattung',
        'bestellung stornieren', 'bestellung abbrechen',
        'rücktritt', 'widerruf', 'kündigung',
        'annullierung', 'rückabwicklung'
    ]
    
    # Stornierungsschlüsselwörter (Englisch)
    CANCELLATION_KEYWORDS_EN = [
        'cancel', 'cancellation', 'cancelled',
        'refund', 'return', 'returning',
        'order cancellation', 'cancel order',
        'withdrawal', 'revocation',
        'void', 'annul', 'nullify'
    ]
    
    # Amazon-spezifische Begriffe
    AMAZON_KEYWORDS = [
        'amazon', 'bestellung', 'order',
        'bestellnummer', 'order number',
        'artikel', 'product', 'item'
    ]
    
    # Prioritäts-Schlüsselwörter (höhere Gewichtung)
    HIGH_PRIORITY_KEYWORDS = [
        'dringend', 'urgent', 'sofort', 'immediately',
        'wichtig', 'important', 'asap'
    ]

class SecurityConfig:
    """Sicherheitseinstellungen"""
    
    # Session Timeout (Minuten)
    SESSION_TIMEOUT = 60
    
    # Maximale Login-Versuche
    MAX_LOGIN_ATTEMPTS = 3
    
    # Rate Limiting
    MAX_REQUESTS_PER_MINUTE = 30
    
    # Passwort Anforderungen
    MIN_PASSWORD_LENGTH = 16  # App-Passwort ist 16 Zeichen
    
    # Logging Level
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

class ExportConfig:
    """Export-Konfiguration"""
    
    # Unterstützte Formate
    SUPPORTED_FORMATS = ['csv', 'excel', 'json', 'pdf']
    
    # Standard-Dateiname Template
    FILENAME_TEMPLATE = "stornierungsanfragen_{timestamp}"
    
    # CSV Einstellungen
    CSV_SEPARATOR = ','
    CSV_ENCODING = 'utf-8-sig'  # BOM für Excel
    
    # Excel Einstellungen
    EXCEL_SHEET_NAME = 'Stornierungsanfragen'
    EXCEL_AUTO_FILTER = True