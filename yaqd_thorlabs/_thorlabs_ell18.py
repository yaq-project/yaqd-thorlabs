from ._thorlabs_ellx import ThorlabsEllx


class ThorlabsEll18(ThorlabsEllx):
    """deprecated: use thorlabs-elliptec-rotation"""

    _kind = "thorlabs-ell18"
    _native_units = "deg"
