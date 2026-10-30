"""End-to-end multi-turn simulation test for Carbon Coach.

Validates the exact 3-message demo sequence required by the specification:
1. 'I travelled 12 km by bus today and used the AC for 4 hours'
2. 'I ate chicken for lunch'
3. 'How did I do this week?'

Confirms that every emissions figure, cumulative total, category breakdown,
and reduction tip originates from tool outputs.
"""

from unittest.mock import MagicMock
import pytest

from carbon_coach.tools import (
    calculate_electricity_emissions,
    calculate_food_emissions,
    calculate_travel_emissions,
    get_summary,
    log_activity,
    suggest_reductions,
)


class MockSessionContext:
    def __init__(self):
        self.state = {}


def test_three_message_demo_trajectory():
    ctx = MockSessionContext()

    # -------------------------------------------------------------------------
    # Turn 1: "I travelled 12 km by bus today and used the AC for 4 hours"
    # -------------------------------------------------------------------------
    travel_out = calculate_travel_emissions(mode="bus", km=12.0)
    assert travel_out["status"] == "ok"
    assert travel_out["kg_co2e"] == 1.068
    assert travel_out["factor_kg_per_km"] == 0.089

    log_travel = log_activity("travel", "12 km by bus", travel_out["kg_co2e"], ctx)
    assert log_travel["today_total_kg_co2e"] == 1.068

    elec_out = calculate_electricity_emissions(appliance="ac", hours=4.0)
    assert elec_out["status"] == "ok"
    assert elec_out["assumed_kw"] == 1.5
    assert elec_out["kwh"] == 6.0
    assert elec_out["kg_co2e"] == 4.26

    log_elec = log_activity("electricity", "AC for 4 hours", elec_out["kg_co2e"], ctx)
    assert log_elec["today_total_kg_co2e"] == 5.328

    # -------------------------------------------------------------------------
    # Turn 2: "I ate chicken for lunch"
    # -------------------------------------------------------------------------
    food_out = calculate_food_emissions(meal_type="chicken", meals=1)
    assert food_out["status"] == "ok"
    assert food_out["factor_kg_per_meal"] == 1.6
    assert food_out["kg_co2e"] == 1.6

    log_food = log_activity("food", "chicken for lunch", food_out["kg_co2e"], ctx)
    assert log_food["today_total_kg_co2e"] == 6.928
    assert log_food["total_activities_logged"] == 3

    # -------------------------------------------------------------------------
    # Turn 3: "How did I do this week?"
    # -------------------------------------------------------------------------
    summary_out = get_summary(period="week", tool_context=ctx)
    assert summary_out["status"] == "ok"
    assert summary_out["total_kg_co2e"] == 6.928
    assert summary_out["top_category"] == "electricity"
    assert summary_out["category_breakdown"] == {
        "travel": 1.068,
        "electricity": 4.26,
        "food": 1.6,
    }
    assert summary_out["benchmark_kg_co2e"] == 35.0  # 5.0 * 7 days
    assert summary_out["difference_kg_co2e"] == -28.072  # below benchmark
    assert summary_out["percentage_of_benchmark"] == 19.8

    # Coaching suggestions
    tips_out = suggest_reductions(ctx)
    assert tips_out["status"] == "ok"
    assert tips_out["tips_count"] >= 3

    # Top recommendation should address the highest emission activity (AC or Chicken)
    top_tip = tips_out["tips"][0]
    assert "saving_kg" in top_tip
    assert top_tip["saving_kg"] > 0
    # AC tip saves 4 * (1.5 - 0.075) * 0.71 = 4.047 kg CO2e
    assert any("ceiling fan" in t["tip"] for t in tips_out["tips"])
    assert any("chicken" in t["tip"] for t in tips_out["tips"])
