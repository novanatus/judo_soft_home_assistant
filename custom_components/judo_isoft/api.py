import aiohttp
import asyncio
import ssl
import json
import logging
import async_timeout
from datetime import datetime, timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from collections import deque

_LOGGER = logging.getLogger(__name__)

class JudoAPI:
    def __init__(self, ip, username, password):
        self.base_url = f"https://{ip}/api/rest"
        self.auth = aiohttp.BasicAuth(username, password)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        self.session = aiohttp.ClientSession(auth=self.auth, connector=aiohttp.TCPConnector(ssl=ssl_context))

        

    async def close(self):
        await self.session.close()

    async def _request(self, method, endpoint, payload=None):
        """Hilfsmethode für API-Requests mit Cache-Implementierung."""
        url = f"{self.base_url}/{endpoint}"
        _LOGGER.info(f"Judo API: {method} Anfrage an {url} mit Payload {payload}")


        try:
            async with async_timeout.timeout(10):  # Timeout setzen
                async with self.session.request(method, url, json=payload) as response:
                    if response.status != 200:
                        _LOGGER.error(f"API-Fehler: {response.status} - {await response.text()}")
                        return None
                    result = await response.json()

                    
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
     _LOGGER.debug(f"Erstellter API-Endpunkt: {endpoint}")

     # API-Anfrage an den Endpunkt
     data = await self.get_data(endpoint)
    
     if data:
         _LOGGER.debug(f"Antwort vom Endpunkt {endpoint}: {data}")
        
         # Da die Antwort ein Hex-String ist, verarbeite den Hex-String direkt
         hex_string = data  # Direkt als Hex-String verwenden
         _LOGGER.debug(f"Extrahierter Hex-String: {hex_string}")

         # Hier den Hex-String verarbeiten, um die Werte zu extrahieren
         hourly_values = []
         total_value = 0

         # Der Hex-String ist immer 32 Byte lang (d.h. 64 Zeichen)
         for i in range(0, len(hex_string), 8):  # Jeder Abschnitt hat 8 Zeichen (4 Byte)
             hex_value = hex_string[i:i + 8]  # 8 Zeichen = 4 Byte
             try:
                 # Wandelt den Hex-Wert in Dezimal um und fügt ihn zu den Stundenwerten hinzu
                 value = int(hex_value, 16)  
                 hourly_values.append(value)
                 total_value += value  # Addiere den Wert zum Gesamtwert
             except ValueError:
                 _LOGGER.error(f"Fehler beim Verarbeiten des Hex-Strings: {hex_string}")
                 return None
        
         # Rückgabe der berechneten Werte
         return {
             "hourly_values": hourly_values,
             "total_value": total_value,
         }
     else:
         _LOGGER.error(f"Keine Antwort vom Endpunkt {endpoint} erhalten")
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
            update_interval=timedelta(seconds=300),  # Alle 30 Sekunden abrufen
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
