# Changelog

All notable changes to this project will be documented in this file.

## [1.x.x]
- Now, marked as deprecated.

## [2.0.0]

- Initial v2 release: framework-agnostic SDK

## [2.0.1]

### Added
- Update new tests for sdk
- Support loading plugins by tree folder, multiple-version

### Fixed
- **sdk_state.py**: `add_tool_used` and routing now call `RoutingHelpers._add_tool_avoiding_duplicates` and `RoutingHelpers._calculate_consecutive_repeats` (were incorrectly `StateHelpers`), resolving `AttributeError` in state/routing tests.
