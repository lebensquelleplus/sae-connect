import os
from pathlib import Path

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
