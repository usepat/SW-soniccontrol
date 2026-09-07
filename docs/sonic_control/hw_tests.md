@defgroup hw_tests
@ingroup SonicControl
@addtogroup hw_tests
@{

# Hw Tests

## Requirements

The device can execute in diagnostics debugger mode some hardware tests.  
Those tests are for checking if the single hardware components like leds, button, transducer etc. are working as expected.  
SonicControl gui offers a testing suite for it.  
For that it fetches the available tests from the device and displays them, they can then be executed by the user via a run button.  
Some tests may require user interaction or validation. For example pressing a button or validating if the led is really turned on.  
Finally a report can be created from the current test results.

## Implementation

The `TestExecutor` class can fetch information about what tests are available via `load_tests()` and can execute tests via `run_test` and `stop_test`. SemiAutomated tests that need user interaction may consist of multiple steps and in that case an event is raised. Additionally to that arguments are fetched for the this task (We provide here arguments, because later on in the future plugins for external sensors and actuators may be created that interact with the hw tests and execute the semi automated steps. Making all of this fully automated).  
The Testing Tab in the Diagnostics Window then listens to this event and pop ups a Message Box. For interaction tasks it uses the `proceed_semi_automated_test()` function to continue the test and for validation tasks it simply sets the result for the test directly.

@}