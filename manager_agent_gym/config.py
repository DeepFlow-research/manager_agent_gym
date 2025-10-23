import os
from pathlib import Path
from datetime import datetime

from pydantic_settings import BaseSettings

from manager_agent_gym.core.workflow.schemas.config import (
    OutputConfig,
    SimulationConfig,
)
from manager_agent_gym.core.common.logging import logger


class Settings(BaseSettings):
    ENV: str = "local"
    OPENAI_API_KEY: str = "na"
    ANTHROPIC_API_KEY: str = "na"
    EXA_API_KEY: str = "na"
    COHERE_API_KEY: str = "na"
    E2B_API_KEY: str = "na"

    # Default simulation configuration
    default_output_dir: str = "./simulation_outputs"

    # Default max timesteps if not overridden by environment
    default_max_timesteps: int = 5

    def create_simulation_config(
        self,
        base_output_dir: str | Path | None = None,
        run_id: str | None = None,
        **kwargs,
    ) -> SimulationConfig:
        """Create a simulation configuration with custom output settings."""
        output_config = OutputConfig(
            base_output_dir=Path(base_output_dir or self.default_output_dir),
            run_id=run_id,
            **kwargs,
        )
        return SimulationConfig(output=output_config)

    def resolve_max_timesteps(self, fallback: int | None = None) -> int:
        """Resolve max timesteps from env MAG_MAX_TIMESTEPS or provided fallback/default."""
        env_val = os.environ.get("MAG_MAX_TIMESTEPS")
        if env_val:
            try:
                return int(env_val)
            except ValueError:
                pass
        return int(fallback or self.default_max_timesteps)

    def build_labeled_output_config(
        self,
        label: str,
        base_output_dir: str | Path | None = None,
        create_run_subdirectory: bool = True,
        run_suffix: str | None = None,
        label_as_subdir: bool = True,
    ) -> OutputConfig:
        """Create OutputConfig where run_id includes a label (e.g., script name).

        - base_output_dir can be overridden by MAG_OUTPUT_DIR env var.
        - If label_as_subdir is True, the base directory becomes base/label and run_id will
          be the timestamp or provided run_suffix. Otherwise, run_id encodes the label.
        """
        base_dir = Path(
            os.environ.get("MAG_OUTPUT_DIR")
            or base_output_dir
            or self.default_output_dir
        )
        # Place label as a subdirectory for better organization if requested
        if label_as_subdir:
            base_dir = base_dir / label
        timestamp = run_suffix or datetime.now().strftime("%Y%m%d_%H%M%S")
        run_id = timestamp if label_as_subdir else f"{label}_{timestamp}"
        return OutputConfig(
            base_output_dir=base_dir,
            run_id=run_id,
            create_run_subdirectory=create_run_subdirectory,
        )

    class Config:
        env_file = Path(__file__).resolve().parents[1] / ".env"


settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings


if settings.OPENAI_API_KEY != "na":
    os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
if settings.ANTHROPIC_API_KEY != "na":
    os.environ["ANTHROPIC_API_KEY"] = settings.ANTHROPIC_API_KEY
if settings.EXA_API_KEY != "na":
    os.environ["EXA_API_KEY"] = settings.EXA_API_KEY
if settings.COHERE_API_KEY != "na":
    os.environ["COHERE_API_KEY"] = settings.COHERE_API_KEY
if settings.E2B_API_KEY != "na":
    os.environ["E2B_API_KEY"] = settings.E2B_API_KEY

# Soft validation: warn on missing env vars instead of erroring hard
if settings.ENV == "local":
    missing = [k for k, v in settings.model_dump().items() if v in ["na", None]]
    if missing:
        logger.warning(
            "Optional env vars missing; features may be disabled: %s",
            ", ".join(missing),
        )
