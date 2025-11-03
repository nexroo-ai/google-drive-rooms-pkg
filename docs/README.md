# Google Calendars – AI Rooms Workflow Addon

## Overview

Addon for Rooms AI to interact with **Google Calendar**: list events, check free/busy windows, and create events (with optional Google Meet).

**Addon Type:** `google_calendars`

## Features

- List events within a time window (UTC-safe parsing, ordering by start time).
- Free/Busy query for one or more calendars.
- Create events (date-time or all‑day), attendees, reminders, colors, notifications, optional Meet link.
- Built‑in config defaults (calendar id, max results, timezone, request timeout).

## Add to Rooms AI using poetry

```bash
poetry add git+https://github.com/synvex-ai/google-calendars-rooms-pkg.git
```

In the web interface, follow the online guide for adding an addon. You can also use JSON in the web interface.

## Configuration

### Addon Configuration

Add this addon to your AI Rooms workflow configuration:

```json
{
  "addons": [
    {
      "id": "google-calendar-1",
      "type": "google_calendars",
      "name": "Google Calendar Addon",
      "description": "Calendar actions: list / freebusy / create",
      "enabled": true,
      "config": {
        "default_calendar_id": "primary",
        "default_max_results": 10,
        "default_time_window_days": 7,
        "default_timezone": "Europe/Paris",
        "request_timeout_s": 10,
        "enable_debug": false
      },
      "secrets": {
        "google_calendars_api_key": "ENV_GOOGLE_CALENDAR_TOKEN"
      }
    }
  ]
}
```

### Configuration Fields

#### BaseAddonConfig Fields

All addons inherit these base configuration fields:

| Field           | Type    | Required | Default | Description                              |
| --------------- | ------- | -------- | ------- | ---------------------------------------- |
| `id`          | string  | Yes      | -       | Unique identifier for the addon instance |
| `type`        | string  | Yes      | -       | Type of the addon (`google_calendars`) |
| `name`        | string  | Yes      | -       | Display name of the addon                |
| `description` | string  | Yes      | -       | Description of the addon                 |
| `enabled`     | boolean | No       | true    | Whether the addon is enabled             |

#### CustomAddonConfig Fields (Google Calendar‑specific)

| Field                        | Type    | Required | Default          | Description                    |
| ---------------------------- | ------- | -------- | ---------------- | ------------------------------ |
| `default_calendar_id`      | string  | No       | `primary`      | Fallback calendar id           |
| `default_max_results`      | integer | No       | `10`           | Max results for listing events |
| `default_time_window_days` | integer | No       | `7`            | Forward lookup window (days)   |
| `default_timezone`         | string  | No       | `Europe/Paris` | Default IANA timezone          |
| `request_timeout_s`        | integer | No       | `10`           | HTTP timeout (seconds)         |
| `enable_debug`             | boolean | No       | `false`        | Extra debug logs               |

### Required Secrets

| Secret Key                   | Environment Variable          | Description                                     |
| ---------------------------- | ----------------------------- | ----------------------------------------------- |
| `google_calendars_api_key` | `ENV_GOOGLE_CALENDAR_TOKEN` | **OAuth 2.0 access token** (Bearer token) |

### Environment Variables

Create a `.env` file in your workflow directory:

```bash
ENV_GOOGLE_CALENDAR_TOKEN=ya29.
```

> Tip: In production, inject tokens via your secret manager (GitHub Actions Secrets, GitLab CI variables, etc.).

## How to obtain a Google Calendar OAuth token (with Postman)

1) **Create a Google Cloud project** and enable [`<u>`Google Calendar API – Enable &amp; Setup`</u>`](https://console.cloud.google.com/flows/enableapi?apiid=calendar-json.googleapis.com)
2) Configure **OAuth consent screen** (External/Internal) and add scopes.
3) Create **OAuth client credentials** (type *Web application* or *Desktop*): keep *Client ID* and *Client Secret*.
4) In **Postman** (Authorization → Type: *OAuth 2.0*):

   - **Auth URL**: `https://accounts.google.com/o/oauth2/v2/auth`
   - **Token URL**: `https://oauth2.googleapis.com/token`
   - **Client ID** / **Client Secret**: use from step 3
   - **Scope** (choose what you need):
     - `https://www.googleapis.com/auth/calendar` *(full)*
     - `https://www.googleapis.com/auth/calendar.events` *(manage events)*
     - `https://www.googleapis.com/auth/calendar.readonly` *(read)*
     - `https://www.googleapis.com/auth/calendar.events.readonly` *(read events)*
     - `https://www.googleapis.com/auth/calendar.freebusy` *(free/busy)*
   - **Client Authentication**: *Send as Basic Auth header* (recommended)
   - **Callback URL**: use one registered for your client (e.g. `https://oauth.pstmn.io/v1/callback` for Postman).
5) Click **Get New Access Token**, log in to your Google account, consent, then **Use Token**.
6) Copy the **Access Token** value and set it as `ENV_GOOGLE_CALENDAR_TOKEN` in your `.env`.
7) **Security notes**

   - Access tokens are **short‑lived**. For servers, implement the **refresh token** flow and rotate tokens automatically.
   - Never commit tokens to Git; add `.env` to `.gitignore`.
   - Revoke credentials from Google Cloud if a token leaks.

---

## Available Actions

### `list_events`

List single events in a time window (ordered by start time).

**Parameters:**

- `calendarId` (string, optional; default: `config.default_calendar_id`)
- `maxResults` (integer, optional; default: `config.default_max_results`)
- `timeMin` (datetime or ISO string, **required**)
- `timeMax` (datetime or ISO string, optional; must be strictly > `timeMin`)

**Output Structure:**

- `data` (object): Raw response from Google Calendar `events.list`.

**Workflow Usage:**

```json
{
  "id": "list-events",
  "action": "google-calendar-1::list_events",
  "parameters": {
    "calendarId": "primary",
    "maxResults": 10,
    "timeMin": "2025-09-16T00:00:00Z",
    "timeMax": "2025-09-20T23:59:59Z"
  }
}
```

---

### `freebusy_query`

Query free/busy for one or more calendars.

**Parameters:**

- `timeMin` (datetime or ISO string, **required**)
- `timeMax` (datetime or ISO string, **required**; strictly > `timeMin`)
- `items` (array, **required**): list of calendar IDs or objects with `id` (e.g. `["primary"]` or `[{"id":"primary"}]`)
- `timeZone` (string, optional): IANA timezone (default UTC)
- `calendarExpansionMax` (int, optional)
- `groupExpansionMax` (int, optional)

**Output Structure:**

- `data` (object): Raw response from Google Calendar `freeBusy.query`.

**Workflow Usage:**

```json
{
  "id": "freebusy",
  "action": "google-calendar-1::freebusy_query",
  "parameters": {
    "timeMin": "2025-09-16T00:00:00Z",
    "timeMax": "2025-09-18T23:59:59Z",
    "items": ["primary"],
    "timeZone": "Europe/Paris"
  }
}
```

---

### `create_events`

Create calendar events. Supports **date‑time** *or* **all‑day** events, attendees, reminders, notifications, and optional Meet link.

**Parameters:**

- **Required**:
  - `calendarId` (string) – target calendar id (e.g. `primary`)
  - EITHER (`start_dt`, `end_dt`) as datetimes/ISO strings **OR** (`start_date`, `end_date`) as `YYYY-MM-DD` (end exclusive)
  - `summary` (string) – event title
- **Optional**:
  - `description` (string), `location` (string)
  - `attendees` (array of emails)
  - `colorId` (string, `"1"`..`"11"`)
  - `sendUpdates` (`"all" | "externalOnly" | "none"`)
  - `create_conference` (boolean) – if `true`, adds a Google Meet link
  - `reminders_overrides` (array of `{method, minutes}`) – sets `useDefault=false`

**Output Structure:**

- `data` (object): Raw created event from Google Calendar `events.insert`.

**Workflow Usage (datetime):**

```json
{
  "id": "create-event-1",
  "action": "google-calendar-1::create_events",
  "parameters": {
    "calendarId": "primary",
    "summary": "AI Rooms Test Event",
    "description": "Created via workflow",
    "start_dt": "2025-09-16T10:00:00Z",
    "end_dt": "2025-09-16T11:00:00Z",
    "location": "Paris",
    "attendees": ["a@example.com", "b@example.com"],
    "create_conference": true
  }
}
```

**Workflow Usage (all‑day):**

```json
{
  "id": "create-event-2",
  "action": "google-calendar-1::create_events",
  "parameters": {
    "calendarId": "primary",
    "summary": "All‑day offsite",
    "start_date": "2025-09-17",
    "end_date": "2025-09-18",
    "colorId": "5",
    "sendUpdates": "all"
  }
}
```

## Testing & Lint

Like all Rooms AI deployments, addons should be tested and linted.

### Running the Tests

```bash
poetry run pytest tests/ --cov=src/google_calendars_rooms_pkg --cov-report=term-missing
```

### Running the linter

```bash
poetry run ruff check . --fix
```

### Pull Requests & versioning

We use semantic versioning in CI/CD to automate versions.
Use the appropriate commit message syntax for semantic release in GitHub.

## Developers / Maintainers

- Romain Michaux :  [romain.michaux@nexroo.com](mailto:romain.michaux@nexroo.com)
