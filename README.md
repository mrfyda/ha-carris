# Carris Bus Integration

Home Assistant custom integration for **Carris** - Lisbon's municipal bus operator.

## Contents

| Path | Description |
|------|-------------|
| [custom_components/carris/](custom_components/carris/) | Home Assistant integration |
| [CARRIS_API.md](CARRIS_API.md) | Full API documentation |

## Quick Start

### 1. Install the integration

```bash
cp -r custom_components/carris /path/to/homeassistant/config/custom_components/
```

### 2. Restart Home Assistant

### 3. Add via UI

- **Settings → Devices & Services → Add Integration → Carris**
- Enter stop ID (e.g., `9804` for Dom Fuas Roupinho westbound)
- Select route (e.g., `742`)

## Example Stop IDs

| Stop ID | Name | Routes |
|---------|------|--------|
| 9803 | R. D. Fuas Roupinho (East) | 203, 718, 742, 37B |
| 9804 | R. D. Fuas Roupinho (West) | 203, 718, 742 |

## API Usage (without Home Assistant)

```bash
# Get token
TOKEN=$(curl -s -X POST \
  -H "X-Gravitee-Api-Key: 8844d854-9c37-4f22-b4d4-50a3626da5da" \
  "https://gateway.carris.pt/gateway/sitecarris/token" | jq -r '.access_token')

# Get next buses
curl -s \
  -H "X-Gravitee-Api-Key: 8844d854-9c37-4f22-b4d4-50a3626da5da" \
  -H "Authorization: Bearer $TOKEN" \
  "https://gateway.carris.pt/gateway/sitecarris/busstops/getnextroutesatstop?stopIds=9804"
```

See [CARRIS_API.md](CARRIS_API.md) for full documentation.

## License

MIT
