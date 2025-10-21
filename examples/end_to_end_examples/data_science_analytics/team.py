"""
Data Science Analytics Demo

Team timeline with specialized AI agents following project phases,
and late-phase human stakeholders for sign-offs.
"""

from manager_agent_gym.schemas.agents import (
    AIAgentConfig,
    HumanAgentConfig,
)


def create_team_configs():
    data_engineer = AIAgentConfig(
        agent_id="data_engineer",
        agent_type="ai",
        system_prompt=(
            "You are a Data Engineer focusing on ingestion pipelines, data quality checks, and lineage documentation. You are also responsible for the security of the data and the systems that process it."
        ),
        agent_description="Data Engineer",
        agent_capabilities=[
            "Ingestion pipelines",
            "Data quality checks",
            "Lineage documentation",
            "Data security",
        ],
    )
    data_scientist = AIAgentConfig(
        agent_id="data_scientist",
        agent_type="ai",
        system_prompt=(
            "You are a Data Scientist specializing in feature engineering, baseline modeling, and experimentation."
        ),
        agent_description="Data Scientist",
        agent_capabilities=[
            "Feature engineering",
            "Baseline modeling",
            "Experimentation",
        ],
    )
    mlops_engineer = AIAgentConfig(
        agent_id="mlops_engineer",
        agent_type="ai",
        system_prompt=(
            "You are an MLOps Engineer implementing reproducibility, CI/CD, packaging, and monitoring."
        ),
        agent_description="MLOps Engineer",
        agent_capabilities=["Reproducibility", "CI/CD", "Packaging", "Monitoring"],
    )
    analytics_analyst = AIAgentConfig(
        agent_id="analytics_analyst",
        agent_type="ai",
        system_prompt=(
            "You are an Analytics Analyst preparing KPI/ROI analysis and executive readouts."
        ),
        agent_description="Analytics Analyst",
        agent_capabilities=["KPI/ROI analysis", "Executive readouts"],
    )

    # Human roles for sign-offs
    security_reviewer = HumanAgentConfig(
        agent_id="security_reviewer",
        agent_type="human_mock",
        system_prompt="Security reviewer conducting dependency/secrets scans and deployment gate.",
        name="Security Reviewer",
        role="Security Review",
        experience_years=8,
        background="Security engineering",
        agent_description="Security Reviewer",
        agent_capabilities=["Dependency/secrets scans", "Deployment gate"],
    )
    risk_officer = HumanAgentConfig(
        agent_id="risk_officer",
        agent_type="human_mock",
        system_prompt="Risk officer reviewing fairness, explainability, and governance artifacts.",
        name="Risk Officer",
        role="Responsible AI Governance",
        experience_years=10,
        background="Risk and compliance",
        agent_description="Risk Officer",
        agent_capabilities=["Fairness", "Explainability", "Governance"],
    )

    return {
        "data_engineer": data_engineer,
        "data_scientist": data_scientist,
        "mlops_engineer": mlops_engineer,
        "analytics_analyst": analytics_analyst,
        "security_reviewer": security_reviewer,
        "risk_officer": risk_officer,
    }


def create_team_timeline() -> dict[int, list]:
    cfg = create_team_configs()
    return {
        0: [
            ("add", cfg["data_engineer"], "Ingestion & data quality"),
            ("add", cfg["data_scientist"], "Feature engineering & baseline"),
        ],
        10: [
            ("add", cfg["mlops_engineer"], "Reproducibility & experiment tracking"),
        ],
        20: [
            ("add", cfg["analytics_analyst"], "KPI analysis & readout drafting"),
        ],
        40: [
            ("add", cfg["risk_officer"], "RAI review: fairness & explainability"),
        ],
        50: [
            ("add", cfg["security_reviewer"], "Security review & deployment gate"),
        ],
    }
