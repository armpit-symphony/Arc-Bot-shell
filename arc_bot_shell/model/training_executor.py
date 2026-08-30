"""Guardian-grant-enforced loopback model support for reviewed SOP drafts."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Callable, Mapping
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


LOCAL_MODEL_CAPABILITY = "local_model_preview"
LOCAL_MODEL_ACTION = "arc.local_model_preview"
MAX_PROMPT_CHARS = 8_000
MAX_DRAFT_CHARS = 4_000
MAX_RESPONSE_BYTES = 256 * 1024


class LocalModelExecutionError(RuntimeError):
    """The bounded local-model execution failed closed."""


def _loopback_base_url(value: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise LocalModelExecutionError("local model endpoint is required")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as exc:
        raise LocalModelExecutionError("local model endpoint is malformed") from exc
    if (
        parsed.scheme != "http"
        or (parsed.hostname or "").lower() not in {"127.0.0.1", "localhost"}
        or parsed.username is not None
        or parsed.password is not None
        or port is None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise LocalModelExecutionError(
            "local model endpoint must be an HTTP loopback base URL"
        )
    return value.rstrip("/")


def _required_text(value: Any, name: str, limit: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LocalModelExecutionError(f"{name} is required")
    normalized = value.strip()
    if len(normalized) > limit:
        raise LocalModelExecutionError(f"{name} exceeds {limit} characters")
    return normalized


def _default_transport(url: str, payload: bytes, timeout_seconds: float) -> bytes:
    request = Request(
        url,
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
        if getattr(response, "status", 200) != 200:
            raise LocalModelExecutionError("local model returned a non-success status")
        body = response.read(MAX_RESPONSE_BYTES + 1)
    if len(body) > MAX_RESPONSE_BYTES:
        raise LocalModelExecutionError("local model response exceeded the bounded size")
    return body


@dataclass
class OllamaTrainingDraftExecutor:
    """Execute one local SOP draft only after a bound LIMA execution grant."""

    endpoint: str = "http://127.0.0.1:11434"
    model: str = "qwen2.5:7b"
    operator_opt_in: bool = False
    timeout_seconds: float = 90.0
    transport: Callable[[str, bytes, float], bytes] = _default_transport

    def __post_init__(self) -> None:
        self.endpoint = _loopback_base_url(self.endpoint)
        self.model = _required_text(self.model, "model", 200)
        if any(character.isspace() for character in self.model):
            raise LocalModelExecutionError("model must not contain whitespace")
        if not isinstance(self.operator_opt_in, bool):
            raise LocalModelExecutionError("operator opt-in must be a boolean")
        if not 1 <= float(self.timeout_seconds) <= 300:
            raise LocalModelExecutionError("timeout must be between 1 and 300 seconds")

    def execute(self, *, prompt: str, grant: Any) -> dict[str, Any]:
        """Call loopback Ollama after validating the exact single-use grant."""

        if not self.operator_opt_in:
            raise LocalModelExecutionError("Arc local-model execution opt-in is required")
        prompt_text = _required_text(prompt, "prompt", MAX_PROMPT_CHARS)
        grant_payload: Mapping[str, Any]
        if hasattr(grant, "to_dict"):
            grant_payload = grant.to_dict()
        elif isinstance(grant, Mapping):
            grant_payload = grant
        else:
            raise LocalModelExecutionError("a LIMA execution grant is required")
        required = {
            "execution_allowed": True,
            "requires_operator_opt_in": True,
            "side_effects_allowed": False,
            "granted_capability": LOCAL_MODEL_CAPABILITY,
            "bound_action_type": LOCAL_MODEL_ACTION,
        }
        if any(
            grant_payload.get(key) != expected for key, expected in required.items()
        ):
            raise LocalModelExecutionError(
                "LIMA execution grant is not valid for local-model preview"
            )

        encoded = json.dumps(
            {
                "model": self.model,
                "prompt": prompt_text,
                "stream": False,
                "options": {"temperature": 0.2, "num_predict": 700},
            },
            ensure_ascii=True,
            separators=(",", ":"),
        ).encode("utf-8")
        try:
            raw = self.transport(
                f"{self.endpoint}/api/generate",
                encoded,
                float(self.timeout_seconds),
            )
            response = json.loads(raw)
        except LocalModelExecutionError:
            raise
        except Exception as exc:
            raise LocalModelExecutionError("local model is unavailable") from exc
        draft = _required_text(
            response.get("response") if isinstance(response, Mapping) else None,
            "local model draft",
            MAX_DRAFT_CHARS,
        )
        return {
            "status": "draft_completed",
            "model": self.model,
            "draft": draft,
            "network_scope": "loopback_only",
            "credentials_used": False,
            "external_side_effects": False,
            "grant_id": str(grant_payload.get("grant_id", "")),
            "guardian_decision_id": str(
                grant_payload.get("guardian_decision_id", "")
            ),
        }


__all__ = [
    "LOCAL_MODEL_ACTION",
    "LOCAL_MODEL_CAPABILITY",
    "LocalModelExecutionError",
    "OllamaTrainingDraftExecutor",
]
