from typing import Any, Callable

import ttkbootstrap as ttk


class DebounceJob:
    def __init__(
        self,
        command: Callable[..., Any],
        widget: ttk.tk.Widget | ttk.Window,
        debounce_time_ms: int = 250,
    ) -> None:
        self._command: Callable[..., Any] = command
        self._debounce_time_ms: int = debounce_time_ms
        self._widget: ttk.tk.Widget | ttk.Window = widget
        self._job: str | None = None
        self._pending_args: tuple[Any, ...] = ()
        self._pending_kwargs: dict[str, Any] = {}

    def __call__(self, event: Any = None, *args, **kwargs) -> None:
        self._pending_args = args
        self._pending_kwargs = kwargs

        def execute_command() -> None:
            if self._command is None:
                return
            self._command(*self._pending_args, **self._pending_kwargs)
            self._job = None

        if self._job is not None:
            self._widget.after_cancel(self._job)
        self._job = self._widget.after(self._debounce_time_ms, execute_command)
