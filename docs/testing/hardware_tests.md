@defgroup HardwareTests
@ingroup Testing
@addtogroup HardwareTests
@{

# hardware tests

## Requirements

We have to test the hardware components: if leds are blinking, i2c, adc measurement and so on...  
For that we have a firmware that executes test. Some are automated some semi automated, that means they need input from a Person, like a button press or validation if the leds are blinking. Therefore the tester needs a GUI with that he can execute the test, see if they pass, see which tests are available and with that he can get demands from the device how to interact with it.  
Finally we also want to get a test report.

## Implementation

We can send commands to fetch test informations, number of tests and test suites, execute automated tests, start semi automated tests and get the result of semi automated tests. So after we discovered the test suites, we can give information, which one could not be built and then we can fetch their tests and execute them. After execution we can display the state of each test, if it passed or not with an optional assert message on failure. For semi automated tests, we have to first start the test, then we get as an answer a user demand, that we can display to the user over a label or message box. It also gives us information if the user needs to do a validation task or if he has to interact with the device. In the first case, the user gets a yes, no button for validation, in the second case he just gets a finish button. After pressing that the program fetches the test result of the semi automated test and continues to execute the next one.  
After everything finished we can serialize the results into a json file.

@}