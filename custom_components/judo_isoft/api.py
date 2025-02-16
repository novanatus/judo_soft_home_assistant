import aiohttp
import asyncio
import logging
import async_timeout
from datetime import datetime, timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

class JudoAPI:
    def __init__(self, ip, username, password):
        self.base_url = f"http://{ip}/api/rest"
        self.auth = aiohttp.BasicAuth(username, password)
        self.session = aiohttp.ClientSession(auth=self.auth)  # Wiederverwendbare Session

    async def close(self):
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
        data = await self.get_data("2900")
        if data:
            total_liters = int(data[:2], 16) + (int(data[2:4], 16) << 8) + (int(data[4:6], 16) << 16) + (int(data[6:8], 16) << 24)
            return total_liters / 1000  # Umrechnung von Litern in m³
        return None

    async def get_tagesstatistik(self):
        """Ruft die Tagesstatistik für den aktuellen Tag ab."""
        # Aktuelles Datum ermitteln
        today = datetime.today()

        # Umwandeln des Datums in den Hex-Wert (z.B. 13.08.2023 => 000D0807E7)
        hex_date = self.date_to_hex(today)
        
        # Den API-Endpunkt mit dem Hex-Wert des aktuellen Datums erstellen
        endpoint = f"FB{hex_date}"
        
        # Daten abrufen
        data = await self.get_data(endpoint)
        return data if data else None

    def date_to_hex(self, date: datetime):
        """Konvertiert das heutige Datum in einen Hex-Wert im Format DDMMYY (z.B. 2023-08-13 -> 000D0807E7)."""
        # Umwandlung des aktuellen Datums in Hex-Werte
        hex_date = f"{date.day:04X}{date.month:02X}{date.year % 100:02X}"
        return hex_date

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
                "weichwassermenge": await self.api.get_weichwassermenge(),  # Weichwassermenge hinzufügen
                "tagesstatistik": await self.api.get_tagesstatistik(),  # Tagesstatistik für den aktuellen Tag hinzufügen
            }
        except Exception as err:
            raise UpdateFailed(f"Fehler beim Abrufen der Judo-Daten: {err}")
