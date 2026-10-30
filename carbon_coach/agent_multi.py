"""Multi-agent coordinator implementation for Carbon Coach.

Contains two specialized sub-agents orchestrated by a coordinator root_agent:
1. tracker_agent: Parses activities and executes calculate_* and log_activity.
2. coach_agent: Handles get_summary, suggest_reductions, and campus leaderboard.
"""

import os
from google.adk.agents import Agent

from .tools import (
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

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")

# ---------------------------------------------------------------------------
# 1. TRACKER SUB-AGENT
# Specializes in extracting activity parameters, executing pure calculations,
# and writing entries to the session state log.
# ---------------------------------------------------------------------------
TRACKER_INSTRUCTION = """You are the Activity Tracker for Carbon Coach.
Your sole job is to parse carbon-emitting activities, compute emissions using calculation tools, and log them into session memory.

CRITICAL RULES:
1. NEVER do arithmetic or guess emissions numbers. Always call calculate_travel_emissions, calculate_electricity_emissions, calculate_food_emissions, or calculate_waste_emissions.
2. If details are missing or ambiguous, ask a short clarifying question instead of guessing.
3. Immediately after every successful calculation, call log_activity with the category, details, and kg_co2e.
4. Report the activity emissions and the new today running total returned by log_activity.
5. If the user asks for summaries or coaching tips, hand off or defer to the coach.
"""

tracker_agent = Agent(
    name="tracker_agent",
    description="Calculates and logs carbon footprint activities (travel, electricity, food, waste).",
    model=GEMINI_MODEL,
    instruction=TRACKER_INSTRUCTION,
    tools=[
        calculate_travel_emissions,
        calculate_electricity_emissions,
        calculate_food_emissions,
        calculate_waste_emissions,
        log_activity,
    ],
)

# ---------------------------------------------------------------------------
# 2. COACH SUB-AGENT
# Specializes in progress summaries, benchmark comparisons, and personalized tips.
# ---------------------------------------------------------------------------
COACH_INSTRUCTION = """You are the Reduction Coach for Carbon Coach.
Your job is to provide friendly, motivating insights, progress summaries, benchmark comparisons, and actionable reduction tips.

CRITICAL RULES:
1. For queries like "how did I do", "this week's total", "summary", call get_summary.
2. For queries like "how can I improve", "give me tips", "how to reduce", call suggest_reductions.
3. NEVER make up savings or emission percentages. Only use numbers returned by get_summary or suggest_reductions.
4. For campus leaderboard inquiries, use get_leaderboard and register_group.
5. Keep your advice positive, non-judgmental, and practical for Indian students and families.
"""

coach_agent = Agent(
    name="coach_agent",
    description="Provides emissions summaries, benchmark comparisons, campus leaderboards, and personalized reduction tips.",
    model=GEMINI_MODEL,
    instruction=COACH_INSTRUCTION,
    tools=[
        get_summary,
        suggest_reductions,
        register_group,
        get_leaderboard,
    ],
)

# ---------------------------------------------------------------------------
# 3. COORDINATOR ROOT AGENT
# Orchestrates tracker_agent and coach_agent.
# ---------------------------------------------------------------------------
COORDINATOR_INSTRUCTION = """You are the Carbon Coach Coordinator.
You welcome the user and delegate requests to the appropriate specialist agent:
- For logging new activities (travel, electricity, food, waste), delegate to tracker_agent.
- For checking progress, summaries, benchmarks, campus leaderboards, or asking for reduction tips, delegate to coach_agent.
- If the user provides a greeting, welcome them warmly and briefly explain how you can help track and reduce their carbon footprint.
- Never state made-up emission numbers yourself.
"""

multi_root_agent = Agent(
    name="carbon_coach_coordinator",
    description="Coordinator for Carbon Coach multi-agent architecture.",
    model=GEMINI_MODEL,
    instruction=COORDINATOR_INSTRUCTION,
    sub_agents=[tracker_agent, coach_agent],
)
