import datetime
import inspect
import json
import logging
import logging.config
import os
import pathlib
import sys
import threading
import time
import traceback
from functools import lru_cache
from logging import Logger
from typing import Optional

from omni_logger.config.logger_config import (
    LOGGING_CONFIG,
    get_setting,
    logger_settings,
)
from omni_logger.handlers.queue_handler import listener_busy


@lru_cache(maxsize=1)
def get_lock():
    # A threading lock to ensure thread-safe operations for logger settings and configurations
    return threading.Lock()


class OmniLogger:
    """
    A singleton logger class that manages centralized logging configuration and settings.

    OmniLogger serves as a centralized logger with configurable attributes and settings for logging
    across the application. It includes configuration options for log file path, stdout and stderr
    redirection, and a lock mechanism to prevent concurrent access to certain methods.

    Attributes:
        logger (Logger): The main logger instance used throughout the application.
        logger_name (str): The name assigned to the logger.
        config (dict): The current logging configuration.
        log_dir_name (str): The file path for log output, if specified.
        _stdout (IO): Original stdout stream.
        _stderr (IO): Original stderr stream.
        _instance (OmniLogger): The singleton instance of the OmniLogger.
        _log_file_locked (bool): Indicates whether the log file is locked (True) or unlocked (False).
    """

    logger: Logger
    logger_name: str
    config: dict
    log_dir_name: Optional[str] = None
    _stdout = None
    _stderr = None
    _instance = None
    _log_file_locked = False

    # Initialize the base logger settings and handle instance creation
    def __new__(
        cls,
        logger_name: Optional[str] = None,
        log_dir_name: Optional[str] = None,
        lock_log_file: bool = False,
        *args,
        **kwargs,
    ):
        # Set the logger name for identification
        if logger_name is None:
            cls.logger_name = get_setting("logger_config.default_logger_name")
        else:
            cls.logger_name = logger_name

        # Check if an instance of the logger already exists
        if cls._instance is None:
            # Get a new logger instance with the configured name
            cls.logger = logging.getLogger(cls.logger_name)

            # Apply configuration setting (from the JSON confing file) to the logger
            cls.add_dict_config()

            # Store references to the system's original stdout and stderr
            cls._stdout = sys.stdout
            cls._stderr = sys.stderr

            # Redirect system stdout and stderr to the logger for capturing all output
            sys.excepthook = cls.log_uncaught_exception
            sys.stdout = cls.PrintLogger()
            sys.stderr = cls.StderrToLogger()

            # Start a background thread to periodically refresh the logger's configuration
            cls.start_refresh_thread()

            # Create and return the singleton logger instance
            cls._instance = super().__new__(cls, *args, **kwargs)

        # Update the log file path if a custom directory name is provided
        if log_dir_name is not None:
            if cls._log_file_locked:  # Check if the log file change is locked
                # Notify that the log file path cannot be changed due to the lock
                cls.force_print(
                    f"Log file update is locked. Current log directory remains: {cls.log_dir_name}"
                )
            else:
                # Update the log directory name and path
                cls.update_log_file_path(log_dir_name)
                cls.force_print(f"Log file path updated to: {cls.log_dir_name}")

            # Lock the log file if specified and not already locked
            if lock_log_file and not cls._log_file_locked:
                # Lock the log file and notify the user
                cls.force_print(
                    f"Log file changes are now locked. Locked directory: {cls.log_dir_name}"
                )
                cls._log_file_locked = True

        return cls._instance

    @classmethod
    def remove_log_file_lock(cls):
        """
        Unlocks the log file.

        This class method clears the internal lock flag `_log_file_locked`, allowing
        changes to the log file again. It also prints a message to indicate that
        logging is now unlocked.
        """
        # Set the internal flag to indicate the log file is no longer locked
        cls._log_file_locked = False

        # Notify that log file changes are now allowed
        cls.force_print("Log file changes are now unlocked")

    @classmethod
    def log_uncaught_exception(cls, exctype, value, tb):
        """
        Logs any uncaught exceptions to the logger with details about the module, line number, and function where it occurred.

        Parameters:
            exctype (Type[Exception]): The class of the exception raised.
            value (Exception): The instance of the exception raised.
            tb (traceback): The traceback object associated with the exception.
        """

        try:
            # Extract the traceback details from the traceback object (tb) to analyze the exception context
            trace = traceback.extract_tb(tb)
            # Retrieve the last frame in the traceback, representing the location where the exception was raised
            last_frame = trace[-1]
            # Determine the file name from the last frame to identify the module where the exception occurred
            file_path = pathlib.Path(last_frame.filename)
            line = last_frame.lineno
            mod = file_path.stem
            function_name = last_frame.name
            # file_path=last_frame.
        except:
            # In case of extraction failure, return an empty result
            file_path = ""
            line = 0
            mod = ""
            function_name = ""

        # Log the exception at the 'fatal' level with detailed context:
        # - The module name (file name)
        # - Line number where the exception was raised
        # - Function name in which the exception occurred
        # Additional exception details are formatted and included for comprehensive logging output.
        cls.logger.fatal(
            f"Uncaught exception in {file_path}: {''.join(traceback.format_exception(exctype, value, tb))}",
            extra={
                "line": line,  # Line number in the source code where the exception was raised
                "mod": mod,  # Module name derived from the file name (without extension)
                "function_name": function_name,  # Function name within which the exception was raised
                "path": file_path,
            },
        )

    @classmethod
    def get_logger(cls, logger_name: Optional[str] = None):
        """
        Retrieves and returns a logger instance for the class.

        Returns:
            logging.Logger: A configured logger instance associated with the class.
        """
        if logger_name is None:
            logger_name = cls.logger_name

        return logging.getLogger(logger_name)

    @classmethod
    def start_refresh_thread(cls):
        """
        Starts a background thread to refresh settings at regular intervals.

        This method initiates a separate daemon thread to periodically refresh logger settings
        based on configuration values. The thread will check whether periodic refreshing is enabled
        and will use the configured interval to determine how often to refresh settings.
        """

        def refresh_periodically():
            """
            Periodically refreshes settings as long as the refresh flag is enabled.

            Continuously checks the 'refresh_enabled' setting to determine if periodic
            refreshing should continue. Waits for a specified interval before calling the
            `refresh_settings` method to update settings, providing up-to-date configurations
            for the logger.
            """
            while get_setting("logger_config.refresh_enabled"):
                # Pause execution for the specified refresh interval
                time.sleep(get_setting("logger_config.refresh_interval"))

                # Refresh settings to apply any updates from the configuration
                cls.refresh_settings()

        # Create and start a daemon thread for periodic refreshing
        refresh_thread = threading.Thread(target=refresh_periodically, daemon=True)
        refresh_thread.start()

    @classmethod
    def refresh_settings(cls):
        """
        Reloads configuration settings and clears all cache to apply updated configurations.

        This method ensures thread safety by checking if the listener handler is busy
        and locking threads during the refresh to prevent conflicts. It reloads dynaconf
        settings, clears cached settings, and reapplies the configuration to the logger.
        """

        # Wait until the listener is free to avoid conflicts during settings refresh
        while listener_busy.is_set():  # Check if listener is busy
            cls.force_print(f"Logger is busy, waiting...")
            time.sleep(0.5)  # Retry after a short interval to avoid excessive CPU usage

        # Acquire a lock to ensure exclusive access to settings during the refresh process
        with get_lock():
            # Reload dynaconf settings to apply any configuration changes
            logger_settings.reload()

            # Clear the LRU cache for settings retrieval
            get_setting.cache_clear()

            # Reapply the updated configuration to the logger
            cls.add_dict_config()

            # Print a confirmation message to indicate the refresh is complete
            cls.force_print("Settings refreshed!")

    @classmethod
    def add_dict_config(cls):
        """
        Loads and applies the logger configuration form a JSON file

        Retrieves the path of the logger configuration file and loads it as a JSON object.
        Updates the configuration for specific handlers, such as maintaining the original system
        stdout stream and a custom log file path if provided.
        Finally, applies the updated configuration to the logger.
        """
        # Retrieve the logger configuration file path specified in the settings
        config_file_path = pathlib.Path(
            os.getenv("OMNILOGGER_ROOT_PATH_FOR_DYNACONF", ""),  # type: ignore
            get_setting("logger_config.logger_config_file"),
        )

        # add the configuration from a custom configuration file if provided
        if config_file_path.exists():
            # Open the configuration file and load its content as a JSON object
            with open(config_file_path) as f_in:
                # Save the JSON configuration as a class attribute for future access
                cls.config = json.load(f_in)

        # Load the default configuration
        else:
            cls.config = LOGGING_CONFIG

        # If an original system stdout stream is saved, use it for the console handler
        if cls._stdout is not None:
            cls.config["handlers"]["console"]["stream"] = cls._stdout

        # If a custom log file path is specified, set it for the file handler
        if cls.log_dir_name is not None:
            cls.config["handlers"]["file_json"]["filename"] = cls.log_dir_name

        # Apply the updated logger configuration using dictConfig
        logging.config.dictConfig(cls.config)

    @classmethod
    def update_log_file_path(cls, path):
        """
        Updates the log file path with a structured directory hierarchy based on the current date.

        The log file path is structured to include subdirectories for the year and month,
        and the log file name includes the day. This method also creates the necessary directories
        if they do not exist, sets the new log file path, and reconfigures the logger to use it.

        Parameters:
            path (str): The root path or prefix to be used for the log file directory structure.
        """

        # Retrieve the root directory path for log files from settings
        log_dir = pathlib.Path(get_setting("logger_config.logs_directory"))

        # Append the provided path and a year-month subdirectory based on the current date
        log_dir = log_dir.joinpath(
            path,
            datetime.datetime.now(datetime.UTC).strftime("%Y-%m"),
        )

        # Create the logs directory if it doesn't exist, including parent directories
        log_dir.mkdir(parents=True, exist_ok=True)

        # Define the log file path with a year-month-day file name structure
        log_file = log_dir.joinpath(
            f"{path}-{datetime.datetime.now(datetime.UTC).strftime('%Y-%m-%d')}.log.jsonl",
        )

        # Update the class attribute for the log file path and apply the new configuration
        cls.log_dir_name = log_file  # type: ignore
        cls.add_dict_config()

    @staticmethod
    def force_print(msg: str):
        """
        Prints a message to the appropriate output stream with a custom prefix.

        Ensures the message is always treated as a string, adds a newline, and prints
        it either to a specified stdout (`OmniLogger._stdout`) or the system's default `sys.stdout`.
        If neither stream is available, returns `None`.

        Parameters:
            msg (str): The message to print. It will be cast to a string if not already.
        """

        # Ensure the message is treated as a string
        msg = str(msg)

        # Add a newline character to the end of the message for proper formatting in output
        msg += "\n"

        # Check if a custom stdout stream (`OmniLogger._stdout`) is available
        if OmniLogger._stdout:
            # Print to the custom stdout stream with a specific prefix and flush the output
            res = OmniLogger._stdout.write("[Logger.stdout]> " + msg)
            OmniLogger._stdout.flush()
            return res
        # If no custom stdout is set, fall back to printing to `sys.stdout`
        elif sys.stdout is not Logger:
            # Print to system stdout with a prefix and flush the output
            res = sys.stdout.write("[sys.stdout]> " + msg)
            sys.stdout.flush()
            return res
        # Return None if neither custom stdout nor sys.stdout is available for output
        return None

    @staticmethod
    def disable_logger_external_output():
        """
        A simple function to disable the AlertHandler when needed.
        """
        logger_settings.logger_config.handlers.AlertHandler.enabled = False

    class StderrToLogger:
        """
        A custom stream handler that redirects `stderr` output to a logger.
        This class is particularly useful for capturing and logging error messages
        and stack trace information in a structured format.
        """

        def __init__(self):
            """
            Initializes the StderrToLogger instance with an empty buffer to collect messages.
            """
            self.buffer = []

        def write(self, message):
            """
            Writes messages to the buffer, ensuring only non-empty lines are stored.

            Parameters:
            - message (str): The message to log.

            Only collects non-empty lines, and if a line has less than 2 characters,
            it appends it to the previous message in the buffer, ensuring continuity.
            """
            # Only store non-empty lines in the buffer
            if message.strip():
                if len(message.strip()) < 2:
                    # Append short lines to the last buffered message for continuity
                    self.buffer[-1] = self.buffer[-1] + message.rstrip()
                else:
                    # Store full messages as separate entries in the buffer
                    self.buffer.append(message.rstrip())

        def flush(self):
            """
            Flushes the buffer to the logger as a single batch message.

            The flush method inspects the call stack to retrieve contextual information
            about where the error originated (module name, function name, and line number).
            It then logs the collected buffer as a single error message, including this
            contextual data.

            After logging, it clears the buffer for future messages.
            """
            # Retrieve the call stack to gather information about the calling location
            try:
                stack = inspect.trace()
                caller_frame = stack[
                    -1
                ]  # Get the frame of the function that called flush
                function_name = caller_frame.function
                module = inspect.getmodule(caller_frame[0])
                lineno = inspect.getlineno(caller_frame[0])
                # Determine the module name, defaulting to "Terminal" if undefined
                file_path = getattr(module, "__file__", "Terminal")  # type: ignore
                module_name = os.path.splitext(os.path.basename(file_path))[0]  # type: ignore

            except:
                # In case of extraction failure, return an empty result
                function_name = ""
                module = ""
                lineno = 0
                file_path = ""
                module_name = ""

            if self.buffer:  # Log only if there is content in the buffer
                # Log the entire buffered message batch as a single error entry
                OmniLogger.logger.error(
                    msg="\n".join(f"{line}" for line in self.buffer),
                    extra={
                        "line": lineno,
                        "mod": module_name,
                        "function_name": function_name,
                        "path": file_path,
                    },
                )
                # Clear the buffer after logging to prepare for new messages
                self.buffer.clear()

    class PrintLogger:
        """
        A logger that directs print statements to appropriate logging levels based on message content.

        This class inspects the message content to determine the severity level (e.g., DEBUG, INFO, WARNING)
        and routes the message to the corresponding logger method in `OmniLogger`. It uses keywords
        in the message to classify the log type and attaches contextual information (module, line number, function).
        """

        def write(self, message):
            """
            Routes a print message to the appropriate logging level based on its content.

            Analyzes the beginning of the message to determine the log level, such as CRITICAL, ERROR, WARNING,
            INFO, or DEBUG. Adds extra contextual information about the caller (module, line number, and function).

            Parameters:
                message (str): The message to log.
            """
            # Inspect the call stack to gather information about the calling location
            try:
                stack = inspect.stack()
                caller_frame = stack[1]  # Get the caller's stack frame
                function_name = caller_frame.function
                module = inspect.getmodule(caller_frame[0])
                lineno = inspect.getlineno(caller_frame[0])
                file_path = getattr(module, "__file__", "Terminal")  # type: ignore
                module_name = os.path.splitext(os.path.basename(file_path))[0]  # type: ignore
            except:
                # In case of extraction failure, return an empty result
                function_name = ""
                module = ""
                lineno = 0
                file_path = ""
                module_name = ""

            # Strip whitespace and prepare the message for analysis
            message = message.strip()
            message_lower = message.lower()

            # Skip empty or very short messages
            if not message:
                return

            # Determine logging level based on message content
            if (
                message_lower.startswith("critical")
                or message_lower.startswith("fatal")
                or message_lower.startswith("traceback")
                or message_lower.startswith("exception")
            ):
                # Log as CRITICAL
                OmniLogger.logger.critical(
                    message,
                    extra={
                        "line": lineno,
                        "mod": module_name,
                        "function_name": function_name,
                        "path": file_path,
                    },
                )
            elif message_lower.startswith("err"):
                # Log as ERROR
                OmniLogger.logger.error(
                    message,
                    extra={
                        "line": lineno,
                        "mod": module_name,
                        "function_name": function_name,
                        "path": file_path,
                    },
                )
            elif message_lower.startswith("warn"):
                # Log as WARNING
                OmniLogger.logger.warning(
                    message,
                    extra={
                        "line": lineno,
                        "mod": module_name,
                        "function_name": function_name,
                        "path": file_path,
                    },
                )
            elif message_lower.startswith("info"):
                # Log as INFO
                OmniLogger.logger.info(
                    message,
                    extra={
                        "line": lineno,
                        "mod": module_name,
                        "function_name": function_name,
                        "path": file_path,
                    },
                )
            elif message_lower.startswith("debug"):
                # Log as DEBUG
                OmniLogger.logger.debug(
                    message,
                    extra={
                        "line": lineno,
                        "mod": module_name,
                        "function_name": function_name,
                        "path": file_path,
                    },
                )
            else:
                # Default to DEBUG for unclassified messages
                OmniLogger.logger.debug(
                    message,
                    extra={
                        "line": lineno,
                        "mod": module_name,
                        "function_name": function_name,
                        "path": file_path,
                    },
                )

        def flush(self):
            """Flush method for compatibility with file-like interfaces; no action needed."""
            pass


def main():
    """
    Demonstrates basic usage of the OmniLogger.
    This function shows how to initialize the logger,
    redirect print statements, log messages at various levels,
    and capture uncaught exceptions.
    """

    # Initialize the OmniLogger and retrieve the logger instance
    # Optionally, set a custom log file path by passing `log_dir_name` to OmniLogger, e.g., OmniLogger(log_dir_name="mylog").
    # Additionally, you can lock the custom log file by setting `lock_log_file` to True, e.g, OmniLogger(log_dir_name="mylog",lock_log_file=True).
    logger = OmniLogger().get_logger()
    # Redirect print statements to the logger.
    # The logger will interpret print messages based on prefixes (e.g., "debug", "info", "warning").
    # Messages without a specific prefix default to "debug".
    print("info test message from print")
    print("warn test message from print")
    print("test message from print")

    # Log messages directly by calling the logger instance at various log levels
    logger.debug("Debug level test message")
    logger.info("Info level test message")
    logger.warning("Warning level test message")
    logger.error("Error level test message")
    logger.critical("Critical level test message")

    # Trigger an uncaught exception to demonstrate exception handling via the logger
    raise ValueError("This is an uncaught exception example")


if __name__ == "__main__":
    main()
