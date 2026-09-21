from __future__ import annotations

import hashlib
import json
from dataclasses import asdict

from shadowflow.models import (
    ActionKind,
    SemanticLocator,
    ShadowFailure,
    ShadowRun,
    StepExecution,
    WorkflowSpec,
)
from synthetic_app.liveops import (
    BASELINE_ELEMENTS,
    Element,
    LiveOpsState,
    apply_value,
    drifted_elements,
    validate_publish,
)


class SyntheticLiveOpsTwin:
    def __init__(self, variant: str) -> None:
        self.variant = variant
        if variant == "baseline":
            self.elements = dict(BASELINE_ELEMENTS)
        elif variant.startswith("selector-drift"):
            suffix = variant.rsplit("-", 1)[-1]
            try:
                seed = int(suffix)
            except ValueError:
                seed = 1
            self.elements = drifted_elements(seed)
        elif variant == "semantic-drift-publish":
            self.elements = drifted_elements(99)
            publish = self.elements["publish"]
            self.elements["publish"] = Element(
                key=publish.key,
                selector=publish.selector,
                role=publish.role,
                name="Release event",
                label=publish.label,
            )
        else:
            raise ValueError(f"Unknown shadow variant: {variant}")
        self.state = LiveOpsState()

    def resolve(self, locator: SemanticLocator | None) -> Element | None:
        if locator is None:
            return None
        if locator.strategy == "selector" and locator.selector:
            return next(
                (element for element in self.elements.values() if element.selector == locator.selector),
                None,
            )
        if locator.strategy == "role_name" and locator.role and locator.name:
            return next(
                (
                    element
                    for element in self.elements.values()
                    if element.role == locator.role and element.name == locator.name
                ),
                None,
            )
        if locator.strategy == "label" and locator.label:
            return next(
                (element for element in self.elements.values() if element.label == locator.label),
                None,
            )
        if locator.strategy == "text" and locator.text:
            return next(
                (element for element in self.elements.values() if element.name == locator.text),
                None,
            )
        return None

    def digest(self) -> str:
        raw = json.dumps(asdict(self.state), sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()[:16]


def execute_shadow(
    workflow: WorkflowSpec,
    *,
    variant: str,
    simulate_approval: bool = True,
) -> ShadowRun:
    twin = SyntheticLiveOpsTwin(variant)
    steps: list[StepExecution] = []
    failures: list[ShadowFailure] = []
    saw_approval = False

    for step in workflow.steps:
        if step.action == ActionKind.NAVIGATE:
            steps.append(StepExecution(step_id=step.id, status="pass", detail="Synthetic route opened."))
            continue

        element = twin.resolve(step.locator)
        if element is None:
            failure = ShadowFailure(
                code="target_not_found",
                step_id=step.id,
                message=f"Could not resolve target in {variant} with locator {step.locator}.",
                evidence={"variant": variant, "locator": step.locator.model_dump() if step.locator else None},
            )
            failures.append(failure)
            steps.append(StepExecution(step_id=step.id, status="fail", detail=failure.message))
            break

        resolved = f"{element.role}:{element.name} ({element.selector})"
        if step.action in {ActionKind.INPUT, ActionKind.SELECT, ActionKind.UPLOAD}:
            apply_value(twin.state, element.key, step.value)
            steps.append(
                StepExecution(
                    step_id=step.id,
                    status="pass",
                    detail=f"Applied staged value to {element.key}.",
                    resolved_target=resolved,
                )
            )
            continue

        if step.action == ActionKind.PREVIEW:
            errors = validate_publish(twin.state)
            # Preview is allowed before the preview_required predicate itself is set.
            errors = [item for item in errors if item != "preview_required"]
            if errors:
                failure = ShadowFailure(
                    code="preview_contract_failed",
                    step_id=step.id,
                    message="Preview contract rejected staged configuration: " + ", ".join(errors),
                    evidence={"errors": errors},
                )
                failures.append(failure)
                steps.append(
                    StepExecution(step_id=step.id, status="fail", detail=failure.message, resolved_target=resolved)
                )
                break
            twin.state.previewed = True
            steps.append(
                StepExecution(
                    step_id=step.id,
                    status="pass",
                    detail="Preview contract passed in synthetic twin.",
                    resolved_target=resolved,
                )
            )
            continue

        if step.action == ActionKind.PUBLISH:
            errors = validate_publish(twin.state)
            if errors:
                failure = ShadowFailure(
                    code="publish_contract_failed",
                    step_id=step.id,
                    message="Publish contract rejected staged configuration: " + ", ".join(errors),
                    evidence={"errors": errors},
                )
                failures.append(failure)
                steps.append(
                    StepExecution(step_id=step.id, status="fail", detail=failure.message, resolved_target=resolved)
                )
                break
            if step.approval_required:
                saw_approval = True
                if not simulate_approval:
                    steps.append(
                        StepExecution(
                            step_id=step.id,
                            status="approval_required",
                            detail="External publish is blocked until a human approval token exists.",
                            resolved_target=resolved,
                        )
                    )
                    break
            twin.state.published = True
            steps.append(
                StepExecution(
                    step_id=step.id,
                    status="pass",
                    detail=(
                        "Publish side effect simulated only after an approval boundary."
                        if step.approval_required
                        else "Publish side effect simulated."
                    ),
                    resolved_target=resolved,
                )
            )
            continue

        steps.append(
            StepExecution(
                step_id=step.id,
                status="pass",
                detail="No-op action completed.",
                resolved_target=resolved,
            )
        )

    if failures:
        status = "fail"
    elif saw_approval and not simulate_approval:
        status = "approval_required"
    else:
        status = "pass"
    return ShadowRun(
        variant=variant,
        workflow_version=workflow.version,
        status=status,
        steps=steps,
        failures=failures,
        state_digest=twin.digest(),
    )
