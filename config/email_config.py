"""
import os
from pathlib import Path

class EmailConfig:
    #E-Mail Analyse Konfiguration

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
"""

import imaplib
import email
import re
from typing import List, Dict, Optional, Tuple
import json
from datetime import datetime

class EmailVariableFilter:
    def __init__(self):
        # Konfiguration
        self.ABSENDER_MAILS = ['donotreply@amazon.com', 'ebay@ebay.com']
        
        self.BETREFF_FILTER = [
            'Kunde möchte Bestellung {{ Bestellnummer }} stornieren.',
            'Ein Käufer möchte einen Kauf abbrechen'
        ]
        
        self.INHALT_FILTER = [
            'Kunde möchte Bestellung {{ Bestellnummer }}  stornieren.',
            'Käufer: {{ Käufer }}'
        ]
        
        # Speicher für extrahierte Variablen
        self.extracted_data = []
    
    def create_regex_pattern(self, template: str) -> Tuple[str, List[str]]:
        """
        Konvertiert Template mit {{ Variable }} zu Regex-Pattern
        Gibt Pattern und Liste der Variablennamen zurück
        """
        # Finde alle Variablen im Template
        variables = re.findall(r'\{\{\s*(\w+)\s*\}\}', template)
        
        # Ersetze Variablen durch Regex-Gruppen
        pattern = template
        for var in variables:
            # Ersetze {{ Variable }} durch benannte Regex-Gruppe
            pattern = re.sub(
                r'\{\{\s*' + re.escape(var) + r'\s*\}\}',
                rf'(?P<{var}>\S+)',  # \S+ für Nicht-Leerzeichen (Bestellnummern, etc.)
                pattern
            )
        
        # Escape andere Regex-Zeichen im Template
        pattern = re.escape(pattern)
        
        # Ersetze die escaped Gruppen zurück zu echten Regex-Gruppen
        for var in variables:
            escaped_group = re.escape(f'(?P<{var}>\S+)')
            pattern = pattern.replace(escaped_group, rf'(?P<{var}>\S+)')
        
        return pattern, variables
    
    def extract_variables_from_text(self, text: str, templates: List[str]) -> List[Dict]:
        """
        Extrahiert Variablen aus Text basierend auf Templates
        """
        results = []
        
        for template in templates:
            pattern, variables = self.create_regex_pattern(template)
            
            # Suche im Text
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                extracted = {
                    'template': template,
                    'matched_text': match.group(0),
                    'variables': {}
                }
                
                # Extrahiere alle gefundenen Variablen
                for var in variables:
                    try:
                        extracted['variables'][var] = match.group(var)
                    except IndexError:
                        extracted['variables'][var] = None
                
                results.append(extracted)
        
        return results
    
    def check_sender_match(self, sender: str) -> bool:
        """Prüft ob Absender in der Liste ist"""
        return any(allowed_sender.lower() in sender.lower() 
                  for allowed_sender in self.ABSENDER_MAILS)
    
    def get_email_content(self, email_message) -> Tuple[str, str]:
        """Extrahiert Subject und Body aus E-Mail"""
        subject = email_message.get('Subject', '')
        
        # Body extrahieren
        body = ""
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    try:
                        body += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    except:
                        body += str(part.get_payload())
        else:
            try:
                body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
            except:
                body = str(email_message.get_payload())
        
        return subject, body
    
    def process_email(self, email_message) -> Optional[Dict]:
        """
        Verarbeitet eine einzelne E-Mail und extrahiert Variablen
        """
        sender = email_message.get('From', '')
        subject, body = self.get_email_content(email_message)
        
        # 1. Prüfe Absender
        if not self.check_sender_match(sender):
            return None
        
        # 2. Prüfe Betreff
        subject_matches = self.extract_variables_from_text(subject, self.BETREFF_FILTER)
        
        # 3. Prüfe Inhalt
        content_matches = self.extract_variables_from_text(body, self.INHALT_FILTER)
        
        # Wenn Matches gefunden wurden
        if subject_matches or content_matches:
            result = {
                'timestamp': datetime.now().isoformat(),
                'sender': sender,
                'subject': subject,
                'subject_matches': subject_matches,
                'content_matches': content_matches,
                'all_variables': {}
            }
            
            # Sammle alle extrahierten Variablen
            for match in subject_matches + content_matches:
                result['all_variables'].update(match['variables'])
            
            return result
        
        return None
    
    def filter_emails(self, mail, mailbox='INBOX') -> List[Dict]:
        """
        Filtert E-Mails basierend auf Konfiguration
        """
        mail.select(mailbox)
        
        # Suche E-Mails von erlaubten Absendern
        search_parts = []
        for sender in self.ABSENDER_MAILS:
            search_parts.append(f'FROM "{sender}"')
        
        search_criteria = f'({" OR ".join(search_parts)})'
        status, messages = mail.search(None, search_criteria)
        
        results = []
        
        if status == 'OK' and messages[0]:
            message_ids = messages[0].split()
            
            for msg_id in message_ids:
                try:
                    status, msg_data = mail.fetch(msg_id, '(RFC822)')
                    if status == 'OK':
                        email_message = email.message_from_bytes(msg_data[0][1])
                        
                        processed = self.process_email(email_message)
                        if processed:
                            processed['message_id'] = msg_id.decode()
                            results.append(processed)
                            
                except Exception as e:
                    print(f"Fehler beim Verarbeiten der E-Mail {msg_id}: {e}")
        
        self.extracted_data.extend(results)
        return results
    
    def save_extracted_data(self, filename: str = 'extracted_email_data.json'):
        """Speichert extrahierte Daten in JSON-Datei"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.extracted_data, f, ensure_ascii=False, indent=2)
    
    def get_bestellnummern(self) -> List[str]:
        """Gibt alle extrahierten Bestellnummern zurück"""
        bestellnummern = []
        for entry in self.extracted_data:
            if 'Bestellnummer' in entry['all_variables']:
                bestellnummer = entry['all_variables']['Bestellnummer']
                if bestellnummer and bestellnummer not in bestellnummern:
                    bestellnummern.append(bestellnummer)
        return bestellnummern
    
    def print_results(self):
        """Gibt Ergebnisse formatiert aus"""
        print(f"\n=== GEFILTERTE E-MAILS ({len(self.extracted_data)}) ===")
        
        for i, entry in enumerate(self.extracted_data, 1):
            print(f"\n--- E-Mail {i} ---")
            print(f"Absender: {entry['sender']}")
            print(f"Betreff: {entry['subject']}")
            print(f"Timestamp: {entry['timestamp']}")
            
            if entry['all_variables']:
                print("Extrahierte Variablen:")
                for var, value in entry['all_variables'].items():
                    print(f"  {var}: {value}")
        
        # Zusammenfassung der Bestellnummern
        bestellnummern = self.get_bestellnummern()
        if bestellnummern:
            print(f"\n=== ALLE BESTELLNUMMERN ({len(bestellnummern)}) ===")
            for nummer in bestellnummern:
                print(f"  - {nummer}")

# Beispiel für erweiterte Patterns
class AdvancedEmailFilter(EmailVariableFilter):
    def __init__(self):
        super().__init__()
        
        # Erweiterte Templates mit verschiedenen Variablentypen
        self.BETREFF_FILTER = [
            'Kunde möchte Bestellung {{ Bestellnummer }} stornieren.',
            'Rückgabe für Bestellung {{ Bestellnummer }}',
            'Bestellung {{ Bestellnummer }} - Status: {{ Status }}',
            'Ein Käufer möchte einen Kauf abbrechen'
        ]
        
        self.INHALT_FILTER = [
            'Kunde möchte Bestellung {{ Bestellnummer }} stornieren.',
            'Käufer: {{ Käufer }}',
            'Artikel: {{ Artikelname }} ({{ Bestellnummer }})',
            'Rückerstattung von {{ Betrag }} für {{ Bestellnummer }}'
        ]
    
    def create_regex_pattern(self, template: str) -> Tuple[str, List[str]]:
        """
        Erweiterte Pattern-Erstellung mit verschiedenen Variablentypen
        """
        variables = re.findall(r'\{\{\s*(\w+)\s*\}\}', template)
        pattern = template
        
        for var in variables:
            # Verschiedene Patterns je nach Variablenname
            if 'nummer' in var.lower() or 'id' in var.lower():
                # Bestellnummern: Buchstaben, Zahlen, Bindestriche
                regex_group = rf'(?P<{var}>[A-Za-z0-9\-]+)'
            elif 'betrag' in var.lower() or 'preis' in var.lower():
                # Geldbeträge: Zahlen mit Komma/Punkt und Währung
                regex_group = rf'(?P<{var}>[0-9]+[,.]?[0-9]*\s*[€$£]?)'
            elif 'datum' in var.lower():
                # Datumsangaben
                regex_group = rf'(?P<{var}>\d{{1,2}}\.\d{{1,2}}\.\d{{2,4}}|\d{{4}}-\d{{2}}-\d{{2}})'
            elif 'name' in var.lower() or 'käufer' in var.lower():
                # Namen: Buchstaben und Leerzeichen
                regex_group = rf'(?P<{var}>[A-Za-zÄÖÜäöüß\s]+)'
            else:
                # Standard: Alles außer Leerzeichen
                regex_group = rf'(?P<{var}>\S+)'
            
            pattern = re.sub(
                r'\{\{\s*' + re.escape(var) + r'\s*\}\}',
                regex_group,
                pattern
            )
        
        # Escape andere Regex-Zeichen
        pattern = re.escape(pattern)
        
        # Ersetze escaped Gruppen zurück
        for var in variables:
            if 'nummer' in var.lower() or 'id' in var.lower():
                regex_group = rf'(?P<{var}>[A-Za-z0-9\-]+)'
            elif 'betrag' in var.lower() or 'preis' in var.lower():
                regex_group = rf'(?P<{var}>[0-9]+[,.]?[0-9]*\s*[€$£]?)'
            elif 'datum' in var.lower():
                regex_group = rf'(?P<{var}>\d{{1,2}}\.\d{{1,2}}\.\d{{2,4}}|\d{{4}}-\d{{2}}-\d{{2}})'
            elif 'name' in var.lower() or 'käufer' in var.lower():
                regex_group = rf'(?P<{var}>[A-Za-zÄÖÜäöüß\s]+)'
            else:
                regex_group = rf'(?P<{var}>\S+)'
            
            escaped_group = re.escape(regex_group)
            pattern = pattern.replace(escaped_group, regex_group)
        
        return pattern, variables

# Verwendungsbeispiel
def main():
    # IMAP-Verbindung (Beispiel-Konfiguration)
    IMAP_SERVER = "imap.gmail.com"
    USERNAME = "ihre-email@gmail.com" 
    PASSWORD = "ihr-passwort"
    
    try:
        # Verbindung herstellen
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(USERNAME, PASSWORD)
        
        # Filter initialisieren
        email_filter = AdvancedEmailFilter()
        
        # E-Mails filtern
        results = email_filter.filter_emails(mail, 'INBOX')
        
        # Ergebnisse anzeigen
        email_filter.print_results()
        
        # Daten speichern
        email_filter.save_extracted_data('bestellungen_stornierungen.json')
        
        # Nur Bestellnummern ausgeben
        bestellnummern = email_filter.get_bestellnummern()
        print(f"\nGefundene Bestellnummern: {bestellnummern}")
        
        mail.close()
        mail.logout()
        
    except Exception as e:
        print(f"Fehler: {e}")

if __name__ == "__main__":
    main()