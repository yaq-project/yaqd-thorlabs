__all__ = ["ThorlabsAptMotor"]

import asyncio
from typing import Dict, Any, List

import serial  # type: ignore
import thorlabs_apt_protocol as apt  # type: ignore
from yaqd_core import UsesUart, UsesSerial, IsHomeable, HasLimits, HasPosition, IsDaemon

from ._serial import SerialDispatcherApt


class ThorlabsAptMotor(UsesUart, UsesSerial, IsHomeable, HasLimits, HasPosition, IsDaemon):
    _kind = "thorlabs-apt-motor"
    serial_dispatchers: Dict[str, SerialDispatcherApt] = {}

    def __init__(self, name, config, config_filepath):
        self._source = config["source"]
        self._dest = config["dest"]
        self._chan_ident = config["chan_ident"]
        self._steps_per_unit = config["steps_per_unit"]

        if config["serial_port"] in ThorlabsAptMotor.serial_dispatchers:
            self._serial = ThorlabsAptMotor.serial_dispatchers[config["serial_port"]]
        else:
            self._serial = SerialDispatcherApt(
                serial.Serial(
                    config["serial_port"],
                    config["baud_rate"],
                    timeout=0,
                    rtscts=True,
                )
            )
            self._serial.port.rts = True
            self._serial.port.reset_input_buffer()
            self._serial.port.reset_output_buffer()
            self._serial.port.rts = False
            ThorlabsAptMotor.serial_dispatchers[config["serial_port"]] = self._serial
        self._read_queue = asyncio.Queue()
        self._serial.workers[self._dest, self._chan_ident] = self._read_queue

        super().__init__(name, config, config_filepath)

        self._units = config["units"]
        self._serial.write(apt.hw_no_flash_programming(self._dest, self._source))
        self._serial.write(apt.hw_req_info(self._dest, self._source))
        if config["automatic_status_updates"]:
            self._serial.write(apt.hw_start_updatemsgs(self._dest, self._source))
        else:
            self._tasks.append(self._loop.create_task(self.request_status()))

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
        self._home_event = asyncio.Event()
        self._serial.write(apt.mot_move_home(self._dest, self._source, self._chan_ident))
        await self._home_event.wait()
        self.set_position(self._state["destination"])

    async def request_status(self):
        while True:
            self._serial.write(
                apt.mot_req_statusupdate(self._dest, self._source, self._chan_ident)
            )
            await asyncio.sleep(0.2)

    async def update_state(self):
        """Continually monitor and update the current daemon state."""
        while True:
            try:
                reply = await self._read_queue.get()
                # mot_move_completed, mot_get_statusupdate, mot_get_dcstatusupdate, mot_get_statusbits
                if reply.msgid in (0x0464, 0x0481, 0x042A, 0x0491):
                    if hasattr(reply, "position"):  # might be short, that's not an error...
                        self._state["position"] = self.steps_to_units(reply.position)
                        self._busy = reply.moving_forward or reply.moving_reverse or reply.homing
                # mot_move_homed
                elif reply.msgid == 0x0444:
                    self._home_event.set()
                # hw_get_info
                elif reply.msgid == 0x0006:
                    self._serial_number = str(reply.serial_number)
                    self._model = reply.model_number.decode().strip()
                # mot_get_stageaxisparams
                elif reply.msgid == 0x04F2:
                    self._steps_per_unit = reply.counts_per_unit
                    self._state["hw_limits"] = (
                        self.steps_to_units(reply.min_pos),
                        self.steps_to_units(reply.max_pos),
                    )
                else:
                    self.logger.info(f"Unhandled reply {reply}")
            except Exception as e:
                self.logger.error(e)

    def direct_serial_write(self, message: bytes):
        self._busy = True
        self._serial.write(message)
