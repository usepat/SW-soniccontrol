@defgroup SonicPlugins
@addtogroup SonicPlugins
@{


# SonicControl Plugin Architecture (v1)

## Goals

- Allow plugins to extend the application safely
- Keep the main app public while plugins can remain private
- Support future evolution without massive refactoring
- Avoid dependency conflicts and fragile imports
- Introduce a stable plugin API boundary

---

## High-Level Design

The system is structured around three main concepts:

1. **Main Application (Frozen / Public)**
2. **Plugin API (Stable Contract)**
3. **Plugins (Private Extensions)**

---

## Core Principles

### 1. Explicit API Boundary

All plugin-facing functionality must be accessed through:

`soniccontrol.api.*`

Rules:
- Plugins must only import from `soniccontrol.api.*`
- Anything outside this namespace is considered internal and may change without notice
- The API layer re-exports internal functionality

---

### 2. Thin API Layer (Initial Approach)

The API is initially implemented as a **re-export layer**, not a full abstraction.

Example:

```python
# soniccontrol/api/enums.py
from soniccontrol.core.control import ControlMode

__all__ = ["ControlMode"]
```

This allows:
- Minimal refactoring now
- Future internal restructuring without breaking plugins

---

### 3. Plugin Discovery

Plugins are discovered via:

- Python entry points (preferred)
- Additional plugin directories (for deployment)

Example:

```python
import importlib.metadata

entry_points = importlib.metadata.entry_points().select(group="soniccontrol.plugins")
```

---

### 4. Plugin Execution Modes (Planned)

The system is designed to support three modes:

#### a) In-Process Plugins (Initial Implementation)
- Run inside main app
- Share dependencies with app
- No isolation
- Easiest to implement

#### b) Shared Runtime (Future)
- Separate Python runtime shared by multiple plugins
- Allows additional dependencies
- Still a shared environment

#### c) Isolated Runtime (Future)
- Each plugin runs in its own runtime
- Full dependency isolation
- Likely out-of-process execution

---

### 5. Dependency Strategy (Initial)

For now:

- Plugins must be compatible with main app dependencies
- No conflicting dependency resolution yet
- Validation step will warn or reject incompatible plugins

---

### 6. Plugin API Versioning

A plugin API version is defined:

```python
# soniccontrol/api/version.py
PLUGIN_API_VERSION = "1.0.0"
```

Rules:
- Breaking changes → major version bump
- Additive changes → minor version bump
- Bugfix/internal → patch version bump

---

### 7. API Change Detection (Planned)

To prevent silent breakage:

- A snapshot of the API surface will be generated later
- Changes will require explicit review
- CI can enforce version/changelog updates

This should eventually include:
- function signatures
- class methods
- enum members
- exported names

---

### 8. What Counts as API?

Anything exposed via `soniccontrol.api.*`

#### Includes
- Enums such as `ControlMode`
- Base classes such as `UIComponent`
- Public methods and properties
- Event interfaces and common types

#### Does not include
- Internal modules
- Private attributes like `_something`
- Undocumented implementation details
- Arbitrary imports from outside `soniccontrol.api.*`

---

## Current State / What Will Be Implemented First

### Implemented in v1
- `soniccontrol.api` package
- Re-export of currently used plugin imports
- Plugin discovery cleanup
- Basic compatibility checks
- In-process plugin execution only
- Plugin API version constant

### Not implemented yet
- Shared runtime
- Plugin-specific runtimes
- Full dependency isolation
- API snapshot system
- Advanced compatibility negotiation
- Strongly abstracted interfaces for every plugin interaction

---

## Runtime Strategy (Planned but Not Yet Implemented)

The long-term runtime model supports three tiers:

### Tier 1: Main App Runtime
Plugins run directly inside the main app process and use the same interpreter and dependency set.

Use this for:
- current plugins
- simple extensions
- plugins that are already compatible with app dependencies

### Tier 2: Shared Runtime
A separate shared Python runtime may be provided for plugins that need additional dependencies but remain mutually compatible.

Use this for:
- plugin groups that need extra tools
- plugins that do not conflict with each other
- future expansion beyond trivial plugins

This runtime may eventually be:
- created dynamically as a venv
- unpacked from a prebuilt runtime bundle

### Tier 3: Isolated Runtime
A plugin may eventually run in its own standalone runtime if it has heavy or conflicting dependencies.

Use this for:
- plugins with dependency conflicts
- plugins needing their own toolchain
- future advanced/high-end plugins

Important:
- True dependency isolation only exists when a plugin runs in its own interpreter/runtime
- Merely placing plugin files in a different folder is not enough

---

## Migration Strategy

### Step 1
Create `soniccontrol.api` and move or re-export all currently plugin-used imports there

### Step 2
Update plugins to import only from the API namespace

### Step 3
Clean up plugin discovery and loading

### Step 4
Add compatibility checks and clear logging

### Step 5 (later)
Introduce runtime separation and API evolution controls

---

## Key Rule

If a plugin imports something from `soniccontrol.api`, that thing is part of the plugin API and must be treated as stable.

---

## Practical Development Rules

- Do not redesign everything now
- Keep the API layer thin
- Prefer re-exports over deep refactors in the beginning
- Make the plugin boundary explicit first
- Improve abstractions later, only where needed

---

## Future Evolution

Later improvements may include:
- replacing re-exports with more stable interfaces
- introducing runtime isolation
- adding API snapshot validation
- capability-based plugin compatibility
- stronger CI rules around plugin API changes

---

## Summary

This architecture prioritizes:

- pragmatism now
- flexibility later
- minimal initial refactor
- clear boundaries to avoid future breakage

The first version does not try to solve every future plugin problem. It creates a clean structure that supports current plugins while leaving room for better isolation, stronger contracts, and clearer versioning over time.

@}