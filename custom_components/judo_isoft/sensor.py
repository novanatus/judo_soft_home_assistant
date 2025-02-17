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
         JudoSensor(api, "Tagesstatistik", "get_tagesstatistik", "Liter")
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
            if self._method == "get_betriebsstunden":
                result = await self._get_betriebsstunden()
            elif self._method == "get_gesamtwassermenge":
                result = await self._get_gesamtwassermenge()
            elif self._method == "get_weichwassermenge":
                result = await self._get_weichwassermenge()
            elif self._method == "get_salzstand":
                result = await self._get_salzstand()
            elif self._method == "get_wasserhaerte":
                result = await self._get_wasserhaerte()
            elif self._method == "get_tagesstatistik":  # Hier wird tagesstatistik hinzugefügt
                result = await self._get_tagesstatistik()  # Rufe die Methode für die Tagesstatistik auf    
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
        result = await self._api.get_betriebsstunden()
        if result:
            return f"{result['hours']}h {result['minutes']}m"
        return None

    async def _get_gesamtwassermenge(self):
        result = await self._api.get_gesamtwassermenge()
        if result:
            return f"{result:.2f}"
        return None

    async def _get_weichwassermenge(self):
        result = await self._api.get_weichwassermenge()
        if result:
            return f"{result:.2f}"
        return None

    async def _get_salzstand(self):
        result = await self._api.get_salzstand()
        if result:
            return f"{result}"
        return None

    async def _get_wasserhaerte(self):
        result = await self._api.get_wasserhaerte()
        if result:
            return f"{result}"
        return None

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    @property
    def unit_of_measurement(self):
        return self._unit

    async def _get_tagesstatistik(self):
         data = await self._api.get_tagesstatistik()
         if data:
             total_value = data.get("total_value")  # Hier den Gesamtwert extrahieren
             if total_value is not None:
                return total_value  # Gib nur den Gesamtwert als Zahl zurück (kein " L")
         return None
       
