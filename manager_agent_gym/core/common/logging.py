import logging
from typing import Iterable


# Library logger: do not configure global logging on import.
# Attach a NullHandler so "No handler could be found" warnings are avoided.
logger = logging.getLogger("manager_agent_gym")
logger.addHandler(logging.NullHandler())


def silence_third_party_logs(
    level: int = logging.CRITICAL,
    libraries: Iterable[str] = (
        "litellm",
        "httpx",
        "httpcore",
        "urllib3",
        "openai",
        "anthropic",
    ),
) -> None:
    """Reduce verbosity from common third-party libraries.

    Intended to be called by applications/CLIs, not at import time.
    """
    for name in libraries:
        lg = logging.getLogger(name)
        lg.setLevel(level)
        lg.propagate = False
        for handler in list(lg.handlers):
            lg.removeHandler(handler)


def configure_library_logging(level: int = logging.INFO) -> None:
    """Opt-in basic configuration for library logs.

    Call this from applications or examples to route library logs to the root handlers.
    """
    logger.setLevel(level)
