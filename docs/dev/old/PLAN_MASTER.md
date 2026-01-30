# MapToPoster Code Review Remediation Plan

## Overview

| Metric | Value |
|--------|-------|
| **Source Document** | [2026-01-24-opus-review.md](code-reviews/2026-01-24-opus-review.md) |
| **Plan Created** | 2026-01-24 |
| **Total Issues** | 23 |
| **Total Phases** | 6 |
| **Current Phase** | Not Started |
| **Overall Progress** | 0% |

---

## Issue Inventory (Step 1 Output)

All 23 issues extracted from the code review, grouped by atomic work type:

| ID | Severity | Category | Component | Title | Dependencies |
|----|----------|----------|-----------|-------|--------------|
| CR-0001 | Blocker | Security | cache | Pickle deserialization allows arbitrary code execution | None |
| CR-0002 | High | Reliability | geo | Cache errors swallowed, converted to warnings | CR-0004 |
| CR-0003 | Medium | Bug | config/render | `name_label` parameter accepted but never used | None |
| CR-0004 | Medium | Bug | cache | Exception handling inconsistency in `cache_get` | None |
| CR-0005 | Medium | Reliability | geo | Silent failures with generic error messages | None |
| CR-0006 | Medium | Bug | config | Missing theme key validation | None |
| CR-0007 | Medium | Reliability | geo | Fragile async/sync event loop detection | None |
| CR-0008 | High | Test gap | render | No test coverage for rendering module | CR-0003, CR-0016, CR-0023 |
| CR-0009 | High | Test gap | geo | No test coverage for geographic module | CR-0005, CR-0007, CR-0015 |
| CR-0010 | Low | Config/Build | root | Duplicate cache directories in project | None |
| CR-0011 | Medium | Docs mismatch | README | `--name` CLI option documented but not implemented | CR-0003 |
| CR-0012 | Low | Bug | config | `get_available_themes` silently creates missing directory | None |
| CR-0013 | Low | Reliability | fonts | Font fallback logic incomplete | None |
| CR-0014 | Medium | API/Contract | render | Typography positioning hardcoded, not configurable | None (deferred) |
| CR-0015 | Low | Performance | geo | Blocking `time.sleep()` calls impact UX | CR-0002 |
| CR-0016 | Medium | Reliability | render | Projection fallback exceptions silently caught | None |
| CR-0017 | Low | Config/Build | pyproject.toml | Placeholder URLs in project metadata | None |
| CR-0018 | Low | Dead code | cli | Version flag handling duplicates argparse behavior | None |
| CR-0019 | Medium | Docs mismatch | README | CLI options table omits `--format` and `--version` | None |
| CR-0020 | Medium | Config/Build | .github | No CI workflow to run tests/lint | Phases 1-4 |
| CR-0021 | Medium | Bug | cli | `cli([])` ignores provided args and reads `sys.argv` | None |
| CR-0022 | Medium | Bug | config | Output filename sanitization incomplete for Windows | None |
| CR-0023 | Low | Reliability | render | `create_poster()` does not ensure output directory exists | None |

---

## Phase Status Matrix (Step 2 Output)

| Phase | Name | Status | Issues (Done/Total) | Progress | Blocked | Start Date | End Date |
|-------|------|--------|---------------------|----------|---------|------------|----------|
| 01 | Security & Cache Foundation | Not Started | 0/4 | 0% | No | - | - |
| 02 | Error Handling Consistency | Not Started | 0/5 | 0% | No | - | - |
| 03 | Bug Fixes & Config Hardening | Not Started | 0/6 | 0% | No | - | - |
| 04 | Test Coverage Expansion | Not Started | 0/2 | 0% | Yes (Phases 1-3) | - | - |
| 05 | Documentation & Build | Not Started | 0/5 | 0% | No | - | - |
| 06 | CI/CD & Polish | Not Started | 0/1 | 0% | Yes (Phases 1-5) | - | - |

---

## Dependency Graph

```
Phase 01: Security & Cache Foundation
    │
    └─► Phase 02: Error Handling Consistency
            │
            └─► Phase 03: Bug Fixes & Config Hardening
                    │
                    └─► Phase 04: Test Coverage Expansion ◄── Requires stable code
                            │
                            └─► Phase 05: Documentation & Build (can run parallel)
                                    │
                                    └─► Phase 06: CI/CD & Polish
```

**Key Dependencies:**
- Phase 02 depends on Phase 01: Cache exception contract must be stable before geo module error handling
- Phase 04 depends on Phases 01-03: Tests should cover fixed code, not bugs
- Phase 06 depends on all: CI should verify the remediated codebase

---

## Phase Documents

| Phase | Document | Issues Covered |
|-------|----------|----------------|
| 01 | [PHASE_01_SECURITY_CACHE.md](PHASE_01_SECURITY_CACHE.md) | CR-0001, CR-0004, CR-0010, CR-0015 |
| 02 | [PHASE_02_ERROR_HANDLING.md](PHASE_02_ERROR_HANDLING.md) | CR-0002, CR-0005, CR-0007, CR-0013, CR-0016 |
| 03 | [PHASE_03_BUG_FIXES.md](PHASE_03_BUG_FIXES.md) | CR-0003, CR-0006, CR-0012, CR-0021, CR-0022, CR-0023 |
| 04 | [PHASE_04_TEST_COVERAGE.md](PHASE_04_TEST_COVERAGE.md) | CR-0008, CR-0009 |
| 05 | [PHASE_05_DOCS_BUILD.md](PHASE_05_DOCS_BUILD.md) | CR-0011, CR-0017, CR-0018, CR-0019, CR-0014 |
| 06 | [PHASE_06_CICD.md](PHASE_06_CICD.md) | CR-0020 |

---

## Risk Register

| Risk ID | Description | Probability | Impact | Mitigation | Status |
|---------|-------------|-------------|--------|------------|--------|
| R-01 | Pickle removal breaks existing cached data | High | Medium | Document migration path, provide cache clear command | Open |
| R-02 | OSMnx API changes during remediation | Low | High | Pin version, add integration tests | Open |
| R-03 | Test mocking complexity for geo module | Medium | Medium | Use VCR.py or responses library for HTTP mocking | Open |
| R-04 | Breaking changes to CLI behavior | Medium | Low | Maintain backwards compatibility, add deprecation warnings | Open |

---

## Change Log

| Date | Change | Rationale | Author |
|------|--------|-----------|--------|
| 2026-01-24 | Initial plan created | Based on GPT-5.2-Codex code review | AI Agent |

---

## Success Criteria

The remediation is complete when:

1. ✅ All 23 issues are marked as completed
2. ✅ All 6 phases are marked as completed
3. ✅ Test coverage exceeds 80% on geo.py and render.py
4. ✅ CI workflow passes on main branch
5. ✅ No Blocker or High severity issues remain open
6. ✅ Documentation matches actual CLI capabilities
7. ✅ Security vulnerability (pickle) is eliminated

---

*Last Updated: 2026-01-24*
