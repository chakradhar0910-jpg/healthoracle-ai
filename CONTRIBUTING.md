# Contributing to HealthOracle AI

We welcome contributions to HealthOracle AI! Please follow these guidelines to ensure a smooth contribution process.

## Development Environment Setup

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd healthoracle-ai
   ```

2. **Set up a Virtual Environment**:
   ```bash
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-cov ruff mypy
   ```

4. **Initialize Pre-commit Hooks**:
   ```bash
   pip install pre-commit
   pre-commit install
   ```

## Development Workflow

1. **Conventional Commits**:
   Please write commits matching the conventional commit style:
   - `feat: add new symptom checklist`
   - `fix: correct heart disease scaler loading`
   - `docs: update user manual`
   - `test: add unit test for API prediction`

2. **Coding Standards**:
   - Python code must be formatted using Black/Ruff and pass Ruff lint checks.
   - Run type checks using `mypy`.
   - Write tests for any new endpoints or logic in the `tests/` directory.

## Verifying Code

Run the full validation suite before making a pull request:
```bash
# Run tests
pytest tests/

# Run linter
ruff check backend/ tests/

# Run type checker
mypy backend/ tests/
```

## Pull Request Guidelines

- Create a feature branch from `main` or `master`.
- Ensure all CI tests and linter checks pass.
- Update documentation in `USER_MANUAL.md` or `README.md` if your changes introduce new parameters or behavior.
