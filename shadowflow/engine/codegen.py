from __future__ import annotations

import hashlib
import json

from shadowflow.models import ActionKind, GeneratedArtifact, SemanticLocator, WorkflowSpec


def generate_playwright(workflow: WorkflowSpec) -> GeneratedArtifact:
    lines = [
        "import { test, expect } from '@playwright/test';",
        "",
        "async function requireHumanApproval(action: string): Promise<void> {",
        "  const token = process.env.SHADOWFLOW_APPROVAL_TOKEN;",
        "  if (!token) throw new Error(`Human approval required before: ${action}`);",
        "}",
        "",
        "test('compiled live-ops workflow', async ({ page }) => {",
    ]
    for step in workflow.steps:
        lines.append(f"  // {step.id}: {step.intent}")
        if step.action == ActionKind.NAVIGATE:
            lines.append(f"  await page.goto({json.dumps(str(step.value))});")
            continue
        locator = _locator_expr(step.locator)
        if step.approval_required:
            lines.append(f"  await requireHumanApproval({json.dumps(step.intent)});")
        if step.action == ActionKind.INPUT:
            lines.append(f"  await {locator}.fill({json.dumps(str(step.value), ensure_ascii=False)});")
        elif step.action == ActionKind.SELECT:
            value = json.dumps(step.value, ensure_ascii=False)
            lines.append(f"  await {locator}.selectOption({value});")
        elif step.action == ActionKind.UPLOAD:
            lines.append(f"  await {locator}.setInputFiles({json.dumps(str(step.value))});")
        elif step.action in {ActionKind.CLICK, ActionKind.PREVIEW, ActionKind.PUBLISH}:
            lines.append(f"  await {locator}.click();")
        if step.action == ActionKind.PREVIEW:
            lines.append("  await expect(page.getByText('Preview ready')).toBeVisible();")
    lines.append("});")
    content = "\n".join(lines) + "\n"
    return GeneratedArtifact(
        name="generated/liveops-workflow.spec.ts",
        language="typescript",
        content=content,
        sha256=hashlib.sha256(content.encode("utf-8")).hexdigest(),
    )


def _locator_expr(locator: SemanticLocator | None) -> str:
    if locator is None:
        return "page.locator('body')"
    if locator.strategy == "role_name" and locator.role and locator.name:
        return f"page.getByRole({json.dumps(locator.role)}, {{ name: {json.dumps(locator.name)} }})"
    if locator.strategy == "label" and locator.label:
        return f"page.getByLabel({json.dumps(locator.label)})"
    if locator.strategy == "text" and locator.text:
        return f"page.getByText({json.dumps(locator.text)})"
    if locator.selector:
        return f"page.locator({json.dumps(locator.selector)})"
    return "page.locator('body')"
