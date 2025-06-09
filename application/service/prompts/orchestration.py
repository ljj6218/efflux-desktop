from typing import Dict, Any, List

ORCHESTRATOR_PROGRESS_LEDGER_PROMPT = """
Recall we are working on the following request:

{task}

This is our current plan:

{plan}

We are at step index {step_index} in the plan which is 

Title: {step_title}

Details: {step_details}

agent_name: {agent_name}

And we have assembled the following team:

{team}

The browser the web_surfer accesses is also controlled by the user.


To make progress on the request, please answer the following questions, including necessary reasoning:

    - is_current_step_complete: Is the current step complete? (True if complete, or False if the current step is not yet complete)
    - need_to_replan: Do we need to create a new plan? (True if user has sent new instructions and the current plan can't address it. True if the current plan cannot address the user request because we are stuck in a loop, facing significant barriers, or the current approach is not working. False if we can continue with the current plan. Most of the time we don't need a new plan.)
    - instruction_or_question: Provide complete instructions to accomplish the current step with all context needed about the task and the plan. Provide a very detailed reasoning chain for how to complete the step. If the next agent is the user, pose it directly as a question. Otherwise pose it as something you will do.
    - agent_name: Decide which team member should complete the current step from the list of team members: {names}. 
    - progress_summary: Summarize all the information that has been gathered so far that would help in the completion of the plan including ones not present in the collected information. This should include any facts, educated guesses, or other information that has been gathered so far. Maintain any information gathered in the previous steps.

Important: it is important to obey the user request and any messages they have sent previously.

{additional_instructions}

Please output an answer in pure JSON format according to the following schema. The JSON object must be parsable as-is. DO NOT OUTPUT ANYTHING OTHER THAN JSON, AND DO NOT DEVIATE FROM THIS SCHEMA:

    {{
        "is_current_step_complete": {{
            "reason": string,
            "answer": boolean
        }},
        "need_to_replan": {{
            "reason": string,
            "answer": boolean
        }},
        "instruction_or_question": {{
            "answer": string,
            "agent_name": string (the name of the agent that should complete the step from {names})
        }},
        "progress_summary": "a summary of the progress made so far"

    }}
"""

ORCHESTRATOR_SYSTEM_MESSAGE_EXECUTION = """
You are a helpful AI assistant named Magentic-UI built by Microsoft Research AI Frontiers.
Your goal is to help the user with their request.
You can complete actions on the web, complete actions on behalf of the user, execute code, and more.
The browser the web_surfer accesses is also controlled by the user.
You have access to a team of agents who can help you answer questions and complete tasks.

The date today is: {date_today}
"""


def validate_ledger_json(json_response: Dict[str, Any], agent_names: List[str]) -> bool:
    required_keys = [
        "is_current_step_complete",
        "need_to_replan",
        "instruction_or_question",
        "progress_summary",
    ]

    if not isinstance(json_response, dict):
        return False

    for key in required_keys:
        if key not in json_response:
            return False

    # Check structure of boolean response objects
    for key in [
        "is_current_step_complete",
        "need_to_replan",
    ]:
        if not isinstance(json_response[key], dict):
            return False
        if "reason" not in json_response[key] or "answer" not in json_response[key]:
            return False

    # Check instruction_or_question structure
    if not isinstance(json_response["instruction_or_question"], dict):
        return False
    if (
        "answer" not in json_response["instruction_or_question"]
        or "agent_name" not in json_response["instruction_or_question"]
    ):
        return False
    if json_response["instruction_or_question"]["agent_name"] not in agent_names:
        return False

    # Check progress_summary is a string
    if not isinstance(json_response["progress_summary"], str):
        return False

    return True