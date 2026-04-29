import logging
import sys


class EnvelopeIDFilter(logging.Filter):
    def filter(self, record):
        if not hasattr(record, 'envelope_id'):
            record.envelope_id = "-"
        return True


def setup_logging():
    root = logging.getLogger()

    root.handlers.clear()

    h = logging.StreamHandler(sys.stdout)
    h.addFilter(EnvelopeIDFilter())
    
    fmt = logging.Formatter('%(asctime)s %(levelname)s [%(envelope_id)s] %(name)s: %(message)s', datefmt='%H:%M:%S')
    h.setFormatter(fmt)
    
    root.addHandler(h)
    root.setLevel(logging.INFO)

    logging.getLogger("uvicorn.access").propagate = True