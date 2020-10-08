# yaqd-thorlabs

[![PyPI](https://img.shields.io/pypi/v/yaqd-thorlabs)](https://pypi.org/project/yaqd-thorlabs)
[![Conda](https://img.shields.io/conda/vn/conda-forge/yaqd-thorlabs)](https://anaconda.org/conda-forge/yaqd-thorlabs)
[![yaq](https://img.shields.io/badge/framework-yaq-orange)](https://yaq.fyi/)
[![black](https://img.shields.io/badge/code--style-black-black)](https://black.readthedocs.io/)
[![ver](https://img.shields.io/badge/calver-YYYY.0M.MICRO-blue)](https://calver.org/)
[![log](https://img.shields.io/badge/change-log-informational)](https://gitlab.com/yaq/yaqd-thorlabs/-/blob/master/CHANGELOG.md)

yaq daemons for thorlabs hardware

This package contains the following daemon(s):

- https://yaq.fyi/daemons/thorlabs-bsc201
- https://yaq.fyi/daemons/thorlabs-k10cr1
- https://yaq.fyi/daemons/thorlabs-kdc101
- https://yaq.fyi/daemons/thorlabs-kst101
- https://yaq.fyi/daemons/thorlabs-lts150
- https://yaq.fyi/daemons/thorlabs-lts300

## Windows and APT

This package uses the serial interface to APT with help from [thorlabs-apt-protocol](https://gitlab.com/yaq/thorlabs-apt-protocol).

On Windows, you must toggle a driver setting to make the COM port appear:

Within Device Manager, right click on the APT device (under USB devices), and go to Properties.
On the Advanced tab, check the box that says Load VCP (VCP stands for Virtual COM Port).
Unplug and replug the USB cable to make it load the COM Port.