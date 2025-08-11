import os
from pathlib import Path

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

# Absender Mails
ABSENDER_MAILS = ['donotreply@amazon.com', 'ebay@ebay.com']

# Betreff Filter
BETREFF_FILTER = ['Kunde möchte Bestellung {{ Bestellnummer }} stornieren.', 'Ein Käufer möchte einen Kauf abbrechen']

# Inhalt Filter
INHALT_FILTER = ['Kunde möchte Bestellung {{ Bestellnummer }}  stornieren.', 'Käufer: {{ Käufer }}']
