import json
from loguru import logger
import sys




def serialize(record):
    subset = {
        "timestamp": record["time"].timestamp(),
        "message": record["message"],
        "level": record["level"].name,
    }
    return json.dumps(subset)


def patching(record):
    record["extra"]["serialized"] = serialize(record)

def init_logger():
    LOGURU_LOGGER = logger.patch(patching)
    LOGURU_LOGGER.add(sys.stderr, format="{extra[serialized]}")
    logger.add("app.log", format="{extra[serialized]}", backtrace=True)
    LOGURU_LOGGER.info("Happy logging with Loguru!")
    return LOGURU_LOGGER

LOGURU_LOGGER = init_logger()
