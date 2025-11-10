# LeadSauce CLI - Test Suite

Comprehensive regression test suite for the LeadSauce CLI application.

## Overview

This test suite provides comprehensive coverage for:
- Navigation and keyboard shortcuts
- CRUD operations for all models
- Relationship management
- Task and Goal tracking
- Data integrity
- Edge cases and error handling

## Test Structure

```
tests/
├── conftest.py                          # Shared fixtures and test configuration
├── test_models/                         # Model and database tests
│   ├── test_profile_crud.py            # Profile CRUD operations
│   ├── test_relationships.py           # Profile and Company relationships
│   └── test_tasks_and_goals.py         # Task and Goal management
├── test_utils/                          # Utility and interactive tests
│   └── test_interactive_navigation.py  # Navigation and shortcuts
├── test_commands/                       # CLI command tests (TBD)
└── test_services/                       # Service layer tests (TBD)
```

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Specific Test File
```bash
pytest tests/test_models/test_profile_crud.py
```

### Run Specific Test Class
```bash
pytest tests/test_models/test_profile_crud.py::TestProfileCreate
```

### Run Specific Test
```bash
pytest tests/test_models/test_profile_crud.py::TestProfileCreate::test_create_basic_profile
```

### Run with Verbose Output
```bash
pytest -v
```

### Run with Coverage
```bash
pytest --cov=leadsauce --cov-report=html
```

### Run Tests Matching Pattern
```bash
pytest -k "create"           # Run all tests with 'create' in name
pytest -k "navigation"       # Run all navigation tests
pytest -k "not slow"         # Skip tests marked as slow
```

## Test Fixtures

### Database Fixtures

- **`test_db`**: Temporary SQLite database for each test
- **`sample_companies`**: Pre-populated company data
- **`sample_profiles`**: Pre-populated profile data with relationships
- **`sample_tags`**: Pre-populated tags
- **`sample_tasks`**: Pre-populated tasks linked to profiles
- **`sample_goals`**: Pre-populated goals with tasks
- **`sample_reminders`**: Pre-populated reminders
- **`sample_relationships`**: Pre-populated profile and company relationships
- **`sample_interactions`**: Pre-populated interaction history

### Mock Fixtures

- **`mock_console`**: Mock Rich console for testing output
- **`mock_questionary`**: Mock questionary for simulating user input

## Test Categories

### 1. Model Tests (`test_models/`)

Tests for SQLAlchemy models and database operations:

- **Profile CRUD**: Create, read, update, delete profiles
- **Company CRUD**: Company management
- **Tag Management**: Tag creation and associations
- **Task Management**: Task lifecycle and status
- **Goal Tracking**: Goal creation, progress, achievement
- **Relationships**: Profile-to-profile and company-to-company relationships
- **Data Integrity**: Foreign keys, cascading deletes, constraints

### 2. Interactive Tests (`test_utils/`)

Tests for TUI navigation and keyboard shortcuts:

- **Navigation**: Menu navigation, view switching
- **Keyboard Shortcuts**: Single-key commands, Ctrl+K, Ctrl+R
- **Action Shortcuts**: Menu-specific actions (a/e/d/s/r)
- **Double Backspace**: Cancellation behavior
- **Edge Cases**: Invalid input, empty states

### 3. Command Tests (`test_commands/`)

Tests for CLI commands (TODO):

- Profile commands (add, edit, delete, list, search)
- Company commands
- Task commands
- Goal commands
- Import/Export commands

### 4. Service Tests (`test_services/`)

Tests for service layer (TODO):

- AI integration
- System context
- Command execution

## Known Issues and Inconsistencies

The test suite documents several known inconsistencies found during regression testing:

### Critical Issues

1. **Workshop Navigation Conflict** (`test_interactive_navigation.py:TestWorkshopNavigationConflict`)
   - Workshop menu uses 1-6 for tools, conflicts with global navigation
   - Reference: `REGRESSION_TEST_FINDINGS.md` Issue #1

2. **Ctrl+K/Ctrl+R Availability** (`test_interactive_navigation.py:TestSpecialKeyboardShortcuts`)
   - Shortcuts shown globally but only implemented in Dashboard
   - Reference: `REGRESSION_TEST_FINDINGS.md` Issue #2

### Moderate Issues

3. **Search Menu Inconsistency** (`test_interactive_navigation.py:TestSearchMenuInconsistency`)
   - Search menu lacks action loop like other menus
   - Reference: `REGRESSION_TEST_FINDINGS.md` Issue #3

4. **Import/Export Navigation** (`test_interactive_navigation.py:TestImportExportMenuPattern`)
   - Uses questionary.select instead of single-key shortcuts
   - Reference: `REGRESSION_TEST_FINDINGS.md` Issue #5

5. **Double Backspace** (`test_interactive_navigation.py:TestDoubleBackspace`)
   - Only works in text prompts, not select prompts
   - Reference: `REGRESSION_TEST_FINDINGS.md` Issue #6

## Test Coverage Goals

Target coverage by module:

- **Models**: 90%+ (CRUD operations are straightforward)
- **Interactive (TUI)**: 70%+ (complex UI logic, some parts hard to test)
- **Commands**: 80%+ (business logic should be testable)
- **Services**: 75%+ (integration points may be tricky)
- **Utilities**: 80%+ (pure functions should be easy to test)

**Overall Target**: 80% code coverage

## Writing New Tests

### Test Naming Convention

```python
class Test[Feature][Operation]:
    """Test [feature] [operation]"""

    def test_[specific_behavior](self, fixtures):
        """Test that [specific behavior]"""
        # Arrange
        # Act
        # Assert
```

### Example

```python
class TestProfileCreate:
    """Test Profile creation"""

    def test_create_basic_profile(self, test_db):
        """Test creating a profile with minimum required fields"""
        # Arrange
        profile = Profile(name="Test", seniority="Mid-Level")

        # Act
        test_db.add(profile)
        test_db.commit()

        # Assert
        assert profile.id is not None
        assert profile.name == "Test"
```

### Using Fixtures

```python
def test_with_sample_data(test_db, sample_profiles, sample_companies):
    """Test uses pre-populated data"""
    # sample_profiles and sample_companies are automatically created
    profile = sample_profiles[0]
    company = sample_companies[0]

    # Your test logic here
    assert profile.company_id == company.id
```

### Mocking User Input

```python
@patch('leadsauce.utils.interactive.questionary')
def test_user_input(mock_questionary, test_db):
    """Test function that requires user input"""
    mock_questionary.text.return_value.ask.return_value = "Test Name"
    mock_questionary.confirm.return_value.ask.return_value = True

    # Call function that uses questionary
    result = some_interactive_function()

    assert result == expected_value
```

## Continuous Integration

### Pre-commit Hook (Recommended)

Run tests before each commit:

```bash
# .git/hooks/pre-commit
#!/bin/bash
pytest tests/
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
```

### GitHub Actions (Recommended)

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt
      - run: pip install pytest pytest-cov
      - run: pytest --cov=leadsauce --cov-report=xml
      - uses: codecov/codecov-action@v2
```

## Troubleshooting

### Database Locks

If you see "database is locked" errors:

```python
# Use separate database for each test
@pytest.fixture(scope='function')  # Not 'session' or 'module'
def test_db():
    # Each test gets its own database
```

### Import Errors

Ensure `leadsauce` is in your Python path:

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

Or install in development mode:

```bash
pip install -e .
```

### Slow Tests

Mark slow tests:

```python
@pytest.mark.slow
def test_slow_operation():
    """This test takes a while"""
    pass
```

Skip slow tests:

```bash
pytest -m "not slow"
```

## Contributing

When adding new features:

1. Write tests first (TDD)
2. Ensure tests pass: `pytest`
3. Check coverage: `pytest --cov=leadsauce`
4. Document known issues in test docstrings
5. Update this README if adding new test categories

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/14/core/testing.html)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Rich Testing](https://rich.readthedocs.io/en/stable/testing.html)

## Contact

For questions about tests, see:
- Main documentation: `../README.md`
- Regression findings: `../REGRESSION_TEST_FINDINGS.md`
- CI/CD setup: `.github/workflows/`

---

**Last Updated**: 2025-11-07
**Test Framework**: pytest 7.x
**Coverage Target**: 80%
**Status**: In Development
