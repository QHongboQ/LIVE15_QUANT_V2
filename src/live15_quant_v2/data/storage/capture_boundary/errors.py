"""Explicit fail-closed errors for Capture Boundary inputs."""


class CaptureBoundaryError(ValueError):
    """Base error for an input that cannot become a CaptureFact."""


class UnsupportedCaptureMessageError(CaptureBoundaryError):
    """Raised for unsupported or control-plane messages."""


class CaptureAuthorityError(CaptureBoundaryError):
    """Raised when verified market or reference authority is absent."""


class IncompatibleCaptureInputError(CaptureBoundaryError):
    """Raised when an otherwise supported message conflicts with authority."""
