import logging
import logging.config
import logging.handlers

from omni_logger.config.logger_config import get_setting


class AllowModuleFilter(logging.Filter):
    """
    A logging filter that only allows log messages from specified modules when enabled.

    This filter checks if module-specific logging is enabled in settings (`logger_config.filters.allowed_module.enabled`).
    If enabled, it allows only log messages originating from modules listed in
    `logger_config.filters.allowed_module.allowed_modules` to be logged.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filters log records to allow only those from specific modules if enabled.

        Parameters:
            record (logging.LogRecord): The log record to filter.

        Returns:
            bool: True if the log record should be logged (originates from an allowed module or filter is disabled),
            False if it should be excluded.
        """
        # Map record.module to the custom 'mod' attribute if it exists
        record.module = getattr(record, "mod", record.module)

        # Check if only specific module logging is enabled in settings
        # If disabled, allow all messages; if enabled, allow only messages from specified modules
        return not get_setting(
            "logger_config.filters.allowed_module.enabled"  # Check if module filtering is disabled
        ) or record.module in get_setting(
            "logger_config.filters.allowed_module.allowed_modules"  # Allow messages only from specified modules
        )
