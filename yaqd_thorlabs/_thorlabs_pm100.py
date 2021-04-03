__all__ = ["ThorlabsPM100"]

import asyncio
from typing import Dict, Any, List
from yaqd_core import IsSensor, IsDaemon
import visa
from ThorlabsPM100 import ThorlabsPM100 as Driver


class ThorlabsPM100(IsSensor, IsDaemon):
    _kind = "thorlabs-pm100"

    def __init__(self, name, config, config_filepath):
        self._channel_names = {"power"}
        self._channel_shapes = {"power": []}
        self._channel_units = {"power": "W"}

        inst = visa.instrument(self._config["usb_resource"], term_chars='\n', timeout=1)
        # 'USB0::0x0000::0x0000::DG5Axxxxxxxxx::INSTR',
        self.power_meter = Driver(inst=inst)

        # "https://github.com/clade/ThorlabsPM100"
        # https://pythonhosted.org/ThorlabsPM100/thorlabsPM100.html

    async def update_state(self):
        # Do whatever needs to be done to fill a dictionary mapping names to values
        # (or arrays for shaped data)
        # also include the measurment id in the _measured array
        out = self.meter.read
        return {"power": out}
