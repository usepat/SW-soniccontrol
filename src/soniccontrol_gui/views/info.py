from typing import List

import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame

from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.view import TabView
from soniccontrol_gui.constants import fonts, sizes, ui_labels
from soniccontrol_gui.utils.image_loader import ImageLoader
from soniccontrol_gui.widgets.document import Document, Image, Text
from soniccontrol_gui.resources import images


class Info(UIComponent):
    def __init__(self, parent: UIComponent):
        # Todo implement markdown parser instead of doing this
        content=[
            ui_labels.HOME_HELP_INTRODUCTION,
            # ImageLoader.load_image_resource(images.HOME_CONTROL_PANEL, (300, 200)),
            #ui_labels.HOME_HELP_CONTROL_PANEL,
            Text(ui_labels.FREQUENCY, font=fonts.QTYPE_OT_CONDLIGHT),
            ui_labels.HOME_HELP_FREQUENCY,
            Text(ui_labels.GAIN, font=fonts.QTYPE_OT_CONDLIGHT),
            ui_labels.HOME_HELP_GAIN,
            # Text(ui_labels.CATCH_MODE_LABEL, font=fonts.QTYPE_OT_CONDLIGHT),
            # ui_labels.HOME_HELP_CATCH,
            # Text(ui_labels.WIPE_MODE_LABEL, font=fonts.QTYPE_OT_CONDLIGHT),
            # ui_labels.HOME_HELP_WIPE,
            Text(ui_labels.SEND_LABEL, font=fonts.QTYPE_OT_CONDLIGHT),
            ui_labels.HOME_HELP_SET_VALUES,
            #ui_labels.HOME_HELP_OUTPUT,
            # Image(images.HOME_SIGNAL_CONTROL_PANEL, (400, 35)),
            #ui_labels.HOME_HELP_SIGNAL_CONTROL_PANEL,
            # Text(ui_labels.SIGNAL_ON, font=fonts.QTYPE_OT_CONDLIGHT),
            # ui_labels.HOME_HELP_ON,
            # Text(ui_labels.SIGNAL_OFF, font=fonts.QTYPE_OT_CONDLIGHT),
            # ui_labels.HOME_HELP_OFF,
            # Text(ui_labels.AUTO_LABEL, font=fonts.QTYPE_OT_CONDLIGHT),
            # ui_labels.HOME_HELP_AUTO,
            ui_labels.NEW_LINE,
            ui_labels.NEW_LINE,
            ui_labels.TODO,
            Text(ui_labels.CONTACT, font=fonts.QTYPE_OT_CONDLIGHT),
            Text("Stefan Schöller: stefan.schoeller@usepat.com", font=fonts.QTYPE_OT_CONDLIGHT, selectable=True),
            Text("Christoph Gasser: christoph.gasser@usepat.com", font=fonts.QTYPE_OT_CONDLIGHT, selectable=True),
        ]
        self._view = InfoView(parent.view, self, content)
        super().__init__(parent, self._view)


class InfoView(TabView):
    def __init__(self, master: ttk.Window, presenter: UIComponent, content: List[str | Image | Text], *args, **kwargs) -> None:
        self._presenter = presenter
        self._content = content
        super().__init__(master, *args, **kwargs)

    @property
    def image(self) -> ttk.ImageTk.PhotoImage:
        return ImageLoader.load_image_resource(images.INFO_ICON_BLACK, (25, 25))

    @property
    def tab_title(self) -> str:
        return ui_labels.INFO_LABEL

    def _initialize_children(self) -> None:
        self._main_frame: ttk.Frame = ttk.Frame(self)
        self._heading_frame: ttk.Frame = ttk.Frame(self._main_frame)

        self._heading_part_one: ttk.Label = ttk.Label(
            self._heading_frame,
            text=ui_labels.SONIC_LABEL,
            font=(fonts.QTYPE_OT_CONDLIGHT, fonts.HEADING_SIZE),
            justify=ttk.CENTER,
            anchor=ttk.CENTER,
        )
        self._heading_part_two: ttk.Label = ttk.Label(
            self._heading_frame,
            text=ui_labels.CONTROL_LABEL,
            font=(fonts.QTYPE_OT, fonts.HEADING_SIZE),
            justify=ttk.CENTER,
            anchor=ttk.CENTER,
        )

        self._scroll_frame: ScrolledFrame = ScrolledFrame(self._main_frame)
        self._body_frame: ttk.Frame = ttk.Frame(self._scroll_frame)
        self.columnconfigure(0, weight=sizes.EXPAND)

        self._home_help_heading = ttk.Label(
            self._body_frame,
            text=ui_labels.HOME_LABEL,
            font=(
                fonts.QTYPE_OT_CONDLIGHT,
                fonts.SMALL_HEADING_SIZE,
            ),
            image=ImageLoader.load_image_resource(images.HOME_ICON_BLACK, sizes.TAB_ICON_SIZE),
            compound=ttk.LEFT,
            anchor=ttk.CENTER,
            justify=ttk.CENTER
        )

        self._home_help_frame: Document = Document(
            self._presenter,
            self._body_frame,
            wraplength=400,
            content=self._content
        )

        self._footer_frame: ttk.Frame = ttk.Frame(self._main_frame)
        self._company_name: ttk.Label = ttk.Label(
            self._footer_frame, text=ui_labels.COMPANY_NAME, anchor=ttk.CENTER
        )
        # TODO create the exe inside a github task, and then just fetch the release version
        __version__= "v2.4.0-rc" # TODO: fix the version problem
        self._version: ttk.Label = ttk.Label(
            self._footer_frame,
            text=f"{ui_labels.VERSION_LABEL}: {__version__}",
            anchor=ttk.CENTER,
        )

    def _initialize_publish(self) -> None:
        self._main_frame.pack(expand=True, fill=ttk.BOTH)
        self._main_frame.columnconfigure(0, weight=sizes.EXPAND)
        self._main_frame.rowconfigure(0, weight=sizes.DONT_EXPAND, minsize=40)
        self._main_frame.rowconfigure(1, weight=sizes.EXPAND)
        self._main_frame.rowconfigure(2, weight=sizes.DONT_EXPAND, minsize=15)
        self._heading_frame.grid(row=0, column=0, sticky=ttk.EW)
        self._scroll_frame.grid(row=1, column=0, sticky=ttk.NSEW)
        self._footer_frame.grid(row=2, column=0, sticky=ttk.EW)

        self._heading_frame.columnconfigure(0, weight=sizes.EXPAND)
        self._heading_frame.columnconfigure(1, weight=sizes.EXPAND)
        self._heading_frame.rowconfigure(0, weight=sizes.EXPAND)
        self._heading_part_one.grid(row=0, column=0, sticky=ttk.E)
        self._heading_part_two.grid(row=0, column=1, sticky=ttk.W)

        self._scroll_frame.columnconfigure(0, weight=sizes.EXPAND)
        self._scroll_frame.rowconfigure(0, weight=sizes.EXPAND)
        self._body_frame.grid(row=0, column=0, sticky=ttk.NS)
        self._home_help_heading.grid(row=0, column=0, sticky=ttk.W)
        self._home_help_frame.view.grid(row=1, column=0, sticky=ttk.NSEW)

        self._footer_frame.columnconfigure(0, weight=sizes.EXPAND)
        self._footer_frame.columnconfigure(1, weight=sizes.EXPAND)
        self._footer_frame.rowconfigure(0, weight=sizes.EXPAND)
        self._company_name.grid(row=0, column=0, sticky=ttk.NSEW)
        self._version.grid(row=0, column=1, sticky=ttk.NSEW)

    def set_small_width_layout(self) -> None:
        ...

    def set_large_width_layout(self) -> None:
        ...

    def publish(self) -> None:
        ...
