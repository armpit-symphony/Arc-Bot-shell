"""Loopback-only Ollama executor supplied to the public LIMA harness."""

from __future__ import annotations

from collections.abc import Mapping
import json
import math
import os
import re
import socket
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_OLLAMA_MODEL = "qwen2.5:7b"
DEFAULT_OLLAMA_TIMEOUT_SECONDS = 60.0
LOOPBACK_OLLAMA_EXECUTOR_KIND = "loopback_ollama"
LOOPBACK_OLLAMA_EXECUTOR_NAME = "arc_loopback_ollama_executor"
MAX_PROMPT_CHARACTERS = 2_000
MAX_OUTPUT_CHARACTERS = 32_000
MAX_RESPONSE_BYTES = 1_048_576

_SENSITIVE_ASSIGNMENT = re.compile(
    r"(?i)\b(api[_ -]?key|authorization|bearer|credential|password|secret|token)"
    r"\b\s*[:=]\s*[^\s,;]+"
)


class OllamaExecutorValidationError(ValueError):
    """Raised before network when LIMA executor input is not safe to invoke."""


class _NoRedirectHandler(HTTPRedirectHandler):
    """Turn every redirect into an HTTPError instead of following it."""

    def redirect_request(  # type: ignore[override]
        self,
        req: Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        del req, fp, code, msg, headers, newurl
        return None


def normalize_loopback_ollama_url(value: str) -> str:
    """Validate and normalize an HTTP 127.0.0.1/localhost base URL."""

    if not isinstance(value, str) or not value:
        raise OllamaExecutorValidationError("ollama_url_required")
    if value != value.strip():
        raise OllamaExecutorValidationError("ollama_url_whitespace_not_allowed")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as exc:
        raise OllamaExecutorValidationError("ollama_url_port_invalid") from exc
    if parsed.scheme != "http":
        raise OllamaExecutorValidationError("ollama_url_requires_http")
    if parsed.username is not None or parsed.password is not None:
        raise OllamaExecutorValidationError("ollama_url_credentials_not_allowed")
    if parsed.hostname not in {"127.0.0.1", "localhost"}:
        raise OllamaExecutorValidationError("ollama_url_requires_loopback_host")
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        raise OllamaExecutorValidationError("ollama_url_must_be_a_base_url")
    if port is None or not 1 <= port <= 65535:
        raise OllamaExecutorValidationError("ollama_url_port_required")
    return f"http://{parsed.hostname}:{port}"


def resolve_ollama_model(
    value: str | None = None,
    *,
    environ: Mapping[str, str] | None = None,
) -> str:
    """Resolve one explicit model without fallback to another model/provider."""

    env = os.environ if environ is None else environ
    candidate = value if value is not None else env.get("ARC_OLLAMA_MODEL")
    model = DEFAULT_OLLAMA_MODEL if candidate is None else candidate.strip()
    if not model or any(character.isspace() for character in model):
        raise OllamaExecutorValidationError("ollama_model_invalid")
    return model


def resolve_ollama_timeout_seconds(
    *,
    environ: Mapping[str, str] | None = None,
) -> float:
    """Resolve a finite positive timeout bounded to five minutes."""

    env = os.environ if environ is None else environ
    raw_value = env.get("ARC_OLLAMA_TIMEOUT_SECONDS")
    if raw_value is None or not raw_value.strip():
        return DEFAULT_OLLAMA_TIMEOUT_SECONDS
    try:
        timeout = float(raw_value)
    except ValueError as exc:
        raise OllamaExecutorValidationError("ollama_timeout_invalid") from exc
    if not math.isfinite(timeout) or not 0 < timeout <= 300:
        raise OllamaExecutorValidationError("ollama_timeout_invalid")
    return timeout


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise OllamaExecutorValidationError(f"{field_name}_required")
    return value.strip()


def _validate_runtime_input(runtime_input: Mapping[str, Any]) -> tuple[str, str]:
    if not isinstance(runtime_input, Mapping):
        raise OllamaExecutorValidationError("runtime_input_must_be_a_mapping")
    if runtime_input.get("runtime_consumer") != "arc_bot_shell":
        raise OllamaExecutorValidationError("runtime_consumer_not_allowed")
    if runtime_input.get("requested_action") != "arc.local_model_preview":
        raise OllamaExecutorValidationError("requested_action_not_allowed")
    if runtime_input.get("executor_kind") != LOOPBACK_OLLAMA_EXECUTOR_KIND:
        raise OllamaExecutorValidationError("executor_kind_not_allowed")
    if runtime_input.get("network_scope") != "loopback_only":
        raise OllamaExecutorValidationError("network_scope_not_allowed")
    if runtime_input.get("credentials_used") is not False:
        raise OllamaExecutorValidationError("credentials_not_allowed")
    if runtime_input.get("external_side_effects") is not False:
        raise OllamaExecutorValidationError("external_side_effects_not_allowed")

    decision = runtime_input.get("guardian_decision")
    if not isinstance(decision, Mapping):
        raise OllamaExecutorValidationError("guardian_decision_required")
    decision_id = _required_text(
        runtime_input.get("guardian_decision_id"),
        "guardian_decision_id",
    )
    if decision.get("decision_id") != decision_id:
        raise OllamaExecutorValidationError("guardian_decision_id_mismatch")
    if str(decision.get("status", "")).strip().lower() not in {
        "allow",
        "allowed",
        "approved",
    }:
        raise OllamaExecutorValidationError("guardian_allow_required")
    if decision.get("allowed") is not True:
        raise OllamaExecutorValidationError("guardian_allow_required")
    if decision.get("requires_approval") is not False:
        raise OllamaExecutorValidationError("guardian_approval_pending")

    raw_endpoint = runtime_input.get("endpoint")
    if not isinstance(raw_endpoint, str) or not raw_endpoint:
        raise OllamaExecutorValidationError("endpoint_required")
    endpoint = normalize_loopback_ollama_url(raw_endpoint)
    model = resolve_ollama_model(
        _required_text(runtime_input.get("model"), "model")
    )
    normalized_request = runtime_input.get("normalized_request")
    if not isinstance(normalized_request, Mapping) or not normalized_request:
        raise OllamaExecutorValidationError("normalized_request_required")
    return endpoint, model


def _sanitize_prompt_text(value: Any) -> str:
    text = " ".join(str(value or "").split())
    text = _SENSITIVE_ASSIGNMENT.sub(r"\1=[REDACTED]", text)
    return text[:900]


def build_local_preview_prompt(runtime_input: Mapping[str, Any]) -> str:
    """Build a bounded operator-facing prompt from LIMA-normalized metadata."""

    normalized_request = runtime_input.get("normalized_request")
    if not isinstance(normalized_request, Mapping):
        raise OllamaExecutorValidationError("normalized_request_required")
    summary = _sanitize_prompt_text(normalized_request.get("summary"))
    payload_summary = _sanitize_prompt_text(
        normalized_request.get("payload_summary")
    )
    action_id = _sanitize_prompt_text(normalized_request.get("action_id"))
    task_ref = _sanitize_prompt_text(normalized_request.get("task_ref"))
    prompt = (
        "Arc local preview. Produce a concise operator-facing draft only. "
        "Do not send messages, change files, use tools, access credentials, or "
        "take any external action. No external action should be taken. "
        "This is a local model preview; do not mention or imply cloud-provider use. "
        "Do not claim an action was completed.\n"
        f"Action ID: {action_id or 'local-preview'}\n"
        f"Task reference: {task_ref or 'local-task'}\n"
        f"Request summary: {summary or 'Prepare a safe local preview.'}\n"
        f"Preview guidance: {payload_summary or 'Draft only; no external action.'}"
    )
    return prompt[:MAX_PROMPT_CHARACTERS]


def _open_ollama_request(request: Request, timeout_seconds: float) -> Any:
    opener = build_opener(_NoRedirectHandler())
    return opener.open(request, timeout=timeout_seconds)


def _base_result(
    *,
    endpoint: str,
    model: str,
    duration_ms: int,
    status: str,
    output_text: str = "",
    error_category: str | None = None,
    error_message: str | None = None,
) -> dict[str, Any]:
    return {
        "provider": "ollama",
        "model": model,
        "output_text": output_text,
        "endpoint": endpoint,
        "network_called": True,
        "network_scope": "loopback_only",
        "ollama_called": True,
        "credentials_used": False,
        "external_side_effects": False,
        "duration_ms": max(0, duration_ms),
        "status": status,
        "error_category": error_category,
        "error_message": error_message,
    }


def _controlled_failure(
    *,
    endpoint: str,
    model: str,
    started_at: float,
    category: str,
    message: str,
) -> dict[str, Any]:
    duration_ms = int(max(0.0, time.perf_counter() - started_at) * 1000)
    return _base_result(
        endpoint=endpoint,
        model=model,
        duration_ms=duration_ms,
        status="unavailable",
        error_category=category,
        error_message=message[:512].replace("\r", " ").replace("\n", " "),
    )


def _http_error_category(exc: HTTPError) -> tuple[str, str]:
    if 300 <= exc.code < 400:
        return "executor_error", "Ollama redirect rejected"
    body = b""
    try:
        body = exc.read(MAX_RESPONSE_BYTES)
    except OSError:
        body = b""
    detail = body.decode("utf-8", errors="replace").lower()
    if exc.code == 404 and ("model" in detail or "not found" in detail):
        return "model_unavailable", "Configured Ollama model unavailable"
    if exc.code >= 500:
        return "service_unavailable", "Ollama service unavailable"
    return "executor_error", f"Ollama request failed with HTTP {exc.code}"


def execute_loopback_ollama(
    runtime_input: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Invoke one non-streaming localhost Ollama preview after LIMA validation."""

    endpoint, model = _validate_runtime_input(runtime_input)
    timeout_seconds = resolve_ollama_timeout_seconds()
    prompt = build_local_preview_prompt(runtime_input)
    payload = {"model": model, "prompt": prompt, "stream": False}
    http_request = Request(
        f"{endpoint}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        method="POST",
    )
    started_at = time.perf_counter()
    try:
        with _open_ollama_request(http_request, timeout_seconds) as response:
            status_code = int(getattr(response, "status", 0))
            if not 200 <= status_code < 300:
                return _controlled_failure(
                    endpoint=endpoint,
                    model=model,
                    started_at=started_at,
                    category="executor_error",
                    message=f"Ollama request failed with HTTP {status_code}",
                )
            raw_body = response.read(MAX_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        category, message = _http_error_category(exc)
        return _controlled_failure(
            endpoint=endpoint,
            model=model,
            started_at=started_at,
            category=category,
            message=message,
        )
    except (TimeoutError, socket.timeout):
        return _controlled_failure(
            endpoint=endpoint,
            model=model,
            started_at=started_at,
            category="timeout",
            message="Ollama request timed out",
        )
    except (URLError, ConnectionError, OSError):
        return _controlled_failure(
            endpoint=endpoint,
            model=model,
            started_at=started_at,
            category="service_unavailable",
            message="Ollama service unavailable",
        )
    except Exception:
        return _controlled_failure(
            endpoint=endpoint,
            model=model,
            started_at=started_at,
            category="executor_error",
            message="Ollama executor failed",
        )

    if len(raw_body) > MAX_RESPONSE_BYTES:
        return _controlled_failure(
            endpoint=endpoint,
            model=model,
            started_at=started_at,
            category="malformed_response",
            message="Ollama response exceeded the safe size limit",
        )
    try:
        response_payload = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return _controlled_failure(
            endpoint=endpoint,
            model=model,
            started_at=started_at,
            category="malformed_response",
            message="Ollama returned malformed JSON",
        )
    if not isinstance(response_payload, Mapping):
        return _controlled_failure(
            endpoint=endpoint,
            model=model,
            started_at=started_at,
            category="malformed_response",
            message="Ollama returned an invalid response object",
        )
    output_text = response_payload.get("response")
    if not isinstance(output_text, str) or not output_text.strip():
        return _controlled_failure(
            endpoint=endpoint,
            model=model,
            started_at=started_at,
            category="malformed_response",
            message="Ollama response text was missing",
        )
    duration_ms = int(max(0.0, time.perf_counter() - started_at) * 1000)
    return _base_result(
        endpoint=endpoint,
        model=model,
        duration_ms=duration_ms,
        status="completed",
        output_text=output_text.strip()[:MAX_OUTPUT_CHARACTERS],
    )


__all__ = [
    "DEFAULT_OLLAMA_MODEL",
    "DEFAULT_OLLAMA_TIMEOUT_SECONDS",
    "DEFAULT_OLLAMA_URL",
    "LOOPBACK_OLLAMA_EXECUTOR_KIND",
    "LOOPBACK_OLLAMA_EXECUTOR_NAME",
    "OllamaExecutorValidationError",
    "build_local_preview_prompt",
    "execute_loopback_ollama",
    "normalize_loopback_ollama_url",
    "resolve_ollama_model",
    "resolve_ollama_timeout_seconds",
]
