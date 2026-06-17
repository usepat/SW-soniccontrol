import asyncio
from typing import List, Optional
from .memory_snapshot import AllocationHistogramBin, AllocatorInfo, AllocatorUsage, MemorySnapShot, StackInfo
from soniccontrol.events import Event, EventManager
from soniccontrol.sonic_device import SonicDevice
from soniccontrol import commands as cmds
from soniccontrol import EFieldName


class PerformanceMonitor(EventManager):
    SAMPLED_SNAP_SHOT_EVENT = "SAMPLED_SNAP_SHOT_EVENT"

    def __init__(self, device: SonicDevice):
        super().__init__()
        self._device = device
        self._running: asyncio.Event = asyncio.Event()
        self._task: Optional[asyncio.Task] = None

    def start(self):
        assert not self._running.is_set(), "The updater is already running"
        self._running.set()
        
        def propagate_task_exception(task):
            try:
                # this will raise the exception inside asyncio event loop,
                #  the global exception handler will handle it
                task.result()
            except asyncio.CancelledError:
                pass 

        self._task = asyncio.create_task(self._loop())
        self._task.add_done_callback(propagate_task_exception)

    async def stop(self):
        self._running.clear()
        if self._task is not None:
            await self._task

    async def _loop(self):
        try:
            while self._running:
                snap_shot = await self.sample_memory_snapshot()
                self.emit(
                    Event(
                        PerformanceMonitor.SAMPLED_SNAP_SHOT_EVENT, 
                        snap_shot=snap_shot
                    )
                )
        except asyncio.CancelledError:
            pass
        except Exception:
            self._device._logger.exception("Performance monitor crashed")
            raise

    async def sample_memory_snapshot(self):
        if not self._device.communicator.connection_opened.is_set():
            # if no connection abort this task
            raise asyncio.CancelledError()

        answer = await self._device.execute_command(cmds.GetStackUsage(0))
        stack_usage = StackInfo(
            answer[EFieldName.SIZE],
            answer[EFieldName.CURRENT_USAGE],
            answer[EFieldName.WATERMARK_USAGE]
        )

        answer = await self._device.execute_command(cmds.GetNumAllocators())
        num_allocators = answer[EFieldName.COUNT]

        allocator_stats: List[AllocatorInfo] = []
        for i in range(num_allocators):
            answer = await self._device.execute_command(cmds.GetAllocatorStats(i))

            allocator_stats.append(
                AllocatorInfo(
                    answer[EFieldName.ALLOCATOR_NAME],
                    answer[EFieldName.INDEX],
                    answer[EFieldName.SIZE],
                    AllocatorUsage(
                        answer[EFieldName.CURRENT_ALLOCATIONS],
                        answer[EFieldName.CURRENT_USAGE],
                        answer[EFieldName.CURRENT_WASTED],
                    ),
                    AllocatorUsage(
                        answer[EFieldName.WATERMARK_ALLOCATIONS],
                        answer[EFieldName.WATERMARK_USAGE],
                        answer[EFieldName.WATERMARK_WASTED],
                    )
                )
            )

        answer = await self._device.execute_command(cmds.GetAllocHistogramNumBins())
        num_bins = answer[EFieldName.COUNT]

        allocation_histogram = []
        for i in range(num_bins):
            answer = await self._device.execute_command(cmds.GetAllocHistogramBin(i))
            allocation_histogram.append(
                AllocationHistogramBin(
                    answer[EFieldName.VALUE],
                    answer[EFieldName.LIMIT],
                    answer[EFieldName.SIZE]
                )
            )

        return MemorySnapShot(allocator_stats, allocation_histogram, stack_usage)
    

