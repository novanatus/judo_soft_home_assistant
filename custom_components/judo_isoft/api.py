import aiohttp
import asyncio
import logging
import async_timeout
from datetime import datetime, timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

class JudoAPI:
    def __init__(self, ip, username, password):
        """Initialisiert die Verbindung zur Judo API."""
        self.base_url = f"http://{ip}/api/rest"
        self.auth = aiohttp.BasicAuth(username, password)
        self.session = aiohttp.ClientSession(auth=self.auth)  # Wiederverwendbare Session

    async def close(self):
        """Schließt die Session der API-Verbindung."""
        await self.session.close()

    async def _request(self, method, endpoint, payload=None):
        """Hilfsmethode für API-Requests."""
        url = f"{self.base_url}/{endpoint}"
        _LOGGER.info(f"Judo API: {method} Anfrage an {url} mit Payload {payload}")

        try:
            async with async_timeout.timeout(10):  # Timeout setzen
                async with self.session.request(method, url, json=payload) as response:
                    if response.status != 200:
                        _LOGGER.error(f"API-Fehler: {response.status} - {await response.text()}")
                        return None
                    return await response.json()
        except asyncio.TimeoutError:
            _LOGGER.error("API-Anfrage hat das Timeout überschritten!")
        except Exception as e:
            _LOGGER.error(f"Fehler beim API-Request: {e}")
        return None

    async def get_data(self, endpoint):
        """Daten von der API abrufen."""
        data = await self._request("GET", endpoint)
        return data.get("data") if data else None

    async def get_wasserhaerte(self):
        """Ruft die Wasserhärte ab."""
        data = await self.get_data("5100")
        if data:
            try:
                return int(data[:2], 16)  # Hex-Wert umwandeln
            except ValueError:
                _LOGGER.error(f"Fehler beim Umwandeln der Wasserhärte-Daten: {data}")
        return None

    async def get_salzstand(self):
        """Ruft den Salzstand ab."""
        data = await self.get_data("5600")
        if data:
            try:
                return int(data[:4], 16)  # Hex-Wert umwandeln
            except ValueError:
                _LOGGER.error(f"Fehler beim Umwandeln der Salzstand-Daten: {data}")
        return None

    async def get_gesamtwassermenge(self):
        """Ruft die Gesamtwassermenge ab (in m³)."""
        data = await self.get_data("2800")
        if data:
            total_liters = int(data[:2], 16) + (int(data[2:4], 16) << 8) + (int(data[4:6], 16) << 16) + (int(data[6:8], 16) << 24)
            return total_liters / 1000  # Umrechnung von Litern in m³
        return None

    async def get_weichwassermenge(self):
        """Ruft die Weichwassermenge ab (in m³)."""
        data = await self.get_data("6100")
        if data:
            total_liters = int(data[:2], 16) + (int(data[2:4], 16) << 8) + (int(data[4:6], 16) << 16) + (int(data[6:8], 16) << 24)
            return total_liters / 1000  # Umrechnung von Litern in m³
        return None

    async def get_betriebsstunden(self):
        """Ruft die Betriebsstunden des Geräts ab."""
        data = await self.get_data("7000")
        if data:
            try:
                hours = int(data[:2], 16)
                minutes = int(data[2:4], 16)
                return {"hours": hours, "minutes": minutes}
            except ValueError:
                _LOGGER.error(f"Fehler beim Umwandeln der Betriebsstunden-Daten: {data}")
        return None

    async def get_tagesstatistik(self):
        """Ruft die Tagesstatistik ab (in hex-codierten Werten)."""
        return await self.get_data("7200")

    async def get_wochenstatistik(self):
        """Ruft die Wochenstatistik ab (in hex-codierten Werten)."""
        return await self.get_data("7300")

    async def get_monatsstatistik(self):
        """Ruft die Monatsstatistik ab (in hex-codierten Werten)."""
        return await self.get_data("7400")

    async def get_jahresstatistik(self):
        """Ruft die Jahresstatistik ab (in hex-codierten Werten)."""
        return await self.get_data("7500")

class JudoDataUpdateCoordinator(DataUpdateCoordinator):
    """Koordiniert API-Anfragen für Judo Wasserenthärter."""

    def __init__(self, hass, api: JudoAPI):
        """Initialisierung mit Home Assistant Instanz."""
        self.api = api
        super().__init__(
            hass,
            _LOGGER,
            name="Judo API",
            update_interval=timedelta(seconds=30),  # Alle 30 Sekunden abrufen
        )

    async def _async_update_data(self):
        """Holt die neuesten Daten von der API."""
        try:
            return {
                "wasserhaerte": await self.api.get_wasserhaerte(),
                "salzstand": await self.api.get_salzstand(),
                "gesamtwassermenge": await self.api.get_gesamtwassermenge(),
                "weichwassermenge": await self.api.get_weichwassermenge(),
                "betriebsstunden": await self.api.get_betriebsstunden(),
                "tagesstatistik": await self.api.get_tagesstatistik(),
                "wochenstatistik": await self.api.get_wochenstatistik(),
                "monatsstatistik": await self.api.get_monatsstatistik(),
                "jahresstatistik": await self.api.get_jahresstatistik(),
            }
        except Exception as err:
            raise UpdateFailed(f"Fehler beim Abrufen der Judo-Daten: {err}")
