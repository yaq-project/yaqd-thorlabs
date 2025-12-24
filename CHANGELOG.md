# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

## [2025.12.0]

### Fixed
- asyncio implementation works on python >= 3.14

### Changed
- `thorlabs-pm-triggered`: `_measure` code revised to avoid recursion

### Added
- some example configs

## [2022.7.0]

### Changed
- Log levels of serial communication logging

### Fixed
- Queue problem with ELLX devices which cause busy to toggle early

## [2022.4.0]

### Fixed
- Conditions which could cause busy to be released during motion

## [2022.3.0]

### Fixed
- `yaqd-pm-triggered`: fixed bug where hardware timeouts from measurement were not handled
- Rerender AVPR for sensors such that measurment id is an int

### Added
- new daaemon for pax1000 polarimeters

## [2022.2.1]

### Fixed
- normalized known hardware in tomls
- `yaqd-pm-triggered`: fixed bug where daemon could not recognize Thorlabs instrument ports on some computers.

## [2022.2.0]

### Added
- Support for Ell18 Elliptec rotory mount
- PM-series power meter support (tested on pm100)

### Fixed
- pin thorlabs-apt-protocol>=29.0.0 (older versions do not work with MPC320)

## [2022.1.0]

### Added
- support for MPC320 motorized fiber polarization controller

### Changed
- apt_motor update_state now reads position from MGMSG_MOT_GET_USTATUSUPDATE
- serial dispatcher now respects chan_ident

## [2021.10.0]

### Changed
- rerender avprs based on recent traits update

## [2021.3.0]

### Fixed
- add bsc203 entry point

## [2021.2.0]

### Added
- bsc203 support
- new config, behavior: "polling status"
- hardware support documentation in avprs

### Fixed
- added forgotten config options to is-daemon: enable, log_level, and log_to_file

## [2020.12.0]

### Added
- conda-forge as installation source

### Fixed
- Read units from config

## [2020.11.1]

### Changed
- Update position during motion

## [2020.11.0]

### Fixed
- entry point for KST101 fixed
- entry point "BSC201" was misspelled as "BSC101", fixed
- homing more reliable

### Changed
- regenerated avpr based on recent traits update
- use new trait base classes

## [2020.07.0]

### Changed
- Now uses Avro-RPC [YEP-107](https://yeps.yaq.fyi/107/)
- Uses Flit for distribution

## 2020.06.0

### Added
- initial release

[Unreleased]: https://github.com/yaq-project/yaqd-thorlabs/compare/v2025.12.0...main
[2025.12.0]: https://github.com/yaq-project/yaqd-thorlabs/compare/v2022.7.0...v2025.12.0
[2022.7.0]: https://github.com/yaq-project/yaqd-thorlabs/compare/v2022.4.0...v2022.7.0
[2022.4.0]: https://github.com/yaq-project/yaqd-thorlabs/compare/v2022.3.0...v2022.4.0
[2022.3.0]: https://github.com/yaq-project/yaqd-thorlabs/compare/v2022.2.1...v2022.3.0
[2022.2.1]: https://github.com/yaq-project/yaqd-thorlabs/compare/v2022.2.0...v2022.2.1
[2022.2.0]: https://github.com/yaq-project/yaqd-thorlabs/compare/v2022.1.0...v2022.2.0
[2022.1.0]: https://github.com/yaq-project/yaqd-thorlabs/compare/v2021.10.0...v2022.1.0
[2021.10.0]: https://github.com/yaq-project/yaqd-thorlabs/compare/v2021.3.0...v2021.10.0
[2021.3.0]: https://github.com/yaq-project/yaqd-thorlabs/compare/v2021.2.0...v2021.3.0
[2021.2.0]: https://github.com/yaq-project/yaqd-thorlabs/compare/v2020.12.0...v2021.2.0
[2020.12.0]: https://github.com/yaq-project/yaqd-thorlabs/compare/v2020.11.1...v2020.12.0
[2020.11.1]: https://github.com/yaq-project/yaqd-thorlabs/compare/v2020.11.0...v2020.11.1
[2020.11.0]: https://github.com/yaq-project/yaqd-thorlabs/compare/v2020.07.0...v2020.11.0
[2020.07.0]: https://github.com/yaq-project/yaqd-thorlabs/compare/v2020.06.0...v2020.07.0
