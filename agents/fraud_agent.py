"""
Agentic fraud detection wrapper for the V6 UI.
"""

from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate

from agents.tools.fraud_tools import FRAUD_TOOLS
from llm.groq_client import get_agent_llm

FRAUD_AGENT_PROMPT = """You are a fraud detection specialist at SafeNest bank. You analyze customer accounts for suspicious activity.

You have access to these tools:
{tools}

Use the following format:

Question: the fraud detection query
Thought: think about what to check first
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: a clear security assessment for the customer

IMPORTANT ANALYSIS STEPS:
1. Use get_current_date to establish timeline context
2. Use get_transaction_history to see recent activity
3. Use check_flagged_transactions to see if the system detected issues
4. Use analyze_transaction_patterns for pattern analysis

Begin!

Question: {input}
Thought: {agent_scratchpad}"""


def _create_agent():
    prompt = PromptTemplate(
        template=FRAUD_AGENT_PROMPT,
        input_variables=["input", "agent_scratchpad"],
        partial_variables={
            "tools": "\n".join([f"{tool.name}: {tool.description}" for tool in FRAUD_TOOLS]),
            "tool_names": ", ".join([tool.name for tool in FRAUD_TOOLS]),
        },
    )
    agent = create_react_agent(llm=get_agent_llm(), tools=FRAUD_TOOLS, prompt=prompt)
    return AgentExecutor(
        agent=agent,
        tools=FRAUD_TOOLS,
        verbose=False,
        max_iterations=15,
        handle_parsing_errors=True,
    )


def check_fraud(customer_id: int, query: str = "Is there suspicious activity on my account?") -> str:
    try:
        result = _create_agent().invoke({"input": f"Customer ID: {customer_id}\nQuestion: {query}"})
        return result["output"]
    except Exception as e:
        return f"Error during fraud analysis: {str(e)}"
