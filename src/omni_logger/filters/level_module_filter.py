import logging
import logging.config
import logging.handlers

from omni_logger.config.logger_config import get_setting


class LevelModuleFilter(logging.Filter):
    """
    A logging filter that enforces specific log levels for configured modules.

    This filter checks the settings to determine if module-specific logging levels
    are enabled (`logger_config.filters.level_module.enabled`). When enabled,
    only log messages that meet or exceed the specified logging level for each
    module (as defined in `logger_config.filters.level_module.module_name_level`)
    will be logged.
    """

    def filter(self, record: logging.LogRecord) -> bool:

        # Set the record's module attribute to a custom 'mod' attribute if it exists,
        # otherwise, keep the original module name. This allows custom module names for logging.
        record.module = getattr(record, "mod", record.module)

        # Retrieve the logging levels configuration for each module
        modules_levels = get_setting(
            "logger_config.filters.level_module.module_name_level"
        )

        # Determine if the log record should be allowed:
        # - If the module-level filter is disabled, allow the log
        # - If the module is not in the configured modules_levels, allow the log
        # - If the record's logging level is equal to or above the module's threshold level, allow the log
        return (
            not get_setting("logger_config.filters.level_module.enabled")
            or record.module not in modules_levels
            or record.levelno
            >= getattr(
                logging, modules_levels.get(record.module, "").upper(), logging.DEBUG
            )
        )
