"""
LangChain tools for compliance checks.
"""

import os

import pandas as pd
from langchain.tools import tool

from utils.tool_parsing import parse_int

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CUSTOMERS_PATH = os.path.join(BASE, "data", "customers.csv")
LOANS_PATH = os.path.join(BASE, "data", "loans.csv")
RULES_PATH = os.path.join(BASE, "data", "compliance_rules.csv")

MAX_EMI_RATIO = 0.40
MAX_ACTIVE_LOANS = 2


def _check_emi_ratio_impl(customer_id: int) -> dict:
    customers = pd.read_csv(CUSTOMERS_PATH)
    loans = pd.read_csv(LOANS_PATH)

    customer = customers[customers["customer_id"] == customer_id]
    if customer.empty:
        return {"error": f"Customer {customer_id} not found"}

    c = customer.iloc[0]
    income = int(c["income"])
    active = loans[(loans["customer_id"] == customer_id) & (loans["status"] == "active")]

    if active.empty:
        return {
            "compliant": True,
            "ratio": 0.0,
            "monthly_emi": 0,
            "monthly_income": income,
            "limit": MAX_EMI_RATIO,
        }

    monthly_emi = sum(active.apply(lambda r: r["amount"] / r["tenure_months"], axis=1))
    ratio = monthly_emi / income if income > 0 else 0
    compliant = ratio <= MAX_EMI_RATIO

    return {
        "compliant": compliant,
        "ratio": round(ratio, 3),
        "monthly_emi": int(monthly_emi),
        "monthly_income": income,
        "limit": MAX_EMI_RATIO,
        "violation": f"EMI ratio {ratio:.1%} exceeds limit {MAX_EMI_RATIO:.0%}" if not compliant else None,
    }


def _check_loan_count_impl(customer_id: int) -> dict:
    loans = pd.read_csv(LOANS_PATH)
    active = loans[(loans["customer_id"] == customer_id) & (loans["status"] == "active")]
    count = len(active)
    compliant = count <= MAX_ACTIVE_LOANS
    return {
        "compliant": compliant,
        "active_loans": count,
        "limit": MAX_ACTIVE_LOANS,
        "violation": f"Has {count} active loans, limit is {MAX_ACTIVE_LOANS}" if not compliant else None,
    }


@tool
def get_compliance_rules() -> dict:
    """Fetch all compliance rules from the rules data."""
    try:
        df = pd.read_csv(RULES_PATH)
        rules = []
        for _, rule in df.iterrows():
            rules.append(
                {
                    "rule_id": str(rule["rule_id"]),
                    "rule_name": str(rule["rule_name"]),
                    "threshold": float(rule["threshold"]) if pd.notna(rule["threshold"]) else None,
                    "action": str(rule["action"]),
                    "description": str(rule["description"]),
                }
            )
        return {"rules": rules}
    except Exception as e:
        return {"error": str(e)}


@tool
def check_emi_ratio(customer_id) -> dict:
    """Check whether the customer's EMI ratio is within the allowed limit."""
    try:
        customer_id = parse_int(customer_id, "customer_id")
        return _check_emi_ratio_impl(customer_id)
    except Exception as e:
        return {"error": str(e)}


@tool
def check_loan_count(customer_id) -> dict:
    """Check whether the customer is within the active loan count limit."""
    try:
        customer_id = parse_int(customer_id, "customer_id")
        return _check_loan_count_impl(customer_id)
    except Exception as e:
        return {"error": str(e)}


@tool
def validate_account_compliance(customer_id) -> dict:
    """Run all compliance checks and return a consolidated result."""
    try:
        customer_id = parse_int(customer_id, "customer_id")
        emi_check = _check_emi_ratio_impl(customer_id)
        loan_check = _check_loan_count_impl(customer_id)

        if "error" in emi_check or "error" in loan_check:
            return {"error": "Compliance check failed"}

        violations = []
        if not emi_check["compliant"]:
            violations.append(emi_check["violation"])
        if not loan_check["compliant"]:
            violations.append(loan_check["violation"])

        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "emi_ratio": emi_check["ratio"],
            "active_loans": loan_check["active_loans"],
        }
    except Exception as e:
        return {"error": str(e)}


COMPLIANCE_TOOLS = [
    get_compliance_rules,
    check_emi_ratio,
    check_loan_count,
    validate_account_compliance,
]
