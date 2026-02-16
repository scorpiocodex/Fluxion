# Contributing to Fluxion

Thank you for your interest in contributing to **Fluxion**. Every contribution strengthens the engine.

## Getting Started

### 1. Fork & Clone

```bash
git clone https://github.com/<your-username>/fluxion.git
cd fluxion
```

### 2. Set Up Development Environment

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### 3. Install Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
```

### 4. Verify Setup

```bash
fluxion doctor
pytest
```

## Development Workflow

### Branching

- `main` — stable release branch
- `dev` — active development
- Feature branches: `feat/<description>`
- Bug fixes: `fix/<description>`

### Code Quality

All code must pass before merge:

```bash
ruff check fluxion/ tests/        # Linting
black --check fluxion/ tests/     # Formatting
mypy fluxion/ --ignore-missing-imports  # Type checking
pytest --cov=fluxion              # Tests (55%+ coverage required)
```

### Writing Tests

- Place unit tests in `tests/unit/`
- Place integration tests in `tests/integration/`
- Use `pytest-asyncio` for async tests (auto mode enabled)
- Use `respx` for HTTP request mocking
- Aim to cover both success and error paths

### Commit Messages

Use clear, descriptive commit messages:

```
feat: add HTTP/3 fallback for QUIC connection failures
fix: resolve chunker stall on zero-byte range response
docs: update plugin creation guide
test: add coverage for TLS cert pinning
refactor: simplify retry classifier backoff logic
```

## What to Contribute

### High-Impact Areas

- **Protocol plugins** — Add support for new protocols (S3, WebDAV, BitTorrent, IPFS)
- **Performance** — Optimize the adaptive chunker, scheduler, or bandwidth estimator
- **Platform support** — Improve detection and compatibility for new OS/distro combinations
- **Security** — Strengthen TLS inspection, add OCSP stapling, certificate transparency checks
- **Tests** — Increase coverage, add edge case tests, improve integration tests

### Plugin Development

See the [Plugin System](README.md#-plugins) section of the README for the plugin architecture, base classes, and conventions.

## Pull Request Guidelines

1. Create a feature branch from `dev`
2. Write tests for new functionality
3. Ensure all checks pass (`ruff`, `black`, `mypy`, `pytest`)
4. Write a clear PR description explaining the **what** and **why**
5. Keep PRs focused — one feature or fix per PR

## Reporting Issues

When filing an issue, include:

- Fluxion version (`fluxion version`)
- OS and Python version (`fluxion doctor --json`)
- Steps to reproduce
- Expected vs. actual behavior
- Relevant error output or logs

## Code of Conduct

Be respectful, constructive, and collaborative. We're all building something better.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
