#custom exceptions for all of our agents, in the system

class AgentException(Exception):
    def __init__(self, message: str, agent_name: str | None = None)->None:
        self.message = message
        self.agent_name = agent_name
        super().__init__(message)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(agent={self.agent_name!r}, message={self.message!r})"

class AgentValidationError(AgentException):
    pass

class AgentExecutionError(AgentException):
    pass

class JobFetcherError(AgentException):
    pass

class ProjectMatcherError(AgentException):
    pass

class ResumeGeneratorError(AgentException):
    pass

class CoverLetterWriterError(AgentException):
    pass


#WORFLOW LEVEL EXCEPTIONS
class WorkflowError(Exception):
    def __init__(self, message: str, step: str | None = None)->None:
        self.message = message
        self.step = step
        super().__init__(message)

    def __repr__(self) -> str:
        return f"WorkflowError(step={self.step!r}, message={self.message!r})"



#DATA SOURCE EXCEPTIONS
class DataSourceError(WorkflowError):
    pass

class CSVParsingError(DataSourceError):
    pass

class LinkedInScrapingError(DataSourceError):
    pass

class GoogleSheetsError(DataSourceError):
    pass