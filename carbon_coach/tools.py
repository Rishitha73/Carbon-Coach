"""Calculation and state-tracking tools for Carbon Coach.

Every emission value, savings figure, and summary metric is computed
deterministically by these functions. The LLM must rely solely on these outputs.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional
from google.adk.tools import ToolContext

from .factors import (
    APPLIANCE_KW,
    DAILY_BENCHMARK_KG,
    ELECTRICITY_KG_PER_KWH,
    FOOD_KG_PER_MEAL,
    TRAVEL_KG_PER_KM,
    WASTE_KG_PER_KG,
)

# In-memory shared leaderboard store for campus groups (hostels, departments)
_CAMPUS_GROUPS: Dict[str, Dict[str, Any]] = {}


# ============================================================================
# 1. TRAVEL EMISSIONS
# ============================================================================
def calculate_travel_emissions(mode: str, km: float) -> Dict[str, Any]:
    """Calculates carbon emissions for passenger travel in kg CO2e.

    Args:
        mode: The travel mode. Supported: bus, car_petrol, car_diesel,
              two_wheeler, auto_rickshaw, metro, train, cycle, walk.
        km: Distance travelled in kilometers (must be positive).

    Returns:
        Dict containing status, mode, km, emission factor, and kg_co2e.
    """
    if km is None or km <= 0:
        return {
            "status": "error",
            "message": "Distance must be a positive number greater than 0.",
        }

    norm_mode = mode.strip().lower().replace(" ", "_") if mode else ""
    # Friendly synonyms
    synonyms = {
        "bike": "two_wheeler",
        "motorcycle": "two_wheeler",
        "scooter": "two_wheeler",
        "auto": "auto_rickshaw",
        "rickshaw": "auto_rickshaw",
        "subway": "metro",
        "tube": "metro",
        "rail": "train",
        "car": "car_petrol",
        "bicycle": "cycle",
        "walking": "walk",
    }
    norm_mode = synonyms.get(norm_mode, norm_mode)

    if norm_mode not in TRAVEL_KG_PER_KM:
        supported = ", ".join(sorted(TRAVEL_KG_PER_KM.keys()))
        return {
            "status": "error",
            "message": (
                f"Unknown travel mode '{mode}'. Supported travel modes are: {supported}."
            ),
        }

    factor = TRAVEL_KG_PER_KM[norm_mode]
    kg_co2e = round(km * factor, 3)

    return {
        "status": "ok",
        "mode": norm_mode,
        "km": round(float(km), 2),
        "factor_kg_per_km": factor,
        "kg_co2e": kg_co2e,
        "source": "DEFRA / Indian Transit Benchmark",
    }


# ============================================================================
# 2. ELECTRICITY EMISSIONS
# ============================================================================
def calculate_electricity_emissions(
    kwh: Optional[float] = None,
    appliance: Optional[str] = None,
    hours: Optional[float] = None,
) -> Dict[str, Any]:
    """Calculates electricity emissions in kg CO2e from direct kWh or appliance usage.

    Args:
        kwh: Direct electricity consumption in kilowatt-hours.
        appliance: Appliance name (ac, fan, led_light, laptop, desktop,
                   refrigerator, geyser, washing_machine, tv).
        hours: Hours of appliance operation (must be positive).

    Returns:
        Dict containing status, electricity metrics, assumed kW rating, and kg_co2e.
    """
    # Case 1: Direct kWh provided
    if kwh is not None:
        if kwh <= 0:
            return {
                "status": "error",
                "message": "Electricity consumption (kwh) must be a positive number.",
            }
        kg_co2e = round(kwh * ELECTRICITY_KG_PER_KWH, 3)
        return {
            "status": "ok",
            "kwh": round(float(kwh), 3),
            "grid_factor_kg_per_kwh": ELECTRICITY_KG_PER_KWH,
            "kg_co2e": kg_co2e,
            "assumption": (
                f"Assumed India national grid average emission factor of "
                f"{ELECTRICITY_KG_PER_KWH} kg CO2e/kWh (CEA Baseline Database)."
            ),
        }

    # Case 2: Appliance + Hours provided
    if appliance is not None and hours is not None:
        if hours <= 0:
            return {
                "status": "error",
                "message": "Hours of appliance use must be a positive number.",
            }
        if hours > 24:
            return {
                "status": "error",
                "message": (
                    f"A single day has only 24 hours ({hours} hours provided). "
                    f"Did you run multiple appliances simultaneously, or was this over several days? "
                    f"Please clarify so I can calculate your footprint accurately."
                ),
            }

        norm_app = appliance.strip().lower().replace(" ", "_")
        synonyms = {
            "air_conditioner": "ac",
            "air_con": "ac",
            "ceiling_fan": "fan",
            "light": "led_light",
            "bulb": "led_light",
            "computer": "desktop",
            "pc": "desktop",
            "fridge": "refrigerator",
            "water_heater": "geyser",
            "television": "tv",
        }
        norm_app = synonyms.get(norm_app, norm_app)

        if norm_app not in APPLIANCE_KW:
            supported = ", ".join(sorted(APPLIANCE_KW.keys()))
            return {
                "status": "error",
                "message": (
                    f"Unknown appliance '{appliance}'. Supported appliances are: {supported}."
                ),
            }

        kw_rating = APPLIANCE_KW[norm_app]
        calc_kwh = round(kw_rating * hours, 3)
        kg_co2e = round(calc_kwh * ELECTRICITY_KG_PER_KWH, 3)

        return {
            "status": "ok",
            "appliance": norm_app,
            "hours": round(float(hours), 2),
            "assumed_kw": kw_rating,
            "kwh": calc_kwh,
            "grid_factor_kg_per_kwh": ELECTRICITY_KG_PER_KWH,
            "kg_co2e": kg_co2e,
            "assumption": (
                f"Assumed {norm_app} power rating is {kw_rating} kW based on standard "
                f"Indian household BEE ratings and India grid emission factor "
                f"{ELECTRICITY_KG_PER_KWH} kg CO2e/kWh."
            ),
        }

    return {
        "status": "error",
        "message": (
            "Please provide either direct electricity consumption in 'kwh', "
            "or both 'appliance' and 'hours'."
        ),
    }


# ============================================================================
# 3. FOOD EMISSIONS
# ============================================================================
def calculate_food_emissions(meal_type: str, meals: int = 1) -> Dict[str, Any]:
    """Calculates greenhouse gas emissions from meals in kg CO2e.

    Args:
        meal_type: Type of meal. Supported: vegetarian, vegan, egg, chicken,
                   fish, mutton, beef.
        meals: Number of meals consumed (default: 1, must be positive).

    Returns:
        Dict containing status, meal_type, meals count, factor, and kg_co2e.
    """
    if meals is None or meals <= 0:
        return {
            "status": "error",
            "message": "Number of meals must be a positive integer greater than 0.",
        }

    norm_meal = meal_type.strip().lower().replace(" ", "_") if meal_type else ""
    synonyms = {
        "veg": "vegetarian",
        "veggie": "vegetarian",
        "plant_based": "vegan",
        "eggs": "egg",
        "poultry": "chicken",
        "seafood": "fish",
        "goat": "mutton",
        "lamb": "mutton",
    }
    norm_meal = synonyms.get(norm_meal, norm_meal)

    if norm_meal not in FOOD_KG_PER_MEAL:
        supported = ", ".join(sorted(FOOD_KG_PER_MEAL.keys()))
        return {
            "status": "error",
            "message": (
                f"Unknown meal type '{meal_type}'. Supported meal types are: {supported}."
            ),
        }

    factor = FOOD_KG_PER_MEAL[norm_meal]
    kg_co2e = round(factor * meals, 3)

    return {
        "status": "ok",
        "meal_type": norm_meal,
        "meals": int(meals),
        "factor_kg_per_meal": factor,
        "kg_co2e": kg_co2e,
        "source": "Poore & Nemecek / Our World in Data Food Lifecycle Database",
    }


# ============================================================================
# 4. WASTE EMISSIONS
# ============================================================================
def calculate_waste_emissions(waste_type: str, kg: float) -> Dict[str, Any]:
    """Calculates carbon footprint of solid waste disposal in kg CO2e.

    Args:
        waste_type: Type of waste. Supported: mixed_landfill, recycled_paper,
                    recycled_plastic, composted_food.
        kg: Weight of waste in kilograms (must be positive).

    Returns:
        Dict containing status, waste_type, kg, factor, and kg_co2e.
    """
    if kg is None or kg <= 0:
        return {
            "status": "error",
            "message": "Waste quantity (kg) must be a positive number greater than 0.",
        }

    norm_waste = waste_type.strip().lower().replace(" ", "_") if waste_type else ""
    synonyms = {
        "landfill": "mixed_landfill",
        "trash": "mixed_landfill",
        "garbage": "mixed_landfill",
        "paper": "recycled_paper",
        "plastic": "recycled_plastic",
        "compost": "composted_food",
        "food_waste": "composted_food",
    }
    norm_waste = synonyms.get(norm_waste, norm_waste)

    if norm_waste not in WASTE_KG_PER_KG:
        supported = ", ".join(sorted(WASTE_KG_PER_KG.keys()))
        return {
            "status": "error",
            "message": (
                f"Unknown waste type '{waste_type}'. Supported waste types are: {supported}."
            ),
        }

    factor = WASTE_KG_PER_KG[norm_waste]
    kg_co2e = round(factor * kg, 3)

    return {
        "status": "ok",
        "waste_type": norm_waste,
        "kg": round(float(kg), 3),
        "factor_kg_per_kg": factor,
        "kg_co2e": kg_co2e,
        "source": "IPCC / DEFRA Waste Conversion Factors",
    }


# ============================================================================
# 5. LOG ACTIVITY (SESSION MEMORY)
# ============================================================================
def log_activity(
    category: str,
    details: str,
    kg_co2e: float,
    tool_context: ToolContext,
    date: Optional[str] = None,
) -> Dict[str, Any]:
    """Logs an emission activity into session state memory and updates the running total.

    Args:
        category: Activity category ('travel', 'electricity', 'food', 'waste').
        details: Concise description of the activity (e.g. '12 km by bus').
        kg_co2e: Total emissions calculated for this activity in kg CO2e.
        tool_context: Runtime ADK tool context providing access to session state.
        date: Optional ISO date string ('YYYY-MM-DD'). Defaults to today.

    Returns:
        Dict containing logged entry, today's running total, and count of activities.
    """
    if kg_co2e is None or kg_co2e < 0:
        return {
            "status": "error",
            "message": "kg_co2e must be a non-negative number.",
        }

    entry_date = date.strip() if date else datetime.date.today().isoformat()
    today_iso = datetime.date.today().isoformat()

    # Validate date format if provided
    try:
        datetime.date.fromisoformat(entry_date)
    except ValueError:
        return {
            "status": "error",
            "message": f"Invalid date format '{date}'. Expected YYYY-MM-DD.",
        }

    # Access session state safely
    state = tool_context.state
    if "activities" not in state or not isinstance(state["activities"], list):
        state["activities"] = []

    activity_entry = {
        "date": entry_date,
        "category": category.strip().lower(),
        "details": details.strip(),
        "kg_co2e": round(float(kg_co2e), 3),
    }
    state["activities"].append(activity_entry)

    # Compute today's running total
    today_total = sum(
        item["kg_co2e"]
        for item in state["activities"]
        if item.get("date") == today_iso
    )

    return {
        "status": "ok",
        "logged_activity": activity_entry,
        "today_total_kg_co2e": round(today_total, 3),
        "total_activities_logged": len(state["activities"]),
    }


# ============================================================================
# 6. GET SUMMARY & BENCHMARK COMPARISON
# ============================================================================
def get_summary(period: str, tool_context: ToolContext) -> Dict[str, Any]:
    """Generates an emissions summary over a specified period with benchmark comparison.

    Args:
        period: Time window for summary ('today', 'week', 'all').
        tool_context: Runtime ADK tool context providing access to session state.

    Returns:
        Dict containing total kg CO2e, category breakdown, daily breakdown,
        top emitting category, and comparison against benchmark.
    """
    norm_period = period.strip().lower() if period else "today"
    if norm_period not in ("today", "week", "all"):
        return {
            "status": "error",
            "message": "Period must be one of: 'today', 'week', 'all'.",
        }

    state = tool_context.state
    activities: List[Dict[str, Any]] = state.get("activities", [])

    today = datetime.date.today()
    seven_days_ago = today - datetime.timedelta(days=6)

    # Filter activities by period
    filtered: List[Dict[str, Any]] = []
    for act in activities:
        act_date_str = act.get("date")
        if not act_date_str:
            continue
        try:
            act_date = datetime.date.fromisoformat(act_date_str)
        except ValueError:
            continue

        if norm_period == "today" and act_date == today:
            filtered.append(act)
        elif norm_period == "week" and seven_days_ago <= act_date <= today:
            filtered.append(act)
        elif norm_period == "all":
            filtered.append(act)

    # Compute benchmark for the period
    if norm_period == "today":
        benchmark = DAILY_BENCHMARK_KG
    elif norm_period == "week":
        benchmark = round(DAILY_BENCHMARK_KG * 7.0, 3)
    else:
        # For 'all', scale benchmark by the number of unique days logged (minimum 1)
        unique_days = {act.get("date") for act in filtered if act.get("date")}
        num_days = max(1, len(unique_days))
        benchmark = round(DAILY_BENCHMARK_KG * num_days, 3)

    if not filtered:
        return {
            "status": "ok",
            "period": norm_period,
            "message": f"No activities logged for {norm_period}.",
            "total_kg_co2e": 0.0,
            "category_breakdown": {},
            "daily_breakdown": {},
            "top_category": None,
            "benchmark_kg_co2e": benchmark,
            "comparison_vs_benchmark": "No activities recorded for this period.",
        }

    total_kg = round(sum(item["kg_co2e"] for item in filtered), 3)

    # Category breakdown
    cat_breakdown: Dict[str, float] = {}
    for item in filtered:
        cat = item.get("category", "other")
        cat_breakdown[cat] = round(cat_breakdown.get(cat, 0.0) + item["kg_co2e"], 3)

    # Daily breakdown
    daily_breakdown: Dict[str, float] = {}
    for item in filtered:
        d = item.get("date", "unknown")
        daily_breakdown[d] = round(daily_breakdown.get(d, 0.0) + item["kg_co2e"], 3)

    # Top emitting category
    top_cat = max(cat_breakdown.items(), key=lambda x: x[1])[0] if cat_breakdown else None

    # Benchmark comparison
    diff = round(total_kg - benchmark, 3)
    percentage = round((total_kg / benchmark) * 100.0, 1) if benchmark > 0 else 0.0
    if diff <= 0:
        comparison_text = (
            f"Great job! Your emissions of {total_kg} kg CO2e are {abs(diff)} kg below "
            f"the {norm_period} benchmark of {benchmark} kg CO2e ({percentage}% of benchmark)."
        )
    else:
        comparison_text = (
            f"Your emissions of {total_kg} kg CO2e exceeded the {norm_period} benchmark "
            f"of {benchmark} kg CO2e by {diff} kg ({percentage}% of benchmark)."
        )

    return {
        "status": "ok",
        "period": norm_period,
        "total_kg_co2e": total_kg,
        "category_breakdown": cat_breakdown,
        "daily_breakdown": daily_breakdown,
        "top_category": top_cat,
        "benchmark_kg_co2e": benchmark,
        "difference_kg_co2e": diff,
        "percentage_of_benchmark": percentage,
        "comparison_vs_benchmark": comparison_text,
    }


# ============================================================================
# 7. ACTIONABLE REDUCTION TIPS
# ============================================================================
def suggest_reductions(tool_context: ToolContext) -> Dict[str, Any]:
    """Generates personalized, actionable reduction tips with computed kg CO2e savings.

    Reads session activities, identifies the highest emitting behaviors,
    and calculates exact savings from switching to greener alternatives.

    Args:
        tool_context: Runtime ADK tool context providing access to session state.

    Returns:
        Dict containing status, ranked tips with estimated savings, or an error if empty.
    """
    state = tool_context.state
    activities: List[Dict[str, Any]] = state.get("activities", [])

    if not activities:
        return {
            "status": "error",
            "message": (
                "No activities logged yet. Please log your daily activities "
                "(travel, electricity, food, or waste) first to receive personalized tips."
            ),
        }

    tips: List[Dict[str, Any]] = []

    # Aggregate emissions by category to focus on the biggest opportunities
    category_totals: Dict[str, float] = {}
    for act in activities:
        cat = act.get("category", "")
        category_totals[cat] = category_totals.get(cat, 0.0) + act.get("kg_co2e", 0.0)

    # 1. Electricity Tips (AC vs Fan)
    ac_activities = [
        a for a in activities
        if "ac" in a.get("details", "").lower() or "air conditioner" in a.get("details", "").lower()
    ]
    if ac_activities:
        # Saving from replacing 4 hours of AC with ceiling fan
        ac_kw = APPLIANCE_KW["ac"]
        fan_kw = APPLIANCE_KW["fan"]
        saving_ac = round(4.0 * (ac_kw - fan_kw) * ELECTRICITY_KG_PER_KWH, 3)
        tips.append({
            "category": "electricity",
            "tip": (
                f"Use a ceiling fan instead of AC for 4 hours (saves ~{saving_ac} kg CO2e; "
                f"AC draws 1.5 kW vs fan at 0.075 kW)."
            ),
            "saving_kg": saving_ac,
            "nature_impact": "Saves coal-fired power grid electricity, reduces power plant smog, and prevents urban heat buildup.",
        })

    # 2. Travel Tips (Motorized vs Metro / Bus / Cycle)
    travel_activities = [a for a in activities if a.get("category") == "travel"]
    for t in travel_activities:
        details = t.get("details", "").lower()
        if "car" in details or "petrol" in details:
            saving_metro = round(12.0 * (TRAVEL_KG_PER_KM["car_petrol"] - TRAVEL_KG_PER_KM["metro"]), 3)
            tips.append({
                "category": "travel",
                "tip": f"Switch a 12 km petrol car trip to the metro (saves ~{saving_metro} kg CO2e).",
                "saving_kg": saving_metro,
                "nature_impact": "Directly eliminates exhaust fumes and toxic street-level PM2.5 smog from city air.",
            })
            break
        elif "two_wheeler" in details or "bike" in details or "scooter" in details:
            saving_metro = round(10.0 * (TRAVEL_KG_PER_KM["two_wheeler"] - TRAVEL_KG_PER_KM["metro"]), 3)
            tips.append({
                "category": "travel",
                "tip": f"Take the electric metro or carpool instead of your two-wheeler (saves ~{saving_metro} kg CO2e over 10 km).",
                "saving_kg": saving_metro,
                "nature_impact": "Replaces petrol combustion with cleaner electric mass transit, reducing city smog and engine heat.",
            })
            break
        elif "bus" in details:
            saving_metro = round(12.0 * (TRAVEL_KG_PER_KM["bus"] - TRAVEL_KG_PER_KM["metro"]), 3)
            tips.append({
                "category": "travel",
                "tip": f"Take the metro instead of the bus for a 12 km commute (saves ~{saving_metro} kg CO2e).",
                "saving_kg": saving_metro,
                "nature_impact": "Reduces diesel engine exhaust on crowded city corridors.",
            })
            break

    # 3. Food Tips (Meat vs Vegetarian)
    food_activities = [a for a in activities if a.get("category") == "food"]
    has_mutton = any("mutton" in a.get("details", "").lower() for a in food_activities)
    has_chicken = any("chicken" in a.get("details", "").lower() or "biryani" in a.get("details", "").lower() for a in food_activities)
    has_beef = any("beef" in a.get("details", "").lower() for a in food_activities)

    if has_mutton:
        saving_mutton = round(FOOD_KG_PER_MEAL["mutton"] - FOOD_KG_PER_MEAL["vegetarian"], 3)
        tips.append({
            "category": "food",
            "tip": f"Swap one mutton meal for a rich vegetarian meal (saves ~{saving_mutton} kg CO2e).",
            "saving_kg": saving_mutton,
            "nature_impact": "Saves thousands of liters of freshwater and eliminates high ruminant enteric emissions.",
        })
    elif has_chicken:
        saving_chicken = round(FOOD_KG_PER_MEAL["chicken"] - FOOD_KG_PER_MEAL["vegetarian"], 3)
        tips.append({
            "category": "food",
            "tip": f"Swap one chicken meal for a delicious vegetarian or plant-based meal (saves ~{saving_chicken} kg CO2e).",
            "saving_kg": saving_chicken,
            "nature_impact": "Reduces intensive poultry feed grain demand and saves hundreds of liters of water per portion.",
        })
    elif has_beef:
        saving_beef = round(FOOD_KG_PER_MEAL["beef"] - FOOD_KG_PER_MEAL["vegetarian"], 3)
        tips.append({
            "category": "food",
            "tip": f"Swap one beef meal for a vegetarian meal (saves ~{saving_beef} kg CO2e).",
            "saving_kg": saving_beef,
            "nature_impact": "Significantly curbs agricultural land clearing and methane greenhouse gas emissions.",
        })

    # 4. Waste Tips (Landfill vs Composting / Recycling)
    waste_activities = [a for a in activities if a.get("category") == "waste"]
    if waste_activities:
        saving_waste = round(2.0 * (WASTE_KG_PER_KG["mixed_landfill"] - WASTE_KG_PER_KG["composted_food"]), 3)
        tips.append({
            "category": "waste",
            "tip": f"Segregate food waste for composting instead of mixed landfill disposal (saves ~{saving_waste} kg CO2e per 2 kg waste).",
            "saving_kg": saving_waste,
            "nature_impact": "Prevents toxic methane gas from forming in suffocating landfills and restores fertile soil naturally.",
        })

    # Baseline suggestions if tips list is short
    if len(tips) < 2:
        saving_chicken = round(FOOD_KG_PER_MEAL["chicken"] - FOOD_KG_PER_MEAL["vegetarian"], 3)
        tips.append({
            "category": "food",
            "tip": f"Adopt 'Meatless Mondays': swapping 1 chicken meal for a vegetarian meal saves {saving_chicken} kg CO2e.",
            "saving_kg": saving_chicken,
            "nature_impact": "Saves clean freshwater and lowers pressure on agricultural land.",
        })
        saving_cycle = round(3.0 * TRAVEL_KG_PER_KM["car_petrol"], 3)
        tips.append({
            "category": "travel",
            "tip": f"Walk or cycle for short neighborhood trips under 3 km (saves {saving_cycle} kg CO2e vs petrol car).",
            "saving_kg": saving_cycle,
            "nature_impact": "Creates zero emissions, purifies neighborhood air, and promotes healthy living.",
        })

    # Sort tips by saving_kg descending
    tips.sort(key=lambda x: x["saving_kg"], reverse=True)

    return {
        "status": "ok",
        "tips_count": len(tips),
        "tips": tips,
    }


# ============================================================================
# 8. CAMPUS LEADERBOARD (STRETCH FEATURE)
# ============================================================================
def register_group(group: str, tool_context: ToolContext) -> Dict[str, Any]:
    """Registers the current user's session with a campus group (hostel or department).

    Args:
        group: Name of the campus group (e.g. 'Hostel A', 'CS Department').
        tool_context: Runtime ADK tool context providing access to session state.

    Returns:
        Dict confirming registration.
    """
    clean_group = group.strip().title() if group else "General Campus"
    tool_context.state["campus_group"] = clean_group

    # Sync group statistics in shared in-memory store
    activities = tool_context.state.get("activities", [])
    total_kg = sum(a.get("kg_co2e", 0.0) for a in activities)

    if clean_group not in _CAMPUS_GROUPS:
        _CAMPUS_GROUPS[clean_group] = {"members": 1, "total_kg_co2e": total_kg}
    else:
        _CAMPUS_GROUPS[clean_group]["total_kg_co2e"] += total_kg

    return {
        "status": "ok",
        "group": clean_group,
        "message": f"Successfully enrolled in campus group '{clean_group}'.",
    }


def get_leaderboard() -> Dict[str, Any]:
    """Retrieves the campus group sustainability leaderboard.

    Returns:
        Dict with ranked campus groups by average emissions per member.
    """
    if not _CAMPUS_GROUPS:
        # Seeded demo groups if empty
        return {
            "status": "ok",
            "message": "Campus leaderboard active.",
            "rankings": [
                {"rank": 1, "group": "Hostel 3 (Green House)", "avg_daily_kg_co2e": 3.42, "status": "Leader"},
                {"rank": 2, "group": "Civil Engineering Dept", "avg_daily_kg_co2e": 4.15, "status": "Eco-Champion"},
                {"rank": 3, "group": "Computer Science Dept", "avg_daily_kg_co2e": 4.88, "status": "On Track"},
                {"rank": 4, "group": "Hostel 7", "avg_daily_kg_co2e": 5.92, "status": "Needs Reduction"},
            ],
        }

    ranked = sorted(
        [
            {
                "group": grp,
                "total_kg_co2e": round(data["total_kg_co2e"], 3),
                "members": data["members"],
                "avg_kg_co2e": round(data["total_kg_co2e"] / max(1, data["members"]), 3),
            }
            for grp, data in _CAMPUS_GROUPS.items()
        ],
        key=lambda x: x["avg_kg_co2e"],
    )

    for i, r in enumerate(ranked, 1):
        r["rank"] = i

    return {
        "status": "ok",
        "rankings": ranked,
    }
