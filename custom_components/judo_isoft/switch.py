from homeassistant.components.button import ButtonEntity
from .api import JudoAPI
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Setzt die Taster für Home Assistant auf."""
    config = hass.data[DOMAIN][entry.entry_id]
    api = JudoAPI(config["ip"], config["username"], config["password"])

    async_add_entities([
        JudoLeckageschutzButton(api),
        JudoRegenerationButton(api),
        JudoUrlaubsmodusButton(api)
    ])

class JudoLeckageschutzButton(ButtonEntity):
    """Taster für Leckageschutz."""
    def __init__(self, api):
        self._api = api

    async def async_press(self):
        """Aktion, wenn der Taster gedrückt wird."""
        if await self._api.set_leckageschutz(True):
            _LOGGER.info("Leckageschutz aktiviert.")
        else:
            _LOGGER.error("Fehler beim Aktivieren des Leckageschutzes.")

    @property
    def name(self):
        return "Leckageschutz"

class JudoRegenerationButton(ButtonEntity):
    """Taster für Regeneration."""
    def __init__(self, api):
        self._api = api

    async def async_press(self):
        """Aktion, wenn der Taster gedrückt wird."""
        if await self._api.start_regeneration():
            _LOGGER.info("Regeneration gestartet.")
        else:
            _LOGGER.error("Fehler beim Starten der Regeneration.")

    @property
    def name(self):
        return "Regeneration"

class JudoUrlaubsmodusButton(ButtonEntity):
    """Taster für Urlaubsmodus."""
    def __init__(self, api):
        self._api = api

    async def async_press(self):
        """Aktion, wenn der Taster gedrückt wird."""
        if await self._api.set_urlaubsmodus(True):
            _LOGGER.info("Urlaubsmodus aktiviert.")
        else:
            _LOGGER.error("Fehler beim Aktivieren des Urlaubsmodus.")

    @property
    def name(self):
        return "Urlaubsmodus"
