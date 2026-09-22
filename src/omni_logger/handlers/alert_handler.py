import logging

import requests

from omni_logger import OmniLogger
from omni_logger.config.logger_config import get_setting


class AlertHandler(logging.Handler):
    """
    A custom logging handler that sends alert notifications for log messages with WARNING level or higher.

    This handler checks if it is enabled in settings (`logger_config.handlers.AlertHandler.enabled`).
    If enabled, it sends log messages with severity WARNING, ERROR, or CRITICAL to an external notification
    system via a POST request. The chrono courier's host and API key are configurable in settings.
    """

    def emit(self, record: logging.LogRecord) -> None:
        """
        Sends an alert notification for log records with severity WARNING or higher.

        Checks if the handler is enabled in settings. If enabled, formats the log record and sends
        it to an external chrono courier via a POST request.

        Parameters:
            record (logging.LogRecord): The log record to be processed and potentially sent as an alert.
        """
        # Only process logs if handler is enabled and record severity is WARNING or higher
        if (
            get_setting("logger_config.handlers.AlertHandler.enabled")
            and record.levelno >= logging.WARNING
        ):
            # Format the log message and the email subject to prepare for sending
            log_entry = self.format(record)

            try:
                # Send a POST request to the chrono courier with alert details
                _ = requests.post(
                    f"http://{get_setting('logger_config.handlers.AlertHandler.chrono_courier_host')}/alert",
                    data={
                        "api-key": get_setting(
                            "logger_config.handlers.AlertHandler.chrono_courier_api_key"
                        ),
                        "subject": f"Alert: {record.levelname} in '{record.module}' (line {record.lineno}) at {record.asctime} - '{record.message[:50]}'",
                        "content": log_entry,
                        "log_type": record.levelname,
                    },
                    timeout=10,
                )
            except Exception as e:
                # Log a message if the alert POST request fails
                OmniLogger.force_print(
                    f"POST request (alert) to the chrono courier failed with exception:({e})"
                )
