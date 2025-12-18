# Loan Document Processing

This application is designed to streamline the processing of loan documents. It uses AI/ML models to automatically classify incoming documents and extract relevant data, presenting the results in an interactive web-based dashboard.

## Getting Started

### Prerequisites

- Python 3.10+
- Poetry for dependency management

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd loan-document-processing
    ```

2.  **Install dependencies:**
    ```bash
    poetry install
    ```

3.  **Setup environment variables:**
    Create a `.env` file inside the `src/ui/` directory. You may need to add credentials for the services being used (e.g., OpenAI, Google Cloud).
    ```
    # src/ui/.env
    API_KEY="your_api_key_here"
    PROJECT_ID="project_id_here"
    BUCKET_NAME="bucket_name_here"
    ```

## Usage

To run the web application, execute the following command from the root of the project:

```bash
streamlit run src/ui/main.py
```

## Directory Structure

Here is an overview of the project's directory structure:

```
.
├── pyproject.toml      # Project metadata and dependencies for Poetry
├── README.md           # This file
├── resources/
│   └── documents/      # Directory for storing and accessing documents
└── src/
    ├── backend/        # Core application logic and AI/ML modules
    │   ├── classifier/   # Document classification module
    │   ├── commons/      # Shared utilities (e.g., LLM factory, storage access)
    │   ├── dashboard/    # Logic for dashboard data aggregation
    │   ├── extraction/   # Data extraction module from documents
    │   ├── facade/       # Simplified interface for core backend services
    │   ├── learning_loop/# Module for continuous model improvement
    │   └── prompts/      # LLM prompts and related configurations
    └── ui/             # Streamlit-based user interface
        ├── main.py       # Main entry point for the Streamlit application
        ├── .env          # Environment variable configuration for the UI
        └── pages/        # Individual pages of the Streamlit application
```

## Architecture

**Version 1**

**Objective:** Maximize time-to-market by leveraging out-of-the-box components.

**Architecture & Components**
* **Modular Monolith:** The entire system resides in a single repository and runs in a single process, eliminating DevOps operational complexity.
* **AI Engine:** Multimodal LLMs with Few-Shot Prompting unify document classification and data extraction.
* **Interface (HITL):** Streamlit (Python) is used for agile development of the Human-in-the-Loop workflow.
* **Persistence:** Firestore is used for storing results and metrics.

**Relevant Quality Attributes**
* **Performance:** The system must have a response time of under 30 seconds for classification and extraction.
* **Performance:** The system must have a dashboard load time of under 5 seconds.
* **Portability:** The system must be accessible via major web browsers.
* **Security:** The system must mask sensitive data in logs.
* **Maintainability:** The system must be modular to facilitate maintenance.
* **Availability:** The system must be available during business hours.

**Trade-offs & Limitations**
* **Scalability:** Tight coupling prevents independent scaling of resources (CPU vs. I/O) within each module. It does not allow for granular component scaling.
* **External Dependency:** Reliance on third-party APIs introduces variable costs and a risk of vendor lock-in.

### Context Diagram

<img width="681" height="581" alt="Loan System - Context drawio" src="https://github.com/user-attachments/assets/f79d6b38-918d-4914-bd75-df1acc5aa163" />

### Container Diagram

<img width="1086" height="991" alt="Loan System - Container Diagram drawio" src="https://github.com/user-attachments/assets/0dc59162-4033-4588-bb1b-72922b065c92" />

### Component Diagram

<img width="1471" height="1201" alt="Loan System - Component Diagram drawio" src="https://github.com/user-attachments/assets/2913331d-ebf5-400b-80a3-5eceb2d2a9b4" />

## Code Quality & Tooling

This project uses the following tools to ensure code quality:

-   **Ruff:** For linting and code formatting.
-   **mypy:** For static type checking.
-   **pre-commit:** To run checks automatically before each commit.
