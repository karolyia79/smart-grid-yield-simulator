import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from .const import (
    DOMAIN, CONF_SPOT_PRICE, CONF_LOAD_POWER, CONF_GRID_POWER, 
    CONF_FIXER_API_KEY, CONF_DAILY_IMPORT, CONF_DAILY_EXPORT,
    CONF_BATTERY_CAPACITY, CONF_BATTERY_RESERVE, CONF_BATTERY_SOC
)

class SGYFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if "nordpool" not in self.hass.config.components:
            return self.async_abort(reason="missing_nordpool")
        
        if user_input is not None:
            return self.async_create_entry(title="SGY Simulator", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_FIXER_API_KEY): str,
                vol.Required(CONF_SPOT_PRICE): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Required(CONF_LOAD_POWER): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Required(CONF_GRID_POWER): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Required(CONF_DAILY_IMPORT): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Required(CONF_DAILY_EXPORT): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Required(CONF_BATTERY_SOC): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Required(CONF_BATTERY_CAPACITY, default=10.0): vol.Coerce(float),
                vol.Required(CONF_BATTERY_RESERVE, default=2.0): vol.Coerce(float),
            })
        )
