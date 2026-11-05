from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from typing import Any

from contracts.models import (
    ModelCatalogCapabilities,
    ModelCatalogDefaults,
    ModelCatalogSource,
    ModelCatalogView,
    ImageModelProfile,
)
from services.account_service import account_service
from services.config import config
from utils.helper import CODEX_IMAGE_MODEL, WEB_IMAGE_MODELS, image_model_route, is_codex_image_model


FALLBACK_CHAT_MODELS = [
    "gpt-5.6",
    "auto",
]

FALLBACK_IMAGE_MODELS = list(WEB_IMAGE_MODELS)

_IMAGE_SIZES = (
    ("auto", "auto", "auto"),
    ("1024x1024", "1:1", "1K"), ("1024x1536", "2:3", "1K"), ("1536x1024", "3:2", "1K"),
    ("1008x1344", "3:4", "1K"), ("1344x1008", "4:3", "1K"),
    ("864x1536", "9:16", "1K"), ("1536x864", "16:9", "1K"),
    ("2048x2048", "1:1", "2K"), ("1536x2304", "2:3", "2K"), ("2304x1536", "3:2", "2K"),
    ("1536x2048", "3:4", "2K"), ("2048x1536", "4:3", "2K"),
    ("2560x1440", "16:9", "2K"), ("1440x2560", "9:16", "2K"),
    ("2880x2880", "1:1", "4K"), ("3840x2160", "16:9", "4K"), ("2160x3840", "9:16", "4K"),
    ("3456x2304", "3:2", "4K"), ("2304x3456", "2:3", "4K"),
    ("3264x2448", "4:3", "4K"), ("2448x3264", "3:4", "4K"),
)


def image_model_profile(model: str, upscale: bool = False) -> ImageModelProfile:
    codex = is_codex_image_model(model)
    alias = model.startswith("gpt-image-2.5")
    note = (
        "尺寸和质量通过工具参数提交；上游未报告时，实际图片模型与质量显示未知。"
        if codex else
        "尺寸和质量为提示词目标，实际以返回图片为准；当前无法保证独立选择 Flare / Sunburst。"
    )
    if upscale:
        note += "已启用本地尺寸放大，日志会区分原始与交付尺寸。"
    return ImageModelProfile(
        model=model, label=model + ("（兼容入口）" if alias else ""),
        selection_mode="tool_model" if codex else "compatibility_alias" if alias else "conversation_tool",
        upstream_model=image_model_route(model), image_model_verified=False,
        size_mode="native_parameter" if codex else "prompt_hint",
        quality_mode="native_parameter" if codex else "prompt_hint", note=note,
        size_label="请求尺寸" if codex else "目标尺寸（尽量遵循）",
        quality_label="请求质量" if codex else "目标质量（尽量遵循）",
        size_options=tuple({"value": value, "ratio": ratio, "resolution": resolution,
                            "label": "自动" if value == "auto" else f"{ratio} · {resolution} · {value}"}
                           for value, ratio, resolution in _IMAGE_SIZES),
        quality_options=tuple({"value": value, "label": label} for value, label in
                              (("auto", "自动"), ("low", "低"), ("medium", "中"), ("high", "高"))),
    )


def _normalize_list(raw: object) -> list[str]:
    if not isinstance(raw, list):
        return []
    values: list[str] = []
    seen: set[str] = set()
    for item in raw:
        value = str(item or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        values.append(value)
    return values


def _settings_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _configured_chat_models(settings: dict[str, Any]) -> list[str]:
    catalog = _settings_dict(settings.get("model_catalog"))
    explicit = _normalize_list(catalog.get("chat_models"))
    if explicit:
        return explicit

    combined: list[str] = []
    for key in ("base_chat_models", "specialized_chat_models", "image_capable_chat_models"):
        for model in _normalize_list(catalog.get(key)):
            if model not in combined:
                combined.append(model)
    return combined


def _configured_image_models(settings: dict[str, Any]) -> list[str]:
    image_generation = _settings_dict(settings.get("image_generation"))
    catalog = _settings_dict(settings.get("model_catalog"))
    for source in (
        image_generation.get("model_options"),
        catalog.get("image_api_models"),
        image_generation.get("supported_models"),
    ):
        models = _normalize_list(source)
        if models:
            return models
    return []


def _image_models_from_accounts(accounts: list[dict[str, Any]]) -> list[str]:
    available_accounts = [
        account
        for account in accounts
        if isinstance(account, dict) and account_service._is_image_account_available(account)
    ]
    if not available_accounts:
        return []

    models = list(WEB_IMAGE_MODELS)
    codex_types = {
        normalized
        for account in available_accounts
        if account_service._normalize_source_type(account.get("source_type")) == "codex"
        and (normalized := account_service._normalize_account_type(account.get("type")))
    }

    if codex_types & {"Plus", "Team", "Pro"}:
        models.append(CODEX_IMAGE_MODEL)
    for plan_type in ("Plus", "Team", "Pro"):
        if plan_type in codex_types:
            models.append(f"{plan_type.lower()}-{CODEX_IMAGE_MODEL}")
    return models


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _generated_at() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _revision(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


class ModelCatalogService:
    """Build the model facts shared by management and OpenAI-compatible APIs."""

    def view(self) -> ModelCatalogView:
        settings = config.get()
        configured_chat_models = _configured_chat_models(settings)
        configured_image_models = _configured_image_models(settings)

        chat_source = "config" if configured_chat_models else "fallback"
        chat_models = _unique(configured_chat_models or list(FALLBACK_CHAT_MODELS))

        if configured_image_models:
            image_source = "config"
            image_models = _unique(configured_image_models)
        else:
            account_models = _image_models_from_accounts(account_service.list_accounts())
            image_source = "accounts" if account_models else "fallback"
            image_models = _unique(account_models or list(FALLBACK_IMAGE_MODELS))

        all_models = _unique([*chat_models, *image_models])
        high_resolution_models = [
            model
            for model in image_models
            if model == CODEX_IMAGE_MODEL or model.endswith(f"-{CODEX_IMAGE_MODEL}")
        ]
        defaults = {
            "chat_model": "auto" if "auto" in chat_models else chat_models[0],
            "image_model": "gpt-image-2" if "gpt-image-2" in image_models else image_models[0],
        }
        capabilities = {
            "image_upscale": bool(settings.get("image_upscale_enabled")),
            "high_resolution_image_models": high_resolution_models,
        }
        source = {"chat": chat_source, "image": image_source}
        profiles = tuple(image_model_profile(model, bool(settings.get("image_upscale_enabled"))) for model in image_models)
        revision_payload = {
            "chat_models": chat_models,
            "image_models": image_models,
            "defaults": defaults,
            "capabilities": capabilities,
            "source": source,
            "image_profiles": [p.model_dump(mode="json") for p in profiles],
        }

        return ModelCatalogView(
            generated_at=_generated_at(),
            revision=_revision(revision_payload),
            chat_models=tuple(chat_models),
            image_models=tuple(image_models),
            all_models=tuple(all_models),
            defaults=ModelCatalogDefaults(**defaults),
            capabilities=ModelCatalogCapabilities(
                image_upscale=capabilities["image_upscale"],
                high_resolution_image_models=tuple(high_resolution_models),
            ),
            source=ModelCatalogSource(**source),
            image_profiles=profiles,
        )


model_catalog_service = ModelCatalogService()


def get_model_catalog() -> ModelCatalogView:
    return model_catalog_service.view()
