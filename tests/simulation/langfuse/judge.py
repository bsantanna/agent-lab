import json

from litellm import completion

from tests.simulation.common.config import JUDGE_API_BASE, JUDGE_API_KEY, JUDGE_MODEL

JUDGE_PROMPT = """You are an impartial judge evaluating the response of an LLM agent.

User message:
{message}

Agent response:
{response}

Evaluation criteria:
{criteria}

Respond with a JSON object with the following fields:
- "passed": true only if the agent response satisfies all criteria, false otherwise
- "score": a number between 0.0 and 1.0 rating how well the response meets the criteria
- "reasoning": a short explanation of the verdict
"""


def evaluate(message, response, criteria) -> dict:
    criteria_list = "\n".join(f"- {criterion}" for criterion in criteria)
    kwargs = {}
    if JUDGE_API_BASE:
        kwargs["api_base"] = JUDGE_API_BASE
    if JUDGE_API_KEY:
        kwargs["api_key"] = JUDGE_API_KEY
    result = completion(
        model=JUDGE_MODEL,
        messages=[
            {
                "role": "user",
                "content": JUDGE_PROMPT.format(
                    message=message, response=response, criteria=criteria_list
                ),
            }
        ],
        temperature=1.0,
        response_format={"type": "json_object"},
        **kwargs,
    )
    verdict = json.loads(result.choices[0].message.content)
    return {
        "passed": bool(verdict["passed"]),
        "score": float(verdict["score"]),
        "reasoning": verdict.get("reasoning", ""),
    }
