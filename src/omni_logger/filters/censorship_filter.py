import logging
import logging.config
import logging.handlers

from omni_logger.config.logger_config import get_setting


class CensorshipFilter(logging.Filter):
    """
    A logging filter that censors specified words in log messages when enabled.

    This filter checks if censorship is enabled in the settings (`logger_config.filters.censorship.enabled`).
    If enabled, it replaces each specified word in `logger_config.filters.censorship.words_to_censor`
    with asterisks (*) in the log message.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Censors specific words in the log message if censorship is enabled.

        Parameters:
            record (logging.LogRecord): The log record to filter and potentially modify.

        Returns:
            bool: True to ensure the log record is processed by subsequent filters and handlers.
        """
        # Check if censorship is enabled in settings
        if get_setting("logger_config.filters.censorship.enabled"):
            # Loop through each word specified in the censorship list
            for word in get_setting("logger_config.filters.censorship.words_to_censor"):
                # Replace occurrences of the word in the message with asterisks (*)
                if word in record.msg:
                    record.msg = record.msg.replace(word, "*" * len(word))

        # Return True to allow the log record to be processed further
        return True
