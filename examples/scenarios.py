from __future__ import annotations

from typing import Callable
from pydantic import BaseModel, ConfigDict

from manager_agent_gym.schemas.domain.workflow import Workflow
from manager_agent_gym.schemas.preferences import (
    PreferenceSnapshot,
    PreferenceWeightUpdateRequest,
)
from manager_agent_gym.schemas.preferences.evaluator import Rubric

# Import scenario modules and adapt to a common interface
from examples.end_to_end_examples.icap import (
    create_workflow as create_icaap_workflow,
    create_preferences as create_icaap_preferences,
    create_team_timeline as create_icaap_team_timeline,
    create_preference_update_requests as icaap_update_requests,
    create_evaluator_to_measure_goal_achievement as icaap_goal_achievement,
)
from examples.end_to_end_examples.marketing_campaign import (
    create_workflow as create_marketing_workflow,
    create_marketing_preferences as create_marketing_preferences,
    create_team_timeline as create_marketing_team_timeline,
    create_preference_update_requests as marketing_update_requests,
    create_evaluator_to_measure_goal_achievement as marketing_goal_achievement,
)
from examples.end_to_end_examples.data_science_analytics import (
    create_workflow as create_ds_workflow,
    create_preferences as create_ds_preferences,
    create_team_timeline as create_ds_team_timeline,
    create_preference_update_requests as ds_update_requests,
    create_evaluator_to_measure_goal_achievement as ds_goal_achievement,
)
from examples.end_to_end_examples.orsa import (
    create_workflow as create_orsa_workflow,
    create_preferences as create_orsa_preferences,
    create_team_timeline as create_orsa_team_timeline,
    create_preference_update_requests as orsa_update_requests,
    create_evaluator_to_measure_goal_achievement as orsa_goal_achievement,
)
from examples.end_to_end_examples.legal_contract_negotiation import (
    create_workflow as create_contract_workflow,
    create_preferences as create_contract_preferences,
    create_team_timeline as create_contract_team_timeline,
    create_preference_update_requests as contract_update_requests,
    create_evaluator_to_measure_goal_achievement as contract_goal_achievement,
)
from examples.end_to_end_examples.supply_chain_planning import (
    create_workflow as create_supply_chain_workflow,
    create_preferences as create_supply_chain_preferences,
    create_team_timeline as create_supply_chain_team_timeline,
    create_preference_update_requests as supply_chain_update_requests,
    create_evaluator_to_measure_goal_achievement as supply_chain_goal_achievement,
)
from examples.end_to_end_examples.legal_litigation_ediscovery import (
    create_workflow as create_litigation_workflow,
    create_preferences as create_litigation_preferences,
    create_team_timeline as create_litigation_team_timeline,
    create_preference_update_requests as litigation_update_requests,
    create_evaluator_to_measure_goal_achievement as litigation_goal_achievement,
)
from examples.end_to_end_examples.legal_m_and_a import (
    create_workflow as create_ma_workflow,
    create_preferences as create_ma_preferences,
    create_team_timeline as create_ma_team_timeline,
    create_mna_preference_update_requests as ma_update_requests,
    create_evaluator_to_measure_goal_achievement as ma_goal_achievement,
)
from examples.end_to_end_examples.global_product_recall import (
    create_workflow as create_global_product_recall_workflow,
    create_preferences as create_global_product_recall_preferences,
    create_team_timeline as create_global_product_recall_team_timeline,
    create_preference_update_requests as gpr_update_requests,
    create_evaluator_to_measure_goal_achievement as gpr_goal_achievement,
)
from examples.end_to_end_examples.brand_crisis_management import (
    create_brand_crisis_management_workflow,
    create_brand_crisis_management_preferences,
    create_brand_crisis_management_team_timeline,
    create_preference_update_requests as bcm_update_requests,
    create_evaluator_to_measure_goal_achievement as bcm_goal_achievement,
)
from examples.end_to_end_examples.banking_license_application import (
    create_banking_license_application_workflow,
    create_banking_license_team_timeline,
    create_banking_license_preferences,
    create_preference_update_requests as bla_update_requests,
    create_evaluator_to_measure_goal_achievement as bla_goal_achievement,
)
from examples.end_to_end_examples.tech_company_acquisition import (
    create_tech_acquisition_integration_workflow,
    create_tech_acquisition_integration_preferences,
    create_preference_update_requests as tech_acq_update_requests,
    create_tech_acquisition_team_timeline,
    create_evaluator_to_measure_goal_achievement as tech_acq_goal_achievement,
)
from examples.end_to_end_examples.legal_global_data_breach import (
    create_workflow as create_global_breach_workflow,
    create_preferences as create_global_breach_preferences,
    create_team_timeline as create_global_breach_team_timeline,
    create_preference_update_requests as global_breach_update_requests,
    create_evaluator_to_measure_goal_achievement as global_breach_goal_achievement,
)
from examples.end_to_end_examples.enterprise_saas_negotiation_pipeline import (
    create_workflow as create_saas_msa_factory_workflow,
    create_preferences as create_saas_msa_factory_preferences,
    create_team_timeline as create_saas_msa_factory_team_timeline,
    create_preference_update_requests as saas_msa_factory_update_requests,
    create_evaluator_to_measure_goal_achievement as saas_msa_factory_goal_achievement,
)
from examples.end_to_end_examples.mnc_workforce_restructuring import (
    create_workflow as create_global_rif_workflow,
    create_preferences as create_global_rif_preferences,
    create_team_timeline as create_global_rif_team_timeline,
    create_preference_update_requests as global_rif_update_requests,
    create_evaluator_to_measure_goal_achievement as global_rif_goal_achievement,
)
from examples.end_to_end_examples.genai_feature_launch import (
    create_workflow as create_genai_workflow,
    create_preferences as create_genai_preferences,
    create_team_timeline as create_genai_team_timeline,
    create_preference_update_requests as genai_update_requests,
    create_evaluator_to_measure_goal_achievement as genai_goal_achievement,
)
from examples.end_to_end_examples.ipo_readiness_program import (
    create_workflow as create_ipo_workflow,
    create_preferences as create_ipo_preferences,
    create_team_timeline as create_ipo_team_timeline,
    create_preference_update_requests as ipo_update_requests,
    create_evaluator_to_measure_goal_achievement as ipo_goal_achievement,
)
from examples.end_to_end_examples.pharmaceutical_product_launch import (
    create_workflow as create_pharma_workflow,
    create_preferences as create_pharma_preferences,
    create_team_timeline as create_pharma_team_timeline,
    create_preference_update_requests as pharma_update_requests,
    create_evaluator_to_measure_goal_achievement as pharma_goal_achievement,
)
from examples.end_to_end_examples.uk_university_accreditation import (
    create_workflow as create_uk_uni_workflow,
    create_preferences as create_uk_uni_preferences,
    create_team_timeline as create_uk_uni_team_timeline,
    create_preference_update_requests as uk_uni_update_requests,
    create_evaluator_to_measure_goal_achievement as uk_uni_goal_achievement,
)
from examples.end_to_end_examples.airline_launch_program import (
    create_workflow as create_airline_workflow,
    create_preferences as create_airline_preferences,
    create_team_timeline as create_airline_team_timeline,
    create_preference_update_requests as airline_update_requests,
    create_evaluator_to_measure_goal_achievement as airline_goal_achievement,
)


class ScenarioSpec(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    create_workflow: Callable[[], Workflow]
    create_preferences: Callable[[], PreferenceSnapshot]
    create_team_timeline: Callable[[], dict[int, list]]
    create_preference_update_requests: (
        Callable[[], list[PreferenceWeightUpdateRequest]] | None
    ) = None
    create_evaluator_to_measure_goal_achievement: Callable[[], Rubric] | None = None


SCENARIOS: dict[str, ScenarioSpec] = {
    # ICAP
    "icaap": ScenarioSpec(
        create_workflow=create_icaap_workflow,
        create_preferences=create_icaap_preferences,
        create_team_timeline=create_icaap_team_timeline,
        create_preference_update_requests=icaap_update_requests,
        create_evaluator_to_measure_goal_achievement=icaap_goal_achievement,
    ),
    # Marketing campaign
    "marketing_campaign": ScenarioSpec(
        create_workflow=create_marketing_workflow,
        create_preferences=create_marketing_preferences,
        create_team_timeline=create_marketing_team_timeline,
        create_preference_update_requests=marketing_update_requests,
        create_evaluator_to_measure_goal_achievement=marketing_goal_achievement,
    ),
    # Data science
    "data_science_analytics": ScenarioSpec(
        create_workflow=create_ds_workflow,
        create_preferences=create_ds_preferences,
        create_team_timeline=create_ds_team_timeline,
        create_preference_update_requests=ds_update_requests,
        create_evaluator_to_measure_goal_achievement=ds_goal_achievement,
    ),
    # ORSA
    "orsa": ScenarioSpec(
        create_workflow=create_orsa_workflow,
        create_preferences=create_orsa_preferences,
        create_team_timeline=create_orsa_team_timeline,
        create_preference_update_requests=orsa_update_requests,
        create_evaluator_to_measure_goal_achievement=orsa_goal_achievement,
    ),
    # Legal contract negotiation
    "legal_contract_negotiation": ScenarioSpec(
        create_workflow=create_contract_workflow,
        create_preferences=create_contract_preferences,
        create_team_timeline=create_contract_team_timeline,
        create_preference_update_requests=contract_update_requests,
        create_evaluator_to_measure_goal_achievement=contract_goal_achievement,
    ),
    # Supply chain
    "supply_chain_planning": ScenarioSpec(
        create_workflow=create_supply_chain_workflow,
        create_preferences=create_supply_chain_preferences,
        create_team_timeline=create_supply_chain_team_timeline,
        create_preference_update_requests=supply_chain_update_requests,
        create_evaluator_to_measure_goal_achievement=supply_chain_goal_achievement,
    ),
    # Litigation e-discovery
    "legal_litigation_ediscovery": ScenarioSpec(
        create_workflow=create_litigation_workflow,
        create_preferences=create_litigation_preferences,
        create_team_timeline=create_litigation_team_timeline,
        create_preference_update_requests=litigation_update_requests,
        create_evaluator_to_measure_goal_achievement=litigation_goal_achievement,
    ),
    # Legal M&A
    "legal_m_and_a": ScenarioSpec(
        create_workflow=create_ma_workflow,
        create_preferences=create_ma_preferences,
        create_team_timeline=create_ma_team_timeline,
        create_preference_update_requests=ma_update_requests,
        create_evaluator_to_measure_goal_achievement=ma_goal_achievement,
    ),
    # Global product recall
    "global_product_recall": ScenarioSpec(
        create_workflow=create_global_product_recall_workflow,
        create_preferences=create_global_product_recall_preferences,
        create_team_timeline=create_global_product_recall_team_timeline,
        create_preference_update_requests=gpr_update_requests,
        create_evaluator_to_measure_goal_achievement=gpr_goal_achievement,
    ),
    # Brand crisis management
    "brand_crisis_management": ScenarioSpec(
        create_workflow=create_brand_crisis_management_workflow,
        create_preferences=create_brand_crisis_management_preferences,
        create_team_timeline=create_brand_crisis_management_team_timeline,
        create_preference_update_requests=bcm_update_requests,
        create_evaluator_to_measure_goal_achievement=bcm_goal_achievement,
    ),
    # Banking license application
    "banking_license_application": ScenarioSpec(
        create_workflow=create_banking_license_application_workflow,
        create_preferences=create_banking_license_preferences,
        create_team_timeline=create_banking_license_team_timeline,
        create_preference_update_requests=bla_update_requests,
        create_evaluator_to_measure_goal_achievement=bla_goal_achievement,
    ),
    # Tech company acquisition
    "tech_company_acquisition": ScenarioSpec(
        create_workflow=create_tech_acquisition_integration_workflow,
        create_preferences=create_tech_acquisition_integration_preferences,
        create_team_timeline=create_tech_acquisition_team_timeline,
        create_preference_update_requests=tech_acq_update_requests,
        create_evaluator_to_measure_goal_achievement=tech_acq_goal_achievement,
    ),
    # Global data breach
    "legal_global_data_breach": ScenarioSpec(
        create_workflow=create_global_breach_workflow,
        create_preferences=create_global_breach_preferences,
        create_team_timeline=create_global_breach_team_timeline,
        create_preference_update_requests=global_breach_update_requests,
        create_evaluator_to_measure_goal_achievement=global_breach_goal_achievement,
    ),
    # Enterprise SaaS MSA/SOW Negotiation Pipeline
    "enterprise_saas_negotiation_pipeline": ScenarioSpec(
        create_workflow=create_saas_msa_factory_workflow,
        create_preferences=create_saas_msa_factory_preferences,
        create_team_timeline=create_saas_msa_factory_team_timeline,
        create_preference_update_requests=saas_msa_factory_update_requests,
        create_evaluator_to_measure_goal_achievement=saas_msa_factory_goal_achievement,
    ),
    # MNC Workforce Restructuring
    "mnc_workforce_restructuring": ScenarioSpec(
        create_workflow=create_global_rif_workflow,
        create_preferences=create_global_rif_preferences,
        create_team_timeline=create_global_rif_team_timeline,
        create_preference_update_requests=global_rif_update_requests,
        create_evaluator_to_measure_goal_achievement=global_rif_goal_achievement,
    ),
    # Gen-AI Feature Launch
    "genai_feature_launch": ScenarioSpec(
        create_workflow=create_genai_workflow,
        create_preferences=create_genai_preferences,
        create_team_timeline=create_genai_team_timeline,
        create_preference_update_requests=genai_update_requests,
        create_evaluator_to_measure_goal_achievement=genai_goal_achievement,
    ),
    # IPO Readiness Program
    "ipo_readiness_program": ScenarioSpec(
        create_workflow=create_ipo_workflow,
        create_preferences=create_ipo_preferences,
        create_team_timeline=create_ipo_team_timeline,
        create_preference_update_requests=ipo_update_requests,
        create_evaluator_to_measure_goal_achievement=ipo_goal_achievement,
    ),
    # Pharmaceutical Product Launch
    "pharmaceutical_product_launch": ScenarioSpec(
        create_workflow=create_pharma_workflow,
        create_preferences=create_pharma_preferences,
        create_team_timeline=create_pharma_team_timeline,
        create_preference_update_requests=pharma_update_requests,
        create_evaluator_to_measure_goal_achievement=pharma_goal_achievement,
    ),
    # UK University Accreditation Renewal
    "uk_university_accreditation": ScenarioSpec(
        create_workflow=create_uk_uni_workflow,
        create_preferences=create_uk_uni_preferences,
        create_team_timeline=create_uk_uni_team_timeline,
        create_preference_update_requests=uk_uni_update_requests,
        create_evaluator_to_measure_goal_achievement=uk_uni_goal_achievement,
    ),
    # Airline Launch Program
    "airline_launch_program": ScenarioSpec(
        create_workflow=create_airline_workflow,
        create_preferences=create_airline_preferences,
        create_team_timeline=create_airline_team_timeline,
        create_preference_update_requests=airline_update_requests,
        create_evaluator_to_measure_goal_achievement=airline_goal_achievement,
    ),
}
