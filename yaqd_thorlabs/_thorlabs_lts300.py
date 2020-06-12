from .__version__ import __branch__
from ._thorlabs_apt_motor import ThorlabsAptMotor


class ThorlabsLTS300(ThorlabsAptMotor):
    _kind = "thorlabs-lts300"
    _version = "0.1.0" + f"+{__branch__}" if __branch__ else ""
    defaults = {
        "units": "mm",
        "steps_per_unit": 25600,
    }

    def __init__(self, name, config, config_filepath):
        super().__init__(name, config, config_filepath)
        self._hw_limits = (0, 300)
