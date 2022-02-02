"""A library that provides a Python interface to Nightscout"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Type, TypeVar, cast

import dateutil.parser
import pytz


JsonDict = Dict[str, Any]
_T = TypeVar("_T", bound="BaseModel")


class BaseModel:
    """Base class for models"""

    def __init__(self, **kwargs: Any):
        self._json = None

        attrs = dir(self)
        for key, val in kwargs.items():
            if key in self.__annotations__ and (
                key not in attrs or getattr(self, key) is None
            ):
                setattr(self, key, val)

    @classmethod
    def json_transforms(cls, json_data: JsonDict) -> None:
        """Transform the given JSON into the right key/value pairs for the class"""

    @classmethod
    def new_from_json_dict(cls: Type[_T], data: JsonDict, **kwargs: Any) -> _T:
        """Calls the `json_transforms` method, and then the class' `__init__` with
        the args in the dictionary
        """
        json_data = data.copy()
        if kwargs:
            for key, val in kwargs.items():
                json_data[key] = val

        cls.json_transforms(json_data)

        i = cls(**json_data)
        i._json = data

        # verify that evereything non-optional was set
        missing_keys = set(i.__annotations__.keys()) - set(dir(i))
        if missing_keys:
            raise KeyError(
                f"While deserializing {i.__class__}, "
                f"keys {missing_keys} should have been present, but were not."
            )

        # missing_keys = set()
        # for key in i.__annotations__:
        #     val = getattr(i, key)
        #     if val is None:
        #         missing_keys.add(key)
        # if missing_keys:
        #     print(
        #         f"While deserializing {i.__class__}, "
        #         f"optional keys {missing_keys} were not set"
        #     )

        return i


class ServerStatus(BaseModel):
    """Server Info and Status

    Server side status, default settings and capabilities

    Attributes:
        status (string): Server status
        version (string): Server version
        name (string): Server name
        apiEnabled (bool): If the API is enabled
        settings (Dict[str, Any]): Server settings
    """

    status: str
    version: str
    name: str
    apiEnabled: bool
    settings: Dict[str, Any]


class SGV(BaseModel):
    """Sensor Glucose Value

    Represents a single glucose measurement and direction at a specific time.

    Attributes:
        sgv (int): Glucose measurement value in mg/dl.
        sgv_mmol (int): Glucose measurement value in mmol/L.
        delta (float): Delta between current and previous value.
        date (datetime): The time of the measurementpa
        direction (string): One of ['DoubleUp', 'SingleUp', 'FortyFiveUp', 'Flat',
            'FortyFiveDown', 'SingleDown', 'DoubleDown']
        device (string): the source of the measurement.  For example, 'share2',
            if pulled from Dexcom Share servers
    """

    sgv: float
    sgv_mmol: float
    delta: Optional[float] = None
    delta_mmol: Optional[float] = None
    date: datetime
    direction: str
    device: str

    @classmethod
    def json_transforms(cls, json_data: JsonDict) -> None:
        date_string = json_data.get("dateString")
        if date_string:
            json_data["date"] = dateutil.parser.parse(date_string)
        sgv = json_data.get("sgv")
        if sgv is not None:
            json_data["sgv_mmol"] = SGV.__mgdl_to_mmol_l(sgv)
        delta = json_data.get("delta")
        if delta is not None:
            json_data["delta_mmol"] = SGV.__mgdl_to_mmol_l(delta)

    @staticmethod
    def __mgdl_to_mmol_l(mgdl: Optional[float]) -> Optional[float]:
        return None if mgdl is None else round(mgdl / 18, 1)


class Treatment(BaseModel):
    """Nightscout Treatment

    Represents an entry in the Nightscout treatments store, such as boluses, carb
    entries, temp basals, etc. Many of the following attributes will be set to None,
    depending on the type of entry.

    Attributes:
        eventType (string): The event type.
            Examples: ['Temp Basal', 'Correction Bolus', 'Meal Bolus', 'BG Check']
        timestamp (datetime): The time of the treatment
        insulin (float): The amount of insulin delivered
        programmed (float): The amount of insulin programmed. May differ from insulin
            if the pump was suspended before delivery was finished.
        carbs (int): Amount of carbohydrates in grams consumed
        rate (float): Rate of insulin delivery for a temp basal, in U/hr.
        duration (int): Duration in minutes for a temp basal.
        enteredBy (string): The person who gave the treatment if entered in Care Portal,
            or the device that fetched the treatment from the pump.
        glucose (int): Glucose value for a BG check, in mg/dl.
    """

    temp: Optional[str] = None
    enteredBy: Optional[str] = None
    eventType: str
    glucose: Optional[int] = None
    glucoseType: Optional[str] = None
    units: Optional[str] = None
    device: Optional[str] = None
    created_at: datetime
    timestamp: Optional[datetime] = None
    absolute: Optional[str] = None
    rate: Optional[str] = None
    duration: Optional[str] = None
    carbs: Optional[int] = None
    insulin: Optional[float] = None
    unabsorbed: Optional[str] = None
    suspended: Optional[str] = None
    type: Optional[str] = None
    programmed: Optional[float] = None
    foodType: Optional[str] = None
    absorptionTime: Optional[str] = None

    def __repr__(self) -> str:
        return f"{self.timestamp} {self.eventType}"

    @classmethod
    def json_transforms(cls, json_data: JsonDict) -> None:
        timestamp = json_data.get("timestamp")
        if timestamp:
            if isinstance(timestamp, int):
                json_data["timestamp"] = datetime.fromtimestamp(
                    timestamp / 1000.0, pytz.utc
                )
            else:
                json_data["timestamp"] = dateutil.parser.parse(timestamp)
        if json_data.get("created_at"):
            json_data["created_at"] = dateutil.parser.parse(json_data["created_at"])


class ScheduleEntry(BaseModel):
    """ScheduleEntry

    Represents a change point in one of the schedules on a Nightscout profile.

    Attributes:
        offset (timedelta): The start offset of the entry
        value (float): The value of the entry.
    """

    offset: timedelta
    value: float

    @classmethod
    def json_transforms(cls, json_data: JsonDict) -> None:
        seconds_offset = json_data.get("timeAsSeconds")
        if seconds_offset is not None:
            seconds_offset = float(seconds_offset)
        else:
            hours, minutes = cast(str, json_data.get("time")).split(":")
            seconds_offset = int(hours) * 60 * 60 + int(minutes) * 60
        json_data["offset"] = timedelta(seconds=seconds_offset)
        json_data["value"] = float(json_data["value"])


class AbsoluteScheduleEntry:
    """AbsoluteScheduleEntry

    A ScheduleEntry at an absolute time"""

    start_date: datetime
    value: float

    def __init__(self, start_date: datetime, value: float):
        self.start_date = start_date
        self.value = value

    def __repr__(self) -> str:
        return f"{self.start_date} = {self.value}"


class Schedule(List[ScheduleEntry]):
    """Schedule

    Represents a schedule on a Nightscout profile.

    """

    timezone: pytz.BaseTzInfo

    def __init__(self, entries: List[ScheduleEntry], timezone: pytz.BaseTzInfo):
        entries.sort(key=lambda e: e.offset)
        super().__init__(entries)
        self.timezone = timezone

    # Expects a localized timestamp here
    def value_at_date(self, local_date: datetime) -> float:
        """Get scheduled value at given date

        Args:
            local_date: The datetime of interest.

        Returns:
            The value of the schedule at the given time.

        """
        offset = local_date - local_date.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        return [e.value for e in self if e.offset <= offset][-1]

    def between(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> List[AbsoluteScheduleEntry]:
        """Returns entries between given dates as AbsoluteScheduleEntry objects

        Times passed in should be timezone aware.  Times returned will have a tzinfo
        matching the schedule timezone.

        Args:
            start_date: The start datetime of the period to retrieve entries for.
            end_date: The end datetime of the period to retrieve entries for.

        Returns:
            An array of AbsoluteScheduleEntry objects.

        """
        if start_date > end_date:
            return []

        start_date = start_date.astimezone(self.timezone)
        end_date = end_date.astimezone(self.timezone)

        reference_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        start_offset = start_date - reference_date
        end_offset = start_offset + (end_date - start_date)
        if end_offset > timedelta(days=1):
            boundary_date = start_date + (timedelta(days=1) - start_offset)
            return self.between(start_date, boundary_date) + self.between(
                boundary_date, end_date
            )

        start_index = 0
        end_index = len(self)

        for index, item in enumerate(self):
            if start_offset >= item.offset:
                start_index = index
            if end_offset < item.offset:
                end_index = index
                break

        return [
            AbsoluteScheduleEntry(reference_date + entry.offset, entry.value)
            for entry in self[start_index:end_index]
        ]

    @classmethod
    def new_from_json_array(
        cls,
        data: List[JsonDict],
        timezone: pytz.BaseTzInfo,
    ) -> "Schedule":
        """Creates a `Schedule` instance from a json array"""
        entries = [ScheduleEntry.new_from_json_dict(d) for d in data]
        return cls(entries, timezone)


class Profile(BaseModel):
    """Profile

    Represents a Nightscout profile.

    Attributes:
        dia (float): The duration of insulin action, in hours.
        carb_ratio (Schedule): A schedule of carb ratios, which are in grams/U.
        sens (Schedule): A schedule of insulin sensitivity values, which are in mg/dl/U.
        timezone (timezone): The timezone of the schedule.
        basal (Schedule): A schedule of basal rates, which are in U/hr.
        target_low (Schedule): A schedule the low end of the target range, in mg/dl.
        target_high (Schedule): A schedule the high end of the target range, in mg/dl.
    """

    dia: Optional[float] = None
    carbratio: Optional[Schedule] = None
    carbs_hr: Optional[int] = None
    delay: Optional[int] = None
    sens: Optional[Schedule] = None
    timezone: pytz.BaseTzInfo
    basal: Schedule
    target_low: Optional[Schedule] = None
    target_high: Optional[Schedule] = None

    @classmethod
    def json_transforms(cls, json_data: JsonDict) -> None:
        timezone_str = json_data.get("timezone")
        assert isinstance(timezone_str, str)
        timezone = pytz.timezone(timezone_str)
        json_data["timezone"] = timezone

        for key in ["carbratio", "sens", "target_low", "target_high", "basal"]:
            val = json_data.get(key)
            if val is not None:
                json_data[key] = Schedule.new_from_json_array(val, timezone)
        val = json_data.get("dia")
        if val is not None:
            json_data["dia"] = float(val)


class ProfileDefinition(BaseModel):
    """ProfileDefinition

    Represents a Nightscout profile definition, which can have multiple named profiles.

    Attributes:
        startDate (datetime): The time these profiles start at.
    """

    defaultProfile: str
    store: Dict[str, Profile]
    startDate: datetime
    created_at: datetime
    units: str

    def get_default_profile(self) -> Profile:
        """Returns the default ProfileDefinition"""
        return self.store[self.defaultProfile]

    @classmethod
    def json_transforms(cls, json_data: JsonDict) -> None:
        if json_data.get("startDate"):
            json_data["startDate"] = dateutil.parser.parse(json_data["startDate"])
        if json_data.get("created_at"):
            json_data["created_at"] = dateutil.parser.parse(json_data["created_at"])
        if json_data.get("store"):
            store = {}
            for profile_name in json_data["store"]:
                store[profile_name] = Profile.new_from_json_dict(
                    json_data["store"][profile_name]
                )
            json_data["store"] = store


class ProfileDefinitionSet(List[ProfileDefinition]):
    """ProfileDefinitionSet

    Represents a set of Nightscout profile definitions, each covering a range of time
    from its start time, to the start time of the next profile definition, or until
    now if there are no newer profile defitions.

    """

    def __init__(self, profile_definitions: List[ProfileDefinition]):
        profile_definitions.sort(key=lambda d: d.startDate)
        super().__init__(profile_definitions)

    def get_profile_definition_active_at(self, date: datetime) -> ProfileDefinition:
        """Get the profile definition active at a given datetime

        Args:
            date: The profile definition containing this time will be returned.

        Returns:
            A ProfileDefinition object valid for the specified time.

        """
        return [d for d in self if d.startDate <= date][-1]

    @classmethod
    def new_from_json_array(cls, data: List[JsonDict]) -> "ProfileDefinitionSet":
        """Returns an array of ProfileDefinition from an array of json dicts"""
        defs = [ProfileDefinition.new_from_json_dict(d) for d in data]
        return cls(defs)


class XDripJs(BaseModel):
    """XDripJs

    Represents a xDrip-js source.

    Attributes:
        state (int): CGM Sensor Session State Code
        stateString (string): CGM Sensor Session State String
        stateStringShort (string): CGM Sensor Session State Short String
        txId (string): CGM Transmitter ID
        txStatus (float): CGM Transmitter Status
        txStatusString (string): CGM Transmitter Status String
        txStatusStringShort (string): CGM Transmitter Status Short String
        txActivation (int): CGM Transmitter Activation Milliseconds After Epoch
        mode (string): Mode xdrip-js Application Operationg: expired, not expired, etc.
        timestamp (int): Last Update Milliseconds After Epoch
        rssi (int): Receive Signal Strength of Transmitter
        unfiltered (int): Most Recent Raw Unfiltered Glucose
        filtered (int): Most Recent Raw Filtered Glucose
        noise (int): Calculated Noise Value - 1=Clean, 2=Light, 3=Medium, 4=Heavy
        noiseString (float): Noise Value String
        slope (float): Calibration Slope Value
        intercept (int): Calibration Intercept Value
        calType (string): Algorithm Used to Calculate Calibration Values
        lastCalibrationDate (int): Most Recent Calibration Milliseconds After Epoch
        sessionStart (int): Sensor Session Start Milliseconds After Epoch
        batteryTimestamp (int): Most Recent Batter Status Read Milliseconds After Epoch
        voltagea (float): Voltage of Battery A
        voltageb (float): Voltage of Battery B
        temperature (float): Transmitter Temperature
        resistance (float): Sensor Resistance
    """

    state: Optional[int] = None
    stateString: Optional[str] = None
    stateStringShort: Optional[str] = None
    txId: Optional[str] = None
    txStatus: Optional[float] = None
    txStatusString: Optional[str] = None
    txStatusStringShort: Optional[str] = None
    txActivation: Optional[int] = None
    mode: Optional[str] = None
    timestamp: Optional[int] = None
    rssi: Optional[int] = None
    unfiltered: Optional[int] = None
    filtered: Optional[int] = None
    noise: Optional[int] = None
    noiseString: Optional[float] = None
    slope: Optional[float] = None
    intercept: Optional[int] = None
    calType: Optional[str] = None
    lastCalibrationDate: Optional[int] = None
    sessionStart: Optional[int] = None
    batteryTimestamp: Optional[int] = None
    voltagea: Optional[float] = None
    voltageb: Optional[float] = None
    temperature: Optional[float] = None
    resistance: Optional[float] = None


class UploaderBattery(BaseModel):
    """UploaderBattery

    Represents a Uploader device's battery on Nightscout.

    Attributes:
        batteryVoltage (float): Battery Voltage.
        battery (int): Battery percentage.
        type (string): Uploader type.
    """

    batteryVoltage: Optional[float] = None
    battery: Optional[int] = None
    type: Optional[str] = None


class PumpBattery(BaseModel):
    """PumpBattery

    Represents the Pump's battery on Nightscout.

    Attributes:
        status (string): Pump Battery Status String. For example "normal".
        voltage (float): Pump Battery Voltage Level.
    """

    status: Optional[str] = None
    voltage: Optional[float] = None


class PumpStatus(BaseModel):
    """PumpStatus

    Represents a Pump device status on Nightscout.

    Attributes:
        status (string): Pump Status String.
        bolusing (bool): Is Pump Bolusing.
        suspended (bool): Is Pump Suspended.
        timestamp (datetime): Date time of entry.
    """

    status: Optional[str] = None
    bolusing: Optional[bool] = None
    suspended: Optional[bool] = None
    timestamp: Optional[datetime] = None

    @classmethod
    def json_transforms(cls, json_data: JsonDict) -> None:
        timestamp = json_data.get("timestamp")
        if timestamp:
            if isinstance(timestamp, int):
                json_data["timestamp"] = datetime.fromtimestamp(
                    timestamp / 1000.0, pytz.utc
                )
            else:
                json_data["timestamp"] = dateutil.parser.parse(timestamp)


class PumpDevice(BaseModel):
    """PumpDevice

    Represents a Pump device on Nightscout.

    Attributes:
        clock (datetime): Clock datetime.
        battery (PumpBattery): Pump battery details.
        reservoir (float): Amount of insulin remaining in pump reservoir.
        status (PumpStatus): Pump status details.
    """

    clock: Optional[datetime] = None
    battery: Optional[PumpBattery] = None
    reservoir: Optional[float] = None
    status: Optional[PumpStatus] = None

    @classmethod
    def json_transforms(cls, json_data: JsonDict) -> None:
        if json_data.get("clock"):
            json_data["clock"] = dateutil.parser.parse(json_data["clock"])
        if json_data.get("battery"):
            json_data["battery"] = PumpBattery.new_from_json_dict(json_data["battery"])
        if json_data.get("status"):
            json_data["status"] = PumpStatus.new_from_json_dict(json_data["status"])


class DeviceStatus(BaseModel):
    """DeviceStatus

    Represents a Device on Nightscout. For example a MiaoMiao reader.

    Attributes:
        device (string): Device type and hostname for example openaps://hostname.
        created_at (datetime): Created date.
        openaps (string): OpenAPS devicestatus record.
        loop (string): Loop devicestatus record.
        pump (PumpDevice): Pump device.
        uploader (UploaderBattery): Uploader device's battery.
        xdripjs (XDripJs): xDripJS device.
    """

    device: str
    created_at: datetime
    openaps: Optional[str] = None
    loop: Optional[str] = None
    pump: Optional[PumpDevice] = None
    uploader: Optional[UploaderBattery] = None
    xdripjs: Optional[XDripJs] = None

    @classmethod
    def json_transforms(cls, json_data: JsonDict) -> None:
        if json_data.get("created_at"):
            json_data["created_at"] = dateutil.parser.parse(json_data["created_at"])
        if json_data.get("pump"):
            json_data["pump"] = PumpDevice.new_from_json_dict(json_data["pump"])
        if json_data.get("uploader"):
            json_data["uploader"] = UploaderBattery.new_from_json_dict(
                json_data["uploader"]
            )
        if json_data.get("xdripjs"):
            json_data["xdripjs"] = XDripJs.new_from_json_dict(json_data["xdripjs"])
