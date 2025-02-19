from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .api import JudoAPI

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Setzt die Integration in Home Assistant auf."""
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "ip": entry.data["ip"],
        "username": entry.data["username"],
        "password": entry.data["password"]
    }

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "switch")
    )

    return True
