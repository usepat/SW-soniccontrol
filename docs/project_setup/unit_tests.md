@defgroup UnitTests
@ingroup ProjectSetup
@addtogroup UnitTests
@{

# Unit Testing {#UnitTests}

Unit tests are used for ensuring product quality (That the software is bug free). 
because manually testing code is quite cumbersome and requires a lot of effort, it is good 
to include basic tests that check if your code works as expected.  
Unit testing focuses on ensuring that single units like functions behave as they should. 
There are [guidelines](https://learn.microsoft.com/en-us/dotnet/core/testing/unit-testing-best-practices) on writing good unit tests.  
There is also [system testing and integration testing](@ref SystemTests).

## Pytest Overview

For Python there exists the builtin `unittest` module and the `pytest` library. 
We use `pytest` because of it easy use and nice fixture functionality. 
Also it is compatible with unittest.

Unittest is nice because it provides the `Mock` class. 
Mocks are classes that are used for simulating other ones. 
The can be spies, fakes, stubs or dummies:
- Spy: registers and watches function calls
- Fakes: Simulates a classes behaviour very realistically
- Stub: Just provides a very simple implementation for the classes methods
- Dummy: Is like a "shallow" hull of the class. Little to no simulation.
Unit tests want to test single functions and for that the dependencies get mocked.

Also for mocking API and library functions `monkey_patch` can be used. 

Here is an example pytest test code:
```py
def add(a, b):
    """Add two numbers and return the result."""
    return a + b

def test_add_integers():
    """Test that the addition of two integers returns the correct result."""
    result = add(1, 2)
    assert result == 3

def test_add_string_raises_typeerror():
    """Test that adding a string to a number raises a TypeError."""
    with pytest.raises(TypeError):
        add(1, "two")
```

Because we use a lot of async functionality in our code, we must use `pytest-async`:
```py
@pytest.mark.asyncio
async def test_communicator_close_communication_closes_streamwriter(communicator, connection):
    await communicator.close_communication()

    connection.writer.close.assert_called_once()
    connection.writer.wait_closed.assert_called_once()
```

## Pytest Setup

To setup pytest you have to install it via pip and then install your project in editable mode with `pip install -e .`.
For using pytest correctly you have to configure it in the *pyproject.toml* file:
```toml
[tool.pytest]
testpaths = ["tests"]

[tool.pytest.ini_options]
addopts = [
    "--cov=soniccontrol",
    "--import-mode=importlib"
]
```
You can run the tests with `pytest`. 
You can specify which files and tests it should execute.
There is the `Run unit tests of current file` vs-code task, that only executes the tests in the current file.
Also the *Test Tab* in vscode can be used to select and run tests.

See this [page](@ref CIandCD) on how to setup continuous integration with pytest.

@}