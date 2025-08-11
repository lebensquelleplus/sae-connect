import os
from pathlib import Path

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
