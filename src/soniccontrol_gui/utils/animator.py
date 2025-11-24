from typing import Any, Callable, Coroutine, Generic, Iterable, Optional, TypeVar
import asyncio
import itertools
from async_tkinter_loop import async_handler

class DotAnimationSequence:
    def __init__(self, label="", num_dots=3):
        self._label = label
        self._num_dots = num_dots
        self._current_index = 0

    def __iter__(self):
        return self

    def __next__(self) -> str:
        if self._current_index >= self._num_dots:
            raise StopIteration
        else:
            self._current_index += 1
            return  self._label + "." * self._current_index + " " * (self._num_dots - self._current_index)


AnimationFrame = TypeVar("AnimationFrame")
class Animator(Generic[AnimationFrame]):
    def __init__(self, 
                 sequence: Iterable[AnimationFrame], 
                 apply_on_target: Callable[[AnimationFrame], None], 
                 frame_rate: float,
                 done_callback: Optional[Callable[[], None]] = None
                ):
        self._original_sequence = list(sequence)
        self._apply_on_target = apply_on_target
        self._original_frame_rate = frame_rate
        self._worker: Optional[asyncio.Task] = None
        self._done_callback = done_callback

    def run(self, num_repeats: int = -1, frame_rate: Optional[float] = None) -> None:
        """
            Repeats forever if num_repeats == -1. (This is the default)
        """
        assert (num_repeats >= -1)
        assert(self._worker is None)
        
        if frame_rate is None:
            frame_rate = self._original_frame_rate

        sequence = self._original_sequence
        if num_repeats == -1:
            sequence = itertools.cycle(sequence)
        else:
            sequence = itertools.chain.from_iterable(itertools.repeat(sequence, num_repeats))
        self._worker = asyncio.create_task(self._animate(sequence, frame_rate))

    async def stop(self) -> None:
        assert(self._worker is not None)

        self._worker.cancel()
        await self._worker
        self._worker = None

    @property
    def is_animation_running(self) -> bool:
        return self._worker is not None

    def run_as_load_animation_for_task(self, task: asyncio.Task, **kwargs) -> None:
        self.run(**kwargs)

        @async_handler
        async def _stop_animation_callback(_task) -> None:
            await self.stop()

        task.add_done_callback(_stop_animation_callback)

    async def _animate(self, sequence: Iterable[AnimationFrame], frame_rate: float) -> None:
        seconds_per_frame = 1 / frame_rate
        try:
            for animation_frame in sequence:
                self._apply_on_target(animation_frame)
                await asyncio.sleep(seconds_per_frame)
        except asyncio.CancelledError:
            pass
        finally:
            if self._done_callback is not None:
                self._done_callback()


T = TypeVar("T")
F = TypeVar('F', bound=Callable[..., Coroutine[Any, Any, Any]])
def load_animation(animator: Animator[T], **animation_start_kwargs):
    def decorator(func: F) -> F:
        async def wrapper(*args, **kwargs):
            animator.run(**animation_start_kwargs)
            try:
                ret = await func(*args, **kwargs)
            except asyncio.CancelledError as _:
                ret = None
            finally:
                await animator.stop()
            return ret
        
        return wrapper # type: ignore
    return decorator
