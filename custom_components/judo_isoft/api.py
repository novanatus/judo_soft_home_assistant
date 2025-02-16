import aiohttp
import asyncio
import logging
from datetime import datetime

_LOGGER = logging.getLogger(__name__)

class JudoAPI:
    def __init__(self, ip, username, password):
        self.base_url = f"http://{ip}/api/rest"
        self.auth = aiohttp.BasicAuth(username, password)

    async def get_data(self, endpoint):
        """Asynchroner API-Request mit aiohttp."""
        url = f"{self.base_url}/{endpoint}"
        _LOGGER.info(f"Judo API: Sende Anfrage an {url}")

        async with aiohttp.ClientSession(auth=self.auth) as session:
            try:
                async with session.get(url) as response:
                    if response.status != 200:
                        _LOGGER.error(f"API-Fehler: {response.status} - {await response.text()}")
                        return None
                    data = await response.json()
                    return data.get("data")
            except Exception as e:
                _LOGGER.error(f"Fehler beim API-Request: {e}")
                return None

    async def set_data(self, endpoint, value):
        """Asynchrones API-Update mit aiohttp."""
        url = f"{self.base_url}/{endpoint}"
        payload = {"data": value}
        _LOGGER.info(f"Judo API: Sende POST an {url} mit Payload {payload}")

        async with aiohttp.ClientSession(auth=self.auth) as session:
            try:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        _LOGGER.error(f"API-Fehler: {response.status} - {await response.text()}")
                        return False
                    return True
            except Exception as e:
                _LOGGER.error(f"Fehler beim API-Update: {e}")
                return False

    # Neue Methoden für Statistiken mit dynamischen Endpunkten

    async def get_tagesstatistik(self):
        """Ruft die Tagesstatistik ab (vom aktuellen Tag)."""
        today = datetime.now()  # Aktuelles Datum und Uhrzeit
        day = today.day  # Extrahiert den Tag
        month = today.month  # Extrahiert den Monat
        year = today.year  # Extrahiert das Jahr

        # Wandelt das Datum in Hex um:
        day_hex = f"{day:02X}"  # Umwandlung des Tages in Hex
        month_hex = f"{month:02X}"  # Umwandlung des Monats in Hex
        year_hex = f"{year:04X}"  # Umwandlung des Jahres in Hex

        # Erstelle den Endpunkt mit dem Format FB00<DayHex><MonthHex><YearHex>
        endpoint = f"FB00{day_hex}{month_hex}{year_hex}"

        # API-Anfrage an den Endpunkt
        data = await self.get_data(endpoint)
        
        if data:
            # Umwandeln des Hex-Strings in Liter
            total_liters = 0
            for i in range(0, len(data), 8):  # Jede Zeitperiode hat 8 Hex-Zeichen (4 Bytes)
                hex_value = data[i:i+8]
                value = int(hex_value, 16)  # Umwandeln von Hex nach Dezimal
                total_liters += value  # Addiere den Wert zur Gesamtmenge

            _LOGGER.info(f"Gesamtwasserverbrauch für den Tag: {total_liters} Liter")
            return total_liters
        else:
            return None

    async def get_wochenstatistik(self):
        """Ruft die Wochenstatistik ab (von der aktuellen Kalenderwoche)."""
        week = datetime.now().isocalendar()[1]  # Ermittelt die aktuelle Kalenderwoche
        year = datetime.now().year  # Ermittelt das aktuelle Jahr
        endpoint = f"FC{year}{week:02d}"  # Beispiel: FC202503 für die 3. Woche 2025
        data = await self.get_data(endpoint)
        return data if data else None

    async def get_monatsstatistik(self):
        """Ruft die Monatsstatistik ab (vom aktuellen Monat)."""
        month = datetime.now().month  # Ermittelt den aktuellen Monat
        year = datetime.now().year  # Ermittelt das aktuelle Jahr
        month_hex = f"{month:02X}"  # Umwandlung des Monats in Hex
        year_hex = f"{year:04X}"  # Umwandlung des Jahres in Hex

        # Erstelle den Endpunkt für den aktuellen Monat im Format FD<YearHex><MonthHex>
        endpoint = f"FD{year_hex}{month_hex}"

        # API-Anfrage an den Endpunkt
        data = await self.get_data(endpoint)
        return data if data else None

    async def get_jahresstatistik(self):
        """Ruft die Jahresstatistik ab (vom aktuellen Jahr)."""
        year = datetime.now().year  # Ermittelt das aktuelle Jahr
        year_hex = f"{year:04X}"  # Umwandlung des Jahres in Hex

        # Erstelle den Endpunkt für das aktuelle Jahr im Format FE<YearHex>
        endpoint = f"FE{year_hex}"

        # API-Anfrage an den Endpunkt
        data = await self.get_data(endpoint)
        return data if data else None

    # Betriebsdaten

    async def get_betriebsstunden(self):
        """Ruft die Betriebsstunden des Geräts ab."""
        data = await self.get_data("2500")  # Endpunkt für Betriebsstunden
        if data:
            minutes = int(data[:2], 16)
            hours = int(data[2:4], 16)
            days = int(data[4:6], 16)
            return {"minutes": minutes, "hours": hours, "days": days}
        return None

    async def get_gesamtwassermenge(self):
        """Ruft die Gesamtwassermenge ab (in m³)."""
        data = await self.get_data("2800")  # Endpunkt für Gesamtwassermenge
        if data:
            # LSB first: Wir extrahieren die Bytes und setzen sie zusammen
            total_liters = int(data[:2], 16) + (int(data[2:4], 16) << 8) + (int(data[4:6], 16) << 16) + (int(data[6:8], 16) << 24)
            return total_liters / 1000  # Umrechnung von Litern in m³
        return None

    async def get_weichwassermenge(self):
        """Ruft die Weichwassermenge ab (in m³)."""
        data = await self.get_data("2900")  # Endpunkt für Weichwassermenge
        if data:
            # LSB first: Wir extrahieren die Bytes und setzen sie zusammen
            soft_water_liters = int(data[:2], 16) + (int(data[2:4], 16) << 8) + (int(data[4:6], 16) << 16) + (int(data[6:8], 16) << 24)
            return soft_water_liters / 1000  # Umrechnung von Litern in m³
        return None

    async def get_wasserhaerte(self):
        """Ruft die Wasserhärte ab."""
        data = await self.get_data("5100")
        if data:
            try:
                # Falls die Antwort als Hex vorliegt, wird sie umgewandelt
                return int(data[:2], 16)  # Konvertierung des ersten Teils von Hex in Integer
            except ValueError:
                _LOGGER.error(f"Fehler beim Umwandeln der Wasserhärte-Daten: {data}")
                return None
        else:
            _LOGGER.error("Keine Daten für Wasserhärte erhalten.")
            return None

    async def get_salzstand(self):
        """Ruft den Salzstand ab."""
        data = await self.get_data("5600")
        if data:
            try:
                # Falls die Antwort als Hex vorliegt, wird sie umgewandelt
                return int(data[:4], 16)  # Konvertierung der ersten 4 Zeichen von Hex in Integer
            except ValueError:
                _LOGGER.error(f"Fehler beim Umwandeln der Salzstand-Daten: {data}")
                return None
        else:
            _LOGGER.error("Keine Daten für Salzstand erhalten.")
            return None
