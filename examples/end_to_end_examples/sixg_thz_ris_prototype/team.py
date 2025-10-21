from manager_agent_gym.schemas.agents import AIAgentConfig, HumanAgentConfig


def create_team_configs():
    thz_rf_engineer = AIAgentConfig(
        agent_id="thz_rf_engineer",
        agent_type="ai",
        system_prompt=(
            "You are a THz RF engineer focusing on front-end bring-up, calibration, and link budget validation."
        ),
        agent_description="THz RF Engineer",
        agent_capabilities=[
            "RF front-end bring-up",
            "Calibration routines",
            "Link budget validation",
        ],
    )

    ris_firmware_dev = AIAgentConfig(
        agent_id="ris_firmware_dev",
        agent_type="ai",
        system_prompt=(
            "You develop RIS control firmware/APIs for phase configuration, timing, and host integration."
        ),
        agent_description="RIS Firmware Developer",
        agent_capabilities=[
            "RIS control APIs",
            "Timing and synchronization",
            "Host integration",
        ],
    )

    beam_algorithms_researcher = AIAgentConfig(
        agent_id="beam_algorithms_researcher",
        agent_type="ai",
        system_prompt=(
            "You implement beam training algorithms (hierarchical/compressive) and evaluate convergence and stability."
        ),
        agent_description="Beam Algorithms Researcher",
        agent_capabilities=[
            "Beam training",
            "Algorithm evaluation",
            "Signal processing",
        ],
    )

    phy_mac_integration_engineer = AIAgentConfig(
        agent_id="phy_mac_integration_engineer",
        agent_type="ai",
        system_prompt=(
            "You integrate PHY, MAC scheduling, and RIS control into a stable prototype for the NLOS demo."
        ),
        agent_description="PHY/MAC Integration Engineer",
        agent_capabilities=[
            "PHY/MAC integration",
            "Scheduling",
            "System stability",
        ],
    )

    security_analyst = AIAgentConfig(
        agent_id="security_analyst",
        agent_type="ai",
        system_prompt=(
            "You design threat models, instrument telemetry for jamming/spoofing, and run adversarial drills."
        ),
        agent_description="Security Analyst",
        agent_capabilities=[
            "Threat modeling",
            "Security telemetry",
            "Adversarial drills",
        ],
    )

    data_engineer = AIAgentConfig(
        agent_id="data_engineer",
        agent_type="ai",
        system_prompt=(
            "You build channel sounding pipelines, manage metadata, and ensure dataset/reproducibility packaging."
        ),
        agent_description="Data Engineer",
        agent_capabilities=[
            "Channel sounding",
            "Metadata management",
            "Reproducibility packaging",
        ],
    )

    project_lead = AIAgentConfig(
        agent_id="project_lead",
        agent_type="ai",
        system_prompt=(
            "You coordinate milestones, dependencies, and stakeholder communication to hit the deadline."
        ),
        agent_description="Project Lead",
        agent_capabilities=[
            "Milestone coordination",
            "Dependency management",
            "Stakeholder communication",
        ],
    )

    lab_safety_officer = HumanAgentConfig(
        agent_id="lab_safety_officer",
        agent_type="human_mock",
        system_prompt=(
            "Lab Safety Officer reviewing indoor spectrum/EIRP plans, safety signage, and ethics approvals."
        ),
        name="Lab Safety Officer",
        role="Safety & Compliance",
        experience_years=10,
        background="RF safety and research compliance",
        agent_description="Lab Safety Officer",
        agent_capabilities=[
            "Review EIRP and indoor compliance",
            "Safety/ethics approvals",
        ],
    )

    red_team_lead = HumanAgentConfig(
        agent_id="red_team_lead",
        agent_type="human_mock",
        system_prompt=(
            "Red team lead designing and executing controlled jamming/spoofing drills for the prototype demo."
        ),
        name="Red Team Lead",
        role="Security",
        experience_years=8,
        background="Wireless security",
        agent_description="Red Team Lead",
        agent_capabilities=[
            "Design adversarial drills",
            "Execute controlled tests",
        ],
    )

    return {
        "thz_rf_engineer": thz_rf_engineer,
        "ris_firmware_dev": ris_firmware_dev,
        "beam_algorithms_researcher": beam_algorithms_researcher,
        "phy_mac_integration_engineer": phy_mac_integration_engineer,
        "security_analyst": security_analyst,
        "data_engineer": data_engineer,
        "project_lead": project_lead,
        "lab_safety_officer": lab_safety_officer,
        "red_team_lead": red_team_lead,
    }


def create_team_timeline():
    cfg = create_team_configs()
    return {
        0: [
            ("add", cfg["project_lead"], "Kickoff, dependencies, and timeline"),
            ("add", cfg["thz_rf_engineer"], "RF bring-up planning"),
            ("add", cfg["lab_safety_officer"], "Indoor compliance & safety review"),
        ],
        5: [
            ("add", cfg["ris_firmware_dev"], "RIS control plane development"),
        ],
        10: [
            ("add", cfg["beam_algorithms_researcher"], "Beam training implementation"),
        ],
        15: [
            ("add", cfg["phy_mac_integration_engineer"], "PHY/MAC integration"),
        ],
        20: [
            ("add", cfg["data_engineer"], "Channel sounding campaign"),
            ("add", cfg["security_analyst"], "Security telemetry & drill planning"),
        ],
        25: [
            ("add", cfg["red_team_lead"], "Execute adversarial drill"),
        ],
    }
