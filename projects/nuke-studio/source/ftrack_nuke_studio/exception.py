# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import sys
import traceback


class Error(Exception):
    """ftrack specific error."""

    default_message = "Unspecified error occurred."

    def __init__(self, message=None, details=None):
        """Initialise exception with *message*.

        If *message* is None, the class 'default_message' will be used.

        *details* should be a mapping of extra information that can be used in
        the message and also to provide more context.

        """
        if message is None:
            message = self.default_message

        self.message = message
        self.details = details
        if self.details is None:
            self.details = {}

        self.traceback = traceback.format_exc()

    def __str__(self):
        """Return string representation."""
        keys = {}
        for key, value in self.details.items():
            if isinstance(value, str):
                value = value.encode(sys.getfilesystemencoding())
            keys[key] = value

        return str(self.message.format(**keys))


class ValidationError(Error):
    """Raise when an validation error occurs."""

    default_message = "Validation error."


class PermissionDeniedError(Error):
    """Raise when permission is denied."""

    default_message = "Permission denied."


class TemplateError(Error):
    """Raise when an template error occurs."""

    default_message = "Template error"


# === New Refactored Exceptions ===


class FtrackProcessorError(Exception):
    """Base exception for processor errors."""

    pass


class FtrackValidationError(FtrackProcessorError):
    """Raised when validation fails."""

    def __init__(self, errors=None, missing_types=None, duplicates=None):
        """Initialize with validation results.

        Args:
            errors: Dict of {processor: {attribute: valid_values}}
            missing_types: List of missing asset type names
            duplicates: List of (component_name, task) tuples
        """
        self.errors = errors or {}
        self.missing_types = missing_types or []
        self.duplicates = duplicates or []

        msg = self._format_message()
        super().__init__(msg)

    def _format_message(self):
        """Format user-friendly error message."""
        parts = []

        if self.errors:
            parts.append(f"Invalid settings: {len(self.errors)} processor(s)")

        if self.missing_types:
            parts.append(
                f"Missing asset types: {', '.join(self.missing_types)}"
            )

        if self.duplicates:
            names = [name for name, _ in self.duplicates]
            parts.append(f"Duplicate components: {', '.join(names)}")

        return "; ".join(parts) if parts else "Validation failed"


class FtrackEntityCreationError(FtrackProcessorError):
    """Raised when entity creation fails."""

    def __init__(self, entity_type, name, parent=None, original_error=None):
        self.entity_type = entity_type
        self.name = name
        self.parent = parent
        self.original_error = original_error

        msg = f"Failed to create {entity_type} '{name}'"
        if parent:
            msg += f" under {parent}"
        if original_error:
            msg += f": {original_error}"

        super().__init__(msg)


class FtrackPublishingError(FtrackProcessorError):
    """Raised when publishing fails."""

    def __init__(self, component_name, path, original_error=None):
        self.component_name = component_name
        self.path = path
        self.original_error = original_error

        msg = f"Failed to publish component '{component_name}' at {path}"
        if original_error:
            msg += f": {original_error}"

        super().__init__(msg)


class FtrackLocationError(FtrackProcessorError):
    """Raised when location is invalid."""

    def __init__(self, location_name, reason=None):
        self.location_name = location_name
        self.reason = reason

        msg = f"Invalid location '{location_name}'"
        if reason:
            msg += f": {reason}"

        super().__init__(msg)


class FtrackTemplateError(FtrackProcessorError):
    """Raised when template matching fails."""

    def __init__(self, item_name, template_expression):
        self.item_name = item_name
        self.template_expression = template_expression

        msg = f"Item '{item_name}' does not match template: {template_expression}"
        super().__init__(msg)
