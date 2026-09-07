import asyncio
from typing import List, Optional

from soniccontrol.utils.cyclic_task import CyclicTask
from .memory_snapshot import AllocationHistogramBin, AllocatorInfo, AllocatorUsage, MemorySnapShot, StackInfo
from soniccontrol.utils.events import Event, EventManager
from soniccontrol.sonic_device import SonicDevice
from soniccontrol import commands as cmds
from soniccontrol import EFieldName


class PerformanceMonitor(EventManager, CyclicTask):
    """
        Summary
        =======
        This class fetches meta data from the device about stack and memory usage.
        It is designed like the Updater class. It fetches cyclicly  the data and emits it to its listeners.
    
        This class is used in conjunction with the performance monitor gui from the firmware tools folder. 
    """
    SAMPLED_SNAP_SHOT_EVENT = "SAMPLED_SNAP_SHOT_EVENT"

    def __init__(self, device: SonicDevice, time_between_snapshots_ms: int = 5000):
        EventManager.__init__(self)
        CyclicTask.__init__(self, self._sample_and_emit, time_between_snapshots_ms, device._logger)
        self._device = device


    async def _sample_and_emit(self):
        if not self._device.communicator.connection_opened.is_set():
            # if no connection then make no snap shot. but keep running.
            return

        snap_shot = await self.sample_memory_snapshot()
        self.emit(
            Event(
                PerformanceMonitor.SAMPLED_SNAP_SHOT_EVENT, 
                snap_shot=snap_shot
            )
        )    

    async def sample_memory_snapshot(self):
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
    

