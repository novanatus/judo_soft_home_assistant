from homeassistant.helpers.entity import Entity
from .api import JudoAPI
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    api = JudoAPI(entry.data["ip"])
    async_add_entities([
        JudoSensor(api, "Wasserhärte", "get_wasserhaerte", "°dH"),
        JudoSensor(api, "Salzstand", "get_salzstand", "g"),
        JudoSensor(api, "Gesamtwassermenge", "get_geraet_info", "m³"),
    ], update_before_add=True)

class JudoSensor(Entity):
    def __init__(self, api, name, method, unit):
        self._api = api
        self._name = name
        self._method = method
        self._unit = unit
        self._state = None

    async def async_update(self):
        self._state = getattr(self._api, self._method)()

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    @property
    def unit_of_measurement(self):
        return self._unit
