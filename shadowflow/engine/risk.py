from __future__ import annotations

from shadowflow.models import ActionKind, RiskDecision, SideEffect, WorkflowSpec


def classify_workflow(workflow: WorkflowSpec) -> list[RiskDecision]:
    decisions: list[RiskDecision] = []
    for step in workflow.steps:
        if step.action == ActionKind.PUBLISH:
            effect = SideEffect.EXTERNAL_WRITE
            approval = True
            reason = "Publishing changes player-visible state; shadow validation may simulate it, but live execution needs a human approval token."
        elif step.action in {ActionKind.INPUT, ActionKind.SELECT, ActionKind.UPLOAD}:
            effect = SideEffect.INTERNAL_WRITE
            approval = False
            reason = "Step mutates draft workflow state but is reversible inside the synthetic workspace."
        elif step.action == ActionKind.PREVIEW:
            effect = SideEffect.READ
            approval = False
            reason = "Preview reads the staged configuration without publishing it."
        else:
            effect = SideEffect.NONE
            approval = False
            reason = "No durable external side effect."
        decisions.append(
            RiskDecision(
                step_id=step.id,
                side_effect=effect,
                approval_required=approval,
                reason=reason,
            )
        )
    return decisions


def apply_risk_policy(workflow: WorkflowSpec) -> WorkflowSpec:
    decisions = {item.step_id: item for item in classify_workflow(workflow)}
    steps = []
    for step in workflow.steps:
        decision = decisions[step.id]
        steps.append(
            step.model_copy(
                update={
                    "side_effect": decision.side_effect,
                    "approval_required": decision.approval_required,
                }
            )
        )
    return workflow.model_copy(update={"steps": steps})
