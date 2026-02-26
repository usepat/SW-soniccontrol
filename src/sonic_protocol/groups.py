from dataclasses import dataclass
from typing import NewType, Optional, Dict, Set

GroupId = NewType("GroupId", str)


class _CommunicationGroups:
    communication = GroupId("communication")
    serial_settings = GroupId("communication.serial_settings")

class _ProcedureGroups:
    procedure = GroupId("procedures")
    ramp = GroupId("procedures.ramp")
    wipe = GroupId("procedures.wipe")
    tune = GroupId("procedures.tune")
    scan = GroupId("procedures.scan")
    auto = GroupId("procedures.auto")
    duty_cycle = GroupId("procedures.duty_cycle")

class GROUPS:
    misc = GroupId("misc")

    communication = _CommunicationGroups()
    procedures = _ProcedureGroups
    logging = GroupId("logging")

@dataclass(frozen=True)
class GroupSpec:
    id: GroupId
    title: str
    description: str
    parent: Optional[GroupId] = None
    order: int = 0
    is_release: bool = True

GROUP_SPECS: Dict[GroupId, GroupSpec] = {
    GROUPS.misc: GroupSpec(GROUPS.misc, "Misc", "Commands that are not yet categorized.", order=999),

    GROUPS.communication.communication: GroupSpec(
        GROUPS.communication.communication, "Communication", "Commands that related to communication configuration",
        order=30
    ),
    GROUPS.communication.serial_settings: GroupSpec(
        GROUPS.communication.serial_settings, "" \
        "Seral Settings", 
        "Commands that related to serial communication settings",
        parent=GROUPS.communication.communication,
        order=30
    ),
    GROUPS.procedures.procedure: GroupSpec(
        GROUPS.procedures.procedure,
        "Procedures",
        "Commands for controlling procedures. Procedures are predefined behaviors of the device that control the signal output.",
        order=40,
    ),
    GROUPS.procedures.ramp: GroupSpec(
        GROUPS.procedures.ramp,
        "Ramp",
        "Commands for the Ramp Procedure, which starts and stops at the given freqeuncies and steps through it.",
        parent=GROUPS.procedures.procedure,
        order=40,
    ),
    GROUPS.procedures.scan: GroupSpec(
        GROUPS.procedures.scan,
        "Scan",
        "Commands for the Scan Procedure, which tries to find the current optimal frequency. Setup for Tune Procedure",
        parent=GROUPS.procedures.procedure,
        order=40,
    ),
    GROUPS.procedures.tune: GroupSpec(
        GROUPS.procedures.tune,
        "Tune",
        "Commands for the Tune Procedure, which tries to operate the device at the optimum frequency. Optimal for catching particles",
        parent=GROUPS.procedures.procedure,
        order=40,
    ),
    GROUPS.procedures.auto: GroupSpec(
        GROUPS.procedures.auto,
        "Auto",
        "Commands for the Auto Procedure, which uses the Scan and Tune Procedure. So the actual configuration for the Auto Procedure must be done via Scan and Tune commands",
        parent=GROUPS.procedures.procedure,
        order=40,
    ),
    GROUPS.procedures.wipe: GroupSpec(
        GROUPS.procedures.wipe,
        "Wipe",
        "Commands for the Wipe Procedure, which runs ramps at the given atfs. Optimal for wiping sensors",
        parent=GROUPS.procedures.procedure,
        order=40,
    ),
    GROUPS.procedures.duty_cycle: GroupSpec(
        GROUPS.procedures.duty_cycle,
        "Duty Cycle",
        "Commands for the Duty Cycle procedure that allows to activate a procedure or just the signal output with a specific timing",
        parent=GROUPS.procedures.procedure,
        order=40,
    ),

    GROUPS.logging: GroupSpec(
        GROUPS.logging,
        "Logging",
        "Commands for controlling the log functionality of the device",
        order=50,
    ),

}

def infer_parent(gid: GroupId) -> Optional[GroupId]:
    s = str(gid)
    if "." not in s:
        return None
    return GroupId(s.rsplit(".", 1)[0])


def get_spec(gid: GroupId) -> GroupSpec:
    assert GROUP_SPECS[gid], f"{gid} not defined"
    return GROUP_SPECS[gid]


def check_group_specs(strict_parent_from_path: bool = True) -> None:
    # 1) key matches spec.id
    for key, spec in GROUP_SPECS.items():
        assert key == spec.id, f"Key {key!r} does not match spec.id {spec.id!r}"

    # 2) parent validity + dotted-path consistency
    for gid, spec in GROUP_SPECS.items():
        inferred = infer_parent(spec.id)

        if inferred is None:
            # root group: parent must be None
            assert spec.parent is None, f"Root group {gid!r} must have parent=None, got {spec.parent!r}"
        else:
            # non-root: parent must be defined and exist
            assert spec.parent is not None, f"Non-root group {gid!r} must define parent="
            assert spec.parent in GROUP_SPECS, f"Group {gid!r} has missing parent {spec.parent!r}"

            if strict_parent_from_path:
                assert spec.parent == inferred, (
                    f"Group {gid!r} parent mismatch: parent={spec.parent!r} but inferred={inferred!r} "
                    f"(from '{spec.id}')"
                )

    # 3) cycle detection (DFS)
    visiting: Set[GroupId] = set()
    visited: Set[GroupId] = set()

    def dfs(node: GroupId) -> None:
        if node in visited:
            return
        if node in visiting:
            raise AssertionError(f"Cycle detected at {node!r}")
        visiting.add(node)
        parent = GROUP_SPECS[node].parent
        if parent is not None:
            dfs(parent)
        visiting.remove(node)
        visited.add(node)

    for gid in GROUP_SPECS.keys():
        dfs(gid)

check_group_specs()


