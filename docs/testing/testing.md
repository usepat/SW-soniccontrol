@defgroup Testing
@addtogroup Testing
@{

# Testing

Our project is way to big to test everything manually. We have to use automated tests to ensure bug free code.  
We use the pytest framework for testing together with allure for nice test reports. We also use robot framework for system test, but want to move away from it.

## Hardware Tests

Hardware tests are flashed on the device as firmware code. Sonic control provides an interface to select and execute them. Hardware tests do not test the correctness of code, but the hardware per se (if it is damaged or components wrongly installed).

## Unit Tests

Unit tests are for testing single functions and classes individually. Dependencies get mocked.

## Integration Tests

Integration tests are for testing the working of multiple components together. Its an in between of unit tests and system test. It may simulate and mock some parts and only tests a sub system not the whole system.

### Simulation

If the device is locally simulated on the pc, than the peripherals get mocked and we therefore only test a sub part of the system. Then we talk about integration tests. If instead we test together the real device together with the sonic control gui, we speak of system tests.

### Remote Controller

The remote controller is a helper class for controlling the device. It is a Facade class and hides the complicated logic under a simplified interface.

### GUI Tests

For testing the GUI all widgets get registered under an own name and a GUIDriver can be used to programmatically interact with them. This allows to simulate user interaction.

## System Tests

System tests are for testing the entire setup and not only single components. So testing sonic control together with the real device and real firmware.  
However those tests are not for testing an experimental setup for a customer.

## Acceptance Tests

Are for verifying that a product meets the customers needs. for example if a cleaning procedure works for the customers environment. Final step before shipment.  

@startuml
!include testing.puml
@enduml

@}