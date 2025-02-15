from homeassistant.helpers.entity import Entity
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
        JudoSensor(api, "Tagesstatistik", "get_tagesstatistik", "Daten"),
        JudoSensor(api, "Wochenstatistik", "get_wochenstatistik", "Daten"),
        JudoSensor(api, "Monatsstatistik", "get_monatsstatistik", "Daten"),
        JudoSensor(api, "Jahresstatistik", "get_jahresstatistik", "Daten")
    ], update_before_add=True)

class JudoSensor(Entity):
    def __init__(self, api, name, method, unit):
        self._api = api
        self._name = name
        self._method = method
        self._unit = unit
        self._state = None

    async def async_update(self):
        """Aktualisiert den Zustand des Sensors."""
        # Wenn es eine Methode für das Abrufen von Betriebsdaten gibt, rufen wir sie auf
        if self._method in ["get_betriebsstunden", "get_gesamtwassermenge", "get_weichwassermenge"]:
            result = await getattr(self._api, self._method)()
            if result:
                if self._method == "get_betriebsstunden":
                    self._state = f"{result['hours']}h {result['minutes']}m"
                else:
                    self._state = f"{result:.2f} m³"  # Format für die Wassermenge
            else:
                self._state = "Keine Daten"
        else:
            result = await getattr(self._api, self._method)()
            if result:
                self._state = result
            else:
                self._state = "Keine Daten"

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
