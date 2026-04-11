from __future__ import annotations

import ast
from dataclasses import dataclass
from importlib import metadata, util
import logging
from pathlib import Path
import sys
from typing import Any, Iterable, List

from soniccontrol.api.version import PLUGIN_API_VERSION as CURRENT_PLUGIN_API_VERSION
from soniccontrol.app_config import PLUGIN_DIR

try:
    from packaging.requirements import Requirement
except ImportError:  # pragma: no cover
    Requirement = None  # type: ignore[assignment]


logger = logging.getLogger(__name__)
SUPPORTED_PLUGIN_RUNTIME = "native"


@dataclass(frozen=True)
class PluginCandidate:
    group: str
    name: str
    value: str
    module_name: str
    distribution_name: str
    source: str
    requirements: tuple[str, ...]
    entry_point: metadata.EntryPoint

    @property
    def identifier(self) -> str:
        return f"{self.distribution_name}:{self.name}"


def _ensure_plugin_directory_on_path() -> None:
    PLUGIN_DIR.mkdir(parents=True, exist_ok=True)
    plugin_dir = str(PLUGIN_DIR)
    if plugin_dir not in sys.path:
        sys.path.insert(0, plugin_dir)


def _get_plugin_distribution_paths() -> list[str]:
    _ensure_plugin_directory_on_path()

    paths = [str(PLUGIN_DIR)]
    if getattr(sys, "frozen", False):
        bundled_dependencies_dir = Path(sys._MEIPASS)  # type: ignore[attr-defined]
        paths.append(str(bundled_dependencies_dir))
    return paths


def _iter_candidate_distributions() -> Iterable[tuple[str, Iterable[metadata.Distribution]]]:
    yield "environment", metadata.distributions()
    yield "plugin-directory", metadata.distributions(path=_get_plugin_distribution_paths())


def _get_distribution_name(distribution: metadata.Distribution) -> str:
    return distribution.metadata["Name"] if "Name" in distribution.metadata else "<unknown-plugin>"


def _build_candidate(
    group: str,
    source: str,
    distribution: metadata.Distribution,
    entry_point: metadata.EntryPoint,
) -> PluginCandidate:
    return PluginCandidate(
        group=group,
        name=entry_point.name,
        value=entry_point.value,
        module_name=entry_point.value.split(":", maxsplit=1)[0],
        distribution_name=_get_distribution_name(distribution),
        source=source,
        requirements=tuple(distribution.requires or ()),
        entry_point=entry_point,
    )


def _iter_group_entry_points(
    distribution: metadata.Distribution,
    group: str,
) -> Iterable[metadata.EntryPoint]:
    for entry_point in distribution.entry_points:
        if entry_point.group == group:
            yield entry_point


def discover_plugin_candidates(group: str) -> List[PluginCandidate]:
    candidates: list[PluginCandidate] = []
    seen: set[tuple[str, str, str, str]] = set()

    for source, distributions in _iter_candidate_distributions():
        for distribution in distributions:
            for entry_point in _iter_group_entry_points(distribution, group):
                distribution_name = _get_distribution_name(distribution)
                key = (group, distribution_name, entry_point.name, entry_point.value)
                if key in seen:
                    continue
                seen.add(key)

                candidates.append(_build_candidate(group, source, distribution, entry_point))

    candidates.sort(key=lambda candidate: (candidate.distribution_name, candidate.name, candidate.source))
    return candidates


def _is_requirement_relevant(requirement: Any) -> bool:
    return requirement.marker is None or requirement.marker.evaluate()


def _iter_relevant_requirements(candidate: PluginCandidate) -> Iterable[Any]:
    if Requirement is None:
        return []

    parsed_requirements: list[Any] = []
    for requirement_text in candidate.requirements:
        try:
            requirement = Requirement(requirement_text)
        except Exception as exc:  # pragma: no cover
            logger.warning(
                "Could not parse requirement '%s' declared by plugin %s: %s",
                requirement_text,
                candidate.identifier,
                exc,
            )
            continue

        if _is_requirement_relevant(requirement):
            parsed_requirements.append(requirement)

    return parsed_requirements


def _add_environment_requirement_issue(issues: list[str], requirement: Any) -> None:
    try:
        installed_version = metadata.version(requirement.name)
    except metadata.PackageNotFoundError:
        issues.append(f"missing dependency '{requirement.name}'")
        return

    if requirement.specifier and not requirement.specifier.contains(installed_version, prereleases=True):
        issues.append(f"requires {requirement.name}{requirement.specifier}, found {installed_version}")


def _collect_exact_versions(entries: list[tuple[PluginCandidate, Any]]) -> set[str]:
    return {
        spec.version
        for _, requirement in entries
        for spec in requirement.specifier
        if spec.operator == "=="
    }


def _collect_candidate_requirement_issues(
    candidate: PluginCandidate,
    issues: dict[str, list[str]],
    requirements_by_package: dict[str, list[tuple[PluginCandidate, Any]]],
) -> None:
    for requirement in _iter_relevant_requirements(candidate):
        requirements_by_package.setdefault(requirement.name.lower(), []).append((candidate, requirement))
        _add_environment_requirement_issue(issues[candidate.identifier], requirement)


def _apply_cross_plugin_requirement_checks(
    issues: dict[str, list[str]],
    requirements_by_package: dict[str, list[tuple[PluginCandidate, Any]]],
) -> None:
    for package_name, entries in requirements_by_package.items():
        exact_versions = _collect_exact_versions(entries)

        if len(exact_versions) > 1:
            message = f"conflicting exact versions declared for '{package_name}': {', '.join(sorted(exact_versions))}"
            for candidate, _ in entries:
                issues[candidate.identifier].append(message)
            continue

        if len(exact_versions) != 1:
            continue

        pinned_version = next(iter(exact_versions))
        for candidate, requirement in entries:
            if requirement.specifier and not requirement.specifier.contains(pinned_version, prereleases=True):
                issues[candidate.identifier].append(
                    f"conflicts with plugin set on '{package_name}=={pinned_version}'"
                )


def _collect_requirement_issues(candidates: list[PluginCandidate]) -> dict[str, list[str]]:
    issues: dict[str, list[str]] = {candidate.identifier: [] for candidate in candidates}
    requirements_by_package: dict[str, list[tuple[PluginCandidate, Any]]] = {}

    if Requirement is None:
        logger.warning("Skipping plugin requirement checks because the 'packaging' dependency is unavailable")
        return issues

    for candidate in candidates:
        _collect_candidate_requirement_issues(candidate, issues, requirements_by_package)

    _apply_cross_plugin_requirement_checks(issues, requirements_by_package)

    return issues


def _is_private_plugin_import(module_name: str) -> bool:
    private_roots = ("soniccontrol", "soniccontrol_gui", "sonic_protocol")
    return module_name.startswith(private_roots) and not module_name.startswith("soniccontrol.api")


def _load_plugin_module_ast(candidate: PluginCandidate) -> ast.AST | None:
    spec = util.find_spec(candidate.module_name)
    if spec is None or spec.origin is None or not spec.origin.endswith(".py"):
        return None

    try:
        source = Path(spec.origin).read_text(encoding="utf-8")
        return ast.parse(source, filename=spec.origin)
    except (OSError, SyntaxError) as exc:
        logger.warning("Could not inspect plugin %s for private imports: %s", candidate.identifier, exc)
        return None


def _collect_private_imports(module_ast: ast.AST) -> set[str]:
    private_imports: set[str] = set()
    for node in ast.walk(module_ast):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if _is_private_plugin_import(alias.name):
                    private_imports.add(alias.name)
            continue

        if isinstance(node, ast.ImportFrom) and node.module and _is_private_plugin_import(node.module):
            private_imports.add(node.module)

    return private_imports


def _warn_on_private_imports(candidate: PluginCandidate) -> None:
    module_ast = _load_plugin_module_ast(candidate)
    if module_ast is None:
        return

    private_imports = _collect_private_imports(module_ast)

    if private_imports:
        logger.warning(
            "Plugin %s imports private modules directly: %s",
            candidate.identifier,
            ", ".join(sorted(private_imports)),
        )


def _normalize_runtime_requirements(requirements: Any) -> str:
    if requirements in (None, (), [], {}, "", "none"):
        return "none"
    return str(requirements)


def _has_compatible_plugin_manifest(candidate: PluginCandidate) -> bool:
    module = sys.modules.get(candidate.module_name)
    if module is None:
        return True

    required_api_version = getattr(module, "PLUGIN_API_VERSION", CURRENT_PLUGIN_API_VERSION)
    if required_api_version != CURRENT_PLUGIN_API_VERSION:
        logger.warning(
            "Skipping plugin %s because it requires plugin API %s but the app provides %s",
            candidate.identifier,
            required_api_version,
            CURRENT_PLUGIN_API_VERSION,
        )
        return False

    plugin_runtime = getattr(module, "PLUGIN_RUNTIME", SUPPORTED_PLUGIN_RUNTIME)
    if plugin_runtime != SUPPORTED_PLUGIN_RUNTIME:
        logger.warning(
            "Skipping plugin %s because it requires runtime '%s' but only '%s' is supported",
            candidate.identifier,
            plugin_runtime,
            SUPPORTED_PLUGIN_RUNTIME,
        )
        return False

    runtime_requirements = _normalize_runtime_requirements(
        getattr(module, "PLUGIN_RUNTIME_REQUIREMENTS", "none")
    )
    if runtime_requirements != "none":
        logger.warning(
            "Skipping plugin %s because runtime requirements '%s' are not supported yet",
            candidate.identifier,
            runtime_requirements,
        )
        return False

    return True


def validate_plugin_candidates(candidates: list[PluginCandidate]) -> List[PluginCandidate]:
    issues = _collect_requirement_issues(candidates)
    compatible: list[PluginCandidate] = []

    for candidate in candidates:
        candidate_issues = issues.get(candidate.identifier, [])
        if candidate_issues:
            logger.warning(
                "Skipping incompatible plugin %s from %s: %s",
                candidate.identifier,
                candidate.source,
                "; ".join(candidate_issues),
            )
            continue

        _warn_on_private_imports(candidate)
        compatible.append(candidate)

    return compatible


def load_plugin_candidates(candidates: list[PluginCandidate]) -> List[Any]:
    plugins: list[Any] = []

    for candidate in candidates:
        try:
            plugin = candidate.entry_point.load()
        except Exception as exc:
            logger.warning(
                "Failed to load plugin %s from %s (%s): %s",
                candidate.identifier,
                candidate.source,
                candidate.value,
                exc,
                exc_info=True,
            )
            continue

        if _has_compatible_plugin_manifest(candidate):
            plugins.append(plugin)

    return plugins


def discover_plugins(group: str) -> List[Any]:
    candidates = discover_plugin_candidates(group)
    compatible_candidates = validate_plugin_candidates(candidates)
    return load_plugin_candidates(compatible_candidates)
