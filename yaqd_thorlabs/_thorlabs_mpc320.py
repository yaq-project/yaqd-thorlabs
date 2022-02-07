import asyncio


import thorlabs_apt_protocol as apt  # type: ignore
from ._thorlabs_apt_motor import ThorlabsAptMotor


class ThorlabsMPC320(ThorlabsAptMotor):
    _kind = "thorlabs-mpc320"

    def __init__(self, name, config, config_filepath):
        super().__init__(name, config, config_filepath)
        self._serial.write(
            apt.mod_set_chanenablestate(source=self._source,
                                        dest=self._dest,
                                        chan_ident=0b0111,  # enables all three motors
                                        enable_state=0x01)
        )
        self._state["hw_limits"] = [0, 170]  # no way to read from hardware, as far as I can tell

    async def request_status(self):
        while True:
            self._serial.write(
                apt.mot_req_dcstatusupdate(self._dest, self._source, self._chan_ident)
            )
            await asyncio.sleep(0.2)
