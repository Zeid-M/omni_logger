import logging
import logging.config
import logging.handlers
import time
from collections import OrderedDict

from omni_logger.config.logger_config import get_setting


class LRUDefaultDict:
    """
    A dictionary-like data structure with Least Recently Used (LRU) cache eviction
    and default value functionality, similar to `defaultdict(int)` with LRU behavior.

    This structure maintains a limited-size cache of key-value pairs, automatically
    evicting the least recently used items when the maximum size is reached. When
    accessing a missing key, it provides a default value, which by default is an integer.

    Attributes:
        max_size (int): The maximum number of items the cache can hold.
        default_factory (callable): A function to generate default values for missing keys.
            Defaults to `int`, so missing keys will return 0.
    """

    def __init__(self, max_size, default_factory=int):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.default_factory = default_factory

    def get(self, key):
        """
        Retrieve the value associated with the given key.

        If the key is not present, it will be added to the cache with a default value
        (specified by `default_factory`). Accessing a key marks it as recently used,
        moving it to the end of the cache.

        Args:
            key: The key to retrieve from the cache.

        Returns:
            The value associated with the key, or a default value if the key is missing.
        """
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        else:
            value = self.default_factory()
            self.put(key, value)
            return value

    def put(self, key, value):
        """
        Insert or update the key-value pair in the cache.

        Marks the key as recently used, moving it to the end of the cache. If the
        cache exceeds its maximum size (`max_size`), the least recently used item
        will be removed to make room.

        Args:
            key: The key to insert or update in the cache.
            value: The value to associate with the key.
        """
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)


class ThrottlingFilter(logging.Filter):
    """
    A logging filter that throttles log messages with identical content based on a time interval.

    This filter prevents the same log message from being recorded too frequently. If enabled in settings
    (`logger_config.filters.throttling.enabled`), it allows a message to be logged only if a specified
    interval (`logger_config.filters.throttling.throttle_interval`) has passed since the last log of the same message.
    """

    def __init__(self):
        """
        Initializes the ThrottlingFilter with a dictionary to track the last log time for each message.

        `last_log_time` stores the timestamp of the most recent log for each unique message to control
        throttling based on the specified interval.
        """
        super().__init__()
        self.last_log_time = LRUDefaultDict(
            max_size=5000
        )  # Default time is 0 for unlogged messages

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Determines whether to log a message based on the throttling interval.

        Parameters:
            record (logging.LogRecord): The log record to filter.

        Returns:
            bool: True if the message should be logged, False if it should be throttled.
        """

        # Bypass throttling if the feature is disabled in settings
        if not get_setting("logger_config.filters.throttling.enabled"):
            return True

        current_time = time.time()

        # Check if enough time has passed since the last log of the same message
        if current_time - self.last_log_time.get(record.msg) > get_setting(
            "logger_config.filters.throttling.throttle_interval"
        ):
            # Update the last log time for this message and allow logging
            self.last_log_time.put(key=record.msg, value=current_time)  # type: ignore
            return True  # Log the message

        # Otherwise, throttle (suppress) the log message
        return False
