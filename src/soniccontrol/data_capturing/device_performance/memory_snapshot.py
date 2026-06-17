import datetime
from typing import List

import attrs

@attrs.define()
class AllocatorUsage:
    num_allocations: int
    used_bytes: int
    wasted_bytes: int

@attrs.define()
class AllocatorInfo:
    name: str
    parent_id: int
    size: int

    current_usage: AllocatorUsage
    all_high_usage: AllocatorUsage
    

@attrs.define()
class StackInfo:
    size: int
    current_used_bytes: int
    all_high_used_bytes: int


@attrs.define()
class AllocationHistogramBin:
    value: int
    upper_bound: int
    length: int


@attrs.define()
class MemorySnapShot:
    # allocators contain also one describing the RAM.
    allocators: List[AllocatorInfo]
    allocation_histogram: List[AllocationHistogramBin]
    stack: StackInfo = StackInfo(0, 0, 0)

    time_stamp: datetime.datetime = attrs.field(factory=datetime.datetime.now, init=False)

    def check_performance(self, memory_usage_threshold: float = 0.8):
        assert 0. < memory_usage_threshold < 1., "threshold has to be between 0 and 1"

        stack_usage = self.stack.all_high_used_bytes / self.stack.size
        if stack_usage > memory_usage_threshold:
            raise ResourceWarning(f"stack usage too high: {stack_usage}")
        
        for allocator in self.allocators:
            usage = allocator.all_high_usage.used_bytes / allocator.size
            if usage > memory_usage_threshold:
                raise ResourceWarning(f"memory usage of allocator '{allocator.name}' to high: {usage}")
        

