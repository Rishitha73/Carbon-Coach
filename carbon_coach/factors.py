"""Emission factors and appliance power ratings for Carbon Coach.

All factors are expressed in kg CO2e (carbon dioxide equivalent).
Sources are cited for transparency.
NOTE: Verify all values before live demo presentation.
"""

from typing import Dict

# ---------------------------------------------------------------------------
# TRAVEL EMISSION FACTORS (kg CO2e per passenger-kilometer)
# Sources:
# - UK DEFRA GHG Conversion Factors (2023/2024 update)
# - India urban transit studies & ARAI vehicle average emission estimates
# Verify before demo: Check whether metro emission factor assumes Indian grid mix.
# ---------------------------------------------------------------------------
TRAVEL_KG_PER_KM: Dict[str, float] = {
    "bus": 0.089,             # DEFRA average local public bus per passenger-km
    "car_petrol": 0.170,       # Average petrol passenger car (1 passenger)
    "car_diesel": 0.165,       # Average diesel passenger car (1 passenger)
    "two_wheeler": 0.070,      # Petrol motorbike / scooter (100-150cc average)
    "auto_rickshaw": 0.100,    # CNG/petrol auto-rickshaw per passenger-km (approximate, verify)
    "metro": 0.030,            # Electric urban metro transit (e.g. Delhi/Bangalore/Hyderabad Metro)
    "train": 0.040,            # Indian Railways national broad-gauge electric passenger train
    "cycle": 0.0,              # Zero operational emissions
    "walk": 0.0,               # Zero operational emissions
}

# ---------------------------------------------------------------------------
# ELECTRICITY GRID EMISSION FACTOR (kg CO2e per kWh)
# Source:
# - Central Electricity Authority (CEA), Government of India:
#   "CO2 Baseline Database for the Indian Power Sector" (Version 19 / 2023-2024)
#   Weighted average national grid emission factor including renewables & hydro: ~0.71 kg CO2e/kWh
# Verify before demo: Confirm current CEA baseline database version and year.
# ---------------------------------------------------------------------------
ELECTRICITY_KG_PER_KWH: float = 0.71

# ---------------------------------------------------------------------------
# APPLIANCE POWER RATINGS (Average Power Consumption in Kilowatts - kW)
# Sources:
# - Bureau of Energy Efficiency (BEE India) star rating appliance standards
# - Typical household appliance power ratings
# Verify before demo: Verify rated wattage matches standard household models.
# ---------------------------------------------------------------------------
APPLIANCE_KW: Dict[str, float] = {
    "ac": 1.5,                 # 1.5-ton split AC (average running draw)
    "fan": 0.075,              # Standard ceiling fan (75 Watts)
    "led_light": 0.010,        # Standard LED bulb (10 Watts)
    "laptop": 0.050,           # Average laptop during typical workload (50 Watts)
    "desktop": 0.200,          # Desktop PC with monitor (200 Watts)
    "refrigerator": 0.150,     # Typical double-door refrigerator compressor average (150 Watts)
    "geyser": 2.000,           # Electric water heater / geyser (2000 Watts)
    "washing_machine": 0.500,  # Automatic washing machine cycle (500 Watts)
    "tv": 0.100,               # 43-55 inch LED television (100 Watts)
}

# ---------------------------------------------------------------------------
# FOOD EMISSION FACTORS (kg CO2e per standard meal)
# Sources:
# - Poore & Nemecek (2018), "Reducing food's environmental impacts through
#   producers and consumers", Science / Our World in Data (Food Emissions)
# - Adjusted per standard 300g-400g cooked portion/meal
# Verify before demo: Food portions vary; confirm standard portion assumptions.
# ---------------------------------------------------------------------------
FOOD_KG_PER_MEAL: Dict[str, float] = {
    "vegetarian": 0.7,         # Indian vegetarian meal (grains, lentils, dairy, veggies)
    "vegan": 0.4,              # Plant-based meal without dairy/eggs
    "egg": 0.9,                # Meal with 2 eggs, grains, and vegetables
    "chicken": 1.6,            # Meal featuring broiler chicken (e.g. chicken biryani/curry)
    "fish": 1.5,               # Farmed/freshwater fish meal
    "mutton": 5.0,             # Lamb / mutton meal (high ruminant enteric emissions)
    "beef": 6.0,               # Beef meal (high ruminant enteric & land use emissions)
}

# ---------------------------------------------------------------------------
# WASTE EMISSION FACTORS (kg CO2e per kg of waste disposed)
# Sources:
# - IPCC Guidelines for National Greenhouse Gas Inventories (Waste Sector)
# - DEFRA Waste disposal & recycling conversion factors
# Verify before demo: Landfill methane capture rates vary by municipal corporation.
# ---------------------------------------------------------------------------
WASTE_KG_PER_KG: Dict[str, float] = {
    "mixed_landfill": 0.45,    # Unsorted municipal solid waste sent to open landfill
    "recycled_paper": 0.05,    # Paper diverted to recycling process
    "recycled_plastic": 0.10,  # Rigid/film plastics sorted and recycled
    "composted_food": 0.05,    # Organic wet waste composted aerobically
}

# ---------------------------------------------------------------------------
# DAILY CARBON BENCHMARK (kg CO2e per person per day)
# Sources:
# - Our World in Data / World Bank: India's annual per-capita greenhouse gas
#   emissions are approximately 1.9 tonnes CO2e/year (~5.2 kg CO2e/person/day).
# - Global average is ~12.0 kg CO2e/person/day.
# - IPCC 1.5°C target trajectory recommends < 2.0-2.5 tonnes/year (~6.0 kg/day).
# Value: 5.0 kg CO2e/day is chosen as an illustrative realistic personal benchmark.
# Verify before demo: Illustrative benchmark for urban Indian students & families.
# ---------------------------------------------------------------------------
DAILY_BENCHMARK_KG: float = 5.0
