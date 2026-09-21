from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Element:
    key: str
    selector: str
    role: str
    name: str
    label: str | None = None


@dataclass
class LiveOpsState:
    event_name: str | None = None
    regions: list[str] = field(default_factory=list)
    localizations: dict[str, str] = field(default_factory=dict)
    start_at: str | None = None
    end_at: str | None = None
    banner: str | None = None
    previewed: bool = False
    published: bool = False


BASELINE_ELEMENTS = {
    "event_name": Element("event_name", "#event-name-v17", "textbox", "Event name", "Event name"),
    "regions": Element("regions", "#regions-v17", "listbox", "Regions", "Regions"),
    "locale_ko": Element("locale_ko", "#locale-ko-v17", "textbox", "Korean announcement", "Korean announcement"),
    "locale_ja": Element("locale_ja", "#locale-ja-v17", "textbox", "Japanese announcement", "Japanese announcement"),
    "locale_en": Element("locale_en", "#locale-en-v17", "textbox", "English announcement", "English announcement"),
    "start_at": Element("start_at", "#start-at-v17", "textbox", "Start time UTC", "Start time UTC"),
    "end_at": Element("end_at", "#end-at-v17", "textbox", "End time UTC", "End time UTC"),
    "banner": Element("banner", "#banner-v17", "button", "Choose banner", "Banner asset"),
    "preview": Element("preview", "#preview-v17", "button", "Preview event"),
    "publish": Element("publish", "#publish-v17", "button", "Publish event"),
}


def drifted_elements(seed: int = 1) -> dict[str, Element]:
    # IDs/classes change as the UI is rebuilt, while accessibility semantics stay stable.
    return {
        key: Element(
            key=element.key,
            selector=f"#ui-{seed:02d}-{index:02d}",
            role=element.role,
            name=element.name,
            label=element.label,
        )
        for index, (key, element) in enumerate(BASELINE_ELEMENTS.items(), start=1)
    }


def required_locales(regions: list[str]) -> set[str]:
    mapping = {"KR": "ko-KR", "JP": "ja-JP", "US": "en-US"}
    return {mapping[item] for item in regions if item in mapping}


def validate_publish(state: LiveOpsState) -> list[str]:
    errors: list[str] = []
    if not state.event_name:
        errors.append("event_name_missing")
    if not state.regions:
        errors.append("regions_missing")
    missing = sorted(required_locales(state.regions) - set(state.localizations))
    if missing:
        errors.append("missing_locales:" + ",".join(missing))
    if not state.start_at or not state.end_at:
        errors.append("schedule_missing")
    if state.start_at and state.end_at and state.start_at >= state.end_at:
        errors.append("schedule_invalid")
    if not state.banner:
        errors.append("banner_missing")
    if not state.previewed:
        errors.append("preview_required")
    return errors


def apply_value(state: LiveOpsState, element_key: str, value: Any) -> None:
    if element_key == "event_name":
        state.event_name = str(value)
    elif element_key == "regions":
        state.regions = list(value or [])
    elif element_key == "locale_ko":
        state.localizations["ko-KR"] = str(value)
    elif element_key == "locale_ja":
        state.localizations["ja-JP"] = str(value)
    elif element_key == "locale_en":
        state.localizations["en-US"] = str(value)
    elif element_key == "start_at":
        state.start_at = str(value)
    elif element_key == "end_at":
        state.end_at = str(value)
    elif element_key == "banner":
        state.banner = str(value)
