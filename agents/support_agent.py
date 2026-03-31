"""
Agentic support wrapper for the V6 UI.
"""

from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate

from agents.tools.support_tools import SUPPORT_TOOLS
from llm.groq_client import get_agent_llm

SUPPORT_AGENT_PROMPT = """You are a customer support specialist at SafeNest bank. You help resolve customer queries using past support cases.

You have access to these tools:
{tools}

Use the following format:

Question: the customer support query
Thought: think about what to search for
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: a helpful resolution for the customer

APPROACH:
1. Use search_support_tickets to find similar past cases
2. If the match is weak, use escalate_to_human
3. Always respond helpfully and clearly

Begin!

Question: {input}
Thought: {agent_scratchpad}"""


def _create_agent():
    prompt = PromptTemplate(
        template=SUPPORT_AGENT_PROMPT,
        input_variables=["input", "agent_scratchpad"],
        partial_variables={
            "tools": "\n".join([f"{tool.name}: {tool.description}" for tool in SUPPORT_TOOLS]),
            "tool_names": ", ".join([tool.name for tool in SUPPORT_TOOLS]),
        },
    )
    agent = create_react_agent(llm=get_agent_llm(), tools=SUPPORT_TOOLS, prompt=prompt)
    return AgentExecutor(
        agent=agent,
        tools=SUPPORT_TOOLS,
        verbose=False,
        max_iterations=8,
        handle_parsing_errors=True,
    )


def resolve_query(query: str) -> str:
    try:
        result = _create_agent().invoke({"input": f"Question: {query}"})
        return result["output"]
    except Exception as e:
        return f"Error searching support tickets: {str(e)}"
