# Test Suite

QViewer uses [pytest](https://docs.pytest.org/) for automated testing. The test
suite verifies application behavior and should make regressions easy to locate.

## Running the tests

Run the complete suite from the repository root:

```powershell
cd test
python -m pytest
```

To run an individual test file or test, pass its path or node ID to pytest:

```powershell
cd test
python -m pytest test_file_mgr.py
python -m pytest test_file_mgr.py::test_name
```

## Test organization

- Place automated tests in the `test/` directory.
- Name test files `test_<subject>.py` and test functions `test_<behavior>`.
- Group tests by the component or behavior they exercise.
- Keep test data small and focused on the behavior under test.

## Test creation guidelines

### Test one aspect at a time

Do not create long tests that cover multiple items. Each test should cover one
aspect of the system and have a single, clearly identifiable reason to fail.

### Keep tests independent

Tests must not depend on one another. It must be possible to run each test by
itself, as part of the complete suite, or in a different order with the same
result. A test must create the state it needs and must not rely on state left by
another test.

### Prefer fixtures for shared setup

Prefer pytest fixtures to prepare the context needed by a test. Fixtures should
provide focused, reusable setup and clean up any state or resources they create.
Avoid hiding the action being tested or its assertions inside a fixture.

### Use preparation, action, and verification

A test should normally consist of three distinct parts:

1. **Preparation**: set up the required state, modes, variables, and parameters.
2. **Action**: perform the operation being tested.
3. **Verification**: assert that the observed result is correct.

Separate these parts with a blank line so that the test's intent is easy to
scan. A part may be omitted when it is unnecessary; for example, preparation
may be handled entirely by a fixture.

```python
def test_example(prepared_subject):
    expected_value = "expected"

    actual_value = prepared_subject.perform_action()

    assert actual_value == expected_value
```

## Before submitting changes

- Add or update tests whenever behavior changes.
- Run the relevant individual tests while developing.
- Run the complete suite before submitting the change.
- Record any manual GUI checks that cannot yet be automated.
