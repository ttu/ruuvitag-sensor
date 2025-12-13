from typing import Literal, TypedDict

DeviceType = Literal["ruuvitag", "ruuvi_air"]


class SensorDataBase(TypedDict):
    data_format: int | str


class SensorDataUrl(SensorDataBase):
    humidity: float
    temperature: float
    pressure: float
    identifier: str | None


class SensorData3(SensorDataBase):
    humidity: float
    temperature: float
    pressure: float
    acceleration: float
    acceleration_x: int
    acceleration_y: int
    acceleration_z: int
    battery: int


class SensorData5(SensorDataBase):
    humidity: float
    temperature: float
    pressure: float
    acceleration: float
    acceleration_x: int
    acceleration_y: int
    acceleration_z: int
    tx_power: int
    battery: int
    movement_counter: int
    measurement_sequence_number: int
    mac: str
    rssi: int | None


class SensorData6(SensorDataBase):
    humidity: float
    temperature: float
    pressure: float
    pm_2_5: float
    co2: int
    voc: int
    nox: int
    luminosity: float
    measurement_sequence_number: int
    calibration_in_progress: bool
    mac: str


class SensorDataE1(SensorData6):
    pm_1: float
    pm_4: float
    pm_10: float


class SensorHistoryData(TypedDict):
    humidity: float | None
    temperature: float | None
    pressure: float | None
    timestamp: int


class SensorAirHistoryData(TypedDict):
    humidity: float | None
    temperature: float | None
    pressure: float | None
    pm_1: float | None
    pm_2_5: float | None
    pm_4: float | None
    pm_10: float | None
    co2: int | None
    voc: int | None
    nox: int | None
    measurement_sequence_number: int | None
    timestamp: int


SensorData = SensorDataUrl | SensorData3 | SensorData5 | SensorData6 | SensorDataE1

DataFormat = int | str | None
RawSensorData = str | None
DataFormatAndRawSensorData = tuple[DataFormat, RawSensorData]

Mac = str
MacAndSensorData = tuple[Mac, SensorData]

RawData = str
MacAndRawData = tuple[str, str]

ByteData = tuple[int, ...]
