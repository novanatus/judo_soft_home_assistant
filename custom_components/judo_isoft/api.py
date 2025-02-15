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

    async def get_wasserhaerte(self):
        """Ruft die Wasserhärte ab."""
        data = await self.get_data("5100")
        return int(data[:2], 16) if data else None

    async def get_salzstand(self):
        """Ruft den Salzstand ab."""
        data = await self.get_data("5600")
        return int(data[:4], 16) if data else None

    async def start_regeneration(self):
        """Startet die Regeneration."""
        return await self.set_data("350000", "")

    async def set_wasserhaerte(self, haerte):
        """Setzt die gewünschte Wasserhärte."""
        hex_value = f"{haerte:02X}"
        return await self.set_data("3000", hex_value)

    async def set_leckageschutz(self, status):
        """Schließt oder öffnet den Leckageschutz."""
        return await self.set_data("3C00" if status else "3D00", "")

    async def set_urlaubsmodus(self, status):
        """Aktiviert oder deaktiviert den Urlaubsmodus."""
        return await self.set_data("4100", "01" if status else "00")

    # Neue Methoden für Statistiken mit dynamischen Endpunkten

    async def get_tagesstatistik(self):
        """Ruft die Tagesstatistik ab (vom aktuellen Tag)."""
        today = datetime.now().strftime("%d%m%Y")  # Format für das heutige Datum (TTMMYYYY)
        endpoint = f"FB{today}"  # Beispiel: FB04022025 für den 04.02.2025
        data = await self.get_data(endpoint)
        return data if data else None

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
        endpoint = f"FD{year}{month:02d}"  # Beispiel: FD202502 für Februar 2025
        data = await self.get_data(endpoint)
        return data if data else None

    async def get_jahresstatistik(self):
        """Ruft die Jahresstatistik ab (vom aktuellen Jahr)."""
        year = datetime.now().year  # Ermittelt das aktuelle Jahr
        endpoint = f"FE{year}"  # Beispiel: FE2025 für das Jahr 2025
        data = await self.get_data(endpoint)
        return data if data else None
