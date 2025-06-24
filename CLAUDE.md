# General project information

- this project uses uv as a package manager. 
- to add a new package, run `uv add <package_name>`.

# Claude Development Quality Assurance

This document establishes quality gates and workflows for Claude development sessions to ensure code quality, proper testing, and organized commits.

## Quality Gates - Always Run These

### After Implementing new Features or Refactoring existing Code
```bash
./dev.sh check
```
**Purpose**: Ensure type safety and catch type-related issues early.
**When**: After any modification to Python code in `src/`
**Must Pass**: Yes - Do not proceed if type checking fails

### After Changing Core Logic
```bash
./dev.sh test_unit
```
**Purpose**: Ensure existing functionality still works (regression testing)
**When**: After modifying `src/core/` or critical `src/routes/` logic
**Must Pass**: Yes - Fix any breaking unit tests before continuing

### After API Changes
```bash
./dev.sh test_integration
```
**Purpose**: Ensure API contracts and integrations work correctly
**When**: After modifying API endpoints, request/response models, or integration points
**Must Pass**: Yes - API changes must not break existing integrations

## Testing Requirements

### For New Features
1. **Write unit tests FIRST** - Test-driven approach preferred
2. **Run new tests**: `pytest path/to/new/test_file.py -v`
3. **Ensure they pass** before considering feature complete
4. **Run full unit suite**: `./dev.sh test_unit` to ensure no conflicts

### For New External Integrations
1. **Write integration tests** with VCR cassettes or controlled inputs
2. **Consider E2E tests** if the integration affects real external services
3. **Run integration suite**: `./dev.sh test_integration`

### For Bug Fixes
1. **Write a failing test** that reproduces the bug
2. **Fix the bug** until the test passes
3. **Run unit tests** to ensure no regressions: `./dev.sh test_unit`

## Session Completion Checklist

Before reporting "task complete" or "feature ready", run through this checklist:

### ✅ Code Quality
- [ ] `./dev.sh check` passes (no type errors)
- [ ] Code follows existing patterns and conventions
- [ ] No obvious code smells or technical debt introduced

### ✅ Testing
- [ ] `./dev.sh test_unit` passes (all existing tests work)
- [ ] New features have corresponding unit tests
- [ ] New tests are written and passing
- [ ] Integration tests pass if API/external changes made: `./dev.sh test_integration`

### ✅ Functionality
- [ ] Feature works as expected through manual testing
- [ ] Edge cases and error conditions are handled
- [ ] API responses are correct format and content

### ✅ Documentation
- [ ] Code changes are self-documenting or have comments where necessary
- [ ] API changes are reflected in examples/documentation if needed

### ✅ No Regressions
- [ ] Existing functionality still works
- [ ] No breaking changes to public APIs (unless intentional)
- [ ] Performance hasn't degraded noticeably

## Quick Command Reference

```bash
# Quality Gates
./dev.sh check           # Type checking (always run)
./dev.sh test_unit       # Unit tests (after core changes)
./dev.sh test_integration # Integration tests (after API changes)
./dev.sh test_all        # All tests (before major completion)

# Development
./dev.sh serve           # Start server for manual testing
./curl.sh health         # Quick API health check

# Testing Specific Files
pytest path/to/test_file.py -v              # Run specific test file
pytest -k "test_function_name" -v           # Run specific test function
pytest --cov=src --cov-report=term-missing  # Coverage report
```

## Emergency Debugging

If something breaks and you need to debug quickly:

1. **Check what's running**: Is it Docker or local server?
2. **Restart services**: Stop Docker, restart local server
3. **Verify environment**: `./dev.sh check` for basic validation
4. **Run targeted tests**: `./dev.sh test_unit` for core logic
5. **Check recent changes**: `git diff` to see what changed

## Remember

- **Quality over speed**: Better to take time ensuring quality than to rush and introduce bugs
- **Test early, test often**: Don't wait until the end to run tests
- **Document as you go**: Update examples and documentation when changing APIs
- **Atomic commits**: Each commit should represent one logical change that could stand alone