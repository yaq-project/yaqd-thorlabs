__all__ = ["ThorlabsAptMotor"]

import asyncio
from typing import Dict, Any, List

import serial  # type: ignore
import thorlabs_apt_protocol as apt  # type: ignore
from yaqd_core import ContinuousHardware

from .__version__ import __branch__
from ._serial import SerialDispatcher


class ThorlabsAptMotor(ContinuousHardware):
    _kind = "thorlabs-apt-motor"
    _version = "0.1.0" + f"+{__branch__}" if __branch__ else ""
    traits: List[str] = ["uses-serial", "uses-uart", "is-homeable"]
    defaults: Dict[str, Any] = {
        "source": 0x01,
        "dest": 0x50,
        "chan_ident": 0x01,
        "baud_rate": 115200,
    }
    serial_dispatchers: Dict[str, SerialDispatcher] = {}

    def __init__(self, name, config, config_filepath):
        self._source = config["source"]
        self._dest = config["dest"]
        # Very few hardware actually use chan_ident as anything other than 0x01
        # Until proven desired, I am not going to code for the idea of chan ident
        # being the only thing separating daemons, which manifests in the serial dispatcher
        # -- KFS 2020-06-08
        self._chan_ident = config["chan_ident"]

        if config["serial_port"] in ThorlabsAptMotor.serial_dispatchers:
            self._serial = ThorlabsAptMotor.serial_dispatchers[config["serial_port"]]
        else:
            self._serial = SerialDispatcher(
                serial.Serial(config["serial_port"], config["baud_rate"], timeout=0, rtscts=True,)
            )
            self._serial.port.rts = True
            self._serial.port.reset_input_buffer()
            self._serial.port.reset_output_buffer()
            self._serial.port.rts = False
            ThorlabsAptMotor.serial_dispatchers[config["serial_port"]] = self._serial
        self._read_queue = asyncio.Queue()
        self._serial.workers[self._dest] = self._read_queue

        super().__init__(name, config, config_filepath)

        self._serial.write(apt.hw_no_flash_programming(self._dest, self._source))
        # Looking closer, this may only apply to servos... may have to set steps per unit and hw limits ourselves...
        self._serial.write(apt.mot_req_stageaxisparams(self._dest, self._source, self._chan_ident))
        self._steps_per_unit = 1  # Set in response to stageaxisparams

    def units_to_steps(self, position):
        return round(position * self._steps_per_unit)

    def steps_to_units(self, position):
        return position / self._steps_per_unit

    def _set_position(self, position):
        position = self.units_to_steps(position)
        self._serial.write(
            apt.mot_move_absolute(self._dest, self._source, self._chan_ident, position)
        )

    def home(self):
        self._loop.create_task(self._home())

    async def _home(self):
        self._busy = True
        self._serial.write(apt.mot_move_home(self._dest, self._source, self._chan_ident))
        self._home_event = asyncio.Event()
        await self._home_event.wait()
        self.set_position(self._destination)

    async def update_state(self):
        """Continually monitor and update the current daemon state."""
        # If there is no state to monitor continuously, delete this function
        while True:
            reply = await self._read_queue.get()
            # mot_get_stageaxisparams
            if reply.msgid == 0x04F2:
                self._steps_per_unit = reply.counts_per_unit
                self._hw_limits = (
                    self.steps_to_units(reply.min_pos),
                    self.steps_to_units(reply.max_pos),
                )
            # mot_move_homed
            elif reply.msgid == 0x0444:
                self._home_event.set()
            # mot_move_completed, mot_get_statusupdate, mot_get_dcstatusupdate, mot_get_statusbits
            elif reply.msgid in (0x0464, 0x0481, 0x042A):
                self._position = self.steps_to_units(reply.position)
                self._busy = not reply.settled
            else:
                logger.info(f"Unhandled reply {reply}")

    def direct_serial_write(self, message):
        self._busy = True
        self._serial.write(message)
