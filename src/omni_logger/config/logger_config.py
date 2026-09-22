import os
import pathlib
from functools import lru_cache
from importlib.resources import files

from dynaconf import Dynaconf, Validator
from platformdirs import user_log_dir


def get_log_dir() -> pathlib.Path:
    """
    Creates and returns the log directory for the user, ensuring the directory exists.
    The function retrieves the path of the user-specific log directory using `user_log_dir`

    Returns:
        pathlib.Path: The path to the user log directory.
    """
    log_dir = pathlib.Path(user_log_dir("omni_logger"))
    log_dir.mkdir(exist_ok=True, parents=True)
    return log_dir


def get_log_file():
    """
    Constructs and returns the path to the log file with a `.jsonl` suffix.

    This function appends the filename "log" to the user log directory path
    (retrieved from `get_log_dir()`) and ensures the file has a `.jsonl` suffix.

    Returns:
        pathlib.Path: The full path to the log file with a `.jsonl` extension.
    """
    return get_log_dir().joinpath("log").with_suffix(".jsonl")


# Default logger configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "objects": {"queue": {"class": "queue.Queue", "maxsize": 100000}},
    "formatters": {
        "json": {
            "()": "omni_logger.formatters.json_formatter.JSONFormatter",
            "fmt_keys": {
                "record_id": "record_id",
                "level": "levelname",
                "process": "process",
                "module": "module",
                "function": "funcName",
                "line": "lineno",
                "path": "pathname",
                "thread_name": "threadName",
                "logger": "name",
                "timestamp": "timestamp",
                "message": "message",
            },
        },
        "colored": {
            "()": "omni_logger.formatters.colored_formatter.ColoredFormatter",
            "format": "[%(levelname)-8s|ID:%(process)d|M:%(module)s|F:%(funcName)s|L:%(lineno)4d|T:%(threadName)s] %(asctime)s: %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S%z",
        },
    },
    "filters": {
        "censorship": {"()": "omni_logger.filters.censorship_filter.CensorshipFilter"},
        "throttling": {"()": "omni_logger.filters.throttling_filter.ThrottlingFilter"},
        "exclude_module": {
            "()": "omni_logger.filters.exclude_module_filter.ExcludeModuleFilter"
        },
        "allow_module": {
            "()": "omni_logger.filters.allow_module_filter.AllowModuleFilter"
        },
        "level_module": {
            "()": "omni_logger.filters.level_module_filter.LevelModuleFilter"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "colored",
            "filters": [
                "censorship",
                "throttling",
                "exclude_module",
                "allow_module",
                "level_module",
            ],
            "stream": "ext://sys.stdout",
        },
        "file_json": {
            "class": "logging.FileHandler",
            "level": "DEBUG",
            "formatter": "json",
            "filters": [
                "censorship",
                "throttling",
                "exclude_module",
                "allow_module",
                "level_module",
            ],
            "filename": get_log_file(),
        },
        "queue_handler": {
            "()": "omni_logger.handlers.queue_handler.QueueListenerHandler",
            "handlers": [
                "cfg://handlers.console",
                "cfg://handlers.file_json",
                "cfg://handlers.alert_handler",
            ],
            "queue": "cfg://objects.queue",
        },
        "alert_handler": {
            "()": "omni_logger.handlers.alert_handler.AlertHandler",
            "formatter": "json",
        },
    },
    "loggers": {"root": {"level": "DEBUG", "handlers": ["queue_handler"]}},
}


logger_settings = Dynaconf(
    settings_files=[
        files("omni_logger.config.config_files").joinpath(
            "default_logger_settings.toml"
        ),
        "logger_settings.toml",
    ],
    root_path=os.getenv("OMNILOGGER_ROOT_PATH_FOR_DYNACONF"),
    envvar_prefix="OMNILOGGER",
    environments=True,
    merge_enabled=True,
    default_env="default",
    env="production",
)
logger_settings.validators.register(  # type: ignore
    Validator("logger_config.default_logger_name"),
    Validator("logger_config.logger_config_file"),
    Validator("logger_config.logs_directory"),
    Validator(
        "logger_config.refresh_enabled",
        is_type_of=bool,
    ),
    Validator("logger_config.refresh_interval", gte=1),
    Validator(
        "logger_config.log_record_extra_unneeded_attrs",
    ),
    Validator(
        "logger_config.filters.censorship.enabled",
        is_type_of=bool,
    ),
    Validator(
        "logger_config.filters.censorship.words_to_censor",
    ),
    Validator(
        "logger_config.filters.throttling.enabled",
        is_type_of=bool,
    ),
    Validator(
        "logger_config.filters.throttling.throttle_interval",
        gte=0,
    ),
    Validator(
        "logger_config.filters.exclude_module.enabled",
        is_type_of=bool,
    ),
    Validator("logger_config.filters.exclude_module.excluded_modules"),
    Validator("logger_config.filters.allowed_module.enabled", is_type_of=bool),
    Validator(
        "logger_config.filters.allowed_module.allowed_modules",
    ),
    Validator(
        "logger_config.filters.level_module.enabled",
        is_type_of=bool,
    ),
    Validator(
        "logger_config.filters.level_module.module_name_level",
    ),
    Validator(
        "logger_config.formatter.ColoredFormatter.colors.debug",
    ),
    Validator(
        "logger_config.formatter.ColoredFormatter.colors.info",
    ),
    Validator(
        "logger_config.formatter.ColoredFormatter.colors.warning",
    ),
    Validator(
        "logger_config.formatter.ColoredFormatter.colors.error",
    ),
    Validator(
        "logger_config.formatter.ColoredFormatter.colors.critical",
    ),
    Validator(
        "logger_config.formatter.ColoredFormatter.back_color.debug",
    ),
    Validator(
        "logger_config.formatter.ColoredFormatter.back_color.info",
    ),
    Validator(
        "logger_config.formatter.ColoredFormatter.back_color.warning",
    ),
    Validator(
        "logger_config.formatter.ColoredFormatter.back_color.error",
    ),
    Validator(
        "logger_config.formatter.ColoredFormatter.back_color.critical",
    ),
    Validator(
        "logger_config.handlers.AlertHandler.enabled",
        is_type_of=bool,
    ),
    Validator(
        "logger_config.handlers.AlertHandler.chrono_courier_host",
    ),
    Validator("logger_config.handlers.AlertHandler.chrono_courier_api_key"),
)


@lru_cache()
def get_setting(key):
    return logger_settings[key]
