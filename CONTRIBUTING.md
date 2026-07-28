# Contributing to Enterprise NIDS

Thank you for your interest in contributing to the Machine Learning-Based Enterprise Network Intrusion Detection System (NIDS)!

---

## 🚀 How to Contribute

### 1. Reporting Bugs
- Search existing GitHub Issues before submitting a new bug report.
- Use the **Bug Report Template** (`.github/ISSUE_TEMPLATE/bug_report.md`).
- Include full stack traces, operating system details, and exact reproduction steps.

### 2. Requesting Features
- Use the **Feature Request Template** (`.github/ISSUE_TEMPLATE/feature_request.md`).
- Explain the use case and security benefits of the proposed feature.

### 3. Submitting Pull Requests (PRs)
1. Fork the repository and create a feature branch (`git checkout -b feature/amazing-feature`).
2. Follow PEP8 style guidelines for Python code (`black` and `flake8`).
3. Ensure all unit tests pass (`python scripts/run_tests.py`).
4. Ensure environment validation passes (`python scripts/check_environment.py`).
5. Open a Pull Request adhering to `.github/PULL_REQUEST_TEMPLATE.md`.

---

## 🧪 Local Testing Requirements

All contributions must maintain 100% test pass rates and high test coverage:

```bash
# Run automated test suite
python scripts/run_tests.py

# Run performance benchmark suite
python scripts/run_benchmark.py
```
