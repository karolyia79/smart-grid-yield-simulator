"""Constants for the Smart Grid Yield Simulator."""

DOMAIN = "smart_grid_yield"

# Beállítások kulcsai
CONF_PHASE_SETTING = "phase_setting"
CONF_EXCHANGE_RATE_SENSOR = "exchange_rate_sensor" # Az új, manuális árfolyam szenzorhoz

# Fázis opciók
PHASE_1 = "1_phase"
PHASE_3_AGGREGATED = "3_phase_aggregated"
PHASE_3_INDIVIDUAL = "3_phase_individual"

# Szenzor konfigurációs kulcsok
CONF_SPOT_PRICE = "spot_price_sensor"
CONF_LOAD_POWER = "load_power_sensor"
CONF_PV_POWER = "pv_power_sensor"
CONF_TOTAL_LOSS = "total_loss_sensor"
CONF_BATT_CHARGE = "batt_charge_sensor"
CONF_BATT_DISCHARGE = "batt_discharge_sensor"

# Hálózati mérés kulcsai
CONF_GRID_POWER = "grid_power_sensor"
CONF_GRID_L1 = "grid_l1_sensor"
CONF_GRID_L2 = "grid_l2_sensor"
CONF_GRID_L3 = "grid_l3_sensor"

# Egyéb adatok
CONF_DAILY_IMPORT = "daily_import_sensor"
CONF_DAILY_EXPORT = "daily_export_sensor"
CONF_BATTERY_SOC = "battery_soc_sensor"
CONF_BATTERY_CAPACITY = "battery_capacity"
CONF_BATTERY_RESERVE = "battery_reserve"

# Platformok listája
PLATFORMS = ["sensor"]
