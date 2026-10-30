"""Unit tests for Carbon Coach tool functions.

Tests pure calculations, input validations, error handling, session state logging,
summary generation, and reduction suggestions without requiring an LLM.
"""

import datetime
from unittest.mock import MagicMock
import pytest

from carbon_coach.factors import (
    APPLIANCE_KW,
    DAILY_BENCHMARK_KG,
    ELECTRICITY_KG_PER_KWH,
    FOOD_KG_PER_MEAL,
    TRAVEL_KG_PER_KM,
    WASTE_KG_PER_KG,
)
from carbon_coach.tools import (
    calculate_electricity_emissions,
    calculate_food_emissions,
    calculate_travel_emissions,
    calculate_waste_emissions,
    get_leaderboard,
    get_summary,
    log_activity,
    register_group,
    suggest_reductions,
)


class MockToolContext:
    """Mock ADK ToolContext providing a dictionary state."""

    def __init__(self, initial_state=None):
        self.state = initial_state if initial_state is not None else {}


# ============================================================================
# TRAVEL EMISSIONS TESTS
# ============================================================================
def test_travel_emissions_bus():
    # 12 km by bus: 12 * 0.089 = 1.068
    res = calculate_travel_emissions(mode="bus", km=12.0)
    assert res["status"] == "ok"
    assert res["mode"] == "bus"
    assert res["km"] == 12.0
    assert res["kg_co2e"] == 1.068
    assert res["factor_kg_per_km"] == TRAVEL_KG_PER_KM["bus"]


def test_travel_emissions_synonyms_and_zero():
    # Walk and cycle have 0 emissions
    res_walk = calculate_travel_emissions(mode="walk", km=5.0)
    assert res_walk["status"] == "ok"
    assert res_walk["kg_co2e"] == 0.0

    res_cycle = calculate_travel_emissions(mode="bicycle", km=8.0)
    assert res_cycle["status"] == "ok"
    assert res_cycle["mode"] == "cycle"
    assert res_cycle["kg_co2e"] == 0.0


def test_travel_emissions_unknown_mode():
    res = calculate_travel_emissions(mode="helicopter", km=50.0)
    assert res["status"] == "error"
    assert "Unknown travel mode 'helicopter'" in res["message"]
    assert "bus" in res["message"]


def test_travel_emissions_invalid_distance():
    res_zero = calculate_travel_emissions(mode="bus", km=0)
    assert res_zero["status"] == "error"
    res_neg = calculate_travel_emissions(mode="bus", km=-10)
    assert res_neg["status"] == "error"


# ============================================================================
# ELECTRICITY EMISSIONS TESTS
# ============================================================================
def test_electricity_emissions_direct_kwh():
    res = calculate_electricity_emissions(kwh=10.0)
    assert res["status"] == "ok"
    assert res["kwh"] == 10.0
    assert res["kg_co2e"] == round(10.0 * ELECTRICITY_KG_PER_KWH, 3)
    assert "assumption" in res


def test_electricity_emissions_appliance_ac():
    # AC: 1.5 kW for 4 hours = 6.0 kWh * 0.71 = 4.26 kg CO2e
    res = calculate_electricity_emissions(appliance="ac", hours=4.0)
    assert res["status"] == "ok"
    assert res["appliance"] == "ac"
    assert res["hours"] == 4.0
    assert res["assumed_kw"] == 1.5
    assert res["kwh"] == 6.0
    assert res["kg_co2e"] == 4.26
    assert "1.5 kW" in res["assumption"]


def test_electricity_emissions_unknown_appliance():
    res = calculate_electricity_emissions(appliance="spaceship", hours=2.0)
    assert res["status"] == "error"
    assert "Unknown appliance 'spaceship'" in res["message"]
    assert "ac" in res["message"]


def test_electricity_emissions_missing_and_invalid_args():
    res_empty = calculate_electricity_emissions()
    assert res_empty["status"] == "error"
    res_neg_hours = calculate_electricity_emissions(appliance="fan", hours=-2.0)
    assert res_neg_hours["status"] == "error"
    res_neg_kwh = calculate_electricity_emissions(kwh=-5.0)
    assert res_neg_kwh["status"] == "error"


# ============================================================================
# FOOD EMISSIONS TESTS
# ============================================================================
def test_food_emissions_chicken():
    res = calculate_food_emissions(meal_type="chicken", meals=1)
    assert res["status"] == "ok"
    assert res["meal_type"] == "chicken"
    assert res["meals"] == 1
    assert res["kg_co2e"] == 1.6


def test_food_emissions_multiple_meals():
    # 2 mutton meals: 2 * 5.0 = 10.0
    res = calculate_food_emissions(meal_type="mutton", meals=2)
    assert res["status"] == "ok"
    assert res["kg_co2e"] == 10.0


def test_food_emissions_unknown_and_invalid():
    res_unk = calculate_food_emissions(meal_type="alien_curry", meals=1)
    assert res_unk["status"] == "error"
    assert "Unknown meal type" in res_unk["message"]

    res_zero = calculate_food_emissions(meal_type="vegetarian", meals=0)
    assert res_zero["status"] == "error"


# ============================================================================
# WASTE EMISSIONS TESTS
# ============================================================================
def test_waste_emissions_landfill_and_compost():
    res_landfill = calculate_waste_emissions(waste_type="mixed_landfill", kg=2.0)
    assert res_landfill["status"] == "ok"
    assert res_landfill["kg_co2e"] == 0.9  # 2.0 * 0.45

    res_compost = calculate_waste_emissions(waste_type="composted_food", kg=4.0)
    assert res_compost["status"] == "ok"
    assert res_compost["kg_co2e"] == 0.2  # 4.0 * 0.05


def test_waste_emissions_unknown_and_invalid():
    res_unk = calculate_waste_emissions(waste_type="radioactive", kg=1.0)
    assert res_unk["status"] == "error"
    res_neg = calculate_waste_emissions(waste_type="mixed_landfill", kg=-1.0)
    assert res_neg["status"] == "error"


# ============================================================================
# MEMORY & LOGGING TESTS
# ============================================================================
def test_log_activity_state_persistence():
    ctx = MockToolContext()
    today_iso = datetime.date.today().isoformat()

    # Log first activity
    res1 = log_activity("travel", "12 km by bus", 1.068, ctx)
    assert res1["status"] == "ok"
    assert res1["today_total_kg_co2e"] == 1.068
    assert res1["total_activities_logged"] == 1

    # Log second activity on same day
    res2 = log_activity("electricity", "AC for 4 hours", 4.26, ctx)
    assert res2["status"] == "ok"
    assert res2["today_total_kg_co2e"] == 5.328
    assert res2["total_activities_logged"] == 2

    # Check internal state list
    assert len(ctx.state["activities"]) == 2
    assert ctx.state["activities"][0]["date"] == today_iso


def test_log_activity_date_override():
    ctx = MockToolContext()
    past_date = "2026-10-25"
    res = log_activity("food", "Chicken biryani", 1.6, ctx, date=past_date)
    assert res["status"] == "ok"
    assert res["logged_activity"]["date"] == past_date
    assert res["today_total_kg_co2e"] == 0.0  # past date doesn't count in today's total


# ============================================================================
# GET SUMMARY TESTS
# ============================================================================
def test_get_summary_empty():
    ctx = MockToolContext()
    res = get_summary(period="today", tool_context=ctx)
    assert res["status"] == "ok"
    assert res["total_kg_co2e"] == 0.0
    assert res["top_category"] is None


def test_get_summary_today_and_week():
    ctx = MockToolContext()
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    ten_days_ago = today - datetime.timedelta(days=10)

    # Seed activities
    log_activity("travel", "Bus commute", 1.068, ctx, date=today.isoformat())
    log_activity("electricity", "AC use", 4.26, ctx, date=today.isoformat())
    log_activity("food", "Chicken dinner", 1.6, ctx, date=yesterday.isoformat())
    log_activity("travel", "Long roadtrip", 20.0, ctx, date=ten_days_ago.isoformat())

    # Today summary
    res_today = get_summary("today", ctx)
    assert res_today["status"] == "ok"
    assert res_today["total_kg_co2e"] == 5.328
    assert res_today["top_category"] == "electricity"
    assert res_today["benchmark_kg_co2e"] == DAILY_BENCHMARK_KG

    # Week summary (should include today + yesterday, exclude 10 days ago)
    res_week = get_summary("week", ctx)
    assert res_week["status"] == "ok"
    assert res_week["total_kg_co2e"] == round(1.068 + 4.26 + 1.6, 3)
    assert res_week["benchmark_kg_co2e"] == round(DAILY_BENCHMARK_KG * 7, 3)
    assert "food" in res_week["category_breakdown"]
    assert "electricity" in res_week["category_breakdown"]


# ============================================================================
# SUGGEST REDUCTIONS TESTS
# ============================================================================
def test_suggest_reductions_empty_log():
    ctx = MockToolContext()
    res = suggest_reductions(ctx)
    assert res["status"] == "error"
    assert "No activities logged yet" in res["message"]


def test_suggest_reductions_with_ac_and_chicken():
    ctx = MockToolContext()
    log_activity("electricity", "AC for 4 hours", 4.26, ctx)
    log_activity("food", "Chicken biryani lunch", 1.6, ctx)

    res = suggest_reductions(ctx)
    assert res["status"] == "ok"
    assert res["tips_count"] > 0
    # Tips should have tip text and positive saving_kg
    for tip in res["tips"]:
        assert "saving_kg" in tip
        assert tip["saving_kg"] > 0
        assert "tip" in tip

    # Tips should be ranked descending by saving_kg
    savings = [t["saving_kg"] for t in res["tips"]]
    assert savings == sorted(savings, reverse=True)


# ============================================================================
# CAMPUS LEADERBOARD TESTS
# ============================================================================
def test_campus_leaderboard():
    ctx = MockToolContext()
    log_activity("travel", "Metro trip", 0.36, ctx)
    reg_res = register_group("Hostel 4", ctx)
    assert reg_res["status"] == "ok"
    assert reg_res["group"] == "Hostel 4"

    board = get_leaderboard()
    assert board["status"] == "ok"
    assert len(board["rankings"]) > 0
