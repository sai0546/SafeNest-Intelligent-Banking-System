"""
LangChain tools for the loan eligibility agent.
"""

import os
import re

import pandas as pd
from langchain.tools import tool

from utils.tool_parsing import parse_int

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CUSTOMERS_PATH = os.path.join(BASE, "data", "customers.csv")
LOANS_PATH = os.path.join(BASE, "data", "loans.csv")

MIN_INCOME = 30000
MIN_CREDIT = 650
MAX_ACTIVE_LOANS = 2
INCOME_MULTIPLIER = 60


@tool
def get_customer_profile(customer_id) -> dict:
    """Fetch customer profile details including income and credit score."""
    try:
        customer_id = parse_int(customer_id, "customer_id")
        df = pd.read_csv(CUSTOMERS_PATH)
        customer = df[df["customer_id"] == customer_id]
        if customer.empty:
            return {"error": f"Customer ID {customer_id} not found"}

        c = customer.iloc[0]
        return {
            "name": str(c["name"]),
            "income": int(c["income"]),
            "credit_score": int(c["credit_score"]),
            "existing_loans": int(c["existing_loans"]),
        }
    except Exception as e:
        return {"error": str(e)}


@tool
def check_active_loans(customer_id) -> dict:
    """Check how many active loans the customer currently has."""
    try:
        customer_id = parse_int(customer_id, "customer_id")
        df = pd.read_csv(LOANS_PATH)
        active = df[(df["customer_id"] == customer_id) & (df["status"] == "active")]

        loans = []
        for _, loan in active.iterrows():
            loans.append(
                {
                    "loan_id": str(loan["loan_id"]),
                    "amount": int(loan["amount"]),
                    "interest_rate": float(loan["interest_rate"]),
                    "tenure_months": int(loan["tenure_months"]),
                }
            )

        return {"count": len(active), "loans": loans}
    except Exception as e:
        return {"error": str(e)}


@tool
def calculate_loan_eligibility(income) -> dict:
    """Calculate loan eligibility from income, credit score, and active loans."""
    values = [int(match) for match in re.findall(r"-?\d+", str(income))]
    if len(values) < 3:
        return {
            "eligible": False,
            "max_amount": 0,
            "reasons": ["loan eligibility input must include income, credit score, and active loans"],
        }

    income, credit_score, active_loans = values[:3]
    reasons = []

    if income < MIN_INCOME:
        reasons.append(f"income Rs.{income:,} is below minimum Rs.{MIN_INCOME:,}")
    if credit_score < MIN_CREDIT:
        reasons.append(f"credit score {credit_score} is below minimum {MIN_CREDIT}")
    if active_loans >= MAX_ACTIVE_LOANS:
        reasons.append(f"already has {active_loans} active loans (maximum is {MAX_ACTIVE_LOANS})")

    if reasons:
        return {"eligible": False, "max_amount": 0, "reasons": reasons}

    surplus = max(income - 10000, 0)
    max_amount = int(surplus * INCOME_MULTIPLIER)
    return {"eligible": True, "max_amount": max_amount, "reasons": []}


LOAN_TOOLS = [get_customer_profile, check_active_loans, calculate_loan_eligibility]
