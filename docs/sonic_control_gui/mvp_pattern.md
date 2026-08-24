@defgroup MVPPattern
@ingroup SonicControlGui
@addtogroup MVPPattern
@{

# MVP Pattern {#MVPPattern}

## Brief Description

The MVP pattern is a common Programming Pattern for GUIs. It builds up on its predecessor the MVC pattern.  
This documentation page gives a brief introduction to software architecture design in GUI applications. Read this article on [Gui Architecture](https://web.mit.edu/6.813/www/sp17/classes/05-ui-sw-arch/) for a better understanding.

## What is MVC?

The Model-View-Controller (MVC) pattern is a software architectural design that separates an application into three interconnected components.

### Model (Business Logic)

The Model represents the data and the business logic of the application. It directly manages the data, logic, and rules of the application.
The Model also defines how the data is manipulated and can respond to requests for information or changes to the data.

### View (Display Logic)

The View is the user interface component of the application. It displays the data provided by the Model in a format that's suitable for interaction, such as web pages, forms, charts, or any other UI components.
Views are responsible for presenting data to the user and for receiving input from the user (which is then passed to the Controller).

### Controller (Interaction Logic)

The Controller acts as an intermediary between the Model and the View. It receives user input from the View, processes it (often making changes to the Model), and returns the resulting output display to the View.

### How everything fits together

The Controller receives user interactions from the view and makes changes to the model. When the model changes its data it either notifies the views that subscribed as listener in a event like manner (push based) or the controller updates the view with the values of the model (pull based).

@startuml
!include sonic_control_gui/mvc_pattern.puml
@enduml

## What is MVP?

The MVP (Model-View-Presenter) is very similar to the MVC but handles the presentation logic differently

### Presenter (Interaction Logic and Presentation Logic)

Acts as an intermediary between the View and the Model.
It retrieves data from the Model and formats it for display in the View.
Handles the user input and updates the Model based on interactions.
The Presenter also updates the View with data from the Model. Unlike the Controller in MVC, the Presenter is more tightly coupled with the View.

### How everything fits together

The Presenter receives user interactions from the view, then makes changes to the model. When the model changes the presenter gets notified about it. The Presenter formats the data and updates the view with it.

@startuml
!include sonic_control_gui/mvp_pattern.puml
@enduml

## Other concepts

There are also other concepts like MVVM, MVVM-C, VIPER, Flux, ...
I considered using MVVM (Model View ViewModel), that is an extension of MVP, but because it was much more boilerplate to write. The software was not complex and big enough to justify that much boilerplate for more flexibility and modularity.

## Components

Components are modular units of code. For example a Button. Widgets are components.

### Nesting Components

The Controllers or Presenters of MVP and MVC can reference each other in a hierarchy. Like that more or less all Widgets are build. Each Widget can have child widgets, that can have child widgets by them selfs...
Like this we can nest components in the gui.

@startuml
package Window {
    package TabNavigation {}
    package TabView {
        package Button {
            package Icon {}
            package Text {}
        }
        package Text {}
    }
}
@enduml


### Creating new Components

There are two main ways to create own custom components:
- **Specialization**: Inherit from other components
- **Composition**: Make a new Component by combining already existing ones. 
Both approaches have their pro and cons. Often you can also use a combination of both

### Interacting with Components

The parent component can interact with its child component directly, but if the child component wants to react with its parent it has to emit an event and the parent has to react to this event. Children can also call their parent directly, but this introduces more coupling so events are preferred.  
In general events can be bubbled up or down the "chain" of components. See [Event Bubbling](https://en.wikipedia.org/wiki/Event_bubbling)

## Implementation

In the Code there exists a class [UIComponent](@ref soniccontrol_gui.ui_component.UIComponent) as a base for all Components. They are the same time the Presenter class.  
The [View](@ref soniccontrol_gui.view.View) class is the base class for all Views and contains the whole gui frontend presentation logic. So all [tkinter](https://docs.python.org/3/library/tkinter.html) code. This is important, because the Presenter should have no knowledge about which framework is used. The idea is to switch later to [Dash](https://dash.plotly.com/) or another gui framework. Keep things separate so they can be exchanged easily.  
For the Model there exists no explicit base class, but a model has to inherit from [EventManager](@ref soniccontrol.utils.events.EventManger), because the Presenter listens to its [Events](@ref soniccontrol.utils.events.Event), especially [PropertyChangeEvent](@ref soniccontrol.utils.events.PropertyChangeEvent). Also a Presenter can have multiple Models. 
Models are business logic classes. So is [ProcedureController](@ref soniccontrol.procedures.procedure_controller.ProcedureController) a Model for example.  
But sometimes they can also be pure data classes.

@startuml
!include sonic_control_gui/mvp_code.puml
@enduml

@}