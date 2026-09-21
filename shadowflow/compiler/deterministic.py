from __future__ import annotations

from shadowflow.compiler.base import WorkflowCompiler
from shadowflow.engine.risk import apply_risk_policy
from shadowflow.models import (
    ActionKind,
    SemanticLocator,
    ShadowFailure,
    TraceBundle,
    WorkflowSpec,
    WorkflowStep,
)


class DeterministicDemoCompiler(WorkflowCompiler):
    name = "deterministic-demo"

    def compile(self, trace: TraceBundle) -> WorkflowSpec:
        steps: list[WorkflowStep] = []
        previous: str | None = None
        for index, event in enumerate(trace.events):
            step_id = f"step-{index + 1:02d}"
            locator = None
            if event.target is not None and event.target.selector:
                # Deliberately mirrors a common recorder failure mode: it trusts the captured CSS selector.
                locator = SemanticLocator(
                    strategy="selector",
                    selector=event.target.selector,
                    confidence=0.71,
                )
            steps.append(
                WorkflowStep(
                    id=step_id,
                    intent=_intent(event.action, event.target.accessible_name if event.target else None),
                    action=event.action,
                    locator=locator,
                    value=event.value,
                    depends_on=[previous] if previous else [],
                    source_event_ids=[event.id],
                )
            )
            previous = step_id
        workflow = WorkflowSpec(
            id=f"workflow-{trace.id}",
            title="Recorded live-ops release",
            purpose="Replay a demonstrated live-ops configuration workflow without trusting brittle DOM selectors.",
            version=1,
            compiler_route=self.name,
            steps=steps,
            warnings=["Initial compile intentionally preserves recorder selectors so shadow drift can challenge them."],
        )
        return apply_risk_policy(workflow)

    def repair(
        self,
        trace: TraceBundle,
        workflow: WorkflowSpec,
        failures: list[ShadowFailure],
    ) -> WorkflowSpec:
        failed_steps = {failure.step_id for failure in failures if failure.step_id}
        event_by_id = {event.id: event for event in trace.events}
        steps: list[WorkflowStep] = []
        for step in workflow.steps:
            if step.id not in failed_steps or not step.source_event_ids:
                steps.append(step)
                continue
            event = event_by_id[step.source_event_ids[0]]
            target = event.target
            if step.action == ActionKind.UPLOAD and target and target.label:
                locator = SemanticLocator(
                    strategy="label",
                    label=target.label,
                    confidence=0.96,
                )
            elif target and target.role and target.accessible_name:
                locator = SemanticLocator(
                    strategy="role_name",
                    role=target.role,
                    name=target.accessible_name,
                    confidence=0.96,
                )
            elif target and target.label:
                locator = SemanticLocator(
                    strategy="label",
                    label=target.label,
                    confidence=0.90,
                )
            else:
                locator = step.locator
            steps.append(step.model_copy(update={"locator": locator}))
        # Drift may expose several selector failures one at a time. Convert every remaining selector
        # backed by recorded semantic evidence, so the second attempt is a coherent repair rather than whack-a-mole.
        repaired: list[WorkflowStep] = []
        for step in steps:
            if step.locator is None or step.locator.strategy != "selector" or not step.source_event_ids:
                repaired.append(step)
                continue
            target = event_by_id[step.source_event_ids[0]].target
            if step.action == ActionKind.UPLOAD and target and target.label:
                repaired.append(
                    step.model_copy(
                        update={
                            "locator": SemanticLocator(
                                strategy="label",
                                label=target.label,
                                confidence=0.96,
                            )
                        }
                    )
                )
            elif target and target.role and target.accessible_name:
                repaired.append(
                    step.model_copy(
                        update={
                            "locator": SemanticLocator(
                                strategy="role_name",
                                role=target.role,
                                name=target.accessible_name,
                                confidence=0.96,
                            )
                        }
                    )
                )
            else:
                repaired.append(step)
        repaired_workflow = workflow.model_copy(
            update={
                "version": workflow.version + 1,
                "steps": repaired,
                "warnings": workflow.warnings
                + ["Repaired selector drift by promoting recorded accessibility semantics to stable locators."],
            }
        )
        return apply_risk_policy(repaired_workflow)


def _intent(action: ActionKind, name: str | None) -> str:
    label = name or "page"
    verbs = {
        ActionKind.NAVIGATE: "Open",
        ActionKind.INPUT: "Set",
        ActionKind.SELECT: "Choose",
        ActionKind.UPLOAD: "Attach",
        ActionKind.CLICK: "Activate",
        ActionKind.PREVIEW: "Preview",
        ActionKind.PUBLISH: "Publish",
    }
    return f"{verbs[action]} {label}"
