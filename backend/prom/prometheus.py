from prometheus_client import (
    Counter,
    Histogram,
)
import time
from functools import wraps


PROM_HANDLERS = {}

PROM_HANDLERS['request_count'] = Counter(
    'app_request_count',
    'Application Request Count',
    ['method', 'endpoint', 'http_status']
)

PROM_HANDLERS['request_latency'] = Histogram(
    'app_request_latency_seconds',
    'Application Request Latency',
    ['method', 'endpoint']
)

PROM_HANDLERS['skipped_parser'] = Counter(
    'app_skipped_parser_count',
    'Number of skipped parser requests',
    ['platform']
)

PROM_HANDLERS['failed_parser'] = Counter(
    'app_failed_parser_count',
    'Number of failed parser requests',
    []
)

PROM_HANDLERS['failed_llm'] = Counter(
    'app_failed_llm_count',
    'Number of failed LLM requests',
    ['method', 'endpoint', 'username']
)

PROM_HANDLERS['failed_db_queries'] = Counter(
    'app_failed_db_queries',
    'Number of failed DB queries',
    ['query']
)

def time_request(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        # .observe(time.time() - start_time)
        req = kwargs['request']
        result = await func(*args, **kwargs)
        PROM_HANDLERS['request_latency'].labels(
            req.method,
            req.url.path,
        ).observe(time.time() - start_time)
        return result
    return wrapper
