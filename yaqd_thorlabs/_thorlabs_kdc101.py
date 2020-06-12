from .__version__ import __branch__
from ._thorlabs_apt_motor import ThorlabsAptMotor


class ThorlabsKDC101(ThorlabsAptMotor):
    _kind = "thorlabs-kdc101"
    _version = "0.1.0" + f"+{__branch__}" if __branch__ else ""
    defaults = {
        "units": "mm",
    }
