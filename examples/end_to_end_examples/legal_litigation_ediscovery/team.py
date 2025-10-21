from manager_agent_gym.schemas.agents import (
    AIAgentConfig,
    HumanAgentConfig,
    StakeholderConfig,
)
from manager_agent_gym.schemas.preferences.preference import (
    PreferenceSnapshot,
    Preference,
)


def create_litigation_team_configs():
    ediscovery_engineer = AIAgentConfig(
        agent_id="ediscovery_engineer",
        agent_type="ai",
        system_prompt=(
            "You are an eDiscovery Engineer handling defensible collection, processing, and chain-of-custody."
        ),
        agent_description=(
            "Engineer who makes the evidence pipeline defensible end‑to‑end and audit‑ready under FRCP."
        ),
        agent_capabilities=[
            "Plans and executes forensic collection",
            "Implements processing and culling",
            "Maintains chain‑of‑custody tracking",
            "Documents tools, versions, and parameters",
        ],
    )
    review_analyst = AIAgentConfig(
        agent_id="review_analyst",
        agent_type="ai",
        system_prompt=(
            "You are a Review Analyst conducting ECA, seed selection, TAR training, and QC sampling."
        ),
        agent_description=(
            "Analyst who accelerates review with rigorous sampling, training, and quality control."
        ),
        agent_capabilities=[
            "Runs ECA and custodian/topic scoping",
            "Builds seed sets and trains TAR",
            "Performs QC sampling and metrics",
            "Produces defensibility memos",
        ],
    )
    production_specialist = AIAgentConfig(
        agent_id="production_specialist",
        agent_type="ai",
        system_prompt=(
            "You are a Production Specialist preparing Bates, load files, metadata, and redactions per protocol."
        ),
        agent_description=(
            "Specialist who ships clean, protocol‑compliant productions that opposing can ingest without issue."
        ),
        agent_capabilities=[
            "Prepares Bates and load files",
            "Validates metadata and redactions",
            "Runs privilege and confidentiality checks",
            "Tracks production logs and errata",
        ],
    )

    # Human roles for legal governance
    supervising_attorney = HumanAgentConfig(
        agent_id="supervising_attorney",
        agent_type="human_mock",
        system_prompt="Supervising attorney approving protocols and privilege decisions.",
        name="Supervising Attorney",
        role="Legal Oversight",
        experience_years=12,
        background="Litigation",
        agent_description=(
            "Lead attorney who ensures defensibility, privilege protection, and adherence to protocol."
        ),
        agent_capabilities=[
            "Approves protocols and workflows",
            "Resolves privilege and confidentiality",
            "Chairs QC/exception reviews",
            "Signs off on productions",
        ],
    )
    records_manager = HumanAgentConfig(
        agent_id="records_manager",
        agent_type="human_mock",
        system_prompt="Records manager ensuring legal holds are issued and tracked.",
        name="Records Manager",
        role="Legal Hold",
        experience_years=8,
        background="Records management",
        agent_description=(
            "Custodian coordinator who makes legal holds stick and evidence preservation traceable."
        ),
        agent_capabilities=[
            "Issues and tracks legal holds",
            "Monitors acknowledgments and releases",
            "Coordinates custodian communications",
            "Maintains preservation documentation",
        ],
    )

    stakeholder = StakeholderConfig(
        agent_id="lead_counsel",
        agent_type="stakeholder",
        system_prompt="Lead counsel prioritizing defensibility, confidentiality, and timely production.",
        model_name="o3",
        name="Lead Counsel",
        role="Executive Stakeholder",
        persona_description="Risk-aware, process-driven, with focus on FRCP compliance and privilege protection.",
        agent_description=(
            "Decision owner who balances speed against defensibility and signs off on disclosure risk."
        ),
        agent_capabilities=[
            "Sets defensibility and privilege guardrails",
            "Approves protocol and exception handling",
            "Arbitrates speed vs. risk trade‑offs",
            "Grants final production approvals",
        ],
        response_latency_steps_min=1,
        response_latency_steps_max=3,
        push_probability_per_timestep=0.1,
        suggestion_rate=0.4,
        clarification_reply_rate=0.9,
        strictness=0.7,
        verbosity=2,
        preference_data=PreferenceSnapshot(
            preferences=[
                Preference(name="quality", weight=0.3),
                Preference(name="compliance", weight=0.25),
                Preference(name="confidentiality", weight=0.15),
                Preference(name="speed", weight=0.15),
                Preference(name="cost", weight=0.15),
            ]
        ),
    )

    return {
        "ediscovery_engineer": ediscovery_engineer,
        "review_analyst": review_analyst,
        "production_specialist": production_specialist,
        "supervising_attorney": supervising_attorney,
        "records_manager": records_manager,
        "stakeholder": stakeholder,
    }


def create_litigation_team_timeline() -> dict[int, list]:
    cfg = create_litigation_team_configs()
    return {
        0: [
            ("add", cfg["records_manager"], "Issue legal hold & track acknowledgments"),
            ("add", cfg["ediscovery_engineer"], "Forensic collection & processing"),
        ],
        6: [
            ("add", cfg["review_analyst"], "ECA, seed sets, TAR & QC"),
        ],
        12: [
            ("add", cfg["production_specialist"], "Prepare productions per protocol"),
        ],
        14: [
            (
                "add",
                cfg["supervising_attorney"],
                "Approve protocols & privilege decisions",
            ),
        ],
    }
