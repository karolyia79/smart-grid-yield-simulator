# Smart Grid Yield Simulator

**Smart Grid Yield Simulator** is a financial pre-calculator for Home Assistant, specifically designed for solar panel and battery storage owners. It helps you estimate and track your actual savings by comparing self-consumption and battery usage against **real-time dynamic (spot) market prices**.

This tool is essential for those transitioning from flat-rate (settlement) systems to market-based pricing.

---

## 🚀 Installation Guide

### 1. Prerequisite: Enable Packages
This integration uses the Home Assistant "Packages" system for a modular setup. Ensure you have the following line in your `configuration.yaml` file:

```yaml
homeassistant:
  packages: !include_dir_named packages
```
## 🧮 How the Math Works (The Logic)

The simulator calculates your **"Savings Speed"** ($Ft/h$) in real-time, then integrates this value over time to provide total financial gains. This is essential for understanding the ROI of battery systems under dynamic pricing.

### The Core Formula:
The logic distinguishes between two main states to ensure accuracy:

#### A) Self-Sufficient State (Grid Power ≤ 0)
When your home is powered by Solar or Battery, you are saving the **full retail price** of electricity (the price you would otherwise pay to the utility).
$$Savings = Household\ Load\ (kW) \times Static\ Price\ (e.g.,\ 70.1\ Ft)$$
*Every kWh you don't buy at the fixed high price is a direct saving.*

#### B) Grid Import State (Grid Power > 0)
When you are buying electricity, you only save on the portion provided by your system (self-consumption). The simulation also calculates the benefit based on the delta between the static price and the current market price.
$$Savings = (Self\ Consumed\ Power \times Static\ Price) + (Grid\ Power \times Spot\ Price)$$

### Data Accumulation:
1. **Riemann Sum Integral:** Converts the momentary $Ft/h$ rate into a cumulative $Ft$ value using the `left` integration method for high accuracy.
2. **Utility Meters:** Provides structured Daily, Monthly, and Yearly financial reports automatically.

---

## 📊 Dashboard Card
Add a **Manual Card** to your dashboard and paste this YAML code. The headers are in English, but entity names will automatically translate if your Home Assistant language is set to Hungarian.

```yaml
type: vertical-stack
cards:
  - type: horizontal-stack
    cards:
      - type: gauge
        entity: sensor.dinamikus_brutto_aramar
        name: Gross Price
        min: 0
        max: 120
        severity:
          green: 0
          yellow: 60
          red: 70.1
        needle: true
      - type: gauge
        entity: sensor.deye_inverter_load_power
        name: House Load
        unit: W
        min: 0
        max: 5000
      - type: gauge
        entity: sensor.deye_inverter_battery
        name: Battery
        unit: "%"
        min: 0
        max: 100
        severity:
          red: 0
          yellow: 20
          green: 45
        needle: true
  - type: entities
    title: Daily Energy Flow
    show_header_toggle: false
    entities:
      - type: section
        label: AC Traffic
      - entity: sensor.deye_inverter_today_energy_import
        name: Grid Import
      - entity: sensor.deye_inverter_today_energy_export
        name: Grid Export
      - type: section
        label: Battery Traffic
      - entity: sensor.deye_inverter_today_battery_charge
        name: Today Charge
      - entity: sensor.deye_inverter_today_battery_discharge
        name: Today Discharge
      - type: section
        label: Solar Production
      - entity: sensor.deye_inverter_pv_power
        name: PV Current Power
      - entity: sensor.deye_inverter_today_production
        name: PV Today Total
  - type: entities
    title: Financial Simulation
    show_header_toggle: false
    entities:
      - entity: sensor.sgy_advisor
      - entity: sensor.smart_grid_savings_rate
      - type: section
        label: Accumulated Savings (VAT incl.)
      - entity: sensor.sgy_daily_savings
      - entity: sensor.sgy_monthly_savings
      - entity: sensor.sgy_yearly_savings
