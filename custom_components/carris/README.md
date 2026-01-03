# Carris Bus - Home Assistant Integration

Custom integration for Home Assistant to display real-time bus arrival times from **Carris** (Lisbon municipal bus operator).

## Features

- Real-time bus arrival times
- Filter by specific route or show all buses
- Configurable via UI (no YAML required)
- Automatic token refresh
- Portuguese and English translations

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
3. Enter the stop ID (e.g., `9804`)
4. Select a route or "All routes"

### Finding Stop IDs

You can find stop IDs:
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

## Credits

API reverse-engineered from the CARRISway Android app (v2.0.2).

## License

MIT
