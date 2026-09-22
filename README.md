# OmniLogger

A pre-configured Python logger that captures every system message with ease.

## Description

OmniLogger simplifies logging for developers by providing a ready-to-use Python logger. It seamlessly captures standard log messages, print statements, and even uncaught exceptions, ensuring nothing escapes your logs!

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Features](#features)

## Installation

1. **Download the Package**
   Install OmniLogger using `pip`:

   ```bash
   pip install omni-logger
   ```

2. **(Optional) Configure OmniLogger**
   To customize the OmniLogger settings, follow these steps:
   1. Set the environment variable `OMNILOGGER_ROOT_PATH_FOR_DYNACONF` to specify the directory where the OmniLogger settings file will be stored.

      **Example (Linux/Mac):**

      ```bash
      export OMNILOGGER_ROOT_PATH_FOR_DYNACONF=/path/to/your/settings
      ```

      **Example (Windows, Command Prompt):**

      ```cmd
      set OMNILOGGER_ROOT_PATH_FOR_DYNACONF=C:\path\to\your\settings
      ```

   2. Run the following command to install the custom configuration:

      ```bash
      omni_logger_install_custom_configuration
      ```

   After installation, you can edit the configuration file as needed.

---

## Usage

### **1. Import and Initialize the Logger Start by importing the OmniLogger class and retrieving the logger instance:**

```python
from omni_logger import OmniLogger

# Initialize the OmniLogger and retrieve the logger instance

logger = OmniLogger().get_logger()
```

### **2. Log Messages Use the logger instance to log messages at various levels:**

```python
# Log messages at different levels
logger.debug("This is a debug message")
logger.info("This is an info message")
logger.warning("This is a warning message")
logger.error("This is an error message")
logger.critical("This is a critical message")
```

### **3. Advanced Logging Features:**

OmniLogger enhances your logging experience by automatically capturing additional outputs:

#### 1. Capturing `print` Statements

OmniLogger redirects `print` statements to the logger. It interprets messages based on their prefixes:

- Prefix with `info`, `warn`, `debug`, `error`, or `critical` to log messages at the respective levels.
- Messages without a prefix default to `debug`.

Example:

```python
# Redirect print statements to the logger
print("info: This is an info-level message from print")
print("warn: This is a warning-level message from print")
print("This is a debug-level message from print (default)")
```

#### 2. Capturing Uncaught Exceptions

OmniLogger captures and logs uncaught exceptions automatically, ensuring no errors go unnoticed.

Example:

```python
# Trigger an uncaught exception to demonstrate logging
raise ValueError("This is an uncaught exception example")
```

#### 3. Specific Logs Directory

OmniLogger supports organizing log files in a structured directory hierarchy based on the current date. This structure makes it easy to manage and locate logs for specific periods.

---

##### How It Works

1. **Directory Hierarchy**: The log file path includes subdirectories for the year and month, and the log file name includes the day.
2. **Automatic Directory Creation**: If the required directories do not exist, OmniLogger creates them automatically.
3. **Dynamic Log Path Configuration**: The logger updates its configuration to use the new log file path.

---

##### Configuration Example

You can optionally set a custom log file path when initializing OmniLogger by passing the `log_dir_name` parameter:

```python
from omnilogger import OmniLogger

# Initialize the logger with a custom log directory and file path
logger = OmniLogger(log_dir_name="mylog").get_logger()

# Log a message
logger.info("This log will be saved in a structured directory.")
```

The resulting directory structure will look like this:

```
.
└── mylog
    └── 2024-11
        └── mylog-2024-11-20.log.jsonl
```

Additionally, you can lock the log file to prevent accidental modifications by setting the `lock_log_file` parameter to `True`:

```python
from omnilogger import OmniLogger

# Initialize the logger with a custom log directory and file path, and lock it
logger = OmniLogger(log_dir_name="mylog",lock_log_file=True).get_logger()
```

---

#### **Benefits**

1. **Organized Logs**: Easily navigate logs by year, month, and day.
2. **Automated Management**: OmniLogger handles directory creation and file updates seamlessly.
3. **Customizable Path**: Set your own base directory while enjoying structured subdirectories.

## Features

### Handlers

OmniLogger comes with four pre-configured handlers to manage and output log messages effectively:

#### Console Handler

The Console Handler processes all log messages and displays them directly in the console. This is ideal for real-time monitoring during development.

#### File JSON Handler

The File JSON Handler processes all log messages and saves them in a log file using JSON line formatting. This format is ideal for structured log analysis and reviewing logs at a later time.

#### Alert Handler

The Alert Handler captures all log messages with a log level of WARNING and above, such as ERROR and CRITICAL, and forwards them to the Chrono Courier. This ensures important alerts are sent out promptly for immediate attention.

##### How It Works

1. The Alert Handler checks if it is enabled in the configuration (`enabled = true`).
2. When a log message with a level of `WARNING`, `ERROR`, or `CRITICAL` is generated, the handler forwards the message to the Chrono Courier.
3. The Chrono Courier is configured using the `chrono_courier_host` and `chrono_courier_api_key` settings.

---

##### Configuration in `settings.toml`

To enable and configure the Alert Handler, update the `settings.toml` file:

```toml
# Alert handler for custom alerts (disabled by default)
[logger_config.handlers.AlertHandler]
enabled = false                     # Set to true to enable the Alert Handler
chrono_courier_host = ""       # Host address of the Chrono Courier
chrono_courier_api_key = ""    # API key for authenticating with the Chrono Courier
```

---

##### Example Configuration

Here’s an example configuration where alerts are sent to a hypothetical Chrono Courier:

```toml
[logger_config.handlers.AlertHandler]
enabled = true
chrono_courier_host = "https://api.chronocourier.com"
chrono_courier_api_key = "your_api_key_here"
```

#### Queue Handler

The Queue Handler processes all log messages by adding them to a queue running on a separate thread. This ensures log handling is performed in a non-blocking manner, allowing the main program to continue execution without delays.

### Formatters

#### Colored Formatter

The Colored Formatter enhances log messages by adding font and background colors based on their log level, making it easy to distinguish between different types of logs at a glance. Additionally, it enriches the log messages with detailed metadata, including:

- Log level
- Module name
- Function name
- Line number
- Thread name
- Environment
- Log datetime

This formatter is primarily used in the [Console Handler](#console-handler).

#### JSON Formatter

The JSON Formatter formats log messages in JSON line format, making them suitable for structured log storage and analysis. It enriches each log message with comprehensive metadata, including:

- Log level
- Module name
- Function name
- Line number
- Thread name
- Environment
- Log datetime

Additionally, you can include custom details in the logs using the `extra` argument, allowing you to tailor the log output to your specific needs.

This formatter is primarily used in the [File JSON Handler](#file-json-handler).

Example:

```python
# Log a message with the JSON Formatter, including custom extra fields
logger.info("This is an info message with additional metadata.", extra={"user_id": 123, "action": "login"})
```

### Filters

#### Censorship Filter

The Censorship Filter is a logging filter that censors specified words in log messages when enabled. It ensures sensitive or inappropriate content is masked in your logs.

##### **How It Works**

1. The filter checks if censorship is enabled in the settings (`logger_config.filters.censorship.enabled`).
2. If enabled, it replaces each word listed in `logger_config.filters.censorship.words_to_censor` with asterisks (`*`).

---

##### **Configuration in `settings.toml`**

To enable and configure the Censorship Filter, modify the following section in your `settings.toml` file:

```toml
[logger_config.filters.censorship]
enabled = false               # Set to true to enable censorship
words_to_censor = ["password", "secret", "token"]  # List of words to censor
```

---

##### **Example Usage**

Suppose you enable censorship and configure it to censor `password` and `secret`:

```python
logger.info("User entered password and secret key")
```

**With Censorship Enabled:**

```
[INFO|M:omni_logger_core|F:main|L:505|T:MainThread|E:  ] 2024-11-20T12:27:27+0300: User entered ******** and ******** key
```

**With Censorship Disabled:**

```
[INFO|M:omni_logger_core|F:main|L:505|T:MainThread|E:  ] 2024-11-20T12:27:27+0300: User entered password and secret key
```

#### Throttling Filter

The Throttling Filter is a logging filter designed to limit the frequency of log messages with identical content. This prevents excessive repetition in logs, making them cleaner and easier to analyze.

---

##### How It Works

1. The filter checks if throttling is enabled in the settings (`logger_config.filters.throttling.enabled`).
2. If enabled, it allows a log message to be recorded only if the specified interval (`logger_config.filters.throttling.throttle_interval`) has passed since the last occurrence of the same message.

---

##### Configuration in `settings.toml`

To enable and configure the Throttling Filter, modify the following section in your `settings.toml` file:

```toml
[logger_config.filters.throttling]
enabled = false               # Set to true to enable throttling
throttle_interval = 2         # Interval in seconds to throttle identical log messages
```

---

##### Example Usage

Suppose throttling is enabled with a `throttle_interval` of 2 seconds:

```python
logger.warning("This is a repeated warning!")
logger.warning("This is a repeated warning!")  # Ignored if logged within 2 seconds
```

**Output:**

```
[WARNING|M:omni_logger_core|F:main|L:505|T:MainThread|E:  ] 2024-11-20T12:31:27+0300: - This is a repeated warning! (Logged once)
```

**Behavior:**

- The second log message will be ignored if it occurs within 2 seconds of the first one.
- If 2 seconds have elapsed, the message will be logged again.

#### Level Module Filter

The Level Module Filter enforces module-specific logging levels, allowing you to control the verbosity of logs for different parts of your application. This filter is especially useful for fine-tuning log output in large projects with multiple modules.

---

##### How It Works

1. The filter checks if module-level log filtering is enabled in the settings (`logger_config.filters.level_module.enabled`).
2. When enabled, it logs messages only if they meet or exceed the specified logging level for each module. These levels are defined in the `logger_config.filters.level_module.module_name_level` section.

---

##### Configuration in `settings.toml`

To enable and configure the Level Module Filter, update your `settings.toml` file as follows:

```toml
[logger_config.filters.level_module]
enabled = false  # Set to true to enable module-level log filtering

# Define log level settings for each module
[logger_config.filters.level_module.module_name_level]

# Specify module_name = "log_level" pairs to control logging levels for specific modules
# Supported log levels: "critical", "fatal", "error", "warning", "warn", "info", "debug", "notset"

# Example configuration:
main = "info"      # Logs at "info" level or higher for the "main" module
test = "warning"   # Logs at "warning" level or higher for the "test" module
```

---

##### Example Usage

Suppose module-level filtering is enabled with the following configuration:

```toml
[logger_config.filters.level_module.module_name_level]
main = "info"
test = "warning"
```

In the Python code:

```python
# Logs in the "main" module
logger_main = OmniLogger().get_logger()
logger_main.debug("This debug message will not be logged.")
logger_main.info("This info message will be logged.")

# Logs in the "test" module
logger_test = OmniLogger().get_logger()
logger_test.info("This info message will not be logged.")
logger_test.warning("This warning message will be logged.")
```

**Output:**

```
[INFO|M:main|F:main|L:505|T:MainThread|E:  ] 2024-11-20T12:36:27+0300: This info message will be logged.
[WARNING|M:test|F:test|L:505|T:MainThread|E:  ] 2024-11-20T12:36:47+0300: This warning message will be logged.
```

#### Exclude Module Filter

The Exclude Module Filter is a logging filter that prevents log messages from specified modules from being logged. This is particularly useful for suppressing noisy or irrelevant logs in your application.

---

##### How It Works

1. The filter checks if module exclusion is enabled in the settings (`logger_config.filters.exclude_module.enabled`).
2. When enabled, log messages originating from modules listed in `logger_config.filters.exclude_module.excluded_modules` are ignored.

---

##### Configuration in `settings.toml`

To enable and configure the Exclude Module Filter, modify the `settings.toml` file as follows:

```toml
[logger_config.filters.exclude_module]
enabled = false              # Set to true to enable module exclusion
excluded_modules = []        # List of module names to exclude from logging

```

---

##### Example Usage

Suppose you enable the filter and configure it to exclude `test_module` and `debug_module`:

```toml
[logger_config.filters.exclude_module]
enabled = true
excluded_modules = ["test_module", "debug_module"]
```

In the Python code:

```python
# Logs in the "main" module
logger_main = OmniLogger().get_logger()
logger_main.info("This message will be logged.")

# Logs in the "test_module" (excluded)
logger_test = OmniLogger().get_logger()
logger_test.info("This message will not be logged.")

# Logs in the "debug_module" (excluded)
logger_debug = OmniLogger().get_logger()
logger_debug.info("This message will also not be logged.")
```

**Output:**

```
[INFO|M:main|F:main|L:505|T:MainThread|E:  ] 2024-11-20T12:42:27+0300: This message will be logged.
```

#### Allow Module Filter

The Allow Module Filter is a logging filter that restricts logging to specified modules. It ensures that only log messages originating from the allowed modules are logged, making it useful for focusing on relevant logs in large applications.

---

##### How It Works

1. The filter checks if module-specific logging is enabled in the settings (`logger_config.filters.allowed_module.enabled`).
2. When enabled, only log messages from modules listed in `logger_config.filters.allowed_module.allowed_modules` are logged, and all others are ignored.

---

##### Configuration in `settings.toml`

To enable and configure the Allow Module Filter, update your `settings.toml` file:

```toml
[logger_config.filters.allowed_module]
enabled = false               # Set to true to enable module-specific logging
allowed_modules = []          # List of allowed module names

```

---

##### Example Usage

Suppose you enable the filter and configure it to allow only `main` and `auth` modules:

```toml
[logger_config.filters.allowed_module]
enabled = true
allowed_modules = ["main", "auth"]
```

In the Python code:

```python
# Logs in the "main" module (allowed)
logger_main = OmniLogger().get_logger()
logger_main.info("This message will be logged.")

# Logs in the "auth" module (allowed)
logger_auth = OmniLogger().get_logger()
logger_auth.info("This authentication log will also be logged.")

# Logs in the "debug_module" (not allowed)
logger_debug = OmniLogger().get_logger()
logger_debug.info("This message will not be logged.")
```

**Output:**

```
[INFO|M:main|F:main|L:505|T:MainThread|E:  ] 2024-11-20T12:49:27+0300: This message will be logged.
[INFO|M:auth|F:auth|L:235|T:MainThread|E:  ] 2024-11-20T12:49:40+0300:This authentication log will also be logged.
```

### Periodic Settings Refresh

The periodic settings refresh feature enables the logger to automatically reload its configuration at regular intervals. This is useful in dynamic environments where logger settings may change during runtime.

---

#### How It Works

1. A separate daemon thread is initiated to handle periodic settings refresh.
2. The thread checks if periodic refreshing is enabled (`refresh_enabled`).
3. If enabled, the logger will refresh its settings based on the configured interval (`refresh_interval`), specified in seconds.
4. The logger re-applies the updated settings from the configuration file located in the path specified by the OMNILOGGER_ROOT_PATH_FOR_DYNACONF environment variable.

---

#### Configuration in `settings.toml`

To enable and configure periodic settings refresh, update the following in your `settings.toml` file:

```toml
# Enable or disable automatic refresh of the logger's configuration
refresh_enabled = true  # Set to true to enable periodic refreshing

# Interval (in seconds) for refreshing the logger's configuration
refresh_interval = 600  # The logger will refresh its configuration every 600 seconds (10 minutes)
```

---

#### Key Benefits

- **Dynamic Adaptability**: Automatically applies updates to settings without requiring a restart.
- **Non-Blocking**: Runs in a separate daemon thread, ensuring the main application flow is unaffected.
- **Configurable**: Easily adjust the refresh interval based on your environment's needs.
