"""
Scoring Agent Package

Import what you need:
  from agents.scoring.xai import SHAPExplainer
  from agents.scoring.fairness import FairnessAuditor
  from agents.scoring.agent import ScoringAgent
  from agents.scoring.tools import SCORING_TOOLS

XAI and Fairness modules have no heavy dependencies.
ScoringAgent requires langgraph.
"""

# Avoid early imports - let users import explicitly from submodules
# This prevents dependency errors if langgraph isn't installed yet
