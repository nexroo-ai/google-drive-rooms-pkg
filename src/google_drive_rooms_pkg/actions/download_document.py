from __future__ import annotations

import base64
from typing import Any

import requests
from loguru import logger
from pydantic import BaseModel, Field

from ..configuration.addonconfig import CustomAddonConfig
from .base import ActionResponse, OutputBase, TokensSchema


class ActionInput(BaseModel):
    fileId: str = Field(..., description="ID du fichier à télécharger.")
    export_mime_type: str | None = Field(None, description="Type MIME pour l'export (Google Docs, Sheets, etc.).")


class ActionOutput(OutputBase):
    data: dict[str, Any] | None = None


def download_document(
    config: CustomAddonConfig,
    fileId: str,
    export_mime_type: str | None = None,
) -> ActionResponse:
    tokens = TokensSchema(stepAmount=150, totalCurrentAmount=150)
    logger.debug("[download_document] called")

    if not fileId:
        msg = "Missing required parameter: fileId."
        logger.warning(msg)
        return ActionResponse(
            output=ActionOutput(data={"error": msg}),
            tokens=tokens,
            message=msg,
            code=400,
        )

    try:
        _ = config.get_required_secrets()
        access_token = config.secrets.get("google_drive_access_token")
    except Exception as e:
        msg = f"Invalid configuration for secrets: {e}"
        logger.error(msg)
        return ActionResponse(
            output=ActionOutput(data={"error": msg}),
            tokens=tokens,
            message=msg,
            code=500,
        )

    if not access_token:
        msg = "Missing 'google_drive_access_token' in secrets."
        logger.error(msg)
        return ActionResponse(
            output=ActionOutput(data={"error": msg}),
            tokens=tokens,
            message=msg,
            code=401,
        )

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }

    metadata_url = f"https://www.googleapis.com/drive/v3/files/{fileId}"
    metadata_params = {"fields": "id,name,size,mimeType"}

    logger.debug(f"[download_document] Fetching file metadata for {fileId}")

    try:
        metadata_resp = requests.get(metadata_url, headers=headers, params=metadata_params)
        if metadata_resp.status_code != 200:
            try:
                error_payload = metadata_resp.json()
                err_msg = error_payload.get("error", {}).get("message") or "Failed to fetch file metadata"
            except ValueError:
                err_msg = "Failed to fetch file metadata"
            logger.error(f"[download_document] Metadata fetch failed: {err_msg}")
            return ActionResponse(
                output=ActionOutput(data={"error": err_msg}),
                tokens=TokensSchema(stepAmount=0, totalCurrentAmount=0),
                message=err_msg,
                code=metadata_resp.status_code,
            )

        metadata = metadata_resp.json()
        file_size_bytes = int(metadata.get("size", 0)) if metadata.get("size") else None
        file_name = metadata.get("name", "unknown")
        file_mime_type = metadata.get("mimeType", "")

        max_size_mb = getattr(config, "max_download_size_mb", 50)
        max_size_bytes = max_size_mb * 1024 * 1024

        if file_size_bytes and file_size_bytes > max_size_bytes:
            msg = f"File '{file_name}' size ({file_size_bytes / 1024 / 1024:.2f} MB) exceeds maximum allowed size ({max_size_mb} MB)"
            logger.warning(f"[download_document] {msg}")
            return ActionResponse(
                output=ActionOutput(data={
                    "error": msg,
                    "file_size_bytes": file_size_bytes,
                    "max_size_bytes": max_size_bytes,
                    "file_name": file_name
                }),
                tokens=TokensSchema(stepAmount=0, totalCurrentAmount=0),
                message=msg,
                code=413,
            )

        logger.info(f"[download_document] File metadata: {file_name} ({file_size_bytes} bytes, {file_mime_type})")

    except requests.exceptions.RequestException as e:
        msg = f"Metadata request failed: {e.__class__.__name__}: {e}"
        logger.error(msg)
        return ActionResponse(
            output=ActionOutput(data={"error": str(e)}),
            tokens=TokensSchema(stepAmount=0, totalCurrentAmount=0),
            message=msg,
            code=503,
        )

    is_google_docs_file = file_mime_type.startswith("application/vnd.google-apps.")

    if is_google_docs_file:
        url = f"https://www.googleapis.com/drive/v3/files/{fileId}/export"
        export_type = export_mime_type or "text/plain"
        params = {"mimeType": export_type}
        logger.debug(f"[download_document] Exporting Google Docs file {fileId} as {export_type}")
    else:
        url = f"https://www.googleapis.com/drive/v3/files/{fileId}"
        params = {"alt": "media"}
        if export_mime_type:
            logger.warning(f"[download_document] Ignoring export_mime_type for native file {file_mime_type}")
        logger.debug(f"[download_document] Downloading native file {fileId}")

    logger.debug(f"[download_document] GET {url} params={params}")

    try:
        resp = requests.get(url, headers=headers, params=params)
        status = resp.status_code

        if 200 <= status < 300:
            content = resp.content
            content_type = resp.headers.get("Content-Type", "application/octet-stream")

            logger.info(f"[download_document] File {fileId} downloaded successfully ({len(content)} bytes)")
            return ActionResponse(
                output=ActionOutput(data={
                    "fileId": fileId,
                    "content_base64": base64.b64encode(content).decode("ascii"),
                    "size_bytes": len(content),
                    "content_type": content_type,
                    "export_mime_type": export_mime_type
                }),
                tokens=tokens,
                message=f"File downloaded successfully ({len(content)} bytes)",
                code=status,
            )

        try:
            payload = resp.json()
            err_msg = payload.get("error", {}).get("message") or payload.get("error_description")
        except ValueError:
            err_msg = resp.text[:200] if resp.text else None

        msg = err_msg or f"HTTP {status}"
        logger.warning(f"[download_document] Drive API error: {msg}")
        return ActionResponse(
            output=ActionOutput(data={"error": msg}),
            tokens=TokensSchema(stepAmount=0, totalCurrentAmount=0),
            message=msg,
            code=status,
        )

    except requests.exceptions.RequestException as e:
        msg = f"Request failed: {e.__class__.__name__}: {e}"
        logger.error(msg)
        return ActionResponse(
            output=ActionOutput(data={"error": str(e)}),
            tokens=TokensSchema(stepAmount=0, totalCurrentAmount=0),
            message=msg,
            code=503,
        )
