import abc

import ttkbootstrap as ttk


TkinterView = ttk.tk.Widget | ttk.Window | ttk.Frame | ttk.LabelFrame

class View(ttk.Frame):
    def __init__(self, master: TkinterView, *args, parent_widget_name: str = "", **kwargs) -> None:
        self._parent_widget_name: str = parent_widget_name
        super().__init__(master, *args, **kwargs)
        self._master: TkinterView = master
        self._initialize_children()
        self._initialize_publish()

    @property
    def parent(self) -> TkinterView:
        return self._master

    @property
    def parent_widget_name(self) -> str:
        return self._parent_widget_name

    def scoped_widget_name(self, widget_name: str = "") -> str:
        return self.compose_widget_name(self.parent_widget_name, widget_name) if widget_name else self.parent_widget_name

    @staticmethod
    def compose_widget_name(parent_widget_name: str, widget_name: str) -> str:
        return f"{parent_widget_name}.{widget_name}" if parent_widget_name else widget_name
    
    @property
    def root(self):
        return self.winfo_toplevel()

    @abc.abstractmethod
    def _initialize_children(self) -> None:
        ...

    @abc.abstractmethod
    def _initialize_publish(self) -> None:
        ...


class TabView(View):
    def __init__(self, master: TkinterView, *args, **kwargs) -> None:
        super().__init__(master, *args, **kwargs)

    @property
    @abc.abstractmethod
    def tab_title(self) -> str:
        ...

    @property
    @abc.abstractmethod
    def image(self) -> ttk.ImageTk.PhotoImage:
        ...
