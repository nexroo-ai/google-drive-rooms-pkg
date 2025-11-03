from __future__ import annotations

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from loguru import logger
import requests

from ..configuration.addonconfig import CustomAddonConfig
from .base import ActionResponse, OutputBase, TokensSchema


class ActionInput(BaseModel):
    """
    Paramètres pour lister les documents d’un dossier Google Drive.
    """
    folder_id: str = Field("root", description="Dossier cible (root par défaut).")
    include_trashed: bool = Field(False, description="Inclure les fichiers de la corbeille.")


class ActionOutput(OutputBase):
    data: Optional[Dict[str, Any]] = None


def list_documents(
    config: CustomAddonConfig,
    folder_id: str = "root",
    include_trashed: bool = False,
) -> ActionResponse:
    """
    Action: lister les documents d’un dossier Google Drive.
    """
    tokens = TokensSchema(stepAmount=200, totalCurrentAmount=200)
    logger.debug("[list_documents] called (simplified version)")

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

    trashed_value = "true" if include_trashed else "false"
    query = f"'{folder_id}' in parents and trashed={trashed_value}"

    params = {
        "q": query,
        "pageSize": getattr(config, "page_size", 100),
        "fields": "files(id,name,mimeType,webViewLink,modifiedTime)",
    }

    url = "https://www.googleapis.com/drive/v3/files"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }

    logger.debug(f"[list_documents] GET {url} params={params}")

    try:
        resp = requests.get(url, headers=headers, params=params)
        status = resp.status_code

        try:
            payload = resp.json()
        except ValueError:
            payload = {"raw": resp.text}

        if 200 <= status < 300:
            files = payload.get("files", [])
            msg = f"{len(files)} fichier(s) récupéré(s)."
            logger.info(f"[list_documents] Success: {msg}")
            return ActionResponse(
                output=ActionOutput(data={"files": files, "count": len(files)}),
                tokens=tokens,
                message=msg,
                code=status,
            )

        err_msg = None
        if isinstance(payload, dict):
            err_msg = payload.get("error", {}).get("message") or payload.get("error_description")
        msg = err_msg or f"HTTP {status}"
        logger.warning(f"[list_documents] Drive API error: {msg}")

        return ActionResponse(
            output=ActionOutput(data=payload if isinstance(payload, dict) else {"error": msg}),
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
