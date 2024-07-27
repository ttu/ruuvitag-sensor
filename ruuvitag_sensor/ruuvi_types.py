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


SensorData = Union[SensorDataUrl, SensorData3, SensorData5]

DataFormat = Optional[int]
RawSensorData = Optional[str]
DataFormatAndRawSensorData = Tuple[DataFormat, RawSensorData]

Mac = str
MacAndSensorData = Tuple[Mac, SensorData]

RawData = str
MacAndRawData = Tuple[str, str]

ByteData = Tuple[int, ...]
