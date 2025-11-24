from pathlib import Path
from typing import List, Tuple

import attrs
import ttkbootstrap as ttk

from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.view import View
from soniccontrol_gui.constants import fonts, sizes
from soniccontrol_gui.utils.image_loader import ImageLoader


@attrs.define()
class Text:
    text: str = attrs.field()
    font: str = attrs.field(default=fonts.QTYPE_OT)
    font_size: int = attrs.field(default=fonts.TEXT_SIZE)
    selectable: bool = attrs.field(default=False)

@attrs.define()
class Image:
    image_path: Path = attrs.field()
    image_size: Tuple[int, int] = attrs.field()


class Document(UIComponent):
    def __init__(
            self, 
            parent: UIComponent, 
            parent_view: View,
            content: List[str | Text | Image], 
            paragraph_padding: int = sizes.MEDIUM_PADDING,
            wraplength: int = 0
        ) -> None:
        self._view = DocumentView(parent_view, content, paragraph_padding, wraplength)
        super().__init__(parent, self._view)


class DocumentView(View):
    def __init__(
        self,
        master: ttk.tk.Widget,
        content: List[str | Text | Image],
        paragraph_padding: int = sizes.MEDIUM_PADDING,
        wraplength: int = 0,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(master, *args, **kwargs)
        self._master: ttk.tk.Widget = master
        self._wraplength: int = wraplength
        self._paragraph_padding: int = paragraph_padding
        
        for index, element in enumerate(content):
            if isinstance(element, str):
                uielement = ttk.Label(
                    self, 
                    text=element,
                    wraplength=self._wraplength,
                    anchor=ttk.W,
                    justify=ttk.LEFT
                )
            elif isinstance(element, Text):
                if element.selectable:
                    # Create a read-only Text widget for selectable/copyable text
                    uielement = ttk.Text(
                        self,
                        height=1,  # Single line height
                        wrap=ttk.WORD,
                        state=ttk.NORMAL,
                        cursor="xterm",  # Text cursor to indicate selectability
                        font=(element.font, element.font_size),
                        relief=ttk.FLAT,  # Remove border to look like a label
                        borderwidth=0,
                        highlightthickness=0
                    )
                    uielement.insert("1.0", element.text)
                    uielement.configure(state=ttk.DISABLED)  # Make read-only after inserting text
                else:
                    uielement = ttk.Label(
                        self, 
                        text=element.text,
                        font=(element.font, element.font_size),
                        wraplength=self._wraplength,
                        anchor=ttk.W,
                        justify=ttk.LEFT
                    )
            elif isinstance(element, Image):
                uielement = ttk.Label(
                    self, 
                    text="",
                    wraplength=self._wraplength,
                    anchor=ttk.CENTER,
                    justify=ttk.CENTER,
                    image=ImageLoader.load_image_resource(str(element.image_path), element.image_size)
                )
            uielement.grid(
                row=index + 1,
                column=0,
                sticky=ttk.EW,
                pady=self._paragraph_padding,
                padx=sizes.LARGE_PADDING,
            )
            self.rowconfigure(index + 1, weight=sizes.DONT_EXPAND)

