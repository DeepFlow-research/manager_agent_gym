"""
Global Data Breach Incident Response — Teams
Compact roster (≈10 total including stakeholder), with longer paragraph personas and a timestep schedule.

Exports:
  - create_breach_team_configs()
  - create_breach_team_timeline()
"""

from manager_agent_gym.schemas.agents import (
    AIAgentConfig,
    HumanAgentConfig,
    StakeholderConfig,
)
from manager_agent_gym.schemas.preferences.preference import (
    PreferenceSnapshot,
    Preference,
)


# ---------------------------
# TEAM CONFIGS
# ---------------------------
def create_team_configs():
    """
    Create AI + human personas for global breach response.
    Personas are written as longer paragraphs for clarity and realism.
    """
    # ===== AI Agents (4) =====
    forensic_triage_ai = AIAgentConfig(
        agent_id="forensic_triage_ai",
        agent_type="ai",
        system_prompt=(
            "You are a forensic triage analyst embedded under legal privilege. You guide secure evidence collection "
            "and immediate containment hygiene: snapshotting systems, isolating accounts, and capturing volatile data "
            "without contaminating artifacts. You maintain a chain‑of‑custody ledger and continuously note threats to "
            "evidentiary integrity, flagging any action that could risk spoliation. You write in precise, time‑stamped, "
            "audit‑ready bulletins that legal can drop directly into the privileged record."
        ),
        agent_description=(
            "First‑hour responder that preserves evidence while stopping harm, writing audit‑ready notes under privilege."
        ),
        agent_capabilities=[
            "Guides secure evidence collection",
            "Maintains chain‑of‑custody ledger",
            "Flags spoliation risk and hygiene",
            "Produces time‑stamped incident bulletins",
        ],
    )

    regulatory_matrix_ai = AIAgentConfig(
        agent_id="regulatory_matrix_ai",
        agent_type="ai",
        system_prompt=(
            "You construct the jurisdictional obligations matrix. Starting from data classification and residency mapping, "
            "you identify notification triggers, timelines (e.g., GDPR 72‑hour to DPAs), sector overlays (HIPAA/GLBA), "
            "and contractual notice clauses. You produce side‑by‑side requirements and draft checklists for each audience "
            "(regulators, individuals, partners). You also track timing SLA clocks and surface risks of late or premature notices."
        ),
        agent_description=(
            "Obligations cartographer who turns data classification and residency into a concrete notification plan."
        ),
        agent_capabilities=[
            "Maps jurisdictional triggers/timelines",
            "Builds regulator/individual/partner checklists",
            "Tracks SLA clocks and late‑notice risk",
            "Aligns with counsel on strategy",
        ],
    )

    comms_drafter_ai = AIAgentConfig(
        agent_id="comms_drafter_ai",
        agent_type="ai",
        system_prompt=(
            "You draft regulator submissions, customer and partner notices, internal FAQs, and media holding statements. "
            "You reconcile known facts and uncertainty bands, avoid admissions that are not supported by evidence, and align "
            "tone across audiences. You keep templates jurisdiction‑specific and ensure counsel can approve with minimal edits."
        ),
        agent_description=(
            "Clear communicator who reconciles facts and uncertainty into consistent, approvable notices."
        ),
        agent_capabilities=[
            "Drafts regulator and customer notices",
            "Maintains consistent multi‑audience tone",
            "Coordinates approvals with Legal/Comms",
            "Keeps templates jurisdiction‑specific",
        ],
    )

    timeline_reconstructor_ai = AIAgentConfig(
        agent_id="timeline_reconstructor_ai",
        agent_type="ai",
        system_prompt=(
            "You reconstruct the incident timeline. You ingest logs, EDR telemetry, ticket trails, and interview notes to "
            "derive first/last known bad, dwell time, lateral movement, and exfil indicators. You produce a living chronology "
            "that legal, security, and comms can reference for consistent messaging and decision‑making."
        ),
        agent_description=(
            "Chronologist who derives first/last bad, dwell time, and movement from messy telemetry and notes."
        ),
        agent_capabilities=[
            "Ingests logs/EDR/tickets/interviews",
            "Builds living incident chronology",
            "Identifies exfil indicators and gaps",
            "Keeps teams aligned on the facts",
        ],
    )

    # ===== Human Mock Agents (5) =====
    incident_commander_legal = HumanAgentConfig(
        agent_id="incident_commander_legal",
        agent_type="human_mock",
        system_prompt=(
            "Incident Commander (Legal). You run the response under privilege, establish objectives and cadence, and arbitrate "
            "trade‑offs among speed, completeness, and regulatory risk. You ensure legal holds are issued, evidence is preserved, "
            "and notification determinations are defensible. You coordinate with Security, Privacy, Comms, and the Board, "
            "and you author the privileged final report."
        ),
        name="Incident Commander (Legal)",
        role="Lead Counsel",
        experience_years=14,
        background="Privacy/security counsel; incident response & investigations",
        agent_description=(
            "Legal IC who runs the incident under privilege, keeping speed, accuracy, and defensibility in balance."
        ),
        agent_capabilities=[
            "Sets objectives and cadence",
            "Issues legal holds; preserves evidence",
            "Arbitrates speed vs regulatory risk",
            "Authors privileged final report",
        ],
    )

    privacy_counsel_global = HumanAgentConfig(
        agent_id="privacy_counsel_global",
        agent_type="human_mock",
        system_prompt=(
            "Global Privacy Counsel. You interpret data‑protection obligations across jurisdictions and align regulator "
            "engagement strategy. You review every external notice, check data subject rights and remedies language, and guide "
            "DPIA/ROPA updates post‑incident. You partner closely with the Regulatory Matrix AI and outside counsel as needed."
        ),
        name="Global Privacy Counsel",
        role="Privacy Legal",
        experience_years=12,
        background="Global privacy law; breach notification; DPIA/ROPA governance",
        agent_description=(
            "Global privacy counsel who harmonizes cross‑border obligations and keeps notices defensible."
        ),
        agent_capabilities=[
            "Interprets DP obligations across regions",
            "Reviews external notices for compliance",
            "Guides DPIA/ROPA updates",
            "Coordinates with regulators/outside counsel",
        ],
    )

    security_forensics_lead = HumanAgentConfig(
        agent_id="security_forensics_lead",
        agent_type="human_mock",
        system_prompt=(
            "Security Forensics Lead. You direct technical investigation and containment—vector hypothesis testing, "
            "credential/secret rotations, patch/hardening, and persistence hunts. You balance eradication speed with "
            "evidence preservation and maintain close sync with Legal to avoid spoliation or premature system changes."
        ),
        name="Security Forensics Lead",
        role="Security/IR",
        experience_years=13,
        background="Digital forensics & incident response; threat detection engineering",
        agent_description=(
            "Forensics leader who balances rapid containment with evidentiary integrity."
        ),
        agent_capabilities=[
            "Directs investigation and containment",
            "Coordinates rotations/patching/hardening",
            "Hunts persistence and lateral movement",
            "Aligns actions with Legal to avoid spoliation",
        ],
    )

    communications_lead = HumanAgentConfig(
        agent_id="communications_lead",
        agent_type="human_mock",
        system_prompt=(
            "Communications Lead. You own stakeholder communications: regulator filings (with counsel), customer/partner notices, "
            "employee comms, and press strategy. You ensure consistent facts across channels, prepare spokespeople with Q&A, "
            "and monitor feedback to adjust messaging quickly without compromising legal positions."
        ),
        name="Communications Lead",
        role="External & Internal Comms",
        experience_years=15,
        background="Crisis communications; regulated industries",
        agent_description=(
            "Comms lead who keeps facts consistent across channels and prepares spokespeople under scrutiny."
        ),
        agent_capabilities=[
            "Owns internal/external messaging",
            "Preps Q&A and spokespersons",
            "Monitors feedback and adjusts",
            "Aligns filings with Legal/PR",
        ],
    )

    vendor_risk_manager = HumanAgentConfig(
        agent_id="vendor_risk_manager",
        agent_type="human_mock",
        system_prompt=(
            "Vendor Risk Manager. You coordinate with processors/sub‑processors implicated by the incident, validate their "
            "investigation and remediation updates, and reconcile contract notice obligations and SLAs. You maintain a vendor "
            "evidence dossier and ensure downstream issues are captured in the master timeline and obligations tracker."
        ),
        name="Vendor Risk Manager",
        role="Third‑Party Risk",
        experience_years=10,
        background="Vendor management; security questionnaires; contract SLAs",
        agent_description=(
            "Third‑party risk owner who drives processor updates and reconciles contract SLAs and notices."
        ),
        agent_capabilities=[
            "Engages processors/sub‑processors",
            "Validates investigation/remediation",
            "Tracks SLAs and obligations",
            "Maintains vendor evidence dossier",
        ],
    )

    # ===== Stakeholder (1) =====
    gc_stakeholder = StakeholderConfig(
        agent_id="gc_stakeholder",
        agent_type="stakeholder",
        system_prompt=(
            "You are the General Counsel. In the first 24–72 hours you prioritize speed to get facts and stop harm, while "
            "avoiding premature or inaccurate statements. As the picture clarifies, you emphasize regulatory compliance and "
            "consistency across jurisdictions. Toward closure, you prioritize documentation quality and lessons learned."
        ),
        model_name="o3",
        name="General Counsel (Stakeholder)",
        role="Executive Stakeholder",
        persona_description="Risk‑aware, evidence‑driven, concise. Prefers crisp updates with clear asks/decisions.",
        agent_description=(
            "General Counsel who sets risk appetite, pushes for speed with accuracy, and approves closure."
        ),
        agent_capabilities=[
            "Sets decision thresholds and posture",
            "Approves notification strategy",
            "Demands consistent facts across channels",
            "Signs off on lessons‑learned and fixes",
        ],
        response_latency_steps_min=1,
        response_latency_steps_max=3,
        push_probability_per_timestep=0.12,
        suggestion_rate=0.55,
        clarification_reply_rate=0.9,
        strictness=0.7,
        verbosity=2,
        preference_data=PreferenceSnapshot(
            preferences=[
                Preference(name="speed", weight=0.5),
                Preference(name="compliance", weight=0.3),
                Preference(name="quality", weight=0.2),
            ]
        ),
    )

    return {
        # AI
        "forensic_triage_ai": forensic_triage_ai,
        "regulatory_matrix_ai": regulatory_matrix_ai,
        "comms_drafter_ai": comms_drafter_ai,
        "timeline_reconstructor_ai": timeline_reconstructor_ai,
        # Human
        "incident_commander_legal": incident_commander_legal,
        "privacy_counsel_global": privacy_counsel_global,
        "security_forensics_lead": security_forensics_lead,
        "communications_lead": communications_lead,
        "vendor_risk_manager": vendor_risk_manager,
        # Stakeholder
        "gc_stakeholder": gc_stakeholder,
    }


# ---------------------------
# TEAM TIMELINE
# ---------------------------
def create_team_timeline():
    """
    Timestep → [(action, agent_cfg, rationale)]
    Actions: "add" or "remove".
    """
    cfg = create_team_configs()
    return {
        # Phase 1: Detection, triage, preservation
        0: [
            (
                "add",
                cfg["incident_commander_legal"],
                "Open under privilege; establish cadence; issue legal holds",
            ),
            (
                "add",
                cfg["security_forensics_lead"],
                "Kick off secure triage and initial containment hygiene",
            ),
            (
                "add",
                cfg["forensic_triage_ai"],
                "Guide evidentiary snapshots; maintain chain‑of‑custody ledger",
            ),
            ("add", cfg["gc_stakeholder"], "Set risk posture and decision thresholds"),
        ],
        4: [
            (
                "add",
                cfg["timeline_reconstructor_ai"],
                "Build living chronology from logs and notes",
            ),
            (
                "add",
                cfg["privacy_counsel_global"],
                "Begin jurisdictional analysis; align on facts framing",
            ),
        ],
        # Phase 2: Scoping, data mapping, obligations
        8: [
            (
                "add",
                cfg["regulatory_matrix_ai"],
                "Construct obligations matrix and notification timers",
            ),
            (
                "add",
                cfg["vendor_risk_manager"],
                "Engage implicated processors/sub‑processors and track SLAs",
            ),
        ],
        12: [
            (
                "add",
                cfg["comms_drafter_ai"],
                "Draft regulator and customer/partner notices; internal FAQs",
            ),
        ],
        # Phase 3: Containment, comms, notifications
        16: [
            (
                "add",
                cfg["communications_lead"],
                "Coordinate filings and external messaging with counsel",
            ),
        ],
        20: [
            (
                "remove",
                cfg["forensic_triage_ai"],
                "Evidence collection stabilized; handoff to forensics lead",
            ),
        ],
        24: [
            (
                "remove",
                cfg["timeline_reconstructor_ai"],
                "Timeline stable; minor updates via IC Legal",
            ),
        ],
        # Phase 4: Documentation & closure
        28: [
            (
                "remove",
                cfg["regulatory_matrix_ai"],
                "Obligations executed; residual tracking remains in legal",
            ),
            (
                "add",
                cfg["privacy_counsel_global"],
                "Finalize recordkeeping/DPIA/ROPA updates and lessons learned",
            ),
        ],
        32: [
            ("remove", cfg["comms_drafter_ai"], "Notices sent; PR steady‑state"),
            (
                "add",
                cfg["gc_stakeholder"],
                "Review final report and board brief; close out",
            ),
        ],
    }
