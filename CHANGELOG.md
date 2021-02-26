# Changelog

Observes [Semantic Versioning](https://semver.org/spec/v2.0.0.html) standard and [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) convention.

## [0.1.0b1] - 2021-02-26

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
- Modify dependency check to not perform deep check and use accessible fk relations only. PR #90

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

[0.1.0b1]: https://github.com/datajoint/pharus/compare/0.1.0a5...0.1.0b1
[0.1.0a5]: https://github.com/datajoint/pharus/releases/tag/0.1.0a5