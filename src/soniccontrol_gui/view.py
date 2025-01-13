import abc

import ttkbootstrap as ttk


TkinterView = ttk.tk.Widget | ttk.Window

class View(ttk.Frame):
    def __init__(self, master: TkinterView, *args, **kwargs) -> None:
        super().__init__(master, *args, **kwargs)
        self._master: TkinterView = master
        self._initialize_children()
        self._initialize_publish()

    @property
    def parent(self) -> TkinterView:
        return self._master
    
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
