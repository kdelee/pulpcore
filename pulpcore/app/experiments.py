"""Helpers for production A/B experiments."""

import json
import logging
import random
import time

logger = logging.getLogger("pulp.experiment")


def run_experiment(exp_id, control, candidate, *, p_candidate=0.5, correlation_id=None):
    """Run one experiment variant and log its duration."""
    variant = "B" if random.random() < p_candidate else "A"
    start = time.monotonic()
    result = (candidate if variant == "B" else control)()
    duration_ms = (time.monotonic() - start) * 1000
    logger.info(
        json.dumps(
            {
                "event": "ab_experiment",
                "exp_id": exp_id,
                "variant": variant,
                "duration_ms": round(duration_ms, 3),
                "correlation_id": correlation_id,
            }
        )
    )
    return result
