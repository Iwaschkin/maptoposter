# Phase 05: Documentation & Build Configuration

## Header

| Field | Value |
|-------|-------|
| **Phase ID** | 05 |
| **Phase Name** | Documentation & Build Configuration |
| **Status** | Not Started |
| **Start Date** | - |
| **Completion Date** | - |
| **Dependencies** | None (can run parallel to Phase 04) |
| **Owner/Assignee** | TBD |

---

## Tracking Data

| Metric | Value |
|--------|-------|
| **Total Issues** | 5 |
| **Resolved Issues** | 0 |
| **Remaining Issues** | 5 |
| **Progress** | 0% |
| **Blockers** | None |

---

## Issue Registry

| Issue ID | Description | Priority | Status | Completion Date | Notes |
|----------|-------------|----------|--------|-----------------|-------|
| CR-0011 | `--name` CLI option documented but not implemented | Medium | Not Started | - | Implement or remove from docs |
| CR-0017 | Placeholder URLs in project metadata | Low | Not Started | - | Update pyproject.toml |
| CR-0018 | Version flag handling duplicates argparse behavior | Low | Not Started | - | Use argparse built-in action |
| CR-0019 | CLI options table omits `--format` and `--version` | Medium | Not Started | - | Update README |
| CR-0014 | Typography positioning hardcoded, not configurable | Medium | Not Started | - | Deferred: Document as known limitation |

---

## Execution Plan

### Task 1: Implement `--name` CLI Option (CR-0011)

**Objective:** Add documented `--name` option to CLI, connecting to `name_label` config.

**Context:** CR-0003 (Phase 03) wires `name_label` to typography. This task exposes it via CLI.

**Changes in cli.py:**

```python
def _create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(...)

    # ... existing arguments ...

    # Add --name option (documented in README)
    parser.add_argument(
        "--name",
        "-n",
        type=str,
        default=None,
        help="Override display name on poster (default: city name)",
        dest="name_label",
    )

    return parser

def cli(args: list[str] | None = None) -> int:
    # ... parse args ...

    config = PosterConfig(
        city=parsed.city,
        country=parsed.country,
        name_label=parsed.name_label,  # Pass to config
        # ... other params ...
    )
```

**Files Affected:**
- `src/maptoposter/cli.py`
- `tests/test_cli.py` (add test for --name)

**Validation:**
- [ ] `maptoposter -c "New York" -C "USA" --name "NYC"` displays "N  Y  C"
- [ ] `--name` appears in `--help` output
- [ ] Unit test for --name parsing

---

### Task 2: Fix Placeholder URLs in pyproject.toml (CR-0017)

**Objective:** Replace placeholder URLs with actual repository information.

**Current State:**
```toml
Homepage = "https://github.com/your-username/maptoposter"
Documentation = "https://github.com/your-username/maptoposter#readme"
Repository = "https://github.com/your-username/maptoposter"
```

**Target State:**
```toml
[project.urls]
Homepage = "https://github.com/ACTUAL_USERNAME/maptoposter"
Documentation = "https://github.com/ACTUAL_USERNAME/maptoposter#readme"
Repository = "https://github.com/ACTUAL_USERNAME/maptoposter"
Issues = "https://github.com/ACTUAL_USERNAME/maptoposter/issues"
```

**Note:** Replace `ACTUAL_USERNAME` with the real GitHub username/organization.

**Files Affected:**
- `pyproject.toml`

**Validation:**
- [ ] No `your-username` placeholder strings in pyproject.toml
- [ ] URLs point to valid repository
- [ ] `uv build` succeeds with updated metadata

---

### Task 3: Use argparse Built-in Version Action (CR-0018)

**Objective:** Replace manual version handling with argparse's `action="version"`.

**Current State (cli.py):**
```python
parser.add_argument("--version", "-v", action="store_true", help="Show version and exit")

# Later in cli():
if parsed.version:
    from . import __version__
    print(f"maptoposter {__version__}")
    return 0
```

**Target State:**
```python
from . import __version__

def _create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(...)

    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    return parser

# Remove manual version check from cli() function
```

**Benefits:**
- Standard argparse behavior (exits automatically)
- Consistent with other CLI tools
- Less code to maintain

**Files Affected:**
- `src/maptoposter/cli.py`
- `tests/test_cli.py` (update version tests if needed)

**Validation:**
- [ ] `maptoposter --version` prints version and exits
- [ ] `maptoposter -v` prints version and exits
- [ ] Exit code is 0

---

### Task 4: Update README CLI Options Table (CR-0019)

**Objective:** Document all CLI options including `--format` and `--version`.

**Current State (README.md):**
Missing `--format`, `--version`, and `--name` from options table.

**Target State:**
```markdown
## Command Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| **REQUIRED:** `--city` | `-c` | City name | - |
| **REQUIRED:** `--country` | `-C` | Country name | - |
| **OPTIONAL:** `--theme` | `-t` | Theme name | `noir` |
| **OPTIONAL:** `--distance` | `-d` | Map radius in meters | `10000` |
| **OPTIONAL:** `--width` | `-W` | Image width in inches | `12` |
| **OPTIONAL:** `--height` | `-H` | Image height in inches | `16` |
| **OPTIONAL:** `--dpi` | | Output resolution | `300` |
| **OPTIONAL:** `--format` | `-f` | Output format (png/svg/pdf) | `png` |
| **OPTIONAL:** `--name` | `-n` | Override display name on poster | City name |
| **OPTIONAL:** `--country-label` | | Override country display | Country name |
| **OPTIONAL:** `--all-themes` | | Generate poster with all themes | `false` |
| **OPTIONAL:** `--list-themes` | | List available themes and exit | - |
| **OPTIONAL:** `--version` | `-v` | Show version and exit | - |
| **OPTIONAL:** `--help` | `-h` | Show help message | - |
```

**Files Affected:**
- `README.md`

**Validation:**
- [ ] All CLI arguments are documented
- [ ] Table matches actual argparse definitions
- [ ] Examples use documented options correctly

---

### Task 5: Document Typography Limitations (CR-0014)

**Objective:** Document that typography positioning is hardcoded as a known limitation.

**Note:** Full fix for CR-0014 (configurable typography positioning) is deferred to a future release. This task documents the limitation.

**Add to README.md (Known Limitations section):**
```markdown
## Known Limitations

- **Typography positioning is hardcoded**: Text positions (city name, country, coordinates)
  are fixed relative to the poster dimensions. Very long city names may extend beyond
  margins. Configurable typography layout is planned for a future release.

- **Memory usage for large areas**: Using `--distance` values above 20,000 meters may
  require significant memory and download time.
```

**Files Affected:**
- `README.md`

**Validation:**
- [ ] Known limitations section exists
- [ ] Typography limitation is documented
- [ ] Users understand what to expect

---

## Validation Criteria

Phase 05 is complete when:

1. ✅ **CR-0011:** `--name` option works and is documented
2. ✅ **CR-0017:** No placeholder URLs in pyproject.toml
3. ✅ **CR-0018:** Version uses argparse built-in action
4. ✅ **CR-0019:** CLI options table is complete
5. ✅ **CR-0014:** Typography limitation is documented
6. ✅ `--help` output matches README documentation
7. ✅ All tests pass

---

## Rollback Plan

If Phase 05 fails:

1. Documentation changes are easily reverted
2. CLI changes are backwards-compatible
3. pyproject.toml changes don't affect functionality

**Safe Rollback Command:**
```bash
git checkout HEAD~1 -- src/maptoposter/cli.py README.md pyproject.toml
```

---

*Phase Document Created: 2026-01-24*
