import gc
from functools import wraps


def gc_collect(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        finally:
            gc.collect()

    return wrapper
