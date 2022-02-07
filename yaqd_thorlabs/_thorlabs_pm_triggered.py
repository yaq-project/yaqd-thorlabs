__all__ = ["ThorlabsPMTriggered"]

import asyncio
from collections import namedtuple
import sys
from typing import Dict, Any, List
from yaqd_core import HasMeasureTrigger, IsSensor
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

pm_units = {
    "power": "W",
    "current": "A",
    "voltage": "V",
    "energy": "J",
    "frequency": "Hz",
    # "intensity": "W/cm^2",
    # "fluence": "J/cm^2",
    "resistance": "Ohm",
    "temperature": "C"
}


def to_bitstring(string):
    """first item is lsb
    """
    return f"{int(string):b}"[::-1]


class ThorlabsPMTriggered(HasMeasureTrigger, IsSensor):
    _kind = "thorlabs-pm-triggered"

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
            self.logger.debug(resources)
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
        self.averaging = self._config["averaging"]
        self.inst.write(f"*CLS; SENSe:AVERage:COUNt {self.averaging}")
        self._check_inst()
        opc = self.inst.query("*OPC?")
        self.logger.debug(f"opc? {opc}")
        self.logger.debug("sample average: " + self.inst.query("SENSe:AVERage:COUNt?")[:-1])
        self.inst.write(f"CONF:{self._config['readout']}")
        self._check_inst()
        
    async def _measure(self):
        start = time.time()
        self.inst.write("ABORt; INIT")
        self._check_inst()
        await asyncio.sleep(4e-4 * self.averaging)  # important to wait for requests
        for _ in range(10):
            status = int(self.inst.query("STAT:OPER?")[:-1])
            out = float(self.inst.query("FETCh?")[:-1])
            if int(f"{status:10b}"[-10]):
                end = time.time()
                self.logger.debug(f"dt: {(end-start):0.3f}, sig {out:1.6f}")
                break
            self.logger.debug(f"status: {status}, out {out}")
            await asyncio.sleep(0)
        else:
            self.logger.debug("measure timeout; retrying")
            return self._measure()
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
        flag_bitstring = to_bitstring(sensor_info.pop(-1))
        flags = [sensor_flags[i] for i, x in enumerate(flag_bitstring) if int(x)]
        self.sensor_info = SensorInfo(*sensor_info, flags)
        self.logger.debug(self.sensor_info)
        _channel_units = {}
        _channel_names = []
        if "is_power_sensor" in flags:
            self.logger.debug("power sensor")
            _channel_names.append("power")
            _channel_units["power"] = "W"
        else:
            raise NotImplementedError("Only power sensors are currently supported.")
        if "wavelength_settable" in flags:
            self._state["wavelength"] = float(self.inst.query("SENSe:CORRection:WAVelength?")[:-1])
            self.logger.debug(f"wavelength {self._state['wavelength']} nm")
        self._channel_names = _channel_names
        self._channel_units = _channel_units
        self._channel_shapes = {k:[] for k in self._channel_names}

    def set_wavelength(self, wavelength):
        assert "wavelength_settable" in self.sensor_info["flags"]
        self.inst.write(f"SENSe:CORRection:WAVelength {float(wavelength)}")
        self._state["wavelength"] = self.inst.query("SENSe:CORRection:WAVelength?")
        self.logger.debug(f"new wavelength: {self._state['wavelength']} nm")

    def _check_inst(self):
        errno, err = self.inst.query("SYST:ERR?")[:-1].split(",")
        if int(errno) == 0:
            return
        self.logger.error(err)

    def close(self):
        self.inst.close()
