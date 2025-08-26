"""
Prompts for the AI Agent.

This module contains prompt templates for AI agent task execution,
separated for better maintainability and organization.
"""

# Basic task execution template for AI agents
AI_AGENT_TASK_TEMPLATE = """
TASK: {task_name}

DESCRIPTION: {task_description}

INPUT RESOURCES:
{input_resources}

INSTRUCTIONS:
1. Analyze the task requirements carefully
2. Use available tools as needed to complete the work
3. Generate appropriate output resources
4. Provide your reasoning for the approach taken
5. Assess the quality of your work on a scale of 0-5
6. Note your confidence level in the result (0-1)

Please complete this task and provide structured output with:
- Generated resources (with names, descriptions, and content)
- Your reasoning process
- Quality self-assessment
- Confidence level
- Any execution notes
"""

# Specialized task template with additional context
AI_AGENT_SPECIALIZED_TASK_TEMPLATE = """
TASK: {task_name}

DESCRIPTION: {task_description}

INPUT RESOURCES:
{input_resources}

SPECIALIZATION CONTEXT:
You are operating as a specialist in {specialization}. Apply domain-specific best practices and expertise.

QUALITY REQUIREMENTS:
{quality_requirements}

OUTPUT FORMAT REQUIREMENTS:
{output_format}

INSTRUCTIONS:
1. Analyze the task requirements carefully
2. Use available tools as needed to complete the work
3. Generate appropriate output resources
4. Provide your reasoning for the approach taken
5. Assess the quality of your work on a scale of 0-5
6. Note your confidence level in the result (0-1)

ENHANCED INSTRUCTIONS FOR SPECIALIZED WORK:
- Apply domain expertise and industry best practices
- Consider scalability, maintainability, and long-term implications
- Include relevant documentation and explanations
- Validate your work against professional standards
- Provide comprehensive reasoning for technical decisions

Please complete this task and provide structured output with:
- Generated resources (with names, descriptions, and content)
- Your reasoning process
- Quality self-assessment
- Confidence level
- Any execution notes
"""

# Work review template for AI agents
AI_AGENT_REVIEW_TEMPLATE = """
TASK FOR REVIEW: {original_task_name}

ORIGINAL REQUIREMENTS: {original_task_description}

COMPLETED WORK:
{completed_work}

REVIEW CRITERIA:
{review_criteria}

REVIEW INSTRUCTIONS:
1. Evaluate how well the completed work meets the original requirements
2. Assess the quality and completeness of the deliverables
3. Identify any gaps, errors, or areas for improvement
4. Rate the overall quality on a scale of 0-5
5. Provide specific, actionable feedback

Please provide your review with:
- Overall quality rating (0-5)
- Strengths of the completed work
- Areas for improvement
- Specific recommendations
- Whether the work meets requirements (Yes/No/Partially)
"""

# Collaborative work template for AI agents
AI_AGENT_COLLABORATION_TEMPLATE = """
COLLABORATIVE TASK: {task_name}

YOUR ROLE: {role_in_team}

TEAM CONTEXT: {team_context}

TASK DESCRIPTION: {task_description}

DEPENDENCIES:
Your work depends on the following inputs from team members:
{dependencies}

COLLABORATION INSTRUCTIONS:
1. Complete your specific part of the work according to your role
2. Consider how your work interfaces with other team members' contributions
3. Communicate any blockers or questions clearly
4. Ensure your deliverables are ready for handoff to the next team member
5. Include documentation that helps team coordination

Please complete your part of the collaborative work and provide:
- Your specific deliverables
- Status of dependencies (resolved/pending/blocking)
- Communication notes for team members
- Next steps or handoff instructions
- Quality assessment of your contribution
"""

# Default message for no resources
NO_RESOURCES_MESSAGE = "No input resources provided"

# Default message for no review criteria
NO_REVIEW_CRITERIA_MESSAGE = "No specific review criteria provided"

# Default message for no dependencies
NO_DEPENDENCIES_MESSAGE = "No dependencies on other team members"
