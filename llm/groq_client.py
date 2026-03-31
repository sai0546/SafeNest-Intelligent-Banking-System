"""
LangChain-backed GROQ client that preserves the original V6 interface.
"""

import streamlit as st
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_groq import ChatGroq

MODEL = "llama-3.3-70b-versatile"

VALID_INTENTS = {
    "loan_check",
    "transaction_issue",
    "fraud_check",
    "compliance_check",
    "general_query",
}


def get_llm(temperature: float = 0.0, max_tokens: int = 500) -> ChatGroq:
    return ChatGroq(
        model=MODEL,
        groq_api_key=st.secrets["GROQ_API_KEY"],
        temperature=temperature,
        max_tokens=max_tokens,
    )


def get_agent_llm() -> ChatGroq:
    return get_llm(temperature=0.3, max_tokens=500)


def _usage_counts(message) -> tuple[int, int, int]:
    usage = getattr(message, "usage_metadata", None) or {}
    input_tokens = int(usage.get("input_tokens", 0) or 0)
    output_tokens = int(usage.get("output_tokens", 0) or 0)
    total_tokens = int(usage.get("total_tokens", input_tokens + output_tokens) or 0)
    return input_tokens, output_tokens, total_tokens


def detect_intent(query: str) -> tuple[str, int]:
    prompt = PromptTemplate(
        input_variables=["query"],
        template="""You are a banking intent classifier. Classify this customer query into EXACTLY ONE:
- loan_check        (loan eligibility, applying for a loan)
- transaction_issue (blocked, declined, or failed transactions)
- fraud_check       (suspicious activity, unauthorized transactions)
- compliance_check  (account rules, limits, compliance status)
- general_query     (all other banking support questions)

Reply with ONLY the intent label. Nothing else.

Query: {query}

Intent:""",
    )

    response = (prompt | get_llm(temperature=0.0, max_tokens=15)).invoke({"query": query})
    _, _, total = _usage_counts(response)
    raw = response.content.strip().lower()
    intent = raw.replace(".", "").replace(":", "").strip()
    return (intent if intent in VALID_INTENTS else "general_query"), total


def format_response(query: str, agent_result: str, intent: str) -> tuple[str, int, int]:
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a friendly, professional banking assistant for SafeNest bank.
Write a clear, helpful, natural response in 2-3 sentences.
Be specific. Do not mention AI, agents, or internal systems.
Speak directly using "your" and "you".""",
            ),
            (
                "human",
                """Customer asked: "{query}"
Our system found: {agent_result}

Provide a natural response:""",
            ),
        ]
    )

    response = (prompt | get_llm(temperature=0.3, max_tokens=250)).invoke(
        {"query": query, "agent_result": agent_result, "intent": intent}
    )
    tokens_in, tokens_out, _ = _usage_counts(response)
    return response.content.strip(), tokens_in, tokens_out
