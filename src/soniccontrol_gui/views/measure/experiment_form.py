import copy
import datetime
import json
from pathlib import Path
import shutil
from typing import Any, Callable, Dict, Iterable, List, Optional

import attrs
import cattrs
from sonic_protocol.schema import SIPrefix
from soniccontrol.data_capturing.converter import create_cattrs_converter_for_basic_serialization
from soniccontrol.data_capturing.experiment import ExperimentMetaData, convert_authors
from soniccontrol_gui.ui_component import UIComponent
from sonic_protocol.si_unit import MeterSIVar, SIVar, TemperatureSIVar
from soniccontrol_gui.view import TkinterView, View
from soniccontrol_gui.constants import files, sizes, ui_labels

import ttkbootstrap as ttk
import logging

from soniccontrol_gui.widgets.form_widget import FormWidget, FieldViewBase, BasicTypeFieldView
from soniccontrol_gui.widgets.message_box import MessageBox
from soniccontrol_gui.widgets.user_selection import DynamicUserSelection
from async_tkinter_loop import async_handler
        

@attrs.define(auto_attribs=True)
class Template:
    name: str
    form_data: ExperimentMetaData


class ExperimentForm(UIComponent):
    FINISHED_EDITING_EVENT: str = "<<FINISHED_EDITING>>"

    def __init__(self, parent: UIComponent, widget_name: str, view_slot: View | ttk.Frame | None = None):
        self._logger = logging.getLogger(parent.logger.name + "." + ExperimentForm.__name__)
        self._widget_name = widget_name
        self._view = ExperimentFormView(parent.view if view_slot is None else view_slot)
        super().__init__(parent, self._view )

        self._converter = create_cattrs_converter_for_basic_serialization()
        def experiment_metadata_structure_hook(obj, _):
            
            additional = obj.pop('additional_metadata', {})
            _converter = create_cattrs_converter_for_basic_serialization()
            result = _converter.structure(obj, ExperimentMetaData)
            
            structured_additional = {}
            for k, v in additional.items():
                try:
                    structured_additional[k] = self._converter.structure(v, SIVar)
                except Exception:
                    structured_additional[k] = v
            obj['additional_metadata'] = additional
            result.additional_metadata = structured_additional
            return result
        self._converter.register_structure_hook(
            ExperimentMetaData,  # or Dict[str, Any] if using typing
            experiment_metadata_structure_hook
        )
        self._templates: List[Template] = []
        self._selected_template_index: Optional[int] = None

        # Initialize UI components first
        self._view.set_save_template_command(self._on_save_template)
        self._view.set_new_template_command(self._on_new_template)
        self._view.set_select_template_command(self._on_select_template)
        self._view.set_delete_template_command(self._on_delete_template)

        # Start async initialization
        self._start_async_initialization()

    def _start_async_initialization(self):
        """Start the async initialization process."""
        # Use after_idle to ensure the UI is ready, then start async loading
        self._view.after_idle(self._begin_async_loading)

    @async_handler
    async def _begin_async_loading(self):
        """Begin the async loading process including migration."""
        try:
            # Load and migrate templates first (this may require user input)
            await self._load_and_migrate_templates()
            
            # Only after migration is complete, create the form widget
            self._create_metadata_form()
            
            # Set up the template selection
            self._view.set_template_menu_items(map(lambda template: template.name, self._templates))
            self.selected_template_index = 0 if len(self._templates) > 0 else None
            
        except Exception as e:
            self._logger.error(f"Failed to initialize ExperimentForm: {e}")
            # Fallback: create form without templates
            self._create_metadata_form()

    async def _load_and_migrate_templates(self):
        """Load templates and apply any necessary migrations, including user interactions."""
        if not files.EXPERIMENT_TEMPLATES_JSON.exists():
            with open(files.EXPERIMENT_TEMPLATES_JSON, "w") as file:
                json.dump([], file)
            return

        if ".backup_" in files.EXPERIMENT_TEMPLATES_JSON.name:
            self._logger.warning("Attempting to load a backup file as the main template file: %s", files.EXPERIMENT_TEMPLATES_JSON)

        self._logger.info("Load templates from %s", files.EXPERIMENT_TEMPLATES_JSON)
        with open(files.EXPERIMENT_TEMPLATES_JSON, "r") as file:
            original_data = json.load(file)
            data_dict_list = copy.deepcopy(original_data)
            
            migration_applied = await self._apply_complete_migration(data_dict_list)
            
            if migration_applied:
                self._create_backup_file(files.EXPERIMENT_TEMPLATES_JSON)
                self._logger.info("Migration applied to experiment templates, saving updated file")
                with open(files.EXPERIMENT_TEMPLATES_JSON, "w") as write_file:
                    json.dump(data_dict_list, write_file, indent=2)
            
            self._templates = self._converter.structure(data_dict_list, List[Template])

    def _create_backup_file(self, original_file: Path) -> Path:
        """Create a backup copy of the original file."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = original_file.with_suffix(f".backup_{timestamp}.json")
        
        # Copy the original file to backup
        shutil.copy2(original_file, backup_file)
        self._logger.info("Created backup file: %s", backup_file)
        return backup_file

    async def _apply_complete_migration(self, data_dict_list: List[dict]) -> bool:
        """Apply complete migration including user interactions. Returns True if any migration was performed."""
        migration_applied = False
        for data_dict in data_dict_list:
            form_data = data_dict['form_data']
            try:
                self._converter.structure(form_data, ExperimentMetaData)
            except Exception:
                medium_temperature = form_data.get('medium_temperature', None)
                if medium_temperature is not None:
                    try:    
                        self._converter.structure(medium_temperature, SIVar)
                    except Exception:
                        si_var = TemperatureSIVar(value=medium_temperature, si_prefix=SIPrefix.NONE)
                        form_data['medium_temperature'] = self._converter.unstructure(si_var)
                        migration_applied = True
                
                gap = form_data.get('gap', None)
                if gap is not None:
                    try:    
                        self._converter.structure(gap, SIVar)
                    except Exception:
                        si_var_selection = DynamicUserSelection(
                            self._view.root,
                            message=f"Error in experiment template {form_data['experiment_name']}: {form_data['gap']}.Gap value is not in SI Units please select a valid SI Unit",
                            title="Select SI Unit",
                            target_type=MeterSIVar
                        )
                        si_var = await si_var_selection.wait_for_answer()
                        form_data['gap'] = self._converter.unstructure(si_var)
                        migration_applied = True
                
                cable_length = form_data.get('cable_length', None)
                if cable_length is not None:
                    try:    
                        self._converter.structure(cable_length, SIVar)
                    except Exception:
                        si_var_selection = DynamicUserSelection(
                            self._view.root,
                            message=f"Error in experiment template {form_data['experiment_name']}: {form_data['cable_length']}.Cable_length is not in SI Units please select a valid SI Unit",
                            title="Select SI Unit",
                            target_type=MeterSIVar,

                        )
                        si_var = await si_var_selection.wait_for_answer()
                        form_data['cable_length'] = self._converter.unstructure(si_var)
                        migration_applied = True
        
        return migration_applied
        
    @property
    def selected_template_index(self) -> Optional[int]:
        return self._selected_template_index

    @selected_template_index.setter
    def selected_template_index(self, value: Optional[int]) -> None: 
        self._selected_template_index = value
        if value is None:
            self._view.selected_template = ""
        else:
            selected_template = self._templates[value]
            self._metadata_form.attrs_object = selected_template.form_data
            self._view.template_name = selected_template.name
            self._view.selected_template = selected_template.name

    def _create_metadata_form(self):
        if hasattr(self, '_metadata_form'):
            return
            
        # We do currently support no ListFieldView
        # So instead we define a hook to convert the attribute field of author, so that the form registers a string instead
        # Also we have to define unstructuring/ structuring hooks so that the data provided and read from the form will be correctly serialized
        # The form internally unstructures all the classes into simple python data types with cattrs. 
        # This makes it easier to build recursive forms, because we do not need to handle the serialization/deserialization

        def form_field_author_hook(obj: type, field: "attrs.Attribute[Any]", slot: TkinterView, kwargs: Dict[str, Any] = {}) -> FieldViewBase:
            assert obj is ExperimentMetaData
            assert field.name == "authors"

            return BasicTypeFieldView[str](slot, str, field.name, **kwargs)

        form_field_hooks = {
            (ExperimentMetaData, "authors"): form_field_author_hook
        }

        
        self._metadata_form = FormWidget(self, self._view.metadata_form_slot,  "", ExperimentMetaData, field_hooks=form_field_hooks, widget_name=self._widget_name)
    
    def _save_templates_to_file(self):
        """Save templates to file."""
        self._logger.info("Save templates to %s", files.EXPERIMENT_TEMPLATES_JSON)
        with open(files.EXPERIMENT_TEMPLATES_JSON, "w") as file:
            data_dict = self._converter.unstructure(self._templates, List[Template])
            json.dump(data_dict, file)

    def _on_save_template(self):
        try:
            template = Template(self._view.template_name, self._metadata_form.attrs_object)
            if not self._validate_template_data(template):
                return
        except ValueError:
            MessageBox.show_error(self.view.root, "The form contains invalid fields, marked in red.")
            return
        
        if self._is_current_template_not_chosen():
            self._templates.append(template)
            self.selected_template_index = len(self._templates) - 1
        else:
            assert self.selected_template_index is not None
            self._templates[self.selected_template_index] = template

        self._view.set_template_menu_items(map(lambda template: template.name, self._templates))
        self._view.selected_template = template.name

        self._save_templates_to_file()

    def _validate_template_data(self, template: Template) -> bool:
        if self.selected_template_index is None and template.name in map(lambda template: template.name, self._templates):
            MessageBox.show_error(self.view.root, "A template with this name already exists")
            return False
        
        # No other validation is needed. 
        # Is already done by the form widget and the attrs validators 

        return True

    def _on_new_template(self):
        self._view.template_name = "no name"
        self._metadata_form.set_to_default()
        self.selected_template_index = None

    def _on_delete_template(self):
        if self._is_current_template_not_chosen():
            return

        assert self.selected_template_index is not None
        template = self._templates.pop(self.selected_template_index)
        self._logger.info("Delete template %s", template.name)
        self._save_templates_to_file()

        if len(self._templates) == 0:
            self._on_new_template()

        self._view.set_template_menu_items(map(lambda template: template.name, self._templates))
        self.selected_template_index = 0

    def _on_select_template(self):
        for i, template in enumerate(self._templates):
            if template.name == self._view.selected_template:
                self.selected_template_index = i
                break

    def _is_current_template_not_chosen(self):
        # if the user changes the name of the template, it becomes a totally new template and does not overwrite the old one
        if self.selected_template_index is None:
            return True
        if len(self._templates) == 0:
            return True
        return self._templates[self.selected_template_index].name != self._view.template_name

    def get_metadata(self):
        if self.selected_template_index is None:
            raise Exception("No template selected")
        
        template = Template(self._view.template_name, self._metadata_form.attrs_object)
        if not self._validate_template_data(template):
            raise Exception("Data is not valid")
        
        return template.form_data


class ExperimentFormView(View):
    def __init__(self, master: ttk.Frame | View, *args, **kwargs) -> None:
        super().__init__(master, *args, **kwargs)

    def _initialize_children(self) -> None:        
        self._new_template_button: ttk.Button = ttk.Button(
            self, text=ui_labels.NEW_LABEL, style=ttk.DARK,
        )

        self._selected_template: ttk.StringVar = ttk.StringVar()
        self._template_entry: ttk.Combobox = ttk.Combobox(
            self, textvariable=self._selected_template, style=ttk.DARK
        )
        self._template_entry["state"] = "readonly" # prevent typing a value
        self._save_template_button: ttk.Button = ttk.Button(
            self, text=ui_labels.SAVE_LABEL, style=ttk.DARK
        )
        self._delete_template_button: ttk.Button = ttk.Button(
            self, text=ui_labels.DELETE_LABEL, style=ttk.SUCCESS
        )

        self._template_frame: ttk.Frame = ttk.Frame(
            self
        )
        self._template_name: ttk.StringVar = ttk.StringVar()
        self._template_name_textbox: ttk.Entry = ttk.Entry(
            self._template_frame, textvariable=self._template_name
        )
        self._metadata_form_frame: ttk.Frame = ttk.Frame(self._template_frame)

    def _initialize_publish(self) -> None:
        self.pack(expand=True, fill=ttk.BOTH)
        self.columnconfigure(0, weight=sizes.DONT_EXPAND)
        self.columnconfigure(1, weight=sizes.EXPAND)
        self.columnconfigure(2, weight=sizes.DONT_EXPAND)
        self.columnconfigure(3, weight=sizes.DONT_EXPAND)
        self.columnconfigure(4, weight=sizes.DONT_EXPAND)
        self.rowconfigure(0, weight=sizes.DONT_EXPAND)
        self.rowconfigure(1, weight=sizes.EXPAND)
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
        self._delete_template_button.grid(
            row=0,
            column=3,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
        )
        self._template_frame.grid(row=1, column=0, columnspan=4, sticky=ttk.NSEW)
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
