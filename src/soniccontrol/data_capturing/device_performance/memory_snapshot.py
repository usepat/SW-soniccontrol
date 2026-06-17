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
