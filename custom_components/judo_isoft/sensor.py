from homeassistant.helpers.entity import Entity
from .api import JudoAPI
from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Setzt die Sensoren asynchron auf."""
    config = hass.data[DOMAIN][entry.entry_id]
    api = JudoAPI(config["ip"], config["username"], config["password"])

    # Füge die Sensoren hinzu
    async_add_entities([
        JudoSensor(api, "Wasserhärte", "get_wasserhaerte", "°dH"),
        JudoSensor(api, "Salzstand", "get_salzstand", "g"),
        JudoSensor(api, "Gesamtwassermenge", "get_geraet_info", "m³"),

        # Neue Sensoren für Statistiken
        JudoSensor(api, "Tagesstatistik", "get_tagesstatistik", "L/h"),
        JudoSensor(api, "Wochenstatistik", "get_wochenstatistik", "L/h"),
        JudoSensor(api, "Monatsstatistik", "get_monatsstatistik", "L/h"),
        JudoSensor(api, "Jahresstatistik", "get_jahresstatistik", "L/h"),
    ], update_before_add=True)

class JudoSensor(Entity):
    def __init__(self, api, name, method, unit):
        self._api = api
        self._name = name
        self._method = method
        self._unit = unit
        self._state = None

    async def async_update(self):
        """Aktualisiere den Zustand des Sensors."""
        try:
            self._state = await getattr(self._api, self._method)()
        except Exception as e:
            _LOGGER.error(f"Fehler beim Aktualisieren des Sensors {self._name}: {e}")
            self._state = None

    @property
    def name(self):
        """Gibt den Namen des Sensors zurück."""
        return self._name

    @property
    def state(self):
        """Gibt den Zustand des Sensors zurück."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Gibt die Einheit des Sensors zurück."""
        return self._unit
