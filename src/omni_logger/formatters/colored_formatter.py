import logging

from colorama import Back, Fore, Style

from omni_logger.config.logger_config import get_setting


class ColoredFormatter(logging.Formatter):
    """
    A custom logging formatter that applies color and background formatting to log messages
    based on their severity level.

    This formatter applies different foreground and background colors to each log level,
    which are configurable via settings. Additionally, it includes environment information
    in the log record based on environment variables or default values.
    """

    def format(self, record):
        """
        Formats a log record by applying color and background based on severity level
        and adding environment information.

        Parameters:
            record (logging.LogRecord): The log record to format.

        Returns:
            str: The formatted log message with color and environment details.
        """

        # Retrieve color and background settings for the log level, defaulting to reset values
        color = getattr(
            Fore,
            get_setting(
                f"logger_config.formatter.ColoredFormatter.colors.{record.levelname.lower()}"
            ).upper(),
        )

        back_color = getattr(
            Back,
            get_setting(
                f"logger_config.formatter.ColoredFormatter.back_color.{record.levelname.lower()}"
            ).upper(),
        )

        # Center log information by setting custom line number, module, and function name attributes
        record.lineno = getattr(record, "line", record.lineno)
        record.module = getattr(record, "mod", record.module)
        record.funcName = getattr(record, "function_name", record.funcName)

        # Format the log message with the standard formatter and apply color settings
        message = super().format(record)
        return f"{Style.RESET_ALL}{color}{back_color}{message}{Style.RESET_ALL}"
