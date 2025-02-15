from homeassistant.helpers.entity import ToggleEntity
from .api import JudoAPI
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Setzt die Schalter für Home Assistant auf."""
    config = hass.data[DOMAIN][entry.entry_id]  
    api = JudoAPI(config["ip"], config["username"], config["password"])  
    
    async_add_entities([
        JudoLeckageschutz(api),
        JudoRegeneration(api),
        JudoUrlaubsmodus(api)
    ])

class JudoLeckageschutz(ToggleEntity):
    def __init__(self, api):
        self._api = api
        self._state = False

    async def async_turn_on(self):
        if await self._api.set_leckageschutz(True):  # ✅ FIX: `await` hinzugefügt
            self._state = True
            self.schedule_update_ha_state()

    async def async_turn_off(self):
        if await self._api.set_leckageschutz(False):  # ✅ FIX: `await` hinzugefügt
            self._state = False
            self.schedule_update_ha_state()

    @property
    def is_on(self):
        return self._state

    @property
    def name(self):
        return "Leckageschutz"

class JudoRegeneration(ToggleEntity):
    def __init__(self, api):
        self._api = api
        self._state = False

    async def async_turn_on(self):
        if await self._api.start_regeneration():  # ✅ FIX: `await` hinzugefügt
            self._state = True
            self.schedule_update_ha_state()

    async def async_turn_off(self):
        self._state = False
        self.schedule_update_ha_state()

    @property
    def is_on(self):
        return self._state

    @property
    def name(self):
        return "Regeneration"

class JudoUrlaubsmodus(ToggleEntity):
    def __init__(self, api):
        self._api = api
        self._state = False

    async def async_turn_on(self):
        if await self._api.set_urlaubsmodus(True):  # ✅ FIX: `await` hinzugefügt
            self._state = True
            self.schedule_update_ha_state()

    async def async_turn_off(self):
        if await self._api.set_urlaubsmodus(False):  # ✅ FIX: `await` hinzugefügt
            self._state = False
            self.schedule_update_ha_state()

    @property
    def is_on(self):
        return self._state

    @property
    def name(self):
        return "Urlaubsmodus"
