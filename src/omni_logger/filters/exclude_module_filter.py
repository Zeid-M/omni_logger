import logging
import logging.config
import logging.handlers

from omni_logger.config.logger_config import get_setting


class ExcludeModuleFilter(logging.Filter):
    """
    A logging filter that excludes log messages from specified modules when enabled.

    This filter checks if exclusion is enabled in settings (`logger_config.filters.exclude_module.enabled`).
    If enabled, it prevents log messages originating from modules listed in
    `logger_config.filters.exclude_module.excluded_modules` from being logged.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filters out log messages from specific modules if exclusion is enabled.

        Parameters:
            record (logging.LogRecord): The log record to filter.

        Returns:
            bool: True if the log record should be logged, False if it should be excluded.
        """
        # Map record.module to the custom 'mod' attribute if it exists
        record.module = getattr(record, "mod", record.module)

        # Check if module exclusion is enabled in settings
        # If disabled, allow all messages; if enabled, exclude specified modules
        return not get_setting(
            "logger_config.filters.exclude_module.enabled"  # Check if exclusion is disabled
        ) or record.module not in get_setting(
            "logger_config.filters.exclude_module.excluded_modules"  # Exclude messages from specified modules
        )
