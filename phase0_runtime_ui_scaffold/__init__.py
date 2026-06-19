"""Phase-0 runtime UI scaffold helpers."""

from .adapter import build_phase0_readonly_projection
from .preview import render_phase0_readonly_projection
from .read_feed import (
    DEFAULT_CONTRACT_PATH,
    DEFAULT_PAYLOAD_PATH,
    ReadFeedContractError,
    ReadFeedGateError,
    ReadFeedPayloadError,
    build_phase1_read_feed_projection,
    build_phase1_read_feed_runtime_projection,
    render_phase1_read_feed_projection,
    run_read_feed_preview,
)
from .runtime_consumer import (
    build_phase1_runtime_ui_consumer_projection,
    run_runtime_consumer_preview,
)

__all__ = [
    "build_phase0_readonly_projection",
    "render_phase0_readonly_projection",
    "DEFAULT_CONTRACT_PATH",
    "DEFAULT_PAYLOAD_PATH",
    "ReadFeedContractError",
    "ReadFeedGateError",
    "ReadFeedPayloadError",
    "build_phase1_read_feed_projection",
    "build_phase1_read_feed_runtime_projection",
    "render_phase1_read_feed_projection",
    "run_read_feed_preview",
    "build_phase1_runtime_ui_consumer_projection",
    "run_runtime_consumer_preview",
]
