# Google Drive – AI Rooms Workflow Addon

## Overview

Addon for Rooms AI to interact with **Google Drive**: list documents in folders and delete documents by moving them to trash.

**Addon Type:** `google_drive`

## Features

- List documents in a specific folder with optional trashed files
- Download documents (supports both regular files and Google Workspace file exports)
- Delete documents by moving them to trash
- Built-in config defaults for page size and request timeout

## Add to Rooms AI using poetry

```bash
poetry add git+https://github.com/synvex-ai/google-drive-rooms-pkg.git
```

In the web interface, follow the online guide for adding an addon. You can also use JSON in the web interface.

## Configuration

### Addon Configuration

Add this addon to your AI Rooms workflow configuration:

```json
{
  "addons": [
    {
      "id": "google-drive-1",
      "type": "google_drive",
      "name": "Google Drive Addon",
      "description": "Drive actions: list / download / delete documents",
      "enabled": true,
      "config": {
        "page_size": 100,
        "max_page_size": 1000,
        "max_download_size_mb": 50
      },
      "secrets": {
        "google_drive_access_token": "ENV_GOOGLE_DRIVE_TOKEN"
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
| `type`        | string  | Yes      | -       | Type of the addon (`google_drive`)     |
| `name`        | string  | Yes      | -       | Display name of the addon                |
| `description` | string  | Yes      | -       | Description of the addon                 |
| `enabled`     | boolean | No       | true    | Whether the addon is enabled             |

#### CustomAddonConfig Fields (Google Drive-specific)

| Field                     | Type    | Required | Default | Description                                      |
| ------------------------- | ------- | -------- | ------- | ------------------------------------------------ |
| `page_size`             | integer | No       | `100` | Default page size for listing                    |
| `max_page_size`         | integer | No       | `1000`| Maximum allowed page size                        |
| `max_download_size_mb`  | integer | No       | `50`  | Maximum file size for download (in megabytes)    |

### Required Secrets

| Secret Key                    | Environment Variable       | Description                                     |
| ----------------------------- | -------------------------- | ----------------------------------------------- |
| `google_drive_access_token` | `ENV_GOOGLE_DRIVE_TOKEN` | **OAuth 2.0 access token** (Bearer token)     |

### Environment Variables

Create a `.env` file in your workflow directory:

```bash
ENV_GOOGLE_DRIVE_TOKEN=ya29.
```

> Tip: In production, inject tokens via your secret manager (GitHub Actions Secrets, GitLab CI variables, etc.).

## How to obtain a Google Drive OAuth token (with Postman)

1) **Create a Google Cloud project** and enable [Google Drive API](https://console.cloud.google.com/flows/enableapi?apiid=drive.googleapis.com)
2) Configure **OAuth consent screen** (External/Internal) and add scopes.
3) Create **OAuth client credentials** (type *Web application* or *Desktop*): keep *Client ID* and *Client Secret*.
4) In **Postman** (Authorization → Type: *OAuth 2.0*):

   - **Auth URL**: `https://accounts.google.com/o/oauth2/v2/auth`
   - **Token URL**: `https://oauth2.googleapis.com/token`
   - **Client ID** / **Client Secret**: use from step 3
   - **Scope** (choose what you need):
     - `https://www.googleapis.com/auth/drive` *(full access)*
     - `https://www.googleapis.com/auth/drive.file` *(per-file access)*
     - `https://www.googleapis.com/auth/drive.readonly` *(read-only)*
     - `https://www.googleapis.com/auth/drive.metadata.readonly` *(metadata only)*
   - **Client Authentication**: *Send as Basic Auth header* (recommended)
   - **Callback URL**: use one registered for your client (e.g. `https://oauth.pstmn.io/v1/callback` for Postman).
5) Click **Get New Access Token**, log in to your Google account, consent, then **Use Token**.
6) Copy the **Access Token** value and set it as `ENV_GOOGLE_DRIVE_TOKEN` in your `.env`.
7) **Security notes**

   - Access tokens are **short-lived**. For servers, implement the **refresh token** flow and rotate tokens automatically.
   - Never commit tokens to Git; add `.env` to `.gitignore`.
   - Revoke credentials from Google Cloud if a token leaks.

---

## Available Actions

### `list_documents`

List documents in a Google Drive folder.

**Parameters:**

- `folder_id` (string, optional; default: `"root"`) - Target folder ID
- `include_trashed` (boolean, optional; default: `false`) - Include files from trash

**Output Structure:**

- `data` (object): Contains `files` array and `count`
  - `files`: Array of file objects with `id`, `name`, `mimeType`, `webViewLink`, `modifiedTime`
  - `count`: Number of files retrieved

**Workflow Usage:**

```json
{
  "id": "list-docs",
  "action": "google-drive-1::list_documents",
  "parameters": {
    "folder_id": "root",
    "include_trashed": false
  }
}
```

---

### `delete_document`

Delete a document by moving it to trash.

**Parameters:**

- `fileId` (string, **required**) - ID of the file to move to trash

**Output Structure:**

- `data` (object): Contains `trashed` boolean and `file` object with updated file info
  - `trashed`: `true` if successful
  - `file`: Updated file object with `id`, `name`, `trashed` status

**Workflow Usage:**

```json
{
  "id": "delete-doc",
  "action": "google-drive-1::delete_document",
  "parameters": {
    "fileId": "1abc123def456"
  }
}
```

---

### `download_document`

Download a document from Google Drive. Supports both regular files and Google Workspace files (Docs, Sheets, Slides) with export to different formats.

**Parameters:**

- `fileId` (string, **required**) - ID of the file to download
- `export_mime_type` (string, optional) - MIME type for exporting Google Workspace files (e.g., Google Docs, Sheets, Slides)

**Common Export MIME Types:**

For Google Docs:
- `application/pdf` - PDF
- `text/plain` - Plain text
- `application/vnd.openxmlformats-officedocument.wordprocessingml.document` - Microsoft Word (.docx)
- `text/html` - HTML

For Google Sheets:
- `application/pdf` - PDF
- `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` - Microsoft Excel (.xlsx)
- `text/csv` - CSV

For Google Slides:
- `application/pdf` - PDF
- `application/vnd.openxmlformats-officedocument.presentationml.presentation` - Microsoft PowerPoint (.pptx)

**Output Structure:**

- `data` (object): Contains download information
  - `fileId`: File ID that was downloaded
  - `content_base64`: Base64-encoded file content (all files)
  - `size_bytes`: Size of downloaded content
  - `content_type`: Content-Type from response
  - `export_mime_type`: Export format used (if applicable)

**Note:** Files exceeding `max_download_size_mb` (default 50MB) will return an error with HTTP status code 413.

**Workflow Usage (Regular file):**

```json
{
  "id": "download-file",
  "action": "google-drive-1::download_document",
  "parameters": {
    "fileId": "1abc123def456"
  }
}
```

**Workflow Usage (Export Google Doc as PDF):**

```json
{
  "id": "export-doc-pdf",
  "action": "google-drive-1::download_document",
  "parameters": {
    "fileId": "1abc123def456",
    "export_mime_type": "application/pdf"
  }
}
```

**Workflow Usage (Export Google Sheet as CSV):**

```json
{
  "id": "export-sheet-csv",
  "action": "google-drive-1::download_document",
  "parameters": {
    "fileId": "1xyz789ghi012",
    "export_mime_type": "text/csv"
  }
}
```

---

## Action Response Format

All actions return an `ActionResponse` object with the following structure:

```python
{
  "output": {
    "data": {...}  # Action-specific data
  },
  "tokens": {
    "stepAmount": 100,           # Tokens used for this step
    "totalCurrentAmount": 100    # Running total
  },
  "message": "Success message or error description",
  "code": 200  # HTTP status code
}
```

This standardized format ensures actions can be chained in workflows, with the workflow engine able to:
- Track token usage across steps
- Handle errors based on HTTP status codes
- Pass `output.data` between actions
- Log meaningful messages for debugging

## Testing & Lint

Like all Rooms AI deployments, addons should be tested and linted.

### Running the Tests

```bash
poetry run pytest tests/ --cov=src/google_drive_rooms_pkg --cov-report=term-missing
```

### Running the linter

```bash
poetry run ruff check . --fix
```

### Pull Requests & versioning

We use semantic versioning in CI/CD to automate versions.
Use the appropriate commit message syntax for semantic release in GitHub.

## Developers / Maintainers

- Romain Michaux: [romain.michaux@nexroo.com](mailto:romain.michaux@nexroo.com)
