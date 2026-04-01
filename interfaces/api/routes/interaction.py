from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from config import get_settings
from contracts.decision_input import DecisionInput
from contracts.environment_schema import ContextEnrichmentPreview, EnvironmentEnrichmentResponse
from observability import begin_trace, log_error, log_info, write_trace
from pipeline.orchestrator import PipelineOrchestrator
from pipeline.intent.schemas import InteractionRequest, InteractionResponse
from pipeline.enrichment.service import EnrichmentService
from pipeline.intent.parser import InteractionService
from pipeline.enrichment.preview import EnrichmentPreviewService


router = APIRouter(prefix="/interaction", tags=["interaction"])


def _trace_id_for(http_request: Request, *, name: str) -> str:
    return begin_trace(
        trace_id=http_request.headers.get("X-Trace-Id"),
        name=name,
        metadata={"path": str(http_request.url.path)},
    )


def _build_interaction(payload: dict) -> dict:
    settings = get_settings()
    return InteractionService(settings=settings).preview(payload)


def _build_environment_state(interaction: dict) -> dict:
    settings = get_settings()
    location = interaction["entry_point"]["location"]
    return EnrichmentService(settings=settings).enrich_with_fallback(
        lat=location["lat"],
        lon=location["lon"],
        intent_recognition=interaction["intent_recognition"],
    )


@router.post("/preview", response_model=InteractionResponse)
def preview_interaction(request: InteractionRequest, http_request: Request) -> InteractionResponse:
    trace_id = _trace_id_for(http_request, name="interaction_preview")
    try:
        result = _build_interaction(request.model_dump())
        write_trace(
            trace_id=trace_id,
            event="interaction_preview_completed",
            payload={
                "entry_point": result["entry_point"],
                "intent_recognition": result["intent_recognition"],
            },
        )
        log_info(
            "interaction preview completed",
            trace_id=trace_id,
            path=str(http_request.url.path),
            activity=result["intent_recognition"]["activity"],
        )
        return InteractionResponse(**result)
    except Exception as exc:
        write_trace(trace_id=trace_id, event="interaction_preview_failed", payload={"error": str(exc)})
        log_error("interaction preview failed", trace_id=trace_id, path=str(http_request.url.path), error=str(exc))
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/enrichment-preview", response_model=ContextEnrichmentPreview)
def preview_enrichment(request: InteractionRequest, http_request: Request) -> ContextEnrichmentPreview:
    trace_id = _trace_id_for(http_request, name="enrichment_preview")
    try:
        interaction = _build_interaction(request.model_dump())
        result = EnrichmentPreviewService().preview(
            entry_point=interaction["entry_point"],
            intent_recognition=interaction["intent_recognition"],
        )
        write_trace(trace_id=trace_id, event="enrichment_preview_completed", payload={"preview": result})
        log_info("enrichment preview completed", trace_id=trace_id, path=str(http_request.url.path), status=result["status"])
        return ContextEnrichmentPreview(**result)
    except Exception as exc:
        write_trace(trace_id=trace_id, event="enrichment_preview_failed", payload={"error": str(exc)})
        log_error("enrichment preview failed", trace_id=trace_id, path=str(http_request.url.path), error=str(exc))
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/enrich", response_model=EnvironmentEnrichmentResponse)
def enrich_interaction(request: InteractionRequest, http_request: Request) -> EnvironmentEnrichmentResponse:
    trace_id = _trace_id_for(http_request, name="enrichment")
    try:
        interaction = _build_interaction(request.model_dump())
        location = interaction["entry_point"]["location"]
        environment_state = _build_environment_state(interaction)
        write_trace(
            trace_id=trace_id,
            event="enrichment_completed",
            payload={"location": location, "environment_state": environment_state},
        )
        log_info("enrichment completed", trace_id=trace_id, path=str(http_request.url.path), location=location)
        return EnvironmentEnrichmentResponse(
            entry_point=interaction["entry_point"],
            intent_recognition=interaction["intent_recognition"],
            environment_state=environment_state,
        )
    except Exception as exc:
        write_trace(trace_id=trace_id, event="enrichment_failed", payload={"error": str(exc)})
        log_error("enrichment failed", trace_id=trace_id, path=str(http_request.url.path), error=str(exc))
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/build-payload", response_model=DecisionInput)
def build_decision_payload(request: InteractionRequest, http_request: Request) -> DecisionInput:
    trace_id = _trace_id_for(http_request, name="decision_payload_builder")
    try:
        interaction = _build_interaction(request.model_dump())
        environment_state = _build_environment_state(interaction)
        decision_input = PipelineOrchestrator().build_decision_input(
            entry_point=interaction["entry_point"],
            intent_recognition=interaction["intent_recognition"],
            environment_state=environment_state,
        )
        write_trace(trace_id=trace_id, event="decision_input_built", payload={"decision_input": decision_input})
        log_info(
            "decision input built",
            trace_id=trace_id,
            path=str(http_request.url.path),
            activity=decision_input["request"]["intent"]["activity"],
        )
        return DecisionInput(**decision_input)
    except Exception as exc:
        write_trace(trace_id=trace_id, event="decision_input_build_failed", payload={"error": str(exc)})
        log_error("decision input build failed", trace_id=trace_id, path=str(http_request.url.path), error=str(exc))
        raise HTTPException(status_code=400, detail=str(exc)) from exc
