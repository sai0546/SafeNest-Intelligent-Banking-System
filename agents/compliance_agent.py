"""
Agentic compliance wrapper for the V6 UI.
"""

from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate

from agents.tools.compliance_tools import COMPLIANCE_TOOLS
from llm.groq_client import get_agent_llm

COMPLIANCE_AGENT_PROMPT = """You are a compliance specialist at SafeNest bank. You validate customer accounts against banking regulations.

You have access to these tools:
{tools}

Use the following format:

Question: the compliance check query
Thought: think about which rules to check
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: a clear compliance status report

IMPORTANT CHECKS:
1. Use get_compliance_rules to understand all banking rules
2. Use check_emi_ratio to validate EMI-to-income ratio
3. Use check_loan_count to validate active loan count
4. Use validate_account_compliance for complete validation

Begin!

Question: {input}
Thought: {agent_scratchpad}"""


def _create_agent():
    prompt = PromptTemplate(
        template=COMPLIANCE_AGENT_PROMPT,
        input_variables=["input", "agent_scratchpad"],
        partial_variables={
            "tools": "\n".join([f"{tool.name}: {tool.description}" for tool in COMPLIANCE_TOOLS]),
            "tool_names": ", ".join([tool.name for tool in COMPLIANCE_TOOLS]),
        },
    )
    agent = create_react_agent(llm=get_agent_llm(), tools=COMPLIANCE_TOOLS, prompt=prompt)
    return AgentExecutor(
        agent=agent,
        tools=COMPLIANCE_TOOLS,
        verbose=False,
        max_iterations=10,
        handle_parsing_errors=True,
    )


def check_compliance(customer_id: int, query: str = "Is my account compliant with banking rules?") -> str:
    try:
        result = _create_agent().invoke({"input": f"Customer ID: {customer_id}\nQuestion: {query}"})
        return result["output"]
    except Exception as e:
        return f"Error during compliance check: {str(e)}"
