# Carris Bus - Home Assistant Integration

Custom integration for Home Assistant to display real-time bus arrival times from **Carris** (Lisbon municipal bus operator).

## Features

- Real-time bus arrival times
- Real-time bus location tracking (device tracker)
- Binary sensor for "bus arriving soon" notifications
- Filter by specific route or show all buses
- Search stops by name or enter ID manually
- Configurable update intervals and thresholds
- Automatic token refresh with proactive renewal
- Robust error handling with retry logic
- Portuguese and English translations
- HACS compatible

## Installation

### HACS (Recommended)

1. Add this repository to HACS as a custom repository
2. Search for "Carris" and install
3. Restart Home Assistant

### Manual

1. Copy the `carris` folder to your `custom_components` directory:
   ```bash
   cp -r carris /config/custom_components/
   ```
2. Restart Home Assistant

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **"Carris"**
3. Choose how to find your stop:
   - **Search by name**: Enter part of the stop name and select from results
   - **Manual entry**: Enter the stop ID directly (e.g., `9804`)
4. Select a route or "All routes"

### Options

After setup, you can configure options in the integration settings:
- **Update interval**: How often to fetch new data (30-300 seconds)
- **Arriving soon threshold**: Minutes for "arriving soon" binary sensor (1-30 minutes)

### Finding Stop IDs

If you prefer manual entry, you can find stop IDs:
- In the CARRISway app
- At [carris.pt](https://www.carris.pt)
- Using the API (see [API Documentation](../../CARRIS_API.md))

**Example stops for Dom Fuas Roupinho:**
| Stop ID | Direction | Destination |
|---------|-----------|-------------|
| 9803 | Eastbound | B. Madre Deus |
| 9804 | Westbound | Pólo Univ. Ajuda |

## Sensors

The integration creates sensors with:

| Attribute | Description |
|-----------|-------------|
| `state` | Minutes until next bus |
| `route_number` | Bus route number |
| `destination` | Bus destination |
| `arrival_time` | ISO timestamp of arrival |
| `upcoming_buses` | List of next 5 buses |

## Example Automation

```yaml
automation:
  - alias: "Notify when 742 bus is 5 minutes away"
    trigger:
      - platform: numeric_state
        entity_id: sensor.carris_742_r_d_fuas_roupinho
        below: 6
    action:
      - service: notify.mobile_app
        data:
          message: "742 bus arriving in {{ states('sensor.carris_742_r_d_fuas_roupinho') }} minutes!"
```

## Example Lovelace Card

```yaml
type: entities
title: Next Bus
entities:
  - entity: sensor.carris_742_r_d_fuas_roupinho
    name: "742 to Ajuda"
    icon: mdi:bus
```

## API Documentation

See [CARRIS_API.md](../../CARRIS_API.md) for full API documentation, including:
- Authentication flow
- All available endpoints
- How to refresh API keys

## Troubleshooting

### "Stop not found"
- Verify the stop ID exists using the API or CARRISway app
- Stop IDs are numeric (e.g., `9804`)

### No data showing
- Check Home Assistant logs for errors
- The API token refreshes automatically every 12 hours
- Real-time data may not be available for all routes (especially on weekends)

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/mrfyda/ha-carris.git
cd ha-carris

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=custom_components/carris --cov-report=term-missing
```

### Linting

```bash
# Run ruff linter
ruff check custom_components/carris/

# Run ruff formatter
ruff format custom_components/carris/

# Run type checker
mypy custom_components/carris/ --ignore-missing-imports
```

### CI/CD

This project uses GitHub Actions for continuous integration:

- **Lint**: Runs ruff linter and formatter checks
- **Type Check**: Runs mypy type checking
- **Test**: Runs pytest on Python 3.11 and 3.12
- **Validate**: Validates manifest.json, strings.json, and translations
- **HACS**: Validates HACS requirements

## Credits

API reverse-engineered from the CARRISway Android app (v2.0.2).

## License

MIT
