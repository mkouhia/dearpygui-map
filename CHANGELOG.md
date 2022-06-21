# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- Pre-download tiles at two tile radius around visible area.

## Changed
- Draw raw textures instead of static textures, use common texture registry.

### Fixed
- Use proper User-Agent http header when downloading tiles.
- Tune error logging output.

## [0.1.1] - 2022-06-13
### Fixed
- Change Python requirement to 3.10, as at least type hinting employs
  features released in 3.10.

## [0.1.0] - 2022-06-13
### Added
- First release: a map widget for Dear PyGui.
- Pan map by dragging mouse middle button.
- Zoom map by mouse scrolling.

[Unreleased]: https://github.com/mkouhia/dearpygui-map/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/mkouhia/dearpygui-map/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/mkouhia/dearpygui-map/releases/tag/v0.1.0

