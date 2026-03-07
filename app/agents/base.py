#Base agent class shared by all specialised agents.

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar
from loguru import logger


from app.agents.exceptions import AgentValidationError
from app.agents.schemas import AgentResultMetadata, AgentResultSchema, AgentStatus


InputT=TypeVar("InputT")
OutputT=TypeVar("OutputT")


class AgentResult:
    #Lightweight result object returned by every agent execution.

    def __init__(
        self,
        status: AgentStatus,
        data: dict[str, Any] | None = None,
        error: str | None = None,
        metadata: dict[str, Any] | None = None,
        agent_name: str = "unknown",
    ) -> None:
        self.status = status
        self.data: dict[str, Any] = data or {}
        self.error = error
        self.metadata: dict[str, Any] = metadata or {}
        self.agent_name = agent_name
        self.timestamp = datetime.now(tz=timezone.utc)

    def is_success(self) -> bool:
        return self.status == AgentStatus.SUCCESS


    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }

    def to_schema(self) -> AgentResultSchema:
        return AgentResultSchema(
            status=self.status,
            data=self.data,
            error=self.error,
            metadata=AgentResultMetadata(
                agent_name=self.agent_name,
                **self.metadata,
            ),
            timestamp=self.timestamp,
        )


#Base agent

class BaseAgent(ABC, Generic[InputT, OutputT]):
    """Abstract base for all agents.

    Subclass contract:
    1. Call ``super().__init__(name, version)`` in ``__init__``.
    2. Override ``execute()`` with the core business logic.
    3. Optionally override ``validate_and_parse_input()`` to parse raw dicts
       into typed Pydantic models before ``execute()`` is called.
    """

    def __init__(self, name: str, version: str = "1.0.0") -> None:
        self.name = name
        self.version = version
        # Bind agent context to every log record from this instance.
        self.logger = logger.bind(agent=name, version=version)
    
    # Abstract interface
    @abstractmethod
    async def execute(self, input_data: InputT) -> AgentResult:
        """Implement the agent's primary task.

        Args:
            input_data: Already-validated input (produced by
                ``validate_and_parse_input``).

        Returns:
            ``AgentResult`` with appropriate status and payload.
        """

    #Public entry point
    async def run(self, input_data: Any) -> AgentResult:
        
        start = time.perf_counter()

        try:
            self._log_start(input_data)
            validated = await self.validate_and_parse_input(input_data)
            result = await self.execute(validated)

        except AgentValidationError as exc:
            self._log_error(exc)
            return AgentResult(
                status=AgentStatus.FAILED,
                error=f"Validation error: {exc}",
                agent_name=self.name,
            )
        except Exception as exc:  # noqa: BLE001
            self._log_error(exc)
            return AgentResult(
                status=AgentStatus.FAILED,
                error=f"Execution error: {exc}",
                agent_name=self.name,
            )
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1_000
            

        result.metadata["execution_time_ms"] =elapsed_ms
        result.metadata["version"] =self.version
        result.agent_name =self.name

        if result.is_success():
            self._log_success(result)
        else:
            self._log_error(Exception(result.error or "Unknown error"))

        return result

    async def validate_and_parse_input(self, input_data: Any) -> InputT:
        """Parse and validate raw input before ``execute()`` is called.

        The default implementation passes *input_data* through unchanged.
        Subclasses should override this to parse dicts into typed Pydantic
        models and raise ``AgentValidationError`` on failure.

        Raises:
            AgentValidationError: If the input fails validation.
        """
        return input_data  # type: ignore[return-value]


    def create_success_result(
        self,
        data: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> AgentResult:
        

        return AgentResult(
            status=AgentStatus.SUCCESS,
            data=data,
            metadata=metadata or {},
            agent_name=self.name,
        )

    def create_failure_result(
        self,
        error: str,
        metadata: dict[str, Any] | None = None,
    ) -> AgentResult:
        """Convenience factory for failed results."""
        return AgentResult(
            status=AgentStatus.FAILED,
            error=error,
            metadata=metadata or {},
            agent_name=self.name,
        )



    def _log_start(self, input_data: Any) -> None:
        keys = list(input_data.keys()) if isinstance(input_data, dict) else type(input_data).__name__
        self.logger.info(f"Starting execution | input_keys={keys}")

    def _log_success(self, result: AgentResult) -> None:
        ms = result.metadata.get("execution_time_ms", 0)
        self.logger.info(f"Completed successfully | elapsed={ms:.2f}ms")

    def _log_error(self, exc: Exception) -> None:
        self.logger.error(f"Failed | error={exc}")
        self.logger.exception(exc)
    log_start = _log_start
    log_success = _log_success
    log_error = _log_error