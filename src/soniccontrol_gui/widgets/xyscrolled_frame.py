# type: ignore
# flake8: noqa

from __future__ import annotations

from tkinter import Grid, Pack, Place

import ttkbootstrap as ttk
from ttkbootstrap.constants import *


class XYScrolledFrame(ttk.Frame):
    def __init__(
        self,
        master=None,
        # padding=0,
        bootstyle=DEFAULT,
        autohide=False,
        width=20,
        height=20,
        scrollwidth=None,
        scrollheight=None,
        mousewheel_scroll_orientation: ttk.VERTICAL | ttk.HORIZONTAL =ttk.VERTICAL,
        **kwargs,
    ):
        self._mousewheel_scroll_orientation = mousewheel_scroll_orientation
        self.relx = 0.
        self.rely = 0.
        # content frame container
        self.container = ttk.Frame(
            master=master,
            relief=FLAT,
            borderwidth=0,
            width=width,
            height=height,
            bootstyle=bootstyle.replace("round", ""),
        )
        self.container.bind("<Configure>", self._on_configure)
        self.container.propagate(1)

        # content frame
        super().__init__(
            master=self.container,
            # padding=padding,
            bootstyle=bootstyle.replace("round", ""),
            width=width,
            height=height,
            **kwargs,
        )
        self.place(relx=0.0, rely=0.0, width=scrollwidth, height=scrollheight)

        # vertical scrollbar
        self.hscroll = ttk.Scrollbar(
            master=self.container,
            command=self.xview,
            orient=HORIZONTAL,
            bootstyle=bootstyle,
        )
        self.hscroll.pack(side=BOTTOM, fill=X)

        self.vscroll = ttk.Scrollbar(
            master=self.container,
            command=self.yview,
            orient=VERTICAL,
            bootstyle=bootstyle,
        )
        self.vscroll.pack(side=RIGHT, fill=Y)

        self.winsys = self.tk.call("tk", "windowingsystem")

        # setup autohide scrollbar
        self.autohide = autohide
        if self.autohide:
            self.hide_scrollbars()

        # widget event binding
        self.container.bind("<Enter>", self._on_enter, "+")
        self.container.bind("<Leave>", self._on_leave, "+")
        self.container.bind("<Map>", self._on_map, "+")
        self.bind("<<MapChild>>", self._on_map_child, "+")

        # delegate content geometry methods to container frame
        _methods = vars(Pack).keys() | vars(Grid).keys() | vars(Place).keys()
        for method in _methods:
            if any(["pack" in method, "grid" in method, "place" in method]):
                # prefix content frame methods with 'content_'
                setattr(self, f"content_{method}", getattr(self, method))
                # overwrite content frame methods from container frame
                setattr(self, method, getattr(self.container, method))

    def xview(self, *args):
        if not args:
            first, _ = self.hscroll.get()
            self.xview_moveto(fraction=first)
        elif args[0] == "moveto":
            self.xview_moveto(fraction=float(args[1]))
        elif args[0] == "scroll":
            self.xview_scroll(number=int(args[1]), what=args[2])
        else:
            return

    def xview_moveto(self, fraction: float):
        base, thumb = self._measures_x()
        if fraction < 0:
            first = 0.0
        elif (fraction + thumb) > 1:
            first = 1 - thumb
        else:
            first = fraction
        self.hscroll.set(first, first + thumb)
        self.relx = -first * base
        self.content_place(relx=self.relx, rely=self.rely)

    def xview_scroll(self, number: int, what: str):
        first, _ = self.hscroll.get()
        fraction = (number / 100) + first
        self.xview_moveto(fraction)

    def yview(self, *args):
        if not args:
            first, _ = self.vscroll.get()
            self.yview_moveto(fraction=first)
        elif args[0] == "moveto":
            self.yview_moveto(fraction=float(args[1]))
        elif args[0] == "scroll":
            self.yview_scroll(number=int(args[1]), what=args[2])
        else:
            return

    def yview_moveto(self, fraction: float):
        base, thumb = self._measures_y()
        if fraction < 0:
            first = 0.0
        elif (fraction + thumb) > 1:
            first = 1 - thumb
        else:
            first = fraction
        self.vscroll.set(first, first + thumb)
        self.rely = -first * base
        self.content_place(relx=self.relx, rely=self.rely)

    def yview_scroll(self, number: int, what: str):
        first, _ = self.vscroll.get()
        fraction = (number / 100) + first
        self.yview_moveto(fraction)

    def _add_scroll_binding(self, parent):
        """Recursive adding of scroll binding to all descendants."""
        children = parent.winfo_children()
        for widget in [parent, *children]:
            bindings = widget.bind()
            if self.winsys.lower() == "x11":
                if "<Button-4>" in bindings or "<Button-5>" in bindings:
                    continue
                else:
                    widget.bind("<Button-4>", self._on_mousewheel, "+")
                    widget.bind("<Button-5>", self._on_mousewheel, "+")
            else:
                if "<MouseWheel>" not in bindings:
                    widget.bind("<MouseWheel>", self._on_mousewheel, "+")
            if widget.winfo_children() and widget != parent:
                self._add_scroll_binding(widget)

    def _del_scroll_binding(self, parent):
        """Recursive removal of scrolling binding for all descendants"""
        children = parent.winfo_children()
        for widget in [parent, *children]:
            if self.winsys.lower() == "x11":
                widget.unbind("<Button-4>")
                widget.unbind("<Button-5>")
            else:
                widget.unbind("<MouseWheel>")
            if widget.winfo_children() and widget != parent:
                self._del_scroll_binding(widget)

    def enable_scrolling(self):
        """Enable mousewheel scrolling on the frame and all of its
        children."""
        self._add_scroll_binding(self)

    def disable_scrolling(self):
        """Disable mousewheel scrolling on the frame and all of its
        children."""
        self._del_scroll_binding(self)

    def hide_scrollbars(self):
        """Hide the scrollbars."""
        self.hscroll.pack_forget()
        self.vscroll.pack_forget()

    def show_scrollbars(self):
        """Show the scrollbars."""
        self.hscroll.pack(side=BOTTOM, fill=X)
        self.vscroll.pack(side=RIGHT, fill=Y)

    def autohide_scrollbar(self):
        """Toggle the autohide funtionality. Show the scrollbars when
        the mouse enters the widget frame, and hide when it leaves the
        frame."""
        self.autohide = not self.autohide

    def _measure(self, outer, inner) -> tuple[float, float]:
        base = inner / outer
        if inner == outer:
            thumb = 1.0
        else:
            thumb = outer / inner
        return base, thumb

    def _measures_x(self):
        """Measure the base size of the container and the thumb size
        for use in the xview methods"""
        outer = self.container.winfo_width()
        inner = max([self.winfo_width(), outer])
        return self._measure(outer, inner)
    
    def _measures_y(self):
        """Measure the base size of the container and the thumb size
        for use in the yview methods"""
        outer = self.container.winfo_height()
        inner = max([self.winfo_height(), outer])
        return self._measure(outer, inner)

    def _on_map_child(self, event):
        """Callback for when a widget is mapped to the content frame."""
        if self.container.winfo_ismapped():
            self.xview()
            self.yview()

    def _on_enter(self, event):
        """Callback for when the mouse enters the widget."""
        self.enable_scrolling()
        if self.autohide:
            self.show_scrollbars()

    def _on_leave(self, event):
        """Callback for when the mouse leaves the widget."""
        self.disable_scrolling()
        if self.autohide:
            self.hide_scrollbars()

    def _on_configure(self, event):
        """Callback for when the widget is configured"""
        self.xview()
        self.yview()

    def _on_map(self, event):
        self.xview()
        self.yview()

    def _on_mousewheel(self, event):
        """Callback for when the mouse wheel is scrolled."""
        if self.winsys.lower() == "win32":
            delta = -int(event.delta / 120)
        elif self.winsys.lower() == "aqua":
            delta = -event.delta
        elif event.num == 4:
            delta = -10
        elif event.num == 5:
            delta = 10
        if self._mousewheel_scroll_orientation == ttk.HORIZONTAL:
            self.xview_scroll(delta, UNITS)
        else:
            self.yview_scroll(delta, UNITS)
