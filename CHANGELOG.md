# Changelog

Observes [Semantic Versioning](https://semver.org/spec/v2.0.0.html) standard and [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) convention.

## [0.6.3] - 2022-11-18

### Added

- Added attribute default value to the form component field route response

## [0.6.2] - 2022-11-10

### Fixed

- Convert the return of the insert route and normal record routes to valid json [#146](https://github.com/datajoint/pharus/pull/146)

## [0.6.1] - 2022-11-04

### Added

- Add debug traces for standard routes [#143](https://github.com/datajoint/pharus/pull/143)
- Set a manual sleep due to `jwt` package not validating tokens issued in less than 1 sec [#143](https://github.com/datajoint/pharus/pull/143)

## [0.6.0] - 2022-11-03

### Added

- Allow requests to be thread-safe so that database connections don't cross-pollinate [#142](https://github.com/datajoint/pharus/pull/142)
- Add `basicquery` and `external` as options to extend with dynamic spec [#142](https://github.com/datajoint/pharus/pull/142)

## [0.5.6] - 2022-10-29

### Added

- Add option to flush user privileges if root user available using env vars: `DJ_HOST`, `DJ_ROOT_USER`, `DJ_ROOT_PASS` [#140](https://github.com/datajoint/pharus/pull/140)

## [0.5.5] - 2022-10-26

### Fixed

- Return `id_token` on login since it can be useful in OIDC logout flow PR [#139](https://github.com/datajoint/pharus/pull/139)

## [0.5.4] - 2022-10-20

### Fixed

- Allow form component table map destination templating PR [#138](https://github.com/datajoint/pharus/pull/138)

## [0.5.3] - 2022-10-11

### Fixed

- Flask would add empty body to request method PR [#137](https://github.com/datajoint/pharus/pull/137)

## [0.5.2] - 2022-10-06

### Added

- Create generic component class for custom routes PR [#135](https://github.com/datajoint/pharus/pull/135)

### Fixed

- Component type check condition to allow form POST route overriding PR [#132](https://github.com/datajoint/pharus/pull/132)

## [0.5.1] - 2022-09-27

### Added

- Schema templating for insert queries using query params PR #131
- Add support for OIDC login flow PR #130 (#125)

## [0.5.0] - 2022-09-21

### Fixed

- Bugs with returning UUID and NaN values PR #128

### Added

- Support schemas with a `-` by specifying instead with `__` in dynamic spec PR #128
- Support for new `antd-table` component. Prior `table` component will be deprecated in the next minor release. PR #128
- Support for InsertComponent

## [0.4.1] - 2022-03-24

### Fixed

- Bug with otumat version not being tied to the latest PR #119

## [0.4.0] - 2022-03-18

### Fixed

- Bug with `order_by` not applying from fetch args PR #117

### Added

- Support for new `slider` and `dropdown-query` components PR #118
- Numpy parser for `component_interface.py` to remove numpy types for json serialization PR #118
- Support for loginless mode PR #118

## [0.3.0] - 2022-01-21

### Changed

- Hot-reload mechanism to use `otumat watch` PR #116
- Renamed environment variable defining spec sheet to `PHARUS_SPEC_PATH` PR #116

### Added

- Autoformatting strategy using `black` PR #116
- Support for sci-viz components `metadata`, `image`, `dynamic grid` PR #116
- `component interface` for users to be able to load their own custom interface for sci-viz PR #116

### Fixed

- Various bugs related to datetime PR #116

## [0.2.3] - 2021-11-18

### Added

- Support for plot component PR #155
- Fetch argument specification in `dj_query` PR #155

## [0.2.2] - 2021-11-10

### Fixed

- Optimize dynamic api virtual modules. PR #113

## [0.2.1] - 2021-11-08

### Fixed

- Error with retrieving the module's installation root path. PR #112

## [0.2.0] - 2021-11-02

### Added

- Dynamic api generation from spec sheet.(#103, #104, #105, #107, #108, #110) PR #106, #109
- `dynamic_api_gen.py` Python script that generates `dynamic_api.py`.
- Add Tests for the new dynamic api.
- `server.py` now loads the routes generated dynamically from `dynamic_api.py` when it is present.

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

### Fixed

- `uuid` types not properly restricted on `GET /record`, `DELETE /record`, and `GET /dependency`. PR #102

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

[0.6.3]: https://github.com/datajoint/pharus/compare/0.6.2...0.6.3
[0.6.2]: https://github.com/datajoint/pharus/compare/0.6.1...0.6.2
[0.6.1]: https://github.com/datajoint/pharus/compare/0.6.0...0.6.1
[0.6.0]: https://github.com/datajoint/pharus/compare/0.5.6...0.6.0
[0.5.6]: https://github.com/datajoint/pharus/compare/0.5.5...0.5.6
[0.5.5]: https://github.com/datajoint/pharus/compare/0.5.4...0.5.5
[0.5.4]: https://github.com/datajoint/pharus/compare/0.5.3...0.5.4
[0.5.3]: https://github.com/datajoint/pharus/compare/0.5.2...0.5.3
[0.5.2]: https://github.com/datajoint/pharus/compare/0.5.1...0.5.2
[0.5.1]: https://github.com/datajoint/pharus/compare/0.5.0...0.5.1
[0.5.0]: https://github.com/datajoint/pharus/compare/0.4.1...0.5.0
[0.4.1]: https://github.com/datajoint/pharus/compare/0.4.0...0.4.1
[0.4.0]: https://github.com/datajoint/pharus/compare/0.3.0...0.4.0
[0.3.0]: https://github.com/datajoint/pharus/compare/0.2.3...0.3.0
[0.2.3]: https://github.com/datajoint/pharus/compare/0.2.2...0.2.3
[0.2.2]: https://github.com/datajoint/pharus/compare/0.2.1...0.2.2
[0.2.1]: https://github.com/datajoint/pharus/compare/0.2.0...0.2.1
[0.2.0]: https://github.com/datajoint/pharus/compare/0.1.0...0.2.0
[0.1.0]: https://github.com/datajoint/pharus/compare/0.1.0b2...0.1.0
[0.1.0b2]: https://github.com/datajoint/pharus/compare/0.1.0b0...0.1.0b2
[0.1.0b0]: https://github.com/datajoint/pharus/compare/0.1.0a5...0.1.0b0
[0.1.0a5]: https://github.com/datajoint/pharus/releases/tag/0.1.0a5
