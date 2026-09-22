import atexit
import logging
import logging.handlers
import threading
from logging.config import ConvertingDict, ConvertingList, valid_ident
from queue import Queue

# An event to indicate if the log listener is currently busy processing a record
listener_busy = threading.Event()


class CustomQueueListener(logging.handlers.QueueListener):
    """
    A custom QueueListener that marks itself as busy while processing log records.

    This listener sets a global `listener_busy` flag when a log record is being processed,
    allowing other components to detect when the listener is actively handling logs.
    """

    def handle(self, record: logging.LogRecord) -> None:
        """
        Marks the listener as busy during log processing.

        Sets a global `listener_busy` flag to indicate that the listener is processing a log record.
        This flag is cleared once the log record has been handled.

        Parameters:
            record (logging.LogRecord): The log record to handle.
        """
        listener_busy.set()  # Mark as busy when a log is being processed
        try:
            super().handle(record)  # Process the log entry
        finally:
            listener_busy.clear()  # Ensure the busy flag is cleared after processing


class QueueListenerHandler(logging.handlers.QueueHandler):
    """
    A custom QueueHandler that manages a QueueListener for logging, with automatic startup and cleanup.

    This handler initializes a `CustomQueueListener` to handle log records asynchronously through a queue.
    It also starts the listener upon initialization and registers it to stop when the application exits.
    """

    def __init__(self, handlers, respect_handler_level=False, queue=Queue(-1)):
        """
        Initializes the QueueListenerHandler with specified handlers and starts the listener.

        Parameters:
            handlers (list): The list of handlers to process log records.
            respect_handler_level (bool): If True, respects each handler's level for log filtering.
            queue (Queue, optional): The queue used to pass log records to the listener.
        """
        # Resolve the queue, allowing for custom configurations
        queue = self._resolve_queue(queue)
        super().__init__(queue)

        # Resolve the handlers list
        handlers = self._resolve_handlers(handlers)

        # Initialize and start the listener with the resolved queue and handlers
        self._listener = CustomQueueListener(  # type: ignore
            self.queue, *handlers, respect_handler_level=respect_handler_level
        )
        self._listener.start()

        # Ensure the listener stops gracefully when the application exits
        atexit.register(self._listener.stop)

    @staticmethod
    def _resolve_handlers(l):
        """
        Resolves and returns a list of handlers, converting if needed.

        If the handlers list is an instance of `ConvertingList`, it evaluates each item
        to obtain the actual handler objects.

        Parameters:
            l (list or ConvertingList): The handlers list to resolve.

        Returns:
            list: A list of resolved handler instances.
        """
        if not isinstance(l, ConvertingList):
            return l

        # Convert each item in the ConvertingList by evaluating it
        return [l[i] for i in range(len(l))]

    @staticmethod
    def _resolve_queue(q):
        """
        Resolves and returns a queue instance, handling custom configurations.

        If the queue is a `ConvertingDict`, this method processes the configuration
        to obtain the actual queue instance. Once resolved, the queue is stored in
        the dictionary for future access.

        Parameters:
            q (Queue or ConvertingDict): The queue configuration to resolve.

        Returns:
            Queue: A queue instance configured based on settings.
        """
        if not isinstance(q, ConvertingDict):
            return q

        # Check if a resolved value is already available
        if "__resolved_value__" in q:
            return q["__resolved_value__"]

        # Resolve the class of the queue and initialize it with properties and kwargs
        cname = q.pop("class")
        klass = q.configurator.resolve(cname)  # type: ignore
        props = q.pop(".", None)
        kwargs = {k: q[k] for k in q if valid_ident(k)}  # type: ignore
        result = klass(**kwargs)

        # Set additional properties if defined
        if props:
            for name, value in props.items():
                setattr(result, name, value)

        # Store the resolved queue for future access
        q["__resolved_value__"] = result
        return result
