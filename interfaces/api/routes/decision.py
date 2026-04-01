from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request

from contracts.decision_input import DecisionInput
from contracts.decision_output import DecisionOutput
from observability import begin_trace, log_error, log_info, write_trace
from pipeline.orchestrator import DecisionService
from rendering import DecisionMessageFormatter, RenderedDecision, RenderedDecisionEnvelope


router = APIRouter(prefix="/decision", tags=["decision"])


@router.post("/evaluate", response_model=DecisionOutput)
def evaluate_decision(request: DecisionInput, http_request: Request) -> DecisionOutput:
    trace_id = begin_trace(
        trace_id=http_request.headers.get("X-Trace-Id"),
        name="decision_evaluate",
        metadata={"path": str(http_request.url.path)},
    )
    try:
        service = DecisionService()
        result = service.evaluate(request.model_dump(mode="json"))
        write_trace(trace_id=trace_id, event="decision_evaluated", payload={"decision_output": result})
        log_info(
            "decision evaluated",
            trace_id=trace_id,
            path=str(http_request.url.path),
            decision=result["decision"]["label"],
        )
        return DecisionOutput(**result)
    except Exception as exc:
        write_trace(trace_id=trace_id, event="decision_evaluate_failed", payload={"error": str(exc)})
        log_error("decision evaluate failed", trace_id=trace_id, path=str(http_request.url.path), error=str(exc))
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/debug/layers")
def debug_layers(decision_input: DecisionInput, http_request: Request) -> dict[str, Any]:
    trace_id = begin_trace(
        trace_id=http_request.headers.get("X-Trace-Id"),
        name="decision_debug_layers",
        metadata={"path": str(http_request.url.path)},
    )
    try:
        service = DecisionService()
        result = service.debug_from_decision_input(decision_input.model_dump(mode="json"))
        write_trace(trace_id=trace_id, event="decision_debug_layers_completed", payload={"layers": result})
        log_info("decision debug layers completed", trace_id=trace_id, path=str(http_request.url.path))
        return result
    except Exception as exc:
        write_trace(trace_id=trace_id, event="decision_debug_layers_failed", payload={"error": str(exc)})
        log_error("decision debug layers failed", trace_id=trace_id, path=str(http_request.url.path), error=str(exc))
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/render", response_model=RenderedDecision)
def render_decision(decision_output: DecisionOutput, http_request: Request) -> RenderedDecision:
    trace_id = begin_trace(
        trace_id=http_request.headers.get("X-Trace-Id"),
        name="decision_render",
        metadata={"path": str(http_request.url.path)},
    )
    try:
        rendered = DecisionMessageFormatter().render(decision_output.model_dump(mode="json"))
        write_trace(trace_id=trace_id, event="decision_rendered", payload={"rendered": rendered.model_dump()})
        log_info("decision rendered", trace_id=trace_id, path=str(http_request.url.path))
        return rendered
    except Exception as exc:
        write_trace(trace_id=trace_id, event="decision_render_failed", payload={"error": str(exc)})
        log_error("decision render failed", trace_id=trace_id, path=str(http_request.url.path), error=str(exc))
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/evaluate-rendered", response_model=RenderedDecisionEnvelope)
def evaluate_and_render(request: DecisionInput, http_request: Request) -> RenderedDecisionEnvelope:
    trace_id = begin_trace(
        trace_id=http_request.headers.get("X-Trace-Id"),
        name="decision_evaluate_rendered",
        metadata={"path": str(http_request.url.path)},
    )
    try:
        service = DecisionService()
        structured = DecisionOutput(**service.evaluate(request.model_dump(mode="json")))
        rendered = DecisionMessageFormatter().render(structured)
        write_trace(
            trace_id=trace_id,
            event="decision_evaluated_rendered",
            payload={"structured": structured.model_dump(), "rendered": rendered.model_dump()},
        )
        log_info(
            "decision evaluated and rendered",
            trace_id=trace_id,
            path=str(http_request.url.path),
            decision=structured.decision.label.value,
        )
        return RenderedDecisionEnvelope(structured=structured, rendered=rendered)
    except Exception as exc:
        write_trace(trace_id=trace_id, event="decision_evaluate_rendered_failed", payload={"error": str(exc)})
        log_error("decision evaluate rendered failed", trace_id=trace_id, path=str(http_request.url.path), error=str(exc))
        raise HTTPException(status_code=503, detail=str(exc)) from exc
