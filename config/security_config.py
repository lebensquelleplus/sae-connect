import os
from pathlib import Path

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
