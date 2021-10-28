# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

### Changed

- Fixed error when freezing a dead symlink

## [0.2.0] - 2021-09-23

### Added

- Support for S3 backend
- /tree endpoint: listing all files in a remote. Returns a list of dicts with the file path and 'missing' attribute. 'missing' will be set to true if the file is missing from the local storage.

### Changed

- Run the web process as root to avoid permission problems while listing files (data should be mounted in ro mode anyway)
- Fixed remote listing of symlinks
- Fixed logs flooded when listing remote

## [0.1.5] - 2021-04-29

### Changed

- Fix decoding of utf-8 filenames

## [0.1.4] - 2021-04-29

### Changed

- Fix copied file listing from rclone stderr

### Changed

## [0.1.3] - 2021-04-28

### Changed

- Fix error when pulling a single file in a repo with excludes

## [0.1.2] - 2021-04-15

### Changed

- Fix permission denied on LOG_FOLDER
- Adjust docker-compose.prod.yml
- Fix SQL connection problem
- Fix task logs being mixed

### Added

- `disable_atime_test` option for cases where atime testing is not reliable

## [0.1.1] - 2021-03-17

### Changed

- Check email value in API
- Fix docker image building

## [0.1.0] - 2021-02-17

### Added

- First ever release of Baricadr
