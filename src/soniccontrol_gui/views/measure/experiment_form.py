import json
from typing import Callable, Dict, Iterable, List, Optional, cast

import attrs
from ttkbootstrap.scrolled import ScrolledFrame
from soniccontrol.data_capturing.experiment import Experiment
from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.view import View
from soniccontrol_gui.constants import files, sizes, ui_labels

import ttkbootstrap as ttk
import logging
from marshmallow_annotations.ext.attrs import AttrsSchema

from soniccontrol_gui.widgets.form_widget import BasicTypeFieldView, FieldViewFactoryType, FormWidget, FormFieldAttributes


@attrs.define(auto_attribs=True)
class Template:
    name: str
    form_data: Experiment

class TemplateSchema(AttrsSchema):
    class Meta: # type: ignore
        target = Template


class ExperimentForm(UIComponent):
    FINISHED_EDITING_EVENT: str = "<<FINISHED_EDITING>>"
    EXPERIMENT_EVENT_ARG: str = "experiment"

    def __init__(self, parent: UIComponent):
        self._logger = logging.getLogger(parent.logger.name + "." + ExperimentForm.__name__)
        self._view = ExperimentFormView(parent.view)
        super().__init__(parent, self._view )

        self._template_schema = TemplateSchema(many=True)
        self._templates: List[Template] = []
        self._form_dict = {}
        self._selected_template_index: Optional[int] = None

        self._create_metadata_form()

        self._view.set_save_template_command(self._on_save_template)
        self._view.set_new_template_command(self._on_new_template)
        self._view.set_select_template_command(self._on_select_template)
        self._view.set_delete_template_command(self._on_delete_template)
        self._view.set_finish_command(self._on_finished_editing)

        self._load_templates()
        
    @property
    def selected_template_index(self) -> Optional[int]:
        return self._selected_template_index

    @selected_template_index.setter
    def selected_template_index(self, value: Optional[int]) -> None: 
        if value != self._selected_template_index:
            self._selected_template_index = value

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

    def _load_templates(self):
        if not files.EXPERIMENT_TEMPLATES_JSON.exists():
            with open(files.EXPERIMENT_TEMPLATES_JSON, "w") as file:
                json.dump([], file)

        self._logger.info("Load templates from %s", files.EXPERIMENT_TEMPLATES_JSON)
        with open(files.EXPERIMENT_TEMPLATES_JSON, "r") as file:
            data_dict = json.load(file)
            self._templates = self._template_schema.load(data_dict).data

        self._view.set_template_menu_items(map(lambda template: template.name, self._templates))
        self.selected_template_index = 0 if len(self._templates) > 0 else None

    def _on_save_template(self):
        try:
            experiment = Experiment(**self._form_dict)
        except Exception as e:
            ...
            return
        
        template = Template(self._view.template_name, experiment)
        if not self._validate_template_data(template):
            return
        
        if self.selected_template_index is None:
            self._templates.append(template)
            self._view.set_template_menu_items(map(lambda template: template.name, self._templates))
            self.selected_template_index = len(self._templates) - 1
        else:
            self._templates[self.selected_template_index] = template

        self._logger.info("Save templates to %s", files.EXPERIMENT_TEMPLATES_JSON)
        with open(files.EXPERIMENT_TEMPLATES_JSON, "w") as file:
            data_dict = self._template_schema.dump(self._templates).data
            json.dump(data_dict, file)

    def _validate_template_data(self, template: Template) -> bool:
        return True  # TODO

    def _on_new_template(self):
        self._view.template_name = "no name"
        self._metadata_form.set_to_default()
        self.selected_template_index = None

    def _on_delete_template(self):
        ... # TODO

    def _on_select_template(self):
        for i, template in enumerate(self._templates):
            if template.name == self._view.selected_template:
                self.selected_template_index = i
                break

    def _change_template(self):
        if self.selected_template_index is None:
            self._on_new_template()
        else:
            selected_template = self._templates[self.selected_template_index]
            form_data = attrs.asdict(selected_template.form_data)
            form_data["authors"] = ", ".join(form_data["authors"]) # for authors a StrFieldView is used in the form.
            self._metadata_form.form_data = form_data
            self._view.template_name = selected_template.name

    def _on_finished_editing(self):
        ...  # TODO


class ExperimentFormView(View):
    def __init__(self, master: ttk.Frame | View, *args, **kwargs) -> None:
        super().__init__(master, *args, **kwargs)

    def _initialize_children(self) -> None:
        self._experiment_form_frame: ttk.Frame = ttk.Frame(self)
        
        self._new_template_button: ttk.Button = ttk.Button(
            self._experiment_form_frame, text=ui_labels.NEW_LABEL, style=ttk.DARK,
        )

        self._selected_template: ttk.StringVar = ttk.StringVar()
        self._template_entry: ttk.Combobox = ttk.Combobox(
            self._experiment_form_frame, textvariable=self._selected_template, style=ttk.DARK
        )
        self._template_entry["state"] = "readonly" # prevent typing a value
        self._save_template_button: ttk.Button = ttk.Button(
            self._experiment_form_frame, text=ui_labels.SAVE_LABEL, style=ttk.DARK
        )
        self._delete_template_button: ttk.Button = ttk.Button(
            self._experiment_form_frame, text=ui_labels.DELETE_LABEL, style=ttk.SUCCESS
        )
        self._finish_button: ttk.Button = ttk.Button(
            self._experiment_form_frame, text=ui_labels.FINISH_LABEL, style=ttk.SUCCESS
        )

        self._template_frame: ttk.Frame = ttk.Frame(
            self._experiment_form_frame
        )
        self._template_name: ttk.StringVar = ttk.StringVar()
        self._template_name_textbox: ttk.Entry = ttk.Entry(
            self._template_frame, textvariable=self._template_name
        )
        self._metadata_form_frame: ScrolledFrame = ScrolledFrame(self._template_frame)

    def _initialize_publish(self) -> None:
        self._experiment_form_frame.pack(expand=True, fill=ttk.BOTH)
        self._experiment_form_frame.columnconfigure(0, weight=sizes.DONT_EXPAND)
        self._experiment_form_frame.columnconfigure(1, weight=sizes.EXPAND)
        self._experiment_form_frame.columnconfigure(2, weight=sizes.DONT_EXPAND)
        self._experiment_form_frame.columnconfigure(3, weight=sizes.DONT_EXPAND)
        self._experiment_form_frame.columnconfigure(4, weight=sizes.DONT_EXPAND)
        self._experiment_form_frame.rowconfigure(0, weight=sizes.DONT_EXPAND)
        self._experiment_form_frame.rowconfigure(1, weight=sizes.EXPAND)
        self._new_template_button.grid(
            row=0,
            column=0,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
        )
        self._template_entry.grid(
            row=0,
            column=1,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
            sticky=ttk.EW,
        )
        self._save_template_button.grid(
            row=0,
            column=2,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
        )
        self._finish_button.grid(
            row=0,
            column=3,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
        )
        self._delete_template_button.grid(
            row=0,
            column=4,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
        )
        self._template_frame.grid(row=1, column=0, columnspan=5, sticky=ttk.NSEW)
        self._template_frame.columnconfigure(0, weight=sizes.EXPAND)
        self._template_frame.rowconfigure(0, weight=sizes.DONT_EXPAND)
        self._template_frame.rowconfigure(1, weight=sizes.EXPAND)
        self._template_name_textbox.grid(
            row=0,
            column=0,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
            sticky=ttk.EW,
        )
        self._metadata_form_frame.grid(
            row=1,
            column=0,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
            sticky=ttk.NSEW,
        )

    def set_save_template_command(self, command: Callable[[], None]) -> None:
        self._save_template_button.configure(command=command)

    def set_new_template_command(self, command: Callable[[], None]) -> None:
        self._new_template_button.configure(command=command)

    def set_select_template_command(self, command: Callable[[], None]) -> None: 
        self._template_entry.bind("<<ComboboxSelected>>", lambda _: command())
    
    def set_delete_template_command(self, command: Callable[[], None]) -> None: 
        self._delete_template_button.configure(command=command)

    def set_finish_command(self, command: Callable[[], None]) -> None:
        self._finish_button.configure(command=command)

    @property
    def selected_template(self) -> str: 
        return self._selected_template.get()

    @selected_template.setter
    def selected_template(self, value: str) -> None:
        self._selected_template.set(value)

    def set_template_menu_items(self, items: Iterable[str]) -> None:
        self._template_entry["values"] = list(items)

    @property
    def template_name(self) -> str: 
        return self._template_name.get()

    @template_name.setter
    def template_name(self, value: str) -> None:
        self._template_name.set(value)

    @property
    def metadata_form_slot(self) -> ttk.Frame:
        return self._metadata_form_frame
