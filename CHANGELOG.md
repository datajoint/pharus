# Changelog

Observes [Semantic Versioning](https://semver.org/spec/v2.0.0.html) standard and [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) convention.

## [0.1.0a1] - 2021-02-16
### Added
- List schemas method.
- List tables method.
- Create, Read, Update, Delete (CRUD) operations for DataJoint table tiers: `dj.Manual`, `dj.Lookup`.
- Read table records with proper paging and compounding restrictions (i.e. filters).
- Read table definition method.
- Support for DataJoint attribute types: `varchar`, `int`, `float`, `datetime`, `date`, `time`, `decimal`, `uuid`.
- Check dependency utility to determine child table references.
