"""
LangChain tools for the transaction agent.
"""

import os

import pandas as pd
from langchain.tools import tool

from utils.tool_parsing import parse_int, parse_optional_text

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TRANSACTIONS_PATH = os.path.join(BASE, "data", "transactions.csv")

REASON_EXPLANATIONS = {
    "daily_limit_exceeded": "exceeded the daily transfer limit of Rs.15,000",
    "duplicate_transaction": "identified as a duplicate charge",
    "unusual_large_amount": "flagged for review due to an unusually large amount",
}


@tool
def lookup_transaction(customer_id, transaction_id: str = None) -> dict:
    """Look up a specific transaction or the most recent one for a customer."""
    try:
        customer_id = parse_int(customer_id, "customer_id")
        transaction_id = parse_optional_text(transaction_id)
        df = pd.read_csv(TRANSACTIONS_PATH)
        txns = df[df["customer_id"] == customer_id].sort_values("date", ascending=False)

        if txns.empty:
            return {"error": f"No transactions found for customer {customer_id}"}

        if transaction_id:
            txn = txns[txns["transaction_id"] == transaction_id]
            if txn.empty:
                return {"error": f"Transaction {transaction_id} not found"}
            t = txn.iloc[0]
        else:
            t = txns.iloc[0]

        return {
            "transaction_id": str(t["transaction_id"]),
            "amount": int(t["amount"]),
            "type": str(t["type"]),
            "status": str(t["status"]),
            "reason": str(t["reason"]) if pd.notna(t["reason"]) else "",
            "date": str(t["date"]),
        }
    except Exception as e:
        return {"error": str(e)}


@tool
def get_blocked_transactions(customer_id) -> dict:
    """Get all blocked, flagged, or duplicate transactions for a customer."""
    try:
        customer_id = parse_int(customer_id, "customer_id")
        df = pd.read_csv(TRANSACTIONS_PATH)
        blocked = df[
            (df["customer_id"] == customer_id)
            & (df["status"].isin(["blocked", "flagged", "duplicate_charge"]))
        ].sort_values("date", ascending=False)

        transactions = []
        for _, t in blocked.iterrows():
            reason = str(t["reason"]) if pd.notna(t["reason"]) else ""
            explanation = REASON_EXPLANATIONS.get(reason, reason)
            transactions.append(
                {
                    "transaction_id": str(t["transaction_id"]),
                    "amount": int(t["amount"]),
                    "type": str(t["type"]),
                    "status": str(t["status"]),
                    "reason": reason,
                    "explanation": explanation,
                    "date": str(t["date"]),
                }
            )

        return {"count": len(transactions), "transactions": transactions}
    except Exception as e:
        return {"error": str(e)}


@tool
def explain_block_reason(reason_code: str) -> str:
    """Translate technical block reason codes into customer-friendly text."""
    reason_code = parse_optional_text(reason_code) or ""
    return REASON_EXPLANATIONS.get(reason_code, f"Transaction was {reason_code}")


TRANSACTION_TOOLS = [lookup_transaction, get_blocked_transactions, explain_block_reason]
