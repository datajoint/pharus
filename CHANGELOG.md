# Changelog

Observes [Semantic Versioning](https://semver.org/spec/v2.0.0.html) standard and [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) convention.

## [0.1.0] - 2021-03-31
### Added
- Local database instance pre-populated with sample data for `dev` Docker Compose environment. PR #99
- Capability to insert multiple, update multiple, and delete multiple. PR #99
- Allow dependency restriction to include secondary attributes from parent table. PR #99

### Changed
- Update `datajoint` to newly released `0.13.0`. PR #97
- Rename service `pharus` to `pharus-docs` in `docs` Docker Compose environment to allow simulataneous development. PR #99
- Update NGINX reverse proxy image reference. PR #99
- Refactored API design to align with common REST resource naming convention. (#38) PR #99
- Hide classes and methods that are internal and subject to change. PR #99

### Removed
- `InvalidDeleteRequest` exception is no longer available as it is now allowed to delete more than 1 record at a time. PR #99

## [0.1.0b2] - 2021-03-12

### Fixed
- Fixed behavior where using list_table with a nonexistent schema_name creates it instead of returning an error message (#65) PR #63

### Changed
- Contribution policy to follow directly the general DataJoint Contribution Guideline. (#91) PR #94, #95

### Added
- Issue templates for bug reports and enhancement requests. PR #94, #95
- Docker environment for documentation build. (#92) PR #94, #95
- Add Sphinx-based documentation source and fix parsing issues. (#92) PR #94, #95
- GitHub Actions automation that publishes on release new docs to release and GitHub Pages. (#92) PR #94, #95

## [0.1.0b0] - 2021-02-26

### Security
- Documentation with detail regarding warning on bearer token. (#83) PR #88

### Fixed
- Incorrect virtual module reference of `schema_virtual_module` in table metadata. (#85) PR #88

### Added
- Docker `dev` environment that supports hot reloading. PR #79
- Documentation on setting up environments within `docker-compose` header. PR #79
- `cascade` option for `/delete_tuple` route. (#86) PR #88
- When delete with `cascade=False` fails due to foreign key relations, returns a HTTP error code of `409 Conflict` with a JSON body containing specifics of 1st child. (#86) PR #88

### Changed
- Replaced `DJConnector.snake_to_camel_case` usage with `datajoint.utils.to_camel_case`. PR #88
- Default behavior for `/delete_tuple` now deletes without cascading. (#86) PR #88
- Consolidated `pytest` fixtures into `__init__.py` to facilitate reuse. PR #88
- Modify dependency check to not perform deep check and use accessible fk relations only. (#89) PR #90
- Update nginx image to pull from datajoint organization. (#80) PR #90

### Removed
- Docker `base` environment to simplify dependencies. PR #79

## [0.1.0a5] - 2021-02-18
### Added
- List schemas method.
- List tables method.
- Data entry, update, delete, and view operations for DataJoint table tiers: `dj.Manual`, `dj.Lookup`.
- Read table records with proper paging and compounding restrictions (i.e. filters).
- Read table definition method.
- Support for DataJoint attribute types: `varchar`, `int`, `float`, `datetime`, `date`, `time`, `decimal`, `uuid`.
- Check dependency utility to determine child table references.

[0.1.0]: https://github.com/datajoint/pharus/compare/0.1.0b2...0.1.0
[0.1.0b2]: https://github.com/datajoint/pharus/compare/0.1.0b0...0.1.0b2
[0.1.0b0]: https://github.com/datajoint/pharus/compare/0.1.0a5...0.1.0b0
[0.1.0a5]: https://github.com/datajoint/pharus/releases/tag/0.1.0a5