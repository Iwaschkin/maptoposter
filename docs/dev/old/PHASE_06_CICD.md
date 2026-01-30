# Phase 06: CI/CD Implementation

## Header

| Field | Value |
|-------|-------|
| **Phase ID** | 06 |
| **Phase Name** | CI/CD Implementation |
| **Status** | Not Started |
| **Start Date** | - |
| **Completion Date** | - |
| **Dependencies** | Phases 01-05 (CI should verify remediated codebase) |
| **Owner/Assignee** | TBD |

---

## Tracking Data

| Metric | Value |
|--------|-------|
| **Total Issues** | 1 |
| **Resolved Issues** | 0 |
| **Remaining Issues** | 1 |
| **Progress** | 0% |
| **Blockers** | Waiting for all previous phases |

---

## Issue Registry

| Issue ID | Description | Priority | Status | Completion Date | Notes |
|----------|-------------|----------|--------|-----------------|-------|
| CR-0020 | No CI workflow to run tests/lint | Medium | Not Started | - | Add GitHub Actions workflow |

---

## Execution Plan

### Task 1: Create CI/CD Workflow (CR-0020)

**Objective:** Add GitHub Actions workflow to run tests, linting, and type checking on PRs and pushes.

**Create `.github/workflows/ci.yml`:**

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    name: Test (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.11", "3.12"]

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "latest"

      - name: Set up Python ${{ matrix.python-version }}
        run: uv python install ${{ matrix.python-version }}

      - name: Install dependencies
        run: uv sync --all-extras

      - name: Run tests with coverage
        run: uv run pytest --cov=src/maptoposter --cov-report=xml --cov-report=term-missing

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        if: matrix.python-version == '3.12'
        with:
          files: ./coverage.xml
          fail_ci_if_error: false
        env:
          CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}

  lint:
    name: Lint & Type Check
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "latest"

      - name: Set up Python
        run: uv python install 3.12

      - name: Install dependencies
        run: uv sync --all-extras

      - name: Run Ruff linter
        run: uv run ruff check src/ tests/

      - name: Run Ruff formatter check
        run: uv run ruff format --check src/ tests/

      - name: Run mypy type checker
        run: uv run mypy src/maptoposter/

  pre-commit:
    name: Pre-commit Hooks
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "latest"

      - name: Set up Python
        run: uv python install 3.12

      - name: Install dependencies
        run: uv sync --all-extras

      - name: Run pre-commit
        run: uv run pre-commit run --all-files
```

**Files Affected:**
- `.github/workflows/ci.yml` (new file)

**Validation:**
- [ ] Workflow triggers on push to main
- [ ] Workflow triggers on PR to main
- [ ] Tests pass in CI environment
- [ ] Linting passes
- [ ] Type checking passes
- [ ] Pre-commit hooks pass

---

### Task 2: Add Branch Protection (Optional - Manual Step)

**Objective:** Require CI to pass before merging PRs.

**Manual Steps in GitHub:**
1. Go to repository Settings → Branches
2. Add branch protection rule for `main`
3. Enable "Require status checks to pass before merging"
4. Select required checks: `test`, `lint`, `pre-commit`
5. Enable "Require branches to be up to date before merging"

**Note:** This is a manual GitHub configuration step, not a code change.

---

### Task 3: Add CI Status Badge to README

**Objective:** Show CI status prominently in README.

**Add to top of README.md:**
```markdown
# MapToPoster

[![CI](https://github.com/ACTUAL_USERNAME/maptoposter/actions/workflows/ci.yml/badge.svg)](https://github.com/ACTUAL_USERNAME/maptoposter/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python CLI tool that generates minimalist map posters...
```

**Note:** Replace `ACTUAL_USERNAME` with real GitHub username.

**Files Affected:**
- `README.md`

**Validation:**
- [ ] Badge displays correct CI status
- [ ] Badge links to workflow runs

---

## CI Configuration Details

### Test Matrix

| Python Version | Status |
|----------------|--------|
| 3.11 | Primary support |
| 3.12 | Primary support |

### Quality Checks

| Check | Tool | Configuration |
|-------|------|---------------|
| Linting | Ruff | `ruff.toml` or `pyproject.toml` |
| Formatting | Ruff | `ruff format` |
| Type Checking | mypy | `pyproject.toml` |
| Tests | pytest | `pytest.ini` or `pyproject.toml` |
| Pre-commit | pre-commit | `.pre-commit-config.yaml` |

### Expected CI Run Time

| Job | Estimated Time |
|-----|----------------|
| test (3.11) | ~2-3 minutes |
| test (3.12) | ~2-3 minutes |
| lint | ~30 seconds |
| pre-commit | ~1 minute |
| **Total (parallel)** | ~3-4 minutes |

---

## Validation Criteria

Phase 06 is complete when:

1. ✅ **CR-0020:** CI workflow exists and runs on PRs
2. ✅ All CI jobs pass on main branch
3. ✅ Tests run successfully in CI environment
4. ✅ Linting passes in CI
5. ✅ Type checking passes in CI
6. ✅ CI status badge added to README

---

## Rollback Plan

If Phase 06 fails:

1. CI workflow is additive; removal has no production impact
2. Delete `.github/workflows/ci.yml` to disable CI
3. Remove badge from README

**Safe Rollback Command:**
```bash
rm .github/workflows/ci.yml
git checkout HEAD~1 -- README.md
```

---

## Post-Phase Actions

After Phase 06 completion:

1. **Enable Dependabot** for security updates:
   ```yaml
   # .github/dependabot.yml
   version: 2
   updates:
     - package-ecosystem: "pip"
       directory: "/"
       schedule:
         interval: "weekly"
   ```

2. **Consider adding**:
   - Release workflow for PyPI publishing
   - Nightly test runs against latest dependencies
   - Performance benchmarking

---

*Phase Document Created: 2026-01-24*
