# Changelog

Observes [Semantic Versioning](https://semver.org/spec/v2.0.0.html) standard and [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) convention.

## [Unreleased]
### Added
- Docker `dev` environment that supports hot reloading.
- Documentation on setting up environments within `docker-compose` header.

### Removed
- Docker `base` environment to simplify dependencies.

## [0.1.0a5] - 2021-02-18
### Added
- List schemas method.
- List tables method.
- Data entry, update, delete, and view operations for DataJoint table tiers: `dj.Manual`, `dj.Lookup`.
- Read table records with proper paging and compounding restrictions (i.e. filters).
- Read table definition method.
- Support for DataJoint attribute types: `varchar`, `int`, `float`, `datetime`, `date`, `time`, `decimal`, `uuid`.
- Check dependency utility to determine child table references.

[Unreleased]: https://github.com/datajoint/pharus/compare/0.1.0a5...HEAD
[0.1.0a5]: https://github.com/datajoint/pharus/releases/tag/0.1.0a5