# Leviathan Frontend

This React client powers the Leviathan fishing copilot demo. It includes a Plan Card view with geolocated charts, a sonar assistant, and freshness QA tooling.

## Prerequisites

- Node.js 18+ (19 works too)
- npm 8+

## Setup

```powershell
git clone <repo>
cd sushi-glitch/frontend
npm install
```

## Running Locally

```powershell
Set-Location frontend     # if not already
npm start
```

This launches `http://localhost:3000`.

## Location Permissions

- The Plan Card map centers on your current location using the browser Geolocation API.
- When prompted, allow location access for best results.
- If denied or unsupported, the Plan Card falls back to the default home-port coordinates and shows a status message.
- Location fetch happens once on load; use the “Update Conditions” button in the Plan Card when you want to re-check.

## Map Tiles & Icons

- Uses Leaflet with OpenStreetMap tiles.
- Marker icons load via the Leaflet CDN; no additional assets needed.

## Scripts

- `npm start`: Dev server with hot reload
- `npm run build`: Production bundle
- `npm test`: Jest test runner
