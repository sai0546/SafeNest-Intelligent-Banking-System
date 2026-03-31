"""
Agentic loan eligibility wrapper for the V6 UI.
"""

from langchain.agents import AgentExecutor
from langchain.agents.react.agent import create_react_agent
from langchain.prompts import PromptTemplate

from agents.tools.loan_tools import LOAN_TOOLS
from llm.groq_client import get_agent_llm

LOAN_AGENT_PROMPT = """You are a loan eligibility specialist at SafeNest bank. You help customers understand if they qualify for a personal loan.

You have access to these tools:
{tools}

Use the following format:

Question: the input question about loan eligibility
Thought: think about what information you need
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: a clear, helpful response to the customer

IMPORTANT:
1. Always use get_customer_profile first to get income and credit score
2. Then use check_active_loans to see existing loans
3. Then use calculate_loan_eligibility with the gathered data
4. Provide a clear yes/no answer with the maximum loan amount if eligible

Begin!

Question: {input}
Thought: {agent_scratchpad}"""


def _create_agent():
    prompt = PromptTemplate(
        template=LOAN_AGENT_PROMPT,
        input_variables=["input", "agent_scratchpad"],
        partial_variables={
            "tools": "\n".join([f"{tool.name}: {tool.description}" for tool in LOAN_TOOLS]),
            "tool_names": ", ".join([tool.name for tool in LOAN_TOOLS]),
        },
    )
    agent = create_react_agent(llm=get_agent_llm(), tools=LOAN_TOOLS, prompt=prompt)
    return AgentExecutor(
        agent=agent,
        tools=LOAN_TOOLS,
        verbose=False,
        max_iterations=10,
        handle_parsing_errors=True,
    )


def check_eligibility(customer_id: int, query: str = "Am I eligible for a personal loan?") -> str:
    try:
        result = _create_agent().invoke({"input": f"Customer ID: {customer_id}\nQuestion: {query}"})
        return result["output"]
    except Exception as e:
        return f"Error processing loan eligibility: {str(e)}"
