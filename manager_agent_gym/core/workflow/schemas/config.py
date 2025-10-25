"""Configuration schemas for output directories and simulation settings."""

from pathlib import Path
from pydantic import BaseModel, Field
from datetime import datetime
from manager_agent_gym.core.common.logging import logger


class OutputConfig(BaseModel):
    """Configuration for all simulation output directories."""

    # Base output directory - all other dirs will be created relative to this
    base_output_dir: Path = Field(
        default=Path("./simulation_outputs"),
        description="Base directory for all simulation outputs",
    )

    # Specific output subdirectories
    timestep_dir: Path | None = Field(
        default=None,
        description="Directory for timestep execution logs (default: base_output_dir/timestep_data)",
    )

    workflow_dir: Path | None = Field(
        default=None,
        description="Directory for workflow summaries (default: base_output_dir/workflow_outputs)",
    )

    evaluation_dir: Path | None = Field(
        default=None,
        description="Directory for evaluation results (default: base_output_dir/evaluation_outputs)",
    )

    execution_logs_dir: Path | None = Field(
        default=None,
        description="Directory for detailed execution logs (default: base_output_dir/execution_logs)",
    )

    # Run-specific settings
    create_run_subdirectory: bool = Field(
        default=True,
        description="Whether to create a timestamped subdirectory for each run",
    )

    run_id: str | None = Field(
        default=None, description="Custom run identifier (default: timestamp)"
    )

    def model_post_init(self, __context) -> None:
        """Set default subdirectories if not provided."""
        if self.run_id is None:
            self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Set base directory for this run
        if self.create_run_subdirectory:
            run_base = self.base_output_dir / f"run_{self.run_id}"
        else:
            run_base = self.base_output_dir

        # Set default subdirectories
        if self.timestep_dir is None:
            self.timestep_dir = run_base / "timestep_data"

        if self.workflow_dir is None:
            self.workflow_dir = run_base / "workflow_outputs"

        if self.evaluation_dir is None:
            self.evaluation_dir = run_base / "evaluation_outputs"

        if self.execution_logs_dir is None:
            self.execution_logs_dir = run_base / "execution_logs"

    def ensure_directories_exist(self) -> None:
        """Create all configured output directories."""
        directories = [
            self.base_output_dir,
            self.timestep_dir,
            self.workflow_dir,
            self.evaluation_dir,
            self.execution_logs_dir,
        ]

        for directory in directories:
            if directory is not None:
                directory.mkdir(parents=True, exist_ok=True)

    def get_timestep_file_path(self, timestep: int) -> Path:
        """Get the file path for a specific timestep."""
        filename = f"timestep_{timestep:04d}.json"
        if self.timestep_dir is None:
            raise ValueError("timestep_dir is not configured")
        return self.timestep_dir / filename

    def get_final_metrics_path(self) -> Path:
        """Get the file path for final metrics."""
        if self.timestep_dir is None:
            raise ValueError("timestep_dir is not configured")
        return self.timestep_dir / "final_metrics.json"

    def get_workflow_summary_path(self, timestamp: str | None = None) -> Path:
        """Get the file path for workflow summary."""
        if timestamp is None:
            timestamp = self.run_id
        filename = f"workflow_execution_{timestamp}.json"
        if self.workflow_dir is None:
            raise ValueError("workflow_dir is not configured")
        return self.workflow_dir / filename

    def get_evaluation_results_path(self, timestamp: str | None = None) -> Path:
        """Get the file path for evaluation results."""
        if timestamp is None:
            timestamp = self.run_id
        filename = f"evaluation_results_{timestamp}.json"
        if self.evaluation_dir is None:
            raise ValueError("evaluation_dir is not configured")
        return self.evaluation_dir / filename

    def get_llm_evaluation_details_path(self, timestamp: str | None = None) -> Path:
        """Get the file path for LLM evaluation details."""
        if timestamp is None:
            timestamp = self.run_id
        filename = f"llm_evaluation_details_{timestamp}.json"
        if self.evaluation_dir is None:
            raise ValueError("evaluation_dir is not configured")
        return self.evaluation_dir / filename

    def get_rubrics_dir(self) -> Path:
        """Get directory for rubric definitions."""
        if self.evaluation_dir is None:
            raise ValueError("evaluation_dir is not configured")
        return self.evaluation_dir / "rubrics"

    def get_worker_outputs_dir(self) -> Path:
        """Get directory for preserved worker outputs."""
        if self.evaluation_dir is None:
            raise ValueError("evaluation_dir is not configured")
        return self.evaluation_dir / "worker_outputs"

    def get_calibration_dir(self) -> Path:
        """Get directory for calibration data."""
        if self.evaluation_dir is None:
            raise ValueError("evaluation_dir is not configured")
        return self.evaluation_dir / "calibration_data"
    
    @property
    def base_dir(self) -> Path:
        """Get the base directory for this run (for relative path calculations)."""
        if self.create_run_subdirectory:
            return self.base_output_dir / f"run_{self.run_id}"
        return self.base_output_dir


class SimulationConfig(BaseModel):
    """Complete configuration for a simulation run."""

    # Output configuration
    output: OutputConfig = Field(default_factory=OutputConfig)

    # Execution parameters
    max_timesteps: int = Field(
        default=100, description="Maximum number of timesteps to run"
    )
    simulation_timeout_seconds: int = Field(
        default=600, description="Maximum simulation runtime"
    )

    # Preference dynamics settings
    preference_change_rate: float = Field(
        default=0.15, description="Rate of preference changes per timestep"
    )
    preference_drift_magnitude: float = Field(
        default=0.1, description="Magnitude of gradual preference changes"
    )
    preference_shock_magnitude: float = Field(
        default=0.3, description="Magnitude of sudden preference changes"
    )

    def prepare_simulation(self) -> None:
        """Prepare the simulation environment by creating directories."""
        self.output.ensure_directories_exist()
        logger.info(
            "Simulation outputs will be saved to: %s", self.output.base_output_dir
        )
        if self.output.create_run_subdirectory:
            logger.info("Run ID: %s", self.output.run_id)
