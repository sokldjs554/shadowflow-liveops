from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from typing import Any

from shadowflow.models import ActionKind, TargetSnapshot, TraceBundle, TraceEvent

SENSITIVE_HINTS = re.compile(r"password|passwd|secret|token|api.?key|credential", re.IGNORECASE)


def stable_hash(payload: object) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def sanitize_value(target: TargetSnapshot | None, value: Any) -> tuple[Any, str | None]:
    if target is None:
        return value, None
    descriptor = " ".join(
        part
        for part in [target.accessible_name, target.label, target.text, target.test_id]
        if part
    )
    if SENSITIVE_HINTS.search(descriptor):
        return "<redacted>", f"Redacted sensitive input for {descriptor!r}."
    return value, None


def normalize_bundle(bundle: TraceBundle) -> TraceBundle:
    events: list[TraceEvent] = []
    redactions = list(bundle.redactions)
    for expected_seq, event in enumerate(sorted(bundle.events, key=lambda item: item.seq)):
        value, redaction = sanitize_value(event.target, event.value)
        if redaction:
            redactions.append(redaction)
        metadata = dict(event.metadata)
        metadata.setdefault("source_seq", event.seq)
        events.append(
            event.model_copy(
                update={
                    "seq": expected_seq,
                    "value": value,
                    "metadata": metadata,
                }
            )
        )
    return bundle.model_copy(update={"events": events, "redactions": sorted(set(redactions))})


def event(
    seq: int,
    action: ActionKind,
    *,
    page: str,
    selector: str | None = None,
    role: str | None = None,
    name: str | None = None,
    label: str | None = None,
    value: Any = None,
    metadata: dict[str, Any] | None = None,
) -> TraceEvent:
    target = None
    if selector or role or name or label:
        target = TargetSnapshot(
            selector=selector,
            role=role,
            accessible_name=name,
            label=label,
        )
    before = {"seq": seq, "page": page, "phase": "before", "action": action.value}
    after = {"seq": seq, "page": page, "phase": "after", "action": action.value, "value": value}
    return TraceEvent(
        id=f"evt-{seq:02d}",
        seq=seq,
        at=datetime(2026, 9, 19, 5, 0, seq, tzinfo=UTC),
        page=page,
        action=action,
        target=target,
        value=value,
        before_hash=stable_hash(before),
        after_hash=stable_hash(after),
        metadata=metadata or {},
    )


def synthetic_liveops_trace() -> TraceBundle:
    page = "/synthetic-liveops/events/new"
    events = [
        event(0, ActionKind.NAVIGATE, page=page, value=page),
        event(1, ActionKind.INPUT, page=page, selector="#event-name-v17", role="textbox", name="Event name", label="Event name", value="Autumn Table Week"),
        event(2, ActionKind.SELECT, page=page, selector="#regions-v17", role="listbox", name="Regions", label="Regions", value=["KR", "JP", "US"]),
        event(3, ActionKind.INPUT, page=page, selector="#locale-ko-v17", role="textbox", name="Korean announcement", label="Korean announcement", value="가을 이벤트가 시작됩니다."),
        event(4, ActionKind.INPUT, page=page, selector="#locale-ja-v17", role="textbox", name="Japanese announcement", label="Japanese announcement", value="秋のイベントが始まります。"),
        event(5, ActionKind.INPUT, page=page, selector="#locale-en-v17", role="textbox", name="English announcement", label="English announcement", value="Autumn event is live."),
        event(6, ActionKind.INPUT, page=page, selector="#start-at-v17", role="textbox", name="Start time UTC", label="Start time UTC", value="2026-10-01T00:00:00Z"),
        event(7, ActionKind.INPUT, page=page, selector="#end-at-v17", role="textbox", name="End time UTC", label="End time UTC", value="2026-10-08T00:00:00Z"),
        event(8, ActionKind.UPLOAD, page=page, selector="#banner-v17", role="button", name="Choose banner", label="Banner asset", value="fixtures/autumn-banner.webp", metadata={"mime": "image/webp", "synthetic": True}),
        event(9, ActionKind.PREVIEW, page=page, selector="#preview-v17", role="button", name="Preview event", value=None),
        event(10, ActionKind.PUBLISH, page=page, selector="#publish-v17", role="button", name="Publish event", value=None),
    ]
    return TraceBundle(
        id="trace-liveops-autumn-v1",
        title="Synthetic live-ops event release",
        source="synthetic-demo",
        events=events,
    )
