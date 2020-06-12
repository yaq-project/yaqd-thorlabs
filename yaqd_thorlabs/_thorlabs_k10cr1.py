from .__version__ import __branch__
from ._thorlabs_apt_motor import ThorlabsAptMotor


class ThorlabsK10CR1(ThorlabsAptMotor):
    _kind = "thorlabs-k10cr1"
    _version = "0.1.0" + f"+{__branch__}" if __branch__ else ""
    defaults = {
        "units": "deg",
        "steps_per_unit": 409600 / 3,
    }
