from .__version__ import __branch__
from ._thorlabs_apt_motor import ThorlabsAptMotor


class ThorlabsBSC201(ThorlabsAptMotor):
    _kind = "thorlabs-bsc201"
    _version = "0.1.0" + f"+{__branch__}" if __branch__ else ""
    defaults = {
        "units": "mm",
    }
