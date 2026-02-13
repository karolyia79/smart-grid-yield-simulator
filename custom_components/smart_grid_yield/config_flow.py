import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv

# Feltételezve, hogy a const.py-ban ezek pontosan így szerepelnek
from .const import (
    DOMAIN,
    CONF_PHASE_SETTING,
    PHASE_1,
    PHASE_3_AGGREGATED,
    PHASE_3_INDIVIDUAL,
    CONF_FIXER_API_KEY,
    CONF_SPOT_PRICE,
    CONF_LOAD_POWER,
    CONF_PV_POWER,
    CONF_TOTAL_LOSS,
    CONF_BATT_CHARGE,
    CONF_BATT_DISCHARGE,
    CONF_GRID_L1,
    CONF_GRID_L2,
    CONF_GRID_L3,
    CONF_GRID_POWER,
    CONF_DAILY_IMPORT,
    CONF_DAILY_EXPORT,
    CONF_BATTERY_SOC,
    CONF_BATTERY_CAPACITY,
    CONF_BATTERY_RESERVE,
)

class SGYFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """SGY Simulator Config Flow."""
    VERSION = 1

    def __init__(self):
        """Inicializálás."""
        self.init_data = {}

    async def async_step_user(self, user_input=None):
        """Első lépés: Rendszer típusa és API kulcs."""
        errors = {}
        
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
                            {"value": PHASE_3_INDIVIDUAL, "label": "3 fázisú (L1,L2,L3)"}
                        ], 
                        mode=selector.SelectSelectorMode.DROPDOWN
                    )
                ),
                vol.Required(CONF_FIXER_API_KEY): selector.TextSelector(),
            }),
            errors=errors
        )

    async def async_step_sensors(self, user_input=None):
        """Második lépés: Szenzorok hozzárendelése."""
        errors = {}

        if user_input is not None:
            # Összefésüljük az előző lépés adataival
            full_data = {**self.init_data, **user_input}
            return self.async_create_entry(title="SGY Full Simulator", data=full_data)

        # Mezők összeállítása
        fields = {
            vol.Required(CONF_SPOT_PRICE): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
            vol.Required(CONF_LOAD_POWER): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
            vol.Optional(CONF_PV_POWER): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
            vol.Optional(CONF_TOTAL_LOSS): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
            vol.Optional(CONF_BATT_CHARGE): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
            vol.Optional(CONF_BATT_DISCHARGE): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
        }

        # Fázis-specifikus mezők hozzáadása
        phase_mode = self.init_data.get(CONF_PHASE_SETTING)
        
        if phase_mode == PHASE_3_INDIVIDUAL:
            fields[vol.Required(CONF_GRID_L1)] = selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor"))
            fields[vol.Required(CONF_GRID_L2)] = selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor"))
            fields[vol.Required(CONF_GRID_L3)] = selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor"))
        else:
            fields[vol.Required(CONF_GRID_POWER)] = selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor"))

        # Fix maradék mezők
        fields.update({
            vol.Required(CONF_DAILY_IMPORT): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
            vol.Required(CONF_DAILY_EXPORT): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
            vol.Required(CONF_BATTERY_SOC): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
            vol.Required(CONF_BATTERY_CAPACITY, default=10.0): vol.Coerce(float),
            vol.Required(CONF_BATTERY_RESERVE, default=2.0): vol.Coerce(float),
        })

        return self.async_show_form(
            step_id="sensors", 
            data_schema=vol.Schema(fields),
            errors=errors
        )
