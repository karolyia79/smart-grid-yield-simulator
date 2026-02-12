import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from .const import *

class SGYFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    def __init__(self):
        self.init_data = {}

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            self.init_data.update(user_input)
            return await self.async_step_sensors()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_PHASE_SETTING, default=PHASE_1): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": PHASE_1, "label": "1 fázisú rendszer"},
                            {"value": PHASE_3_AGGREGATED, "label": "3 fázisú (Egyben mért)"},
                            {"value": PHASE_3_INDIVIDUAL, "label": "3 fázisú (Fázisonkénti: L1,L2,L3)"}
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN
                    )
                ),
                vol.Required(CONF_FIXER_API_KEY): str,
            })
        )

    async def async_step_sensors(self, user_input=None):
        if user_input is not None:
            user_input.update(self.init_data)
            return self.async_create_entry(title="SGY Simulator", data=user_input)

        fields = {
            vol.Required(CONF_SPOT_PRICE): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
            vol.Required(CONF_LOAD_POWER): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
        }

        phase_mode = self.init_data[CONF_PHASE_SETTING]
        if phase_mode == PHASE_3_INDIVIDUAL:
            fields[vol.Required(CONF_GRID_L1)] = selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor"))
            fields[vol.Required(CONF_GRID_L2)] = selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor"))
            fields[vol.Required(CONF_GRID_L3)] = selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor"))
        else:
            fields[vol.Required(CONF_GRID_POWER)] = selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor"))

        fields.update({
            vol.Required(CONF_DAILY_IMPORT): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
            vol.Required(CONF_DAILY_EXPORT): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
            vol.Required(CONF_BATTERY_SOC): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
            vol.Required(CONF_BATTERY_CAPACITY, default=10.0): vol.Coerce(float),
            vol.Required(CONF_BATTERY_RESERVE, default=2.0): vol.Coerce(float),
        })

        return self.async_show_form(step_id="sensors", data_schema=vol.Schema(fields))
