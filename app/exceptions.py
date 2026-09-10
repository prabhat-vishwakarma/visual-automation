"""Domain exceptions for the visual automation system."""


class AutomationError(Exception):
    """Base class for all domain errors."""


class ConfigError(AutomationError):
    pass


class AuthenticationTimeout(AutomationError):
    pass


class TargetNotFound(AutomationError):
    pass


class ScreenshotError(AutomationError):
    pass


class OCRRecognitionError(AutomationError):
    pass


class OCRValidationError(AutomationError):
    pass


class InputNotFound(AutomationError):
    pass


class SubmissionError(AutomationError):
    pass


class WorkflowVerificationError(AutomationError):
    pass


class BrowserSessionError(AutomationError):
    pass