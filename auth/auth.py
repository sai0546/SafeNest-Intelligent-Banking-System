import pandas as pd
import os

BASE       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CUSTOMERS  = pd.read_csv(os.path.join(BASE, "data", "customers.csv"))

# ─── Admin credentials (hardcoded for prototype) ───────────────
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


# ══════════════════════════════════════════════════════════════
#  LOGIN
# ══════════════════════════════════════════════════════════════

def login(username: str, password: str) -> dict | None:
    """
    Verifies credentials.
    Returns user dict on success, None on failure.

    For admin login returns role='admin'.
    For customer login returns role='customer'.
    """
    # Admin check
    if username.strip() == ADMIN_USERNAME and password.strip() == ADMIN_PASSWORD:
        return {
            "customer_id": None,
            "name":        "System Admin",
            "username":    ADMIN_USERNAME,
            "role":        "admin",
        }

    # Customer check
    row = CUSTOMERS[
        (CUSTOMERS["username"] == username.strip()) &
        (CUSTOMERS["password"] == password.strip())
    ]
    if not row.empty:
        r = row.iloc[0]
        return {
            "customer_id": int(r["customer_id"]),
            "name":        str(r["name"]),
            "username":    str(r["username"]),
            "role":        "customer",
        }

    return None   # Invalid credentials


# ══════════════════════════════════════════════════════════════
#  AUTHORIZATION  ← THIS IS THE EXACT FUNCTION THE PROFESSOR ASKED ABOUT
# ══════════════════════════════════════════════════════════════

def enforce_access(logged_in_user: dict, requested_customer_id: int) -> tuple[bool, str]:
    """
    LOCATION: auth/auth.py → enforce_access()

    Checks whether the currently logged-in user is allowed to
    access data for `requested_customer_id`.

    Rules:
      - Admin  → can access ANY customer's data
      - Customer → can ONLY access their OWN data
      - If a customer tries to access another customer's data → DENIED

    Returns:
      (True,  "")           if access is allowed
      (False, reason_msg)   if access is denied
    """
    if logged_in_user is None:
        return False, "Not logged in. Please log in first."

    role = logged_in_user.get("role", "customer")

    # Admin has full access
    if role == "admin":
        return True, ""

    # Customer can only access their own data
    own_id = logged_in_user.get("customer_id")
    if own_id != requested_customer_id:
        # Look up the requested name to give a clear error
        row = CUSTOMERS[CUSTOMERS["customer_id"] == requested_customer_id]
        requested_name = row.iloc[0]["name"] if not row.empty else f"ID {requested_customer_id}"
        own_name       = logged_in_user.get("name", "you")
        return (
            False,
            f"Access denied. You are logged in as {own_name} (ID {own_id}). "
            f"You cannot access {requested_name}'s account data. "
            f"Please ask only about your own account."
        )

    return True, ""


# ══════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════

def get_customer_id_from_name(name: str) -> int | None:
    """
    Tries to resolve a name mention in a query to a customer_id.
    E.g. "show Anita's loan" → 1002
    Returns None if no match found.
    """
    name_lower = name.strip().lower()
    for _, row in CUSTOMERS.iterrows():
        if name_lower in str(row["name"]).lower() or \
           name_lower == str(row["username"]).lower():
            return int(row["customer_id"])
    return None


def is_logged_in(session_user: dict | None) -> bool:
    return session_user is not None
