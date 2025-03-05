from typing import Callable, Dict, Iterable, cast

import attrs
from soniccontrol.data_capturing.experiment import Experiment
from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.view import View

import ttkbootstrap as ttk
import logging

from soniccontrol_gui.widgets.form_widget import BasicTypeFieldView, FieldViewFactoryType, FormWidget, FormFieldAttributes


class ExperimentForm(UIComponent):
    FINISHED_EDITING_EVENT: str = "<<FINISHED_EDITING>>"
    EXPERIMENT_EVENT_ARG: str = "experiment"

    def __init__(self, parent: UIComponent):
        self._logger = logging.getLogger(parent.logger.name + "." + ExperimentForm.__name__)
        self._view = ExperimentFormView(parent.view)
        super().__init__(parent, self._view )

        self._form_dict = {}
        self._create_metadata_form()

        self._view.set_load_template_command(self._on_load_template)
        self._view.set_save_template_command(self._on_save_template)
        self._view.set_new_template_command(self._on_new_template)
        self._view.set_select_template_command(self._on_select_template)
        self._view.set_finish_command(self._on_finished_editing)
        
    def _create_metadata_form(self):
        form_attrs = cast(FormFieldAttributes, attrs.fields_dict(Experiment))

        exclude_field_names = ["data", "sonic_control_version", "operating_system", "capture_target", "target_parameters"]
        for exclude_field_name in exclude_field_names:
            del form_attrs[exclude_field_name]

        replace_fields: Dict[str, FieldViewFactoryType] = {
            "authors": lambda view, title, **kwargs: BasicTypeFieldView[str](view, str, title, **kwargs),
        }
        for field_name, field_factory in replace_fields.items():
            form_attrs[field_name] = field_factory

        self._metadata_form = FormWidget(self, self._view.metadata_form_slot, "", form_attrs, self._form_dict)

    def _on_load_template(self):
        ...

    def _on_save_template(self):
        ...

    def _on_new_template(self):
        ...

    def _on_select_template(self):
        ...

    def _on_finished_editing(self):
        ...


class ExperimentFormView(View):
    def __init__(self, master: ttk.Frame | View, *args, **kwargs) -> None:
        super().__init__(master, *args, **kwargs)

    def _initialize_children(self) -> None:
        pass

    def _initialize_publish(self) -> None:
        pass

    def set_load_template_command(self, command: Callable[[], None]) -> None: ...

    def set_save_template_command(self, command: Callable[[], None]) -> None: ...

    def set_new_template_command(self, command: Callable[[], None]) -> None: ...

    def set_select_template_command(self, command: Callable[[], None]) -> None: ...

    def set_finish_command(self, command: Callable[[], None]) -> None: ...

    @property
    def selected_template(self) -> str: 
        ...

    @selected_template.setter
    def selected_template(self, value: str) -> None:
        ...

    def set_template_menu_items(self, items: Iterable[str]) -> None:
        ...

    @property
    def metadata_form_slot(self) -> ttk.Frame:
        ...
