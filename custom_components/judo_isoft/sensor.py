from datetime import timedelta  # Füge diesen Import hinzu
from homeassistant.components.sensor import SensorEntity
from .api import JudoAPI
from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Setzt die Sensoren asynchron auf."""
    config = hass.data[DOMAIN][entry.entry_id]
    api = JudoAPI(config["ip"], config["username"], config["password"])

    # Sensoren für Wasserhärte, Salzstand, Gesamtwassermenge
    async_add_entities([
         JudoSensor(api, "Wasserhärte", "get_wasserhaerte", "°dH"),
         JudoSensor(api, "Salzstand", "get_salzstand", "g"),
         JudoSensor(api, "Gesamtwassermenge", "get_gesamtwassermenge", "m³"),
         JudoSensor(api, "Weichwassermenge", "get_weichwassermenge", "m³"),
         JudoSensor(api, "Betriebsstunden", "get_betriebsstunden", "h"),
         JudoSensor(api, "Tagesstatistik", "get_tagesstatistik", "Liter"),
         JudoSensor(api, "Wochenstatistik", "get_wochenstatistik", "Liter"),
         JudoSensor(api, "Monatsstatistik", "get_monatsstatistik", "Liter"),
         JudoSensor(api, "Jahresstatistik", "get_jahresstatistik", "Liter")
     ], update_before_add=True)

class JudoSensor(SensorEntity):
    def __init__(self, api, name, method, unit):
        self._api = api
        self._name = name
        self._method = method
        self._unit = unit
        self._state = None


    async def async_update(self):
        """Aktualisiert den Zustand des Sensors."""
        try:
            # Falls es sich um Betriebsdaten handelt (z.B. Betriebsstunden, Gesamtwassermenge)
            if self._method == "get_betriebsstunden":
                result = await self._get_betriebsstunden()
            elif self._method == "get_gesamtwassermenge":
                result = await self._get_gesamtwassermenge()
            elif self._method == "get_weichwassermenge":
                result = await self._get_weichwassermenge()
            elif self._method == "get_salzstand":
                result = await self._get_salzstand()
            elif self._method == "get_wasserhaerte":
                result = await self._get_wasserhaerte()  # Neu hinzugefügt
            else:
                result = await getattr(self._api, self._method)()

            if result:
                self._state = result
            else:
                self._state = "Keine Daten"
        except Exception as e:
            _LOGGER.error(f"Fehler beim Abrufen des Sensors {self._name}: {e}")
            self._state = "Fehler"

    async def _get_betriebsstunden(self):
        """Formatiert die Betriebsstunden als 'h m'."""
        result = await self._api.get_betriebsstunden()
        if result:
            return f"{result['hours']}h {result['minutes']}m"
        return None

    async def _get_gesamtwassermenge(self):
        """Formatiert die Gesamtwassermenge als 'm³'."""
        result = await self._api.get_gesamtwassermenge()
        if result:
            return f"{result:.2f} m³"
        return None

    async def _get_weichwassermenge(self):
        """Formatiert die Weichwassermenge als 'm³'."""
        result = await self._api.get_weichwassermenge()
        if result:
            return f"{result:.2f} m³"
        return None

    async def _get_salzstand(self):
        """Gibt den Salzstand in Gramm zurück."""
        result = await self._api.get_salzstand()
        if result:
            return f"{result} g"
        return None

    async def _get_wasserhaerte(self):
        """Gibt die Wasserhärte in °dH zurück."""
        result = await self._api.get_wasserhaerte()  # Hier wird die Methode get_wasserhaerte verwendet
        if result:
            return f"{result} °dH"
        return None

    @property
    def name(self):
        """Gibt den Namen des Sensors zurück."""
        return self._name

    @property
    def state(self):
        """Gibt den aktuellen Zustand des Sensors zurück."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Gibt die Einheit des Sensors zurück."""
        return self._unit

    async def _get_tagesstatistik(self):
        """Summiert die Tagesstatistik und gibt den Wert in Litern zurück."""
        data = await self._api.get_tagesstatistik()
        if data:
            # Hier gehen wir davon aus, dass die Daten hex-codierte Werte für jede Zeitspanne sind
            # Die Funktion summiert diese Werte und gibt sie in Litern zurück
            total_liters = sum([int(data[i:i+2], 16) for i in range(0, len(data), 2)])  # Beispielhafte Berechnung in Litern
            return total_liters
        return None

    async def _get_wochenstatistik(self):
        """Summiert die Wochenstatistik und gibt den Wert in Litern zurück."""
        data = await self._api.get_wochenstatistik()
        if data:
            total_liters = sum([int(data[i:i+2], 16) for i in range(0, len(data), 2)])  # Beispielhafte Berechnung in Litern
            return total_liters
        return None

    async def _get_monatsstatistik(self):
        """Summiert die Monatsstatistik und gibt den Wert in Litern zurück."""
        data = await self._api.get_monatsstatistik()
        if data:
            total_liters = sum([int(data[i:i+2], 16) for i in range(0, len(data), 2)])  # Beispielhafte Berechnung in Litern
            return total_liters
        return None

    async def _get_jahresstatistik(self):
        """Summiert die Jahresstatistik und gibt den Wert in Litern zurück."""
        data = await self._api.get_jahresstatistik()
        if data:
            total_liters = sum([int(data[i:i+2], 16) for i in range(0, len(data), 2)])  # Beispielhafte Berechnung in Litern
            return total_liters
        return None
