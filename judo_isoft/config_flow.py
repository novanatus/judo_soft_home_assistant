import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN

class JudoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Judo iSoft."""

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title="Judo iSoft SAFE+", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required("ip"): str}),
            errors=errors,
        )
