"""
💬 Basic Agent Communication & Coordination

This example demonstrates how agents communicate and coordinate within workflows:
1. Creating multiple agents (AI and simulated human)
2. Setting up the communication system
3. Showing agents sending direct messages and broadcasts
4. Demonstrating message history and thread organization
5. Observing coordination patterns during task execution

This showcases the foundation for multi-agent collaboration!
"""

from examples.common_stakeholders import create_stakeholder_agent
import asyncio
from manager_agent_gym import (
    WorkflowExecutionEngine,
    ChainOfThoughtManagerAgent,
    AgentRegistry,
    CommunicationService,
    PreferenceWeights,
    Preference,
)
from manager_agent_gym.schemas.preferences.evaluator import (
    Evaluator,
    AggregationStrategy,
)
from manager_agent_gym.schemas.workflow_agents import AIAgentConfig, HumanAgentConfig
from manager_agent_gym.schemas.core.communication import MessageType
from examples.end_to_end_examples.icap.workflow import create_workflow


def create_communication_focused_preferences() -> PreferenceWeights:
    """Create preferences that encourage agent communication and coordination."""
    return PreferenceWeights(
        preferences=[
            Preference(
                name="collaboration",
                weight=0.4,
                description="Prioritize tasks that involve agent collaboration",
                evaluator=Evaluator(
                    name="collaboration_eval",
                    description="placeholder",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=[],
                ),
            ),
            Preference(
                name="quality",
                weight=0.3,
                description="Ensure high-quality outputs through coordination",
                evaluator=Evaluator(
                    name="quality_eval",
                    description="placeholder",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=[],
                ),
            ),
            Preference(
                name="efficiency",
                weight=0.3,
                description="Complete tasks efficiently through good communication",
                evaluator=Evaluator(
                    name="efficiency_eval",
                    description="placeholder",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=[],
                ),
            ),
        ],
        timestep=0,
    )


async def setup_communication_demo() -> tuple[
    WorkflowExecutionEngine, CommunicationService
]:
    """Set up a workflow with multiple communicating agents."""

    print("🏗️  Setting up communication demonstration...")

    # Step 1: Create communication service
    print("\n📡 Creating communication service...")
    communication_service = CommunicationService()
    print("✅ Communication hub established")

    # Step 2: Create workflow with multiple tasks requiring coordination
    print("\n📋 Creating collaborative workflow...")
    workflow = create_workflow()
    print(f"✅ Created workflow '{workflow.name}' with {len(workflow.tasks)} tasks")

    # Step 3: Set up diverse agent team
    print("\n👥 Assembling agent team...")
    agent_registry = AgentRegistry()

    # Register existing workflow agents first
    for agent in workflow.agents.values():
        agent_registry.register_agent(agent)

    # Add specialized AI agents with communication tools
    ai_config = AIAgentConfig(
        agent_id="coordinator_ai",
        agent_type="ai_agent",
        system_prompt="You are a coordination specialist AI agent. Your role is to help plan, coordinate, and communicate with other agents to ensure high-quality collaborative work. Focus on clear communication, efficient task coordination, and maintaining team alignment.",
        model_name="gpt-4o-mini",
        agent_description="You are a coordination specialist AI agent. Your role is to help plan, coordinate, and communicate with other agents to ensure high-quality collaborative work. Focus on clear communication, efficient task coordination, and maintaining team alignment.",
        agent_capabilities=[
            "coordinate",
            "communicate",
            "plan",
        ],
    )

    # Register AI agent (tools created automatically including communication)
    agent_registry.register_ai_agent(config=ai_config, additional_tools=[])

    # Add simulated human agent
    human_config = HumanAgentConfig(
        agent_id="human_reviewer",
        agent_type="human_mock",
        system_prompt="You are roleplaying as an experienced quality reviewer. You provide thorough, constructive feedback on work products and communicate clearly with team members. You're professional, detail-oriented, and collaborative.",
        name="Sarah Johnson",
        role="Senior Quality Reviewer",
        experience_years=8,
        expertise_areas=[
            "quality_assurance",
            "technical_review",
            "process_improvement",
        ],
        personality_traits=["thorough", "collaborative", "detail-oriented"],
        work_style="methodical",
        background="8 years of experience in quality assurance across multiple industries, specializing in technical review and process optimization.",
        hourly_rate=75.0,
        model_name="gpt-4o-mini",
        agent_description="You are roleplaying as an experienced quality reviewer. You provide thorough, constructive feedback on work products and communicate clearly with team members. You're professional, detail-oriented, and collaborative.",
        agent_capabilities=[
            "provide_feedback",
            "communicate",
            "review",
        ],
    )

    # Register human agent (tools created automatically including communication)
    agent_registry.register_human_agent(config=human_config, additional_tools=[])

    print(f"✅ Assembled team of {len(agent_registry.list_agents())} agents")

    # Step 4: Create manager focused on coordination
    print("\n🎯 Creating coordination-focused manager...")
    preferences = create_communication_focused_preferences()
    manager = ChainOfThoughtManagerAgent(
        preferences=preferences,
        model_name="gpt-4o-mini",
        manager_persona="Collaborative Team Coordinator",
    )
    print("✅ Manager ready with collaboration preferences")

    # Step 5: Initialize execution engine
    print("\n🚀 Initializing execution engine...")
    stakeholder_agent = create_stakeholder_agent(
        persona="balanced", preferences=preferences
    )
    engine = WorkflowExecutionEngine(
        workflow=workflow,
        manager_agent=manager,
        agent_registry=agent_registry,
        stakeholder_agent=stakeholder_agent,
        communication_service=communication_service,
        max_timesteps=8,  # Longer to see communication patterns
        seed=42,
    )
    print("✅ Execution engine configured")

    return engine, communication_service


async def demonstrate_communication_features(
    communication_service: CommunicationService,
):
    """Show communication features before workflow execution."""

    print("\n📢 Demonstrating communication features...")

    # Send some example messages to establish communication patterns
    print("\n1️⃣ Direct messaging between agents...")
    message1 = await communication_service.send_direct_message(
        from_agent="coordinator_ai",
        to_agent="human_reviewer",
        content="Hi! I'm the coordination specialist. Looking forward to working together on quality tasks.",
        message_type=MessageType.GENERAL,
    )
    print(
        f"   📨 {message1.sender_id} → {message1.receiver_id}: {message1.content[:50]}..."
    )

    # Broadcast message
    print("\n2️⃣ Broadcast to all team members...")
    broadcast = await communication_service.broadcast_message(
        from_agent="coordinator_ai",
        content="Team announcement: Let's focus on clear communication and quality coordination during our workflow execution.",
        message_type=MessageType.BROADCAST,
    )
    print(f"   📢 Broadcast from {broadcast.sender_id}: {broadcast.content[:60]}...")

    # Check message history
    print("\n3️⃣ Viewing communication history...")
    all_messages = communication_service.get_all_messages()
    print(f"   📚 Total messages in system: {len(all_messages)}")

    for msg in all_messages:
        recipient = msg.receiver_id if msg.receiver_id else "ALL"
        print(
            f"   📄 {msg.sender_id} → {recipient} [{msg.message_type.value}]: {msg.content[:40]}..."
        )


async def run_communication_workflow():
    """Run the complete communication demonstration."""

    print("=" * 70)
    print("💬 BASIC AGENT COMMUNICATION & COORDINATION DEMO")
    print("=" * 70)
    print("This example shows how agents communicate and coordinate within workflows")
    print()

    # Setup phase
    engine, communication_service = await setup_communication_demo()

    # Communication demo
    await demonstrate_communication_features(communication_service)

    # Execution phase
    print("\n" + "=" * 50)
    print("🚀 RUNNING COLLABORATIVE WORKFLOW EXECUTION")
    print("=" * 50)
    print("Watch for agent communication during task execution...")
    print()

    # Run with communication monitoring
    async def monitor_messages():
        """Monitor new messages during execution."""
        initial_count = len(communication_service.get_all_messages())
        while True:
            await asyncio.sleep(2)  # Check every 2 seconds
            current_messages = communication_service.get_all_messages()
            new_count = len(current_messages)

            if new_count > initial_count:
                print(f"\n💬 New communication activity! Total messages: {new_count}")
                # Show latest message
                latest = current_messages[-1]
                recipient = latest.receiver_id if latest.receiver_id else "ALL"
                print(
                    f"   Latest: {latest.sender_id} → {recipient}: {latest.content[:50]}..."
                )
                initial_count = new_count

    # Start monitoring
    monitor_task = asyncio.create_task(monitor_messages())

    try:
        # Run the workflow
        timestep_results = await engine.run_full_execution()

        print("\n✅ Workflow execution completed!")
        print(f"   📊 Completed {len(timestep_results)} timesteps")
        print(f"   🏁 Final state: {engine.execution_state}")

    finally:
        monitor_task.cancel()

    # Communication analysis
    print("\n" + "=" * 50)
    print("📊 COMMUNICATION ANALYSIS")
    print("=" * 50)

    final_messages = communication_service.get_all_messages()
    print("\n📈 Communication Statistics:")
    print(f"   Total messages exchanged: {len(final_messages)}")

    # Message type breakdown
    type_counts = {}
    for msg in final_messages:
        msg_type = msg.message_type.value
        type_counts[msg_type] = type_counts.get(msg_type, 0) + 1

    print("\n   Message types:")
    for msg_type, count in type_counts.items():
        print(f"     • {msg_type}: {count}")

    # Agent participation
    senders = set(msg.sender_id for msg in final_messages)
    receivers = set(msg.receiver_id for msg in final_messages if msg.receiver_id)

    print("\n   Agent participation:")
    print(f"     • Agents who sent messages: {len(senders)}")
    print(f"     • Unique senders: {', '.join(sorted(senders))}")
    print(f"     • Agents who received messages: {len(receivers)}")
    print("\n🎉 Communication demonstration complete!")
    print("\nKey Takeaways:")
    print("• Agents can send direct messages and broadcasts")
    print("• Communication history is automatically tracked")
    print("• Managers can observe and coordinate through communication")
    print("• The system supports rich message types and threading")


if __name__ == "__main__":
    asyncio.run(run_communication_workflow())
