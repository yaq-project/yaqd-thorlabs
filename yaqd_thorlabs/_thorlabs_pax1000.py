import asyncio
from collections import namedtuple
import sys
from typing import Dict, Any, List
from yaqd_core import HasMeasureTrigger, IsSensor, UsesSerial
import pyvisa
import time


class ThorlabsPAX1000(UsesSerial, HasMeasureTrigger, IsSensor):
    _kind = "thorlabs-pax1000"

    def __init__(self, name, config, config_filepath):
        super().__init__(name, config, config_filepath)

        if sys.platform.startswith("win32"):
            rm = pyvisa.ResourceManager() # use ni-visa backend
        else:
            rm = pyvisa.ResourceManager("@py")  # use pyvisa-py backend

        # find devices
        resources = rm.list_resources()
        self.logger.debug(resources)
        for resource in resources:
            try:
                serial = resource.split("::")[3]
                if self._config["serial"] == serial:
                    self.inst = rm.open_resource(resource)
                    break
            except Exception as e:
                pass
        else:
            raise ConnectionError(
                f"No resources match.  Found the following resources: {resources}."
            )

        # channels
        self._channel_units = {"revisions": None,
                               "timestamp": None,
                               "adc_min": None,
                               "adc_max": None,
                               "rev_time": None,
                               "theta": "radian",
                               "eta": "radian",
                               "dop": None,
                               "ptotal": None}
        self._channel_names = list(self._channel_units.keys())

        # initialize hardware
        self.inst.write(f"SENSe1:POWer:RANGe:AUTO {int(self._config['autorange'])}")
        self.inst.write(f"INPut:ROTation:VELocity {self._config['velocity']}")
        self._wavelength = float(self.inst.query("SENSe:CORRection:WAVelength?")) * 1e9
        self.inst.write("SENS:CALC 9")  # TODO: other modes could be chosen in a future version
        self.inst.write("INPut:ROTation:STATe 1")
        while not self.inst.query("INPut:ROTation:STATe?"):
            time.sleep(1)

    def close(self):
        self.inst.write("INPut:ROTation:STATe 0")
        self.inst.close()

    def direct_serial_write(self, string):
        self.inst.write(string)

    def get_wavelength(self) -> float:
        return self._wavelength

    async def _measure(self):
        await asyncio.sleep(0.1)
        out = dict()
        latest = self.inst.query("SENSe:DATA:PRIMary:LATest?").split(",")
        latest = [float(i) for i in latest]
        out["revisions"] = latest[0]
        out["timestamp"] = latest[1]
        out["adc_min"] = latest[5]
        out["adc_max"] = latest[6]
        out["rev_time"] = latest[7]
        out["theta"] = latest[9]
        out["eta"] = latest[10]
        out["dop"] = latest[11]
        out["ptotal"] = latest[12]
        return out

    def set_wavelength(self, wavelength):
        out = wavelength / 1e9
        out = format(out, ".3e")
        self.inst.write(f"SENSe:CORRection:WAVelength {out}")
        self.logger.debug(f"new wavelength: {wavelength} nm")
        self._wavelength = float(self.inst.query("SENSe:CORRection:WAVelength?")) * 1e9
