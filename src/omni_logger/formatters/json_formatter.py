import datetime
import json
import logging
import uuid

from omni_logger.config.logger_config import get_setting

# List of built-in attributes of log records to include
LOG_RECORD_BUILTIN_ATTRS = [
    "args",  # Log arguments
    "asctime",  # Log time
    "created",  # Time when log was created
    "exc_info",  # Exception information
    "exc_text",  # Exception text
    "filename",  # Filename of the source of the log
    "funcName",  # Function name of the log origin
    "levelname",  # Log level (INFO, DEBUG, etc.)
    "levelno",  # Log level number
    "lineno",  # Line number in source file
    "module",  # Module where the log originated
    "msecs",  # Milliseconds part of the log time
    "message",  # Log message
    "msg",  # Original log message object
    "name",  # Logger name
    "pathname",  # Full path to source file
    "process",  # Process ID
    "processName",  # Process name
    "relativeCreated",  # Time since logger start
    "stack_info",  # Stack information
    "thread",  # Thread ID
    "threadName",  # Thread name
    "taskName",  # Task name if used with async functions
]


class JSONFormatter(logging.Formatter):
    """
    A custom logging formatter that outputs log records as JSON objects.

    This formatter converts log records into JSON format, with customizable field mappings.
    Additional log attributes can be selectively included or excluded based on settings.

    Parameters:
        fmt_keys (dict[str, str], optional): A dictionary mapping output JSON keys
            to log record attribute names. Default is None, which uses standard fields.
    """

    def __init__(self, *, fmt_keys: dict[str, str] | None = None):
        """
        Initializes JSONFormatter with optional custom field mappings.

        Parameters:
            fmt_keys (dict[str, str], optional): Dictionary mapping JSON keys
                to log record attributes. Default is an empty dictionary.
        """
        super().__init__()
        self.fmt_keys = fmt_keys if fmt_keys is not None else {}

    def format(self, record: logging.LogRecord) -> str:
        """
        Converts a log record into a JSON-formatted string.

        Parameters:
            record (logging.LogRecord): The log record to format.

        Returns:
            str: A JSON-formatted log message.
        """
        # Prepare a dictionary of log fields and convert it to a JSON string
        message = self._prepare_log_dict(record)
        return json.dumps(message, default=str)

    def _prepare_log_dict(self, record: logging.LogRecord):
        """
        Prepares a dictionary representation of a log record for JSON formatting.

        Adds standard fields like message and timestamp, includes exception
        and stack information if present, and processes custom mappings from fmt_keys.

        Parameters:
            record (logging.LogRecord): The log record to process.

        Returns:
            dict: A dictionary representing the log record for JSON output.
        """

        # Define always-included fields such as message and timestamp
        always_fields = {
            "record_id": str(uuid.uuid4()),
            "message": record.getMessage(),
            "timestamp": datetime.datetime.fromtimestamp(
                record.created, tz=datetime.timezone.utc
            ).isoformat(),
        }

        # Center log information by setting custom line number, module, and function name attributes
        record.lineno = getattr(record, "line", record.lineno)
        record.module = getattr(record, "mod", record.module)
        record.funcName = getattr(record, "function_name", record.funcName)

        # Include exception info if present
        if record.exc_info is not None:
            always_fields["exc_info"] = self.formatException(record.exc_info)

        # Include stack trace info if present
        if record.stack_info is not None:
            always_fields["stack_info"] = self.formatStack(record.stack_info)

        # Map custom fields using fmt_keys, falling back to log record attributes if necessary
        message = {
            key: (
                msg_val
                if (msg_val := always_fields.pop(val, None)) is not None
                else getattr(record, val)
            )
            for key, val in self.fmt_keys.items()
        }
        message.update(always_fields)

        # Add remaining log record attributes unless excluded by settings
        for key, val in record.__dict__.items():
            if key in get_setting("logger_config.log_record_extra_unneeded_attrs"):
                continue  # Skip unneeded extra attributes
            if key not in LOG_RECORD_BUILTIN_ATTRS:
                message[key] = val  # Add custom attributes to the message

        return message
