"""Vehicle data sources.

The UI only depends on the `DataSource` interface and the `VehicleData`
snapshot, so swapping dummy data for a real Bluetooth ELM327 adapter later is a
drop-in change -- write an `OBDDataSource` (see the stub at the bottom) and hand
it to the dashboard instead of `DummyDataSource`.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import List


@dataclass
class DTC:
    """A Diagnostic Trouble Code."""
    code: str          # e.g. "P0301"
    desc: str          # human-readable description
    severity: str      # "critical" | "warning" | "info" | "pending"


@dataclass
class VehicleData:
    """A single snapshot of everything the dashboard renders."""
    rpm: float = 0.0
    speed: float = 0.0          # mph
    coolant: float = 0.0        # deg C
    voltage: float = 0.0        # volts
    throttle: float = 0.0       # percent
    connected: bool = False
    vehicle: str = "--"
    vin: str = "--"
    dtcs: List[DTC] = field(default_factory=list)


class DataSource:
    """Interface. Call update(dt) each frame, then read .data."""

    def __init__(self):
        self.data = VehicleData()

    def update(self, dt: float) -> None:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Dummy source: smooth, plausible, animated telemetry + a rotating fault list
# ---------------------------------------------------------------------------

# A pool of realistic OBD-II trouble codes to cycle through.
_DTC_POOL = [
    DTC("P0301", "Cylinder 1 Misfire Detected",       "critical"),
    DTC("P0420", "Catalyst Efficiency Below Threshold", "warning"),
    DTC("P0171", "System Too Lean (Bank 1)",           "warning"),
    DTC("P0128", "Coolant Thermostat Below Regulating", "info"),
    DTC("P0442", "EVAP System Small Leak Detected",     "info"),
    DTC("P0300", "Random / Multiple Cylinder Misfire",  "critical"),
    DTC("P0113", "Intake Air Temp Sensor High Input",   "pending"),
    DTC("C1234", "Wheel Speed Sensor Circuit",          "warning"),
]


class DummyDataSource(DataSource):
    """Generates believable, continuously varying data for design / demo."""

    def __init__(self):
        super().__init__()
        self._t = 0.0
        self._dtc_timer = 0.0
        self._dtc_index = 3          # how many codes currently "present"
        self.data.connected = True
        self.data.vehicle = "2016 Honda Civic 1.5T"
        self.data.vin = "2HGFC2F5XGH500123"
        self._refresh_dtcs()

    def _refresh_dtcs(self):
        self.data.dtcs = _DTC_POOL[: self._dtc_index]

    def update(self, dt: float) -> None:
        self._t += dt
        t = self._t

        # Smooth, layered sine motion so gauges feel alive but not jittery.
        base_rpm = 1500 + 1300 * (0.5 + 0.5 * math.sin(t * 0.6))
        self.data.rpm = base_rpm + 250 * math.sin(t * 2.3) + random.uniform(-40, 40)

        self.data.speed = max(0.0, 42 + 30 * math.sin(t * 0.35) + 4 * math.sin(t * 1.7))
        self.data.throttle = max(0.0, min(100.0, 25 + 22 * math.sin(t * 0.9) + 6 * math.sin(t * 3.1)))
        self.data.coolant = 88 + 6 * math.sin(t * 0.12)         # ~ steady around 90C
        self.data.voltage = 14.1 + 0.25 * math.sin(t * 0.8) + random.uniform(-0.03, 0.03)

        # Every ~8s, change how many trouble codes are "present" to show motion.
        self._dtc_timer += dt
        if self._dtc_timer >= 8.0:
            self._dtc_timer = 0.0
            self._dtc_index = 2 + int((math.sin(t * 0.5) + 1) * 2)  # 2..4
            self._refresh_dtcs()


# ---------------------------------------------------------------------------
# Real adapter stub -- fill this in when the ELM327 is paired over Bluetooth.
# ---------------------------------------------------------------------------
#
#   pip install obd
#   # pair the adapter, then find its serial device, e.g. /dev/rfcomm0:
#   #   sudo rfcomm bind rfcomm0 <ADAPTER_MAC> 1
#
# class OBDDataSource(DataSource):
#     def __init__(self, port="/dev/rfcomm0"):
#         super().__init__()
#         import obd
#         self._obd = obd
#         self.conn = obd.OBD(port)            # or obd.Async(port) for callbacks
#         self.data.connected = self.conn.is_connected()
#
#     def update(self, dt):
#         c = self.conn
#         self.data.connected = c.is_connected()
#         self.data.rpm      = _val(c.query(self._obd.commands.RPM))
#         self.data.speed    = _val(c.query(self._obd.commands.SPEED)) * 0.621371  # km/h->mph
#         self.data.coolant  = _val(c.query(self._obd.commands.COOLANT_TEMP))
#         self.data.voltage  = _val(c.query(self._obd.commands.CONTROL_MODULE_VOLTAGE))
#         self.data.throttle = _val(c.query(self._obd.commands.THROTTLE_POS))
#         # DTCs come back as (code, description) tuples:
#         resp = c.query(self._obd.commands.GET_DTC)
#         self.data.dtcs = [DTC(code, desc, "warning") for code, desc in (resp.value or [])]
#
# def _val(response):
#     return float(response.value.magnitude) if response and response.value is not None else 0.0
