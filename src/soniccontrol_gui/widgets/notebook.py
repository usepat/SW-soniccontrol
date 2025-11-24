from typing import Any, List, Tuple, Union

import ttkbootstrap as ttk

from soniccontrol_gui.utils.widget_registry import WidgetRegistry
from soniccontrol_gui.view import TabView


class Notebook(ttk.Notebook):
    def __init__(self, master: ttk.Window | ttk.tk.Widget, notebook_widget_name: str, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self._images_on: bool = True
        self._titles_on: bool = True
        self._notebook_widget_name = notebook_widget_name
        WidgetRegistry.register_widget(self, notebook_widget_name + "_notebook", None)

    def add_tab(self, tab: TabView, index: int | None = None, **kwargs) -> None:
        WidgetRegistry.register_widget(tab, tab.tab_title + "_tab", self._notebook_widget_name + "_notebook")
        return (
            self.add(
                tab,
                text=tab.tab_title if self._titles_on else "",
                image=tab.image if self._images_on else {},
                compound=ttk.TOP if self._images_on else ttk.RIGHT,
                **kwargs
            )
            if index is None
            else self.insert(
                index,
                tab,
                text=tab.tab_title if self._titles_on else "",
                image=tab.image if self._images_on else {},
                compound=ttk.TOP if self._images_on else ttk.RIGHT,
                **kwargs
            )
        )

    def add_tabs(
        self,
        tabs: List[Union[TabView | None, Tuple[int, TabView]]],
        keep_tabs: bool = False,
        show_titles: bool = True,
        show_images: bool = True,
        **kwargs
    ) -> None:
        if not keep_tabs:
            for tab in self.tabs():
                if tab:
                    self.forget(tab)
        self._images_on = show_images
        self._titles_on = show_titles
        for tab in tabs:
            if tab:
                self.add_tab(
                    tab if isinstance(tab, TabView) else tab[1],
                    index=None if isinstance(tab, TabView) else tab[0],
                    **kwargs
                )

    def configure_tabs(
        self, show_titles: bool = True, show_images: bool = True
    ) -> None:
        for tab_name in self.tabs():
            tab: Any = self.nametowidget(tab_name)
            self.tab(
                tab,
                text=tab.tab_title if show_titles else "",
                image=tab.image if show_images else None,
                compound=ttk.TOP if show_images else ttk.RIGHT,
            )
        self._images_on = show_images
        self._titles_on = show_titles
