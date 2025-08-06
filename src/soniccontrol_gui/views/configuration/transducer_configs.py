from pathlib import Path
from typing import List, Optional
import attrs
import marshmallow as marsh
import ttkbootstrap as ttk

from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.utils.widget_registry import WidgetRegistry
from soniccontrol_gui.view import View
from marshmallow_annotations.ext.attrs import AttrsSchema


@attrs.define(auto_attribs=True)
class ATConfig:
    atk: float = attrs.field(default=0)
    atf: int = attrs.field(default=0)
    att: float = attrs.field(default=0)

@attrs.define(auto_attribs=True)
class TransducerConfig():
    atconfigs: List[ATConfig] = attrs.field()
    init_script_path: Optional[Path] = attrs.field(default=None)
    # We only use this for creating the dropdown menu in the UI
    # the name should not be stored inside the json file, but should be retrieved from the file name
    name: str = attrs.field(default="template", metadata={"exclude": True})



# schemas used for serialization deserialization
class ATConfigSchema(AttrsSchema):
    class Meta:
        target = ATConfig
        register_as_scheme = True

class TransducerConfigSchema(AttrsSchema):
    class Meta:
        target = TransducerConfig
        register_as_scheme = True
        exclude = ("name",)

    init_script_path = marsh.fields.Method(
        serialize="serialize_path", deserialize="deserialize_path", allow_none=True
    )

    def serialize_path(self, obj) -> str | None:
        return obj.init_script_path.as_posix() if obj.init_script_path else None

    def deserialize_path(self, value):
        return Path(value) if value else None
    
    

class ATConfigFrame(UIComponent):
    def __init__(self, parent: UIComponent, view_parent: View | ttk.Frame, index: int, **kwargs):
        self._index = index
        self._view = ATConfigFrameView(view_parent, index, **kwargs)
        super().__init__(parent, self._view)

    @property
    def value(self) -> ATConfig:
        return ATConfig(
            atk = float(self._view.atk),
            atf = int(self._view.atf),
            att = float(self._view.att),
        )
    
    @value.setter
    def value(self, config: ATConfig) -> None:
        self._view.atf = config.atf
        self._view.atk = config.atk
        self._view.att = config.att


class ATConfigFrameView(View):
    def __init__(self, master: ttk.Frame, index: int, *args, **kwargs):
        parent_widget_name = kwargs.pop("parent_widget_name", "")
        self._widget_name = parent_widget_name + ".at_config." + str(index)
        self._index = index
        super().__init__(master, *args, **kwargs)

    def _initialize_children(self) -> None:
        self._atf_var = ttk.IntVar()
        self._atk_var = ttk.DoubleVar()
        self._att_var = ttk.DoubleVar()
    
        self._atf_label = ttk.Label(self, text=f"ATF {self._index}")
        self._atk_label = ttk.Label(self, text=f"ATK {self._index}")
        self._att_label = ttk.Label(self, text=f"ATT {self._index}")

        self._atf_spinbox = ttk.Spinbox(self, textvariable=self._atf_var)
        self._atk_spinbox = ttk.Spinbox(self, textvariable=self._atk_var)
        self._att_spinbox = ttk.Spinbox(self, textvariable=self._att_var)

        WidgetRegistry.register_widget(self._atf_spinbox, "atf_entry", self._widget_name)
        WidgetRegistry.register_widget(self._atk_spinbox, "atk_entry", self._widget_name)
        WidgetRegistry.register_widget(self._att_spinbox, "att_entry", self._widget_name)

    def _initialize_publish(self) -> None:
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)

        self._atf_label.grid(row=0, column=0, padx=10, pady=10, sticky=ttk.E)
        self._atf_spinbox.grid(row=0, column=1, padx=10, pady=10, sticky=ttk.W)

        self._atk_label.grid(row=1, column=0, padx=10, pady=10, sticky=ttk.E)
        self._atk_spinbox.grid(row=1, column=1, padx=10, pady=10, sticky=ttk.W)

        self._att_label.grid(row=2, column=0, padx=10, pady=10, sticky=ttk.E)
        self._att_spinbox.grid(row=2, column=1, padx=10, pady=10, sticky=ttk.W)

    # Properties for atf
    @property
    def atf(self):
        return self._atf_var.get()

    @atf.setter
    def atf(self, value):
        self._atf_var.set(value)

    # Properties for atk
    @property
    def atk(self):
        return self._atk_var.get()

    @atk.setter
    def atk(self, value):
        self._atk_var.set(value)

    # Properties for att
    @property
    def att(self):
        return self._att_var.get()

    @att.setter
    def att(self, value):
        self._att_var.set(value)
