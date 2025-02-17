import aiohttp
import asyncio
import logging
import async_timeout
from datetime import datetime, timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from collections import deque

_LOGGER = logging.getLogger(__name__)

class JudoAPI:
    def __init__(self, ip, username, password):
        self.base_url = f"http://{ip}/api/rest"
        self.auth = aiohttp.BasicAuth(username, password)
        self.session = aiohttp.ClientSession(auth=self.auth)  # Wiederverwendbare Session

        # Cache für die API-Daten
        self._cache = {}

    async def close(self):
        await self.session.close()

    async def _request(self, method, endpoint, payload=None):
        """Hilfsmethode für API-Requests mit Cache-Implementierung."""
        url = f"{self.base_url}/{endpoint}"
        _LOGGER.info(f"Judo API: {method} Anfrage an {url} mit Payload {payload}")

        # Überprüfen, ob die Antwort bereits im Cache ist
        if endpoint in self._cache:
            _LOGGER.info(f"Verwende Cache für {url}")
            return self._cache[endpoint]

        try:
            async with async_timeout.timeout(10):  # Timeout setzen
                async with self.session.request(method, url, json=payload) as response:
                    if response.status != 200:
                        _LOGGER.error(f"API-Fehler: {response.status} - {await response.text()}")
                        return None
                    result = await response.json()

                    # Cache speichern
                    self._cache[endpoint] = result
                    return result
        except asyncio.TimeoutError:
            _LOGGER.error("API-Anfrage hat das Timeout überschritten!")
        except Exception as e:
            _LOGGER.error(f"Fehler beim API-Request: {e}")
        return None

    async def get_data(self, endpoint):
        """Daten von der API abrufen und im Cache speichern."""
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

    async def get_betriebsstunden(self):
        data = await self.get_data("2500")
        if data and len(data) == 6:  # Stellen sicher, dass die Daten die erwartete Länge haben
            minutes = int(data[0:2], 16)   # Erstes Byte → Minuten
            hours = int(data[2:4], 16)     # Zweites Byte → Stunden
            days = int(data[4:8], 16)      # Letzte zwei Bytes → Tage
            
            return f"{days} Tage, {hours}h, {minutes}min"
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
        """Ruft die Tagesstatistik für den aktuellen Tag ab und berechnet den Gesamtwert."""
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
            # Hier den Hex-String verarbeiten, um die Werte zu extrahieren
            hourly_values = []
            total_value = 0

            # Der Hex-String ist immer 32 Byte lang
            for i in range(0, len(data), 8):  # Jeder Abschnitt hat 8 Zeichen (4 Byte)
                hex_value = data[i:i+8]  # 8 Zeichen = 4 Byte
                _LOGGER.error(f"Keine Daten vom Endpunkt {endpoint} erhalten")
                try:
                    # Hex-Wert in Dezimal umwandeln und zu den Stundenwerten hinzufügen
                    value = int(hex_value[:4], 16) 
                    hourly_values.append(value)
                    total_value += value  # Addiere den Wert für den Gesamtwert
                except ValueError:
                    _LOGGER.error(f"Fehler beim Verarbeiten des Hex-Strings: {data}")
                    return None
            
            return {
                "hourly_values": hourly_values,
                "total_value": total_value,
            }
        return None


    async def start_regeneration(self):
        """Startet die Regeneration über den API-Endpunkt."""
        return await self._request("POST", "350000")  # API-Endpunkt für Regeneration

    async def set_leckageschutz(self, status):
        """Aktiviert oder deaktiviert den Leckageschutz (setze Alarm)."""
        endpoint = "3C00" if status else "3C01"  # Setzen (3C00) / Zurücksetzen (3C01) des Leckagealarms
        return await self._request("POST", endpoint)


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
                "betriebsstunden": await self.api.get_betriebsstunden(),
                "salzstand": await self.api.get_salzstand(),
                "gesamtwassermenge": await self.api.get_gesamtwassermenge(),
                "weichwassermenge": await self.api.get_weichwassermenge(),
                "tagesstatistik": await self.api.get_tagesstatistik(),
            }
        except Exception as err:
            raise UpdateFailed(f"Fehler beim Abrufen der Judo-Daten: {err}")
