# Carris Municipal Bus API Documentation

Unofficial documentation reverse-engineered from the CARRISway Android app (v2.0.2).

## Base URL
```
https://gateway.carris.pt/gateway/sitecarris/
```

## Authentication

### Step 1: Get API Key (one-time from Firebase Remote Config)
```bash
# Register Firebase Installation
FID_RESPONSE=$(curl -s -X POST "https://firebaseinstallations.googleapis.com/v1/projects/carrisway-3600c/installations" \
  -H "Content-Type: application/json" \
  -H "x-goog-api-key: AIzaSyDtLCt4bu-DrzjqFdzxu_Wnh6RQbgijRyg" \
  -H "x-android-package: com.carris.passcard" \
  -d '{"fid":"cR3vN7xKpQmW2sY8bL4fT","appId":"1:1028494773320:android:2f1c9d5354c0aa148bdc7d","authVersion":"FIS_v2","sdkVersion":"a:17.0.0"}')

FID=$(echo $FID_RESPONSE | jq -r '.fid')
AUTH_TOKEN=$(echo $FID_RESPONSE | jq -r '.authToken.token')

# Fetch Remote Config (contains API keys)
curl -s -X POST "https://firebaseremoteconfig.googleapis.com/v1/projects/carrisway-3600c/namespaces/firebase:fetch?key=AIzaSyDtLCt4bu-DrzjqFdzxu_Wnh6RQbgijRyg" \
  -H "Content-Type: application/json" \
  -H "x-goog-api-key: AIzaSyDtLCt4bu-DrzjqFdzxu_Wnh6RQbgijRyg" \
  -H "x-android-package: com.carris.passcard" \
  -d "{\"appId\":\"1:1028494773320:android:2f1c9d5354c0aa148bdc7d\",\"appInstanceId\":\"$FID\",\"appInstanceIdToken\":\"$AUTH_TOKEN\"}" | jq '.entries'
```

**Current API Key (Routes):** `8844d854-9c37-4f22-b4d4-50a3626da5da`

### Step 2: Get Bearer Token (valid 24h)
```bash
curl -s -X POST \
  -H "X-Gravitee-Api-Key: 8844d854-9c37-4f22-b4d4-50a3626da5da" \
  "https://gateway.carris.pt/gateway/sitecarris/token"
```

**Response:**
```json
{
  "access_token": "vtUt6uGd...",
  "token_type": "bearer",
  "expires_in": 86399
}
```

### Required Headers for All Requests
```
X-Gravitee-Api-Key: 8844d854-9c37-4f22-b4d4-50a3626da5da
Authorization: Bearer <access_token>
```

---

## Endpoints

### GET /busstops/getall
Get all bus stops.

**Response:** Array of bus stops
```json
[
  {
    "id": 9803,
    "name": "R. D. Fuas Roupinho",
    "location": { "lat": 38.7244087, "lng": -9.1173888 },
    "routes": [
      { "routeNumber": "742", "color": "#8c8c99" }
    ]
  }
]
```

---

### GET /busstops/getnextroutesatstop
Get real-time next bus arrivals at a stop.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| stopIds | string | Stop ID (comma-separated for multiple) |

**Example:**
```
GET /busstops/getnextroutesatstop?stopIds=9803
```

**Response:**
```json
[
  {
    "routeNumber": "742",
    "stopId": 9803,
    "stopTime": "2026-01-03T14:08:32+00:00",
    "destination": "B. Madre Deus"
  }
]
```

---

### GET /routes/getroutes
Get all bus routes.

**Response:**
```json
[
  {
    "routeName": "B. Madre Deus - Pólo Univ. Ajuda",
    "routeNumber": "742",
    "vehicle": { "description": "Autocarro", "iconUrl": "/media/.../bus_.svg" },
    "zone": { "description": "Cinzenta - Circulares", "color": "#8c8c99" }
  }
]
```

---

### GET /routes/getbusstoptimes
Get scheduled times for a route at a specific stop.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| routeNumber | string | Route number (e.g., "742") |
| stopId | int | Stop ID |
| direction | int | 1 or 2 (direction of travel) |
| date | string | Date in YYYY-MM-DD format |

**Example:**
```
GET /routes/getbusstoptimes?routeNumber=742&stopId=9804&direction=1&date=2026-01-03
```

**Response:**
```json
{
  "dayName": "Fim-de-semana",
  "seasonName": "Inverno",
  "stopTimes": [
    "2026-01-03T07:12:47+00:00",
    "2026-01-03T07:27:47+00:00"
  ]
}
```

---

### GET /routes/getroute
Get detailed route information including shape.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| culture | string | Language (default: pt-PT) |

**Note:** Uses `@Url` annotation - full URL path required.

---

### GET /vehicles/getsnapshot
Get real-time positions of all buses.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| culture | string | Language (default: pt-PT) |

**Response:** Array of bus positions with coordinates.

---

## Quick Start Script

```bash
#!/bin/bash
API_KEY="8844d854-9c37-4f22-b4d4-50a3626da5da"
BASE_URL="https://gateway.carris.pt/gateway/sitecarris"

# Get token
TOKEN=$(curl -s -X POST -H "X-Gravitee-Api-Key: $API_KEY" "$BASE_URL/token" | jq -r '.access_token')

# Get next buses at Dom Fuas Roupinho westbound (stop 9804)
curl -s -H "X-Gravitee-Api-Key: $API_KEY" -H "Authorization: Bearer $TOKEN" \
  "$BASE_URL/busstops/getnextroutesatstop?stopIds=9804" | jq '.[] | select(.routeNumber == "742")'
```

---

## Stop IDs for Dom Fuas Roupinho

| Stop ID | Direction | Destination |
|---------|-----------|-------------|
| 9803 | Eastbound | B. Madre Deus |
| 9804 | Westbound | Pólo Univ. Ajuda |

---

## Firebase Project Details (for API key refresh)
- Project ID: `carrisway-3600c`
- Google App ID: `1:1028494773320:android:2f1c9d5354c0aa148bdc7d`
- Google API Key: `AIzaSyDtLCt4bu-DrzjqFdzxu_Wnh6RQbgijRyg`
