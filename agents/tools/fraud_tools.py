"""
LangChain tools for fraud detection.
"""

import os
from datetime import datetime

import pandas as pd
from langchain.tools import tool

from utils.tool_parsing import parse_int

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TRANSACTIONS_PATH = os.path.join(BASE, "data", "transactions.csv")
FRAUD_THRESHOLD = 50000


@tool
def get_transaction_history(customer_id, days=30) -> dict:
    """Fetch recent transaction history for a customer."""
    try:
        customer_id = parse_int(customer_id, "customer_id")
        days = parse_int(days, "days")
        df = pd.read_csv(TRANSACTIONS_PATH)
        txns = df[df["customer_id"] == customer_id].sort_values("date", ascending=False)

        transactions = []
        for _, t in txns.iterrows():
            transactions.append(
                {
                    "transaction_id": str(t["transaction_id"]),
                    "amount": int(t["amount"]),
                    "type": str(t["type"]),
                    "status": str(t["status"]),
                    "reason": str(t["reason"]) if pd.notna(t["reason"]) else "",
                    "date": str(t["date"]),
                }
            )

        return {"count": len(transactions), "transactions": transactions, "days": days}
    except Exception as e:
        return {"error": str(e)}


@tool
def check_flagged_transactions(customer_id) -> dict:
    """Check if any transactions are already flagged by the fraud system."""
    try:
        customer_id = parse_int(customer_id, "customer_id")
        df = pd.read_csv(TRANSACTIONS_PATH)
        flagged = df[(df["customer_id"] == customer_id) & (df["status"] == "flagged")]

        flags = []
        for _, t in flagged.iterrows():
            flags.append(
                {
                    "transaction_id": str(t["transaction_id"]),
                    "amount": int(t["amount"]),
                    "date": str(t["date"]),
                    "reason": str(t["reason"]) if pd.notna(t["reason"]) else "",
                }
            )

        return {"has_flags": len(flags) > 0, "count": len(flags), "flagged_transactions": flags}
    except Exception as e:
        return {"error": str(e)}


@tool
def analyze_transaction_patterns(customer_id) -> dict:
    """Analyze transactions for suspicious patterns."""
    try:
        customer_id = parse_int(customer_id, "customer_id")
        df = pd.read_csv(TRANSACTIONS_PATH)
        txns = df[df["customer_id"] == customer_id]

        if txns.empty:
            return {"suspicious": False, "patterns": []}

        patterns = []
        large = txns[txns["amount"] > FRAUD_THRESHOLD]
        if not large.empty:
            patterns.append(f"{len(large)} transaction(s) above Rs.{FRAUD_THRESHOLD:,}")

        duplicates = txns[txns["status"] == "duplicate_charge"]
        if not duplicates.empty:
            patterns.append(f"{len(duplicates)} duplicate charge(s) detected")

        blocked = txns[txns["status"] == "blocked"]
        if len(blocked) > 1:
            patterns.append(f"{len(blocked)} blocked transactions")

        return {"suspicious": len(patterns) > 0, "patterns": patterns, "total_transactions": len(txns)}
    except Exception as e:
        return {"error": str(e)}


@tool
def get_current_date() -> str:
    """Return the current date to make the agent time-aware."""
    return datetime.now().strftime("%Y-%m-%d")


FRAUD_TOOLS = [
    get_transaction_history,
    check_flagged_transactions,
    analyze_transaction_patterns,
    get_current_date,
]
