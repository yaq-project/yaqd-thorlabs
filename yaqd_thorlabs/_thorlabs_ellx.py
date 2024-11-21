import asyncio
from typing import Dict
import struct

from yaqd_core import (
    UsesUart,
    UsesSerial,
    HasTransformedPosition,
    IsHomeable,
    HasLimits,
    HasPosition,
    IsDaemon,
)
from yaqd_core import aserial

from ._serial import SerialDispatcherEll


class ThorlabsEllx(
    UsesUart, UsesSerial, HasTransformedPosition, IsHomeable, HasLimits, HasPosition, IsDaemon
):
    _kind = "thorlabs-ellx"
    error_dict = {
        0: "",
        1: "Communication Timeout [1]",
        2: "Mechanical Timeout [2]",
        3: "Command error or not supported [3]",
        4: "Value out of range [4]",
        5: "Module isolated [5]",
        6: "Module out of isolation [6]",
        7: "Initializing Error [7]",
        8: "Thermal Error [8]",
        9: "Busy [9]",
        10: "Sensor Error [10]",
        11: "Motor Error [11]",
        12: "Out of Range [12]",
        13: "Overcurrent Error [13]",
    }

    serial_dispatchers: Dict[str, SerialDispatcherEll] = {}

    def __init__(self, name, config, config_filepath):
        self._homing = True
        self._move_started = False
        self._ignore_ready = 0
        self._address = config["address"]
        if config["serial_port"] in ThorlabsEllx.serial_dispatchers:
            self._serial = ThorlabsEllx.serial_dispatchers[config["serial_port"]]
        else:
            self._serial = SerialDispatcherEll(
                aserial.ASerial(config["serial_port"], config["baud_rate"])
            )
            ThorlabsEllx.serial_dispatchers[config["serial_port"]] = self._serial
        self._read_queue = asyncio.Queue()
        self._serial.workers[self._address] = self._read_queue
        super().__init__(name, config, config_filepath)
        self._units = config["units"]
        self._native_units = self._units
        self._conversion = config["scalar"]
        self._serial.write(f"{self._address:X}gs\r\n".encode())
        self._state["status"] = ""
        self._tasks.append(self._loop.create_task(self._home()))
        self._tasks.append(self._loop.create_task(self._consume_from_serial()))

    def _set_position(self, position):
        self._move_started = True
        if not self._homing:
            pos = round(position * (self._conversion))
            pos1 = struct.pack(">l", pos).hex().upper()
            self._serial.write(f"{self._address:X}ma{pos1}\r\n".encode())

    async def update_state(self):
        while True:
            if not self._homing and not self._move_started:
                self._serial.write(f"{self._address:X}gs\r\n".encode())
                self._serial.write(f"{self._address:X}gp\r\n".encode())
            await asyncio.sleep(0.2)

    async def _consume_from_serial(self):
        while True:
            comm, val = await self._read_queue.get()
            self.logger.debug(f"incoming serial: {comm} {val}")

            if "PO" == comm:
                position = struct.unpack(">l", bytes.fromhex(val))[0]
                position /= self._conversion
                self._state["position"] = position
            elif "GS" == comm:
                self._busy = (int(val, 16) != 0) or self._homing or self._move_started
                self._state["status"] = self.error_dict.get(int(val, 16), "")
                if int(val, 16) not in (0, 9):
                    # ignore normal busy/ready mode, log any other error
                    self.logger.error(f"ERROR CODE: {self._state['status']}")
            else:
                self.logger.warning(f"Unhandled serial response: {comm}{val}")

            self._read_queue.task_done()
            if self._read_queue.empty():
                self._move_started = False

    def home(self):
        self._busy = True
        self._loop.create_task(self._home())

    async def _home(self):
        self._homing = True
        await self._serial.write_queue.join()
        await asyncio.sleep(0.2)
        await self._read_queue.join()
        self._serial.write(f"{self._address:X}ho0\r\n".encode())
        self._homing = False
        await asyncio.sleep(0.2)
        await self._read_queue.join()
        self._busy = True
        await self._not_busy_sig.wait()
        self.set_position(self.get_destination())

    def direct_serial_write(self, command: bytes):
        self._busy = True
        self._serial.write(f"{self._address:X}{command.decode()}\r\n".encode())

    def close(self):
        self._serial.flush()
        self._serial.close()


if __name__ == "__main__":
    ThorlabsEllx.main()
