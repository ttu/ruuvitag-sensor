from typing import Optional, Tuple, TypedDict, Union


class SensorDataBase(TypedDict):
    data_format: int


class SensorDataUrl(SensorDataBase):
    humidity: float
    temperature: float
    pressure: float
    identifier: Optional[str]


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
    rssi: Optional[int]


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


class SensorHistoryData(TypedDict):
    humidity: Optional[float]
    temperature: Optional[float]
    pressure: Optional[float]
    timestamp: int


SensorData = Union[SensorDataUrl, SensorData3, SensorData5, SensorData6]

DataFormat = Optional[int]
RawSensorData = Optional[str]
DataFormatAndRawSensorData = Tuple[DataFormat, RawSensorData]

Mac = str
MacAndSensorData = Tuple[Mac, SensorData]

RawData = str
MacAndRawData = Tuple[str, str]

ByteData = Tuple[int, ...]
