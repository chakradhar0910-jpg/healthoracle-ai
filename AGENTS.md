# Developer & AI Agent Context (AGENTS.md)

Welcome, AI Developer Agent! This document outlines key context, architectural patterns, and quality gates for maintaining and modifying the **HealthOracle AI** codebase.

---

## 🏗 Repository Architecture

```
HealthOracle-AI/
├── .specify/            # Spec-Kit configuration & templates
├── backend/
│   ├── app.py           # FastAPI entry point, endpoints, and CORS config
│   ├── model.py         # Singleton model manager (loads models, scales inputs, predicts)
│   ├── schemas.py       # Pydantic models for validation contracts
│   ├── train.py         # ML model training script (ingests data + synthetic, fits ensemble)
│   └── utils.py         # Feature engineering & patient clinical recommendations
├── frontend/
│   ├── index.html       # Apple-inspired layout (dashboard + forms)
│   ├── styles.css       # Glassmorphism dark mode custom stylesheet
│   └── script.js        # UI logic + API connection + fallback local inference
├── specs/               # Product/feature specs folder
└── tests/               # Backend endpoint & unit test cases
```

---

## 📜 Coding Principles & Rules

### I. Modular ML Pipeline (Library-First)
All data processing, feature scaling, model training, and predictions must remain separate from the web routing layer.
- Keep ML logic in `backend/model.py`, `backend/train.py`, and `backend/utils.py`.
- The routes in `backend/app.py` should only handle HTTP concerns (status codes, request payload validation, and CORS).

### II. Explicit Contracts (Pydantic Models)
Do not pass untyped dictionaries around. Define all request and response structures explicitly using Pydantic schemas in `backend/schemas.py`.

### III. Local Standalone execution
Do not add dependencies on external APIs or database services for core execution. The app must run completely locally.

### IV. Premium UI & No Placeholders
The frontend uses custom vanilla styling. Do not introduce half-implemented features or temporary placeholders. Keep the interface polished, responsive, and cohesive.

---

## 🛠 Tooling & Quality Gates

Ensure that changes do not break the repository quality score:

- **Linting & Formatting**: Enforced via **Ruff**, **Pylint**, and **Flake8**.
  - **Ruff**: Runs fast linter checks. Run `ruff check backend/ tests/`. Format validation runs via `ruff format --check backend/ tests/`. Configured in `pyproject.toml`.
  - **Pylint**: Runs code analysis and quality checks. Run `pylint backend/`. Configured in `.pylintrc` and `pyproject.toml`.
  - **Flake8**: Enforces pep8 style checking. Run `flake8 backend/`. Configured in `.flake8`.
- **Type Checking**: Enforced via **Mypy**. Run `mypy backend/ tests/`. Configured in `pyproject.toml`.
- **Dead Code Detection**: Enforced via **Vulture**. Run `vulture backend/`. Configured in `.vulture` and `pyproject.toml`.
- **Security & SAST Analysis**: Enforced via **Bandit** and **Semgrep**.
  - **Bandit**: Scans for Python security issues. Run `bandit -r backend/ -c bandit.yaml`. Configured in `bandit.yaml` and `pyproject.toml`.
  - **Semgrep**: Scans code with pattern matching. Run `semgrep --config=.semgrep.yaml backend/`. Configured in `.semgrep.yaml`.
- **Code Modernization**: Enforced via **Pyupgrade**. Run `find backend/ -name "*.py" | xargs pyupgrade --py311-plus`. Configured in `pyproject.toml`.
- **Unit Testing**: Enforced via **Pytest** with coverage checks. Run `pytest tests/`.
- **Pre-commit Checks**: Registered hooks check YAML files, trailing whitespaces, enforce Ruff formatting, run type-checking, search for secrets, and audit dependencies.
- **GitLab CI Pipeline**: Configured stages run all of the above tests automatically on commit (`test`, `lint`, `format`, `type_check`, `coverage`).

