# AI Agents Configuration

Guidelines for AI assistants working on **ruuvitag-sensor** — a Python library for communicating with RuuviTag BLE sensors and Ruuvi Air devices, decoding measurement data from BLE broadcasts and GATT history.

**Rule:** Do not create new documentation files. Update existing docs (`README.md`, `developer_notes.md`, this file). If a new file seems necessary, ask first.

---

## Project Overview

- **Package:** `ruuvitag_sensor` (v4.0.0, Production/Stable)
- **Language:** Python 3.10+ (supports 3.10–3.14)
- **Build:** setuptools + wheel (`pyproject.toml`)
- **Dependencies:** `bleak` (BLE), `reactivex` (RxPY), `ptyprocess` (Linux only)
- **Dev deps:** `pytest`, `pytest-asyncio`, `ruff`, `mypy`
- **License:** MIT
- **Docs:** `README.md` (usage), `developer_notes.md` (dev guide, BLE internals, release)

---

## Architecture

```
ruuvitag_sensor/
├── ruuvi.py              # Main API: RuuviTagSensor (static methods)
├── ruuvitag.py           # RuuviTag/RuuviTagAsync (single-sensor class)
├── ruuvi_rx.py           # ReactiveX wrapper (RuuviTagReactive)
├── ruuvi_types.py        # TypedDict definitions for sensor data
├── data_formats.py       # BLE advertisement parsing & format detection
├── decoder.py            # get_decoder() router, parse_mac(), re-exports
├── log.py                # Logging: enable_console(), file logging
├── __main__.py           # CLI entry point
├── decoders/             # One module per data format
│   ├── __init__.py       # Exports all decoder classes
│   ├── url_decoder.py    # DF2/DF4 (deprecated, Eddystone URL)
│   ├── df3_decoder.py    # DF3 (deprecated, simple raw)
│   ├── df5_decoder.py    # DF5 (RuuviTag primary format)
│   ├── df6_decoder.py    # DF6 (Ruuvi Air broadcast)
│   ├── dfe1_decoder.py   # DFE1 (Ruuvi Air extended, preferred over DF6)
│   ├── history_decoder.py      # RuuviTag history (single-record per entry)
│   └── air_history_decoder.py  # Ruuvi Air history (multi-record batches)
└── adapters/             # BLE communication backends
    ├── __init__.py       # Abstract base classes, get_ble_adapter()
    ├── bleak_ble.py      # Bleak (default, async, cross-platform)
    ├── nix_hci.py        # BlueZ hcitool/hcidump (Linux, sync, legacy)
    ├── bleson.py         # Bleson (experimental, not recommended)
    ├── nix_hci_file.py   # File-based BlueZ emulation (testing)
    ├── dummy.py          # Hardcoded test data (CI/offline)
    ├── utils.py          # Adapter utilities
    └── development/      # Dev tools (dev_bleak_scanner.py)

tests/
├── test_data_formats.py              # Format detection tests
├── test_ruuvitag_sensor.py           # Sync API tests (mocked adapter)
├── test_ruuvitag_sensor_async.py     # Async API tests
├── test_bleak_history_notification.py
├── hcidump-2.x.txt, hcidump-3.x.txt # Test fixture files
├── decoders/                         # Per-decoder test modules
│   ├── test_url_decoder.py, test_df3_decoder.py, test_df5_decoder.py
│   ├── test_df6_decoder.py, test_dfe1_decoder.py
│   ├── test_history_decoder.py, test_air_history_decoder.py
│   └── test_get_decoder.py           # get_decoder() routing tests
└── integration/                      # Real BLE integration tests
    ├── test_integration_bleak_get_data.py
    ├── test_integration_bleak_history.py
    └── test_integration_bleak_air_history.py

examples/                  # Usage examples (async, sync, MQTT, InfluxDB, HTTP servers)
```

---

## Data Flow

1. **BLE adapter** receives raw advertisement bytes
2. **`DataFormats.convert_data(raw_hex)`** in `data_formats.py`:
   - Dechunks BLE AD structure (length + type + data chunks)
   - Identifies Ruuvi manufacturer ID `9904` + format byte
   - Returns `(data_format, payload)` tuple
3. **`get_decoder(data_format)`** in `decoder.py`:
   - Uses `match` statement to return the correct decoder instance
   - Format IDs: `int` for most (2,3,4,5,6), `str` for E1 (`"E1"`)
4. **Decoder's `decode_data(payload)`** returns `SensorData` dict
5. **`parse_mac(data_format, payload_mac)`** extracts MAC (only DF5 has MAC in payload)

---

## Data Formats

| Format | Decoder | Device | Status | Key Fields |
|--------|---------|--------|--------|------------|
| 2, 4 | `UrlDecoder` | RuuviTag | Deprecated | temp, humidity, pressure, identifier |
| 3 | `Df3Decoder` | RuuviTag | Deprecated | + acceleration (x/y/z), battery |
| **5** | `Df5Decoder` | **RuuviTag** | **Primary** | + tx_power, movement_counter, sequence, mac, rssi |
| **6** | `Df6Decoder` | **Ruuvi Air** | Active | + pm2_5, co2, voc, nox, luminosity |
| **E1** | `DfE1Decoder` | **Ruuvi Air** | Active | + pm1, pm4, pm10 (extends DF6, preferred) |
| History | `HistoryDecoder` | RuuviTag | Active | Single measurement per entry + timestamp |
| Air History | `AirHistoryDecoder` | Ruuvi Air | Active | Multi-record batches + timestamps |

**Important:** RuuviTag and Ruuvi Air use **different history protocols** — different NUS services, different data structures, different decoders.

---

## BLE Adapters

| Adapter | Class | Async | Platform | Selection |
|---------|-------|-------|----------|-----------|
| **Bleak** | `BleCommunicationBleak` | Yes | All | Default |
| BlueZ | `BleCommunicationNix` | No | Linux | `RUUVI_BLE_ADAPTER=bluez` |
| Bleson | `BleCommunicationBleson` | No | Linux/macOS | `RUUVI_BLE_ADAPTER=bleson` (experimental) |
| File | `BleCommunicationNixFile` | No | All | `RUUVI_NIX_FROMFILE=path` |
| Dummy | `BleCommunicationDummy` | No | All | `CI=true` env var |

Adapter selection logic is in `adapters/__init__.py:get_ble_adapter()`. Bleak supports history data via GATT connections.

---

## Main API (ruuvi.py)

`RuuviTagSensor` uses **static methods only**:

| Method | Type | Purpose |
|--------|------|---------|
| `get_data_async(macs, bt_device)` | Async generator | Stream live broadcasts |
| `get_data(callback, macs, run_flag, bt_device)` | Sync callback | Stream data (BlueZ only) |
| `get_data_for_sensors(macs, duration, bt_device)` | Sync | Collect data for duration |
| `get_data_for_sensors_async(macs, duration, bt_device)` | Async | Async version |
| `find_ruuvitags(bt_device)` / `_async` | Sync/Async | Discover sensors |
| `get_history_async(mac, start_time, max_items, device_type)` | Async generator | Stream history entries |
| `download_history(mac, start_time, timeout, max_items, device_type)` | Async | Download all history |

---

## Code Standards

- **Style:** PEP 8, type hints on function signatures, single-purpose functions, descriptive names
- **Line length:** 120 characters
- **Formatting:** `ruff format` (double quotes, spaces)
- **Linting:** `ruff check` with extensive rule set (A, ARG, ASYNC, B, C4, C90, DTZ, E, F, G, I, PERF, PIE, PL, PTH, Q, RUF, SIM, UP, W)
- **Type checking:** `mypy` (Python 3.10 target, ignores missing imports)
- **Ignored rules:** `PLR2004` (magic values in comparisons), `RUF006` (asyncio.create_task refs)

**Run before committing:**
```bash
ruff check && ruff format --check && mypy ./ruuvitag_sensor/
```

---

## Testing

```bash
pytest                                  # All tests
pytest tests/decoders/                  # Decoder tests only
pytest tests/decoders/test_df5_decoder.py -k 'test_name'  # Single test
pytest --show-capture all               # Show print output
pytest --cov=ruuvitag_sensor            # With coverage
pytest -k "not integration"            # Skip integration tests (need real BLE)
```

**Patterns:**
- Framework: pytest (migrated from unittest)
- Async: `@pytest.mark.asyncio` with `asyncio_mode = "auto"` (no decorator needed)
- Mocking: `@patch("ruuvitag_sensor.ruuvi.ble", BleCommunicationDummy())` for adapter
- Test data: Hex strings matching real BLE payloads
- Each decoder has its own test file in `tests/decoders/`
- Integration tests in `tests/integration/` require real BLE hardware

---

## Common Tasks

### Adding a new data format
1. Create decoder class in `decoders/new_decoder.py` (follow existing patterns, implement `decode_data()`)
2. Export in `decoders/__init__.py`
3. Add format detection in `data_formats.py` (match manufacturer data bytes)
4. Register in `get_decoder()` match statement in `decoder.py`
5. Add tests in `tests/decoders/test_new_decoder.py`
6. Update `README.md` and this file

### Adding async support
- Add `_async` variant of method
- Only Bleak supports async
- Use `asyncio` patterns, test with `@pytest.mark.asyncio`

### Debugging BLE issues
- Identify which adapter is in use (check env vars)
- Enable logging: `import ruuvitag_sensor.log; ruuvitag_sensor.log.enable_console()`
- Use dummy adapter for isolated testing
- Check platform-specific notes below

---

## Platform Notes

| Platform | Adapter | Notes |
|----------|---------|-------|
| **Linux** | Bleak (default), BlueZ | BlueZ needs sudo; multiple adapters via hci0/hci1 |
| **macOS** | Bleak only | Uses UUIDs instead of MAC addresses for BLE devices |
| **Windows** | Bleak only | Passive scanning; less tested |

---

## CI/CD

GitHub Actions (`.github/workflows/build.yml`):
- **Trigger:** Push, PR, weekly (Monday)
- **Matrix:** Python 3.10, 3.11, 3.12, 3.13, 3.14 on Ubuntu
- **Steps:** Install deps → `ruff check` → `mypy` → `ruff format --check` → `pytest -v`

---

## Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Run lint/format/type checks and tests
4. Build: `python -m build`
5. Test on testpypi first
6. Tag: `git tag x.x.x && git push origin --tags`
7. Upload: `twine upload dist/*`
8. Copy `README.md` to `docs/` for doc site

---

## Key Design Decisions

- **Static methods on `RuuviTagSensor`:** No instance state needed; the class is a namespace for API methods
- **`decoder.py` re-exports:** `from ruuvitag_sensor.decoder import Df5Decoder` still works for backward compatibility after decoders were extracted to `decoders/` package
- **Format ID types:** Most formats use `int` (2,3,4,5,6), but E1 uses `str` (`"E1"`) — both accepted by `get_decoder()`
- **Adapter auto-selection:** Environment variables override defaults; CI automatically uses dummy adapter
- **History protocols differ:** RuuviTag sends one measurement per notification; Ruuvi Air sends multi-record batches with different NUS service UUIDs

---

## Resources

- **Project:** [GitHub](https://github.com/ttu/ruuvitag-sensor) · [PyPI](https://pypi.org/project/ruuvitag-sensor/) · [Docs](https://ttu.github.io/ruuvitag-sensor/)
- **Ruuvi:** [ruuvi.com](https://ruuvi.com/) · [Data format docs](https://docs.ruuvi.com/)
- **BLE:** [Bleak](https://github.com/hbldh/bleak) · [Bleson](https://github.com/TheCellule/python-bleson)

**Personal:** Use `AGENTS.local.md` (in `.gitignore`) for local preferences.
