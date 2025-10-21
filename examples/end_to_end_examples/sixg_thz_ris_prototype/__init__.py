# pyright: reportMissingTypeStubs=false, reportMissingImports=false
"""
6G THz + RIS Field Prototype Demo

Real-world use case: University-led consortium delivering a time-bounded research
prototype to empirically evaluate a reconfigurable intelligent surface (RIS)
assisted terahertz (THz) link (140–300 GHz) in an indoor testbed, including
hardware bring-up, channel sounding, beam training algorithms, and security
telemetry for adversarial resilience.

Demonstrates:
- Research sprint planning with tight milestones and acceptance criteria
- Hardware-software co-design across RF front-ends, baseband, and control SW
- Experiment design, reproducibility, and data management best practices
- Security-by-design with attack-surface instrumentation and red-team drills
"""

from .workflow import create_workflow
from .preferences import (
    create_preferences,
    create_preference_update_requests,
    create_evaluator_to_measure_goal_achievement,
)
from .team import create_team_timeline

__all__ = [
    "create_workflow",
    "create_preferences",
    "create_preference_update_requests",
    "create_evaluator_to_measure_goal_achievement",
    "create_team_timeline",
]
