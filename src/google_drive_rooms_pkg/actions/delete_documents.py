from __future__ import annotations

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from loguru import logger
import requests

from ..configuration.addonconfig import CustomAddonConfig
from .base import ActionResponse, OutputBase, TokensSchema


class ActionInput(BaseModel):
    """
    Paramètres pour envoyer un fichier à la corbeille sur Google Drive.
    """
    fileId: str = Field(..., description="ID du fichier à envoyer à la corbeille.")


class ActionOutput(OutputBase):
    data: Optional[Dict[str, Any]] = None


def delete_document(
    config: CustomAddonConfig,
    fileId: str,
) -> ActionResponse:
    """
    Action : envoyer un document à la corbeille sur Google Drive.
    """
    tokens = TokensSchema(stepAmount=100, totalCurrentAmount=100)
    logger.debug("[delete_document] called (simplified version)")

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

    url = f"https://www.googleapis.com/drive/v3/files/{fileId}"
    params = {"fields": "id,name,trashed"}
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    body = {"trashed": True}
    timeout_s = getattr(config, "request_timeout_s", 10)

    logger.debug(f"[delete_document] PATCH {url} body={body} timeout={timeout_s}s")

    try:
        resp = requests.patch(url, headers=headers, params=params, json=body, timeout=timeout_s)
        status = resp.status_code

        try:
            payload = resp.json()
        except ValueError:
            payload = {"raw": resp.text}

        if 200 <= status < 300:
            logger.info(f"[delete_document] File {fileId} moved to trash.")
            return ActionResponse(
                output=ActionOutput(data={"trashed": True, "file": payload}),
                tokens=tokens,
                message="File moved to trash successfully",
                code=status,
            )

        err_msg = None
        if isinstance(payload, dict):
            err_msg = payload.get("error", {}).get("message") or payload.get("error_description")
        msg = err_msg or f"HTTP {status}"
        logger.warning(f"[delete_document] Drive API error: {msg}")
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
