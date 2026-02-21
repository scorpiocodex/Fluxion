# Contributing to Fluxion

Thank you for your interest in contributing to **Fluxion — The Intelligent Network Command Engine**.

## Getting Started

### Prerequisites

- Python 3.11+
- Git

### Setup

```bash
# Fork and clone
git clone https://github.com/scorpiocodex/Fluxion.git
cd Fluxion

# Install in editable dev mode (includes all dev dependencies)
pip install -e ".[dev]"

# Verify installation
fluxion version
fluxion doctor
```

## Development Workflow

### Running Tests

```bash
# All tests with coverage
pytest

# Specific module
pytest tests/unit/test_cli.py -v

# Without coverage (faster)
pytest --no-cov -q
```

### Linting & Formatting

```bash
# Lint with ruff
ruff check fluxion/ tests/

# Auto-fix lint issues
ruff check --fix fluxion/ tests/

# Format with black
black fluxion/ tests/

# Type check with mypy
mypy fluxion/ --ignore-missing-imports
```

### Running All Checks (matches CI)

```bash
ruff check fluxion/ tests/ && black --check fluxion/ tests/ && mypy fluxion/ --ignore-missing-imports && pytest
```

## Code Style

- **Formatter**: Black (100-char line length)
- **Linter**: Ruff (`E, F, W, I, N, UP, B, A, SIM, TCH` rules)
- **Type checker**: mypy (strict mode)
- **Target Python**: 3.11+
- **Async**: All I/O-bound operations must be `async`/`await`
- **Models**: Use Pydantic for all data structures
- **UI**: Use Rich for all terminal output

## Project Structure

```
fluxion/
├── cli/app.py          # CLI commands — add new commands here
├── core/engine.py      # Download engine — core transport logic
├── hud/panels.py       # UI panels — add new panel renderers here
├── performance/        # Adaptive transport algorithms
├── security/           # TLS, integrity, proxy
├── stealth/            # Browser impersonation, cookies
├── protocols/          # FTP, SFTP, QUIC handlers
├── plugins/            # Plugin system
├── installer/          # Init, config, doctor
└── platform/           # OS/arch detection
```

## Adding a New Command

1. Add a new `@app.command()` function in `fluxion/cli/app.py`
2. Add command data to `_HELP_CATEGORIES` and `_COMMAND_DETAILS` in `fluxion/hud/panels.py`
3. Add tests in `tests/unit/test_cli.py`
4. Update `README.md` with command documentation

## Adding a New Protocol

1. Create `fluxion/protocols/<protocol>.py` implementing async download
2. Register it in `fluxion/core/engine.py`
3. Add tests in `tests/unit/`
4. Document in README

## Pull Request Guidelines

1. Fork the repository and create a feature branch
2. Write tests for your changes (maintain 55%+ coverage)
3. Ensure all linters and type checks pass
4. Update documentation if needed
5. Submit a pull request with a clear description

## Bug Reports

Use the [GitHub Issues](https://github.com/scorpiocodex/Fluxion/issues) page. Include:
- Python version (`python --version`)
- Fluxion version (`fluxion version`)
- Platform info (`fluxion doctor --json`)
- Minimal reproduction steps
- Full error output with `--trace` flag

## Feature Requests

Open a [GitHub Issue](https://github.com/scorpiocodex/Fluxion/issues) with:
- Use case description
- Expected behavior
- Comparison with existing tools (if applicable)

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
