"""Generate synthetic SFT conversations for rubric decomposer training.

This script takes GDPEval tasks with gold rubrics and generates multi-turn
conversations between a stakeholder and rubric generation agent that would
naturally elicit the gold rubric.

Following the RUBICON paper (Section 3.3, Stage I):
"We perform a single SFT stage using synthetic clarification dialogues
between the decomposer and a simulated stakeholder induced by the true 
evaluator U*."

The generated conversations follow a natural progression:
1. Agent asks about evaluation criteria
2. Stakeholder provides high-level goals
3. Agent asks for specifics on key aspects
4. Stakeholder clarifies with examples
5. Agent synthesizes into structured rubric
"""

import asyncio
import json
from pathlib import Path
from tqdm.asyncio import tqdm_asyncio
from openai import AsyncOpenAI
import logging
import os
from typing import Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


CONVERSATION_GENERATION_PROMPT = """You are generating a realistic multi-turn conversation between a STAKEHOLDER and a RUBRIC AGENT that naturally leads to the given gold rubric.

The conversation should feel natural and pedagogical - the agent is learning what the stakeholder values through clarification questions.

## CRITICAL: CONVERSATION STRUCTURE

**MAXIMUM 5 TURNS TOTAL** (alternating agent → stakeholder → agent → stakeholder → agent)

The agent needs to extract all information needed for the gold rubric in just 5 turns, so:
- **Turn 1 (Agent)**: Opens with broad question about evaluation priorities
- **Turn 2 (Stakeholder)**: Gives high-level priorities (still brief: 1-4 sentences)
- **Turn 3 (Agent)**: Asks multiple related follow-up questions to drill down (can be longer if needed)
- **Turn 4 (Stakeholder)**: Responds to those questions (longer is OK - 3-8 sentences to cover everything)
- **Turn 5 (Agent)**: Confirms understanding and says they'll create the rubric (DO NOT output the actual rubric JSON)

**OR even shorter:**
- Some conversations might only need 3 turns if the stakeholder is clear upfront
- Turn 1: Agent asks → Turn 2: Stakeholder gives comprehensive answer → Turn 3: Agent confirms and says they'll build the rubric

**Stakeholder response lengths with 5-turn constraint:**
- Turn 2: Usually **1-4 sentences** (high-level priorities)
- Turn 4: Can be **3-8 sentences** if agent asked multiple questions and stakeholder needs to address them all
- Still keep it realistic - stakeholder shouldn't write essays, but can give a paragraph when responding to multiple questions

## TASK CONTEXT

**Sector**: {sector}
**Occupation**: {occupation}

**Task Description**:
{task_prompt}

**Gold Rubric** (the conversation should naturally lead here):
```json
{rubric_json}
```

## CRITICAL: REALISTIC STAKEHOLDER VARIATION

This is training data - we need DIVERSITY in stakeholder quality and communication style.
Randomly pick ONE of these stakeholder personas for this conversation:

### Persona A: Excellent Communicator (20% of conversations)
- Clear, organized, but still BRIEF
- Responses: Usually 2-4 sentences, occasionally 5 if giving an example
- Example: "For this analysis, accuracy is critical - all figures should be verifiable. Also need clear documentation of assumptions. And make it professional for executive review."

### Persona B: Average Communicator (50% of conversations)  
- Gives decent direction but needs some back-and-forth
- Responses: 1-3 sentences typically
- Example: "I want it thorough and professional. Accuracy matters most here."

### Persona C: Vague/Exploratory (20% of conversations)
- Doesn't know exactly what they want upfront
- Says things like "I'll know it when I see it", "just make it look professional"
- Responses: 1-2 sentences, very brief
- Example: "Just make sure it's done well." → Agent has to probe: "What aspects of quality matter most?" → "Oh, like the numbers being right."

### Persona D: Rushed/Terse (10% of conversations)
- Very brief, minimal elaboration
- Responses: 1-2 sentences max, often sentence fragments
- Example: "Accuracy first. Then clarity." or "Make it professional."

## HUMAN IMPERFECTIONS (Add these naturally, don't overdo it)

**Incomplete thoughts**: "What I really need is... well, mostly just that it's clear to the client"
**Hedging/Uncertainty**: "I think probably accuracy matters most? But also, I don't know, maybe clarity is equally important"
**Tangents**: "We had a project last year where the analysis looked great but the client couldn't understand it, so..."
**Vagueness requiring follow-up**: "It needs to be professional" → Agent: "What aspects of professionalism are most important?" → "Oh, like formatting and making it look polished"
**Contradictions**: "Keep it concise... but also make sure it's thorough" (agent has to reconcile)
**Jargon or assumptions**: Uses field-specific terms without explaining, agent may need to clarify

## RESPONSE LENGTH VARIATION

With the 5-turn constraint, responses will be longer than pure back-and-forth:

**Agent questions:**
- Turn 1: Brief opener (1-2 sentences)
- Turn 3: Multiple related questions grouped together (can be 3-6 sentences to cover different aspects efficiently)

**Stakeholder responses:**
- Turn 2 (initial): **1-4 sentences** giving high-level priorities
- Turn 4 (detailed): **3-8 sentences** addressing multiple aspects the agent asked about
  - Example: "For structure, yes use Excel with two tabs. On the variance calculation, I prefer percentage change - put it right after Q3. For sample size, use 90% confidence and 10% error. And make sure formatting is professional with clear headers."

**IMPORTANT**: Longer responses are acceptable given the 5-turn constraint. Stakeholder shouldn't ramble, but can give a solid paragraph to address multiple questions at once.

## INSTRUCTIONS

1. **Pick a persona**: Choose A, B, C, or D for this stakeholder
2. **Maximum 5 turns**: Keep conversation to 5 turns or fewer (3 turns is fine for simple rubrics)
3. **Agent groups questions efficiently**: Turn 3 can ask multiple related things to extract info quickly
4. **Stakeholder responses scale appropriately**: Brief in Turn 2, more detailed in Turn 4 when addressing multiple aspects
5. **Add imperfections**: Include 1-3 human imperfections from the list above
6. **Match the gold rubric**: Despite the condensed format, final rubric must match gold
7. **Use domain language**: Stakeholder speaks like someone from {sector} / {occupation}

## OUTPUT FORMAT

Return a JSON object with this structure:
```json
{{
  "conversation": [
    {{"role": "agent", "content": "..."}},
    {{"role": "stakeholder", "content": "..."}},
    {{"role": "agent", "content": "..."}},
    {{"role": "stakeholder", "content": "..."}},
  ]
}}
```

**DO NOT include a `final_rubric` field** - we already have the gold rubric separately.

Generate the conversation now!"""


async def generate_sft_conversation(
    task_id: str,
    sector: str,
    occupation: str,
    task_prompt: str,
    gold_rubric: dict[str, Any],
    model: str = "gpt-5",
    seed: int = 42,
) -> dict[str, Any]:
    """Generate a synthetic SFT conversation for a task with gold rubric.
    
    Args:
        task_id: Unique task identifier
        sector: Industry sector
        occupation: Job role
        task_prompt: The task description given to workers
        gold_rubric: The gold standard rubric (StagedRubric dict)
        model: LLM model to use for generation
        seed: Random seed for reproducibility
        
    Returns:
        Dictionary with conversation and metadata
    """
    
    # Format the rubric nicely for the prompt
    rubric_json = json.dumps(gold_rubric, indent=2)
    
    prompt = CONVERSATION_GENERATION_PROMPT.format(
        sector=sector,
        occupation=occupation,
        task_prompt=task_prompt,
        rubric_json=rubric_json,
    )
    
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert at generating realistic training conversations for rubric-based evaluation systems."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            seed=seed,
            # Note: GPT-5 only supports temperature=1.0 (default)
        )
        
        result = json.loads(response.choices[0].message.content)
        
        return {
            "task_id": task_id,
            "sector": sector,
            "occupation": occupation,
            "task_prompt": task_prompt,
            "conversation": result["conversation"],
            "gold_rubric": gold_rubric,
        }
        
    except Exception as e:
        logger.error(f"Error generating conversation for {task_id}: {e}")
        return None


async def generate_all_sft_conversations(
    rubrics_file: Path,
    dataset_path: Path,
    output_file: Path,
    model: str = "gpt-5",
    seed: int = 42,
    max_concurrent: int = 10,
    limit: int | None = None,
):
    """Generate SFT conversations for all rubrics.
    
    Args:
        rubrics_file: Path to staged_rubrics.jsonl with gold rubrics
        dataset_path: Path to GDPEval dataset parquet
        output_file: Where to save the generated conversations
        model: LLM model to use
        seed: Random seed
        max_concurrent: Maximum concurrent API requests
        limit: Limit number of conversations to generate (for debugging)
    """
    
    import pandas as pd
    
    logger.info(f"Loading rubrics from {rubrics_file}")
    rubrics = []
    with open(rubrics_file, "r") as f:
        for line in f:
            rubrics.append(json.loads(line))
    
    logger.info(f"Loading dataset from {dataset_path}")
    df = pd.read_parquet(dataset_path)
    
    # Create task_id -> task mapping
    task_map = {row["task_id"]: row for _, row in df.iterrows()}
    
    # Check for existing conversations
    existing_task_ids = set()
    if output_file.exists():
        with open(output_file, "r") as f:
            for line in f:
                conv = json.loads(line)
                existing_task_ids.add(conv["task_id"])
        logger.info(f"Found {len(existing_task_ids)} existing conversations, skipping...")
    
    # Filter to tasks with rubrics and not yet processed
    tasks_to_process = []
    for rubric_data in rubrics:
        task_id = rubric_data["task_id"]
        if task_id in existing_task_ids:
            continue
        if task_id not in task_map:
            logger.warning(f"Task {task_id} not found in dataset, skipping")
            continue
        
        task_row = task_map[task_id]
        tasks_to_process.append({
            "task_id": task_id,
            "sector": task_row["sector"],
            "occupation": task_row["occupation"],
            "task_prompt": task_row["prompt"],
            "gold_rubric": rubric_data["rubric"],
        })
    
    if limit is not None and limit > 0:
        tasks_to_process = tasks_to_process[:limit]
        logger.info(f"Limiting to first {limit} tasks (for debugging)")
    
    logger.info(f"Generating SFT conversations for {len(tasks_to_process)} tasks...")
    
    if len(tasks_to_process) == 0:
        logger.info("All tasks already processed!")
        return 0
    
    # Semaphore for concurrency control
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def generate_with_semaphore(task_data):
        """Generate conversation with concurrency limiting."""
        async with semaphore:
            try:
                return await generate_sft_conversation(
                    task_id=task_data["task_id"],
                    sector=task_data["sector"],
                    occupation=task_data["occupation"],
                    task_prompt=task_data["task_prompt"],
                    gold_rubric=task_data["gold_rubric"],
                    model=model,
                    seed=seed,
                )
            except Exception as e:
                logger.error(f"Error generating conversation for {task_data['task_id']}: {e}")
                return None
    
    # Generate with progress bar
    tasks = [generate_with_semaphore(task_data) for task_data in tasks_to_process]
    conversations = await tqdm_asyncio.gather(*tasks, desc="Generating SFT conversations")
    
    # Save results
    output_file.parent.mkdir(parents=True, exist_ok=True)
    successful = 0
    with open(output_file, "a") as f:
        for conv in conversations:
            if conv:
                f.write(json.dumps(conv) + "\n")
                successful += 1
    
    logger.info(f"✓ Generated {successful}/{len(tasks_to_process)} SFT conversations")
    logger.info(f"✓ Saved to {output_file}")
    
    return successful


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate SFT conversations for rubric decomposer training"
    )
    parser.add_argument(
        "--rubrics-file",
        type=Path,
        required=True,
        help="Path to staged_rubrics.jsonl with gold rubrics"
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=None,
        help="Path to GDPEval dataset parquet"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output file for SFT conversations"
    )
    parser.add_argument("--model", default="gpt-5", help="LLM model to use")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument(
        "--max-concurrent", type=int, default=10, help="Max concurrent requests"
    )
    parser.add_argument("--limit", type=int, default=None, help="Limit number of tasks")
    args = parser.parse_args()
    
    # Set defaults
    if args.dataset is None:
        args.dataset = Path(__file__).parent.parent / "data" / "raw" / "gdpeval.parquet"
    
    if args.output is None:
        rubrics_dir = args.rubrics_file.parent
        args.output = rubrics_dir / "sft_conversations.jsonl"
    
    asyncio.run(
        generate_all_sft_conversations(
            rubrics_file=args.rubrics_file,
            dataset_path=args.dataset,
            output_file=args.output,
            model=args.model,
            seed=args.seed,
            max_concurrent=args.max_concurrent,
            limit=args.limit,
        )
    )

