"""Engines subpackage."""
from . import (frequency, hot_cold, gap_analysis, markov_chain,
               bayesian, pattern_detection, entropy, monte_carlo, ensemble)

ENGINE_REGISTRY = {
    'frequency': frequency,
    'hot_cold': hot_cold,
    'gap_analysis': gap_analysis,
    'markov_chain': markov_chain,
    'bayesian': bayesian,
    'pattern_detection': pattern_detection,
    'entropy': entropy,
    'monte_carlo': monte_carlo,
    'ensemble': ensemble,
}

__all__ = ['ENGINE_REGISTRY'] + list(ENGINE_REGISTRY.keys())
