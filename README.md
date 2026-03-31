# SafeNest

SafeNest is an intelligent banking assistant built as a Streamlit application. It lets a customer ask banking questions in natural language and returns a focused response by routing the request to the right specialist agent. The project is designed as a realistic banking support prototype that combines a simple user experience with intent detection, agent-based processing, access control, caching, usage tracking, and structured banking data.

## Why This Project Exists

Modern banking users expect fast, clear answers without navigating multiple menus or waiting for manual support for every question. SafeNest addresses that gap by providing:

- A single conversational entry point for common banking queries
- Specialized processing for loans, transactions, fraud, compliance, and support
- Guardrails to prevent users from accessing other customers' information
- A lightweight admin view for monitoring usage and system activity

The goal is not just to answer questions, but to demonstrate how an AI-assisted banking workflow can be made safer, clearer, and easier to operate.

## What SafeNest Does

SafeNest accepts a user query such as:

- `Am I eligible for a personal loan?`
- `Why was my last transaction blocked?`
- `Is there suspicious activity on the account?`
- `Is the account compliant with banking rules?`
- `How do I increase my transfer limit?`

The application then:

1. Authenticates the user
2. Verifies the query is about the logged-in customer
3. Checks whether a cached answer already exists
4. Detects the query intent
5. Routes the request to the correct banking agent
6. Formats the response for the user interface
7. Records usage, logs activity, and displays the result in Streamlit

## Core Capabilities

- Natural-language banking query handling
- Intent-based routing to domain-specific agents
- Customer-side and admin-side interfaces
- Daily usage limit tracking
- Query caching for repeated requests
- Access-denial handling for third-party customer references
- Debug visibility for raw agent output
- Support case similarity search using vector data

## Available Agents

### Loan Eligibility Agent

Evaluates whether a customer is likely to qualify for a loan by using customer profile data, loan records, and decision logic.

### Transaction Agent

Explains blocked, declined, or unusual transactions using transaction history and transaction-specific tools.

### Fraud Detection Agent

Reviews account activity to identify suspicious patterns and flags possible fraud-related issues.

### Compliance Agent

Checks the customer account against defined banking and policy rules stored in the compliance data.

### Support Agent

Uses support ticket knowledge and similarity-based matching to answer general service questions and provide resolution guidance.

## How the System Works

### 1. Login and Session Handling

Users sign in through the Streamlit interface. The app stores the authenticated user in session state and uses that context throughout the interaction.

### 2. Query Submission

Customers can either type a question manually or click one of the suggested queries shown in the UI.

### 3. Access Validation

Before any LLM call is made, the app checks whether the query appears to reference another customer. If so, the request is blocked immediately.

### 4. Cache Check

If the same user has already asked the same question, SafeNest can return the cached result instead of repeating the full processing flow.

### 5. Intent Detection

The app sends the customer query to the LLM layer, which classifies the request into one of the supported intent groups.

### 6. Agent Routing

The coordinator sends the request to the correct specialist agent based on the detected intent.

### 7. Response Formatting

The agent returns a raw result. The LLM formatting layer turns that result into a clear customer-facing answer.

### 8. Logging and Usage Tracking

The system records activity such as logins, queries, access denials, cache hits, and errors. It also tracks token usage and daily query limits.

## User Experience

The customer-facing interface includes:

- Secure login
- Suggested frequently used banking questions
- A simple text input for new questions
- A response area that shows the latest answers first
- A usage-limit indicator
- Cached-response labeling where applicable

The admin interface includes:

- Cache clearing
- Token limit reset controls
- User-level statistics
- Log visibility
- User search and account-related data review

## Project Structure

```text
SafeNest_V6/
├── app.py
├── README.md
├── requirements.txt
├── safenest.log
├── .streamlit/
│   └── secrets.toml
├── agents/
│   ├── loan_agent.py
│   ├── transaction_agent.py
│   ├── fraud_agent.py
│   ├── compliance_agent.py
│   ├── support_agent.py
│   └── tools/
│       ├── loan_tools.py
│       ├── transaction_tools.py
│       ├── fraud_tools.py
│       ├── compliance_tools.py
│       └── support_tools.py
├── auth/
│   └── auth.py
├── coordinator/
│   └── coordinator.py
├── data/
│   ├── customers.csv
│   ├── transactions.csv
│   ├── loans.csv
│   ├── support_tickets.csv
│   ├── compliance_rules.csv
│   └── vector_store/
│       ├── index.faiss
│       └── index.pkl
├── llm/
│   └── groq_client.py
├── models/
│   └── similarity_model.py
└── utils/
    ├── cache.py
    ├── logger.py
    └── tool_parsing.py
```

## Technology Stack

- Python
- Streamlit
- Groq API
- LangChain packages
- Pandas
- NumPy
- scikit-learn
- FAISS
- sentence-transformers

## Data Used by the Project

The application runs on structured local datasets stored under the `data/` directory.

- `customers.csv` stores customer identity and profile details
- `transactions.csv` stores transaction records
- `loans.csv` stores loan-related information
- `support_tickets.csv` stores support history
- `compliance_rules.csv` stores rule definitions
- `vector_store/` stores the prebuilt similarity index used for support search

## Prerequisites

Before running the project, make sure you have:

- Python 3.10 or later installed
- `pip` available in your environment
- A valid Groq API key

## Installation

### 1. Open the project folder

```bash
cd "D:\Virtusa Project\SafeNest_V6"
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the virtual environment

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

On Command Prompt:

```cmd
.venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

## Configure Secrets

Create or update the file `.streamlit/secrets.toml` with your Groq API key:

```toml
GROQ_API_KEY = "your_groq_api_key_here"
```

## How to Run the Project

From the project root folder, run:

```bash
streamlit run app.py
```

After startup, Streamlit will open the application in your browser, typically at:

```text
http://localhost:8501
```

## Demo Accounts

The application includes built-in demo users for testing.

| Username | Password | Role |
|---|---|---|
| `arjun` | `arjun123` | Customer |
| `rahul` | `rahul123` | Customer |
| `anita` | `anita123` | Customer |
| `vikram` | `vikram123` | Customer |
| `priya` | `priya123` | Customer |
| `admin` | `admin123` | Admin |

## Example Customer Queries

- `Am I eligible for a personal loan?`
- `Why was my last transaction blocked?`
- `My card was charged twice`
- `Is there suspicious activity on the account?`
- `Is the account compliant with banking rules?`
- `How do I increase my transfer limit?`

## Key Design Decisions

### Specialized Routing

Instead of using one generic answer flow for every banking question, SafeNest routes requests to purpose-specific agents. This keeps the logic easier to maintain and improves response relevance.

### Safety Before Intelligence

The project checks for cross-customer references before spending LLM tokens. This is important in banking scenarios where privacy and data separation matter.

### Cached Reuse

Repeated questions can be answered from cache, which improves speed and reduces repeated processing cost.

### Separate Customer and Admin Views

Customers see a simplified experience focused on asking questions. Admin users get visibility into operations, usage, and support controls.

## Logs and Monitoring

Application activity is recorded in:

```text
safenest.log
```

This log can help during testing, troubleshooting, and demo walkthroughs.

## Troubleshooting

### The app does not start

- Make sure all dependencies are installed
- Confirm the virtual environment is activated
- Check that `streamlit` is available in the current Python environment

### API-related errors occur

- Verify the Groq API key is present in `.streamlit/secrets.toml`
- Confirm the key is valid and active
- Check whether the account has hit usage or rate limits

### Responses do not appear correctly

- Confirm the project is being run from the correct folder
- Check the browser console and Streamlit logs for rendering or runtime issues
- Review `safenest.log` for backend-side errors

## Intended Outcome

SafeNest is built to demonstrate a practical AI-enabled banking assistant that is understandable, structured, and presentable as a project delivery. It shows how conversational UX, routing logic, security checks, and operational controls can work together in a single application.

## Authoring Note

This README is written as a delivery document for the project. It focuses on what the system does, why it exists, how it works, and how to run it successfully.
