__all__ = ["ThorlabsPM100"]

import asyncio
from collections import namedtuple
import sys
from typing import Dict, Any, List
from yaqd_core import HasMeasureTrigger, IsSensor
# from yaqd_scpi import SCPISensor  # inherit from this?
import pyvisa
import time

sensor_flags = [
    "is_power_sensor",
    "is_energy_sensor",
    None,
    None,
    "response_settable",
    "wavelength_settable",
    "tau_settable",
    None,
    "has_temperature_sensor",
]

SensorInfo = namedtuple(
    "SensorInfo",
    ["model", "serial", "last_calibration", "type", "subtype", "flags"]
)

MeterInfo = namedtuple(
    "MeterInfo",
    ["maker", "model", "serial", "firmware_version"]
)


class ThorlabsPM100(HasMeasureTrigger, IsSensor):
    _kind = "thorlabs-pm100"

    def __init__(self, name, config, config_filepath):
        super().__init__(name, config, config_filepath)
        self._channel_names = ["power"]
        self._channel_shapes = {"power": []}
        self._channel_units = {
            "power": "W",
            "current": "A",
            "voltage": "V",
            "energy": "J",
            "frequency": "Hz",
            "intensity": "W/cm^2",
            "fluence": "J/cm^2",
            "resistance": "Ohm",
            "temperature": "C",
        }

        if sys.platform.startswith("win32"):
            rm = pyvisa.ResourceManager() # use ni-visa backend
        else:
            rm = pyvisa.ResourceManager("@py")  # use pyvisa-py backend

        # find devices
        resources = rm.list_resources()
        self.logger.debug(resources)
        for resource in resources:
            port, vender, product, serial, device = resource.split("::")
            if (vender == "0x1313") and (device == "INSTR"):  # thorlabs instrument
                # if serial is not specified; grab the first valid device
                if self._config["serial"] in [None, serial]:
                    self.inst = rm.open_resource(resource)
                    self.resource = resource
                    self.power_meter_info = MeterInfo(*self.inst.query("*IDN?")[:-1].split(","))
                    self.logger.info(self.power_meter_info)
                    break
        else:
            raise ConnectionError(f"No resources match.  Found the following resources: {resources}.")
        # initiate configuration
        self.update_sensor()
        self.wait = self._config["wait"]
        self.inst.write(f"SENSe:AVERage:COUNt {self._config['averaging']}")
        self.logger.debug("sample average: " + self.inst.query("SENSe:AVERage:COUNt?")[:-1])
        self.inst.write(f"CONF:{self._config['readout']}")

    def _configure_measurement(self):
        self.inst.write("ABORt")
        self.inst.write("STAT:OPER?")
        self.inst.write("INIT")

    async def _measure(self):
        self._configure_measurement()
        await asyncio.sleep(self.wait)
        start = time.time()
        while True:
            try:
                out = self.inst.query("FETCh?")[:-1]
                end = time.time()
                break
            except Exception as err:
                self.logger.error(err)
                time.sleep(0.1)
        self.logger.debug(f"dt: {end-start}, sig {out}")
        return {"power": float(out)}

    def direct_scpi_query(self, query:str) -> str:
        if query.endswith("?"):
            return self.inst.query(query)
        else:
            raise ValueError(f"string {query} is not a query.")

    def direct_scpi_write(self, write:str) -> None:
        self.inst.write(write)

    def update_sensor(self):
        sensor_info = self.inst.query("SYSTem:SENSor:IDN?")[:-1].split(",")
        flag_bitmap = f"{int(sensor_info[-1]):b}"
        flags = [sensor_flags[i] for i, x in enumerate(flag_bitmap[::-1]) if int(x)]
        sensor_info[-1] = flags
        self.logger.info(sensor_info)
        self.sensor_info = SensorInfo(*sensor_info)
        self.logger.debug(self.sensor_info)

    def close(self):
        self.inst.close()
