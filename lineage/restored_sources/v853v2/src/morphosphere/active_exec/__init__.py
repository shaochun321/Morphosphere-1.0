"""Active execution layer — sole active runtime path."""

from .pipeline import run_pipeline, PipelineResult

__all__ = ["run_pipeline", "PipelineResult"]
