from catalyst.contrib.registry import (
    Criterion, CRITERIONS, GRAD_CLIPPERS, Model, MODELS, Module, MODULES,
    Optimizer, OPTIMIZERS, Sampler, SAMPLERS, Scheduler, SCHEDULERS, Transform,
    TRANSFORMS
)
from catalyst.core.registry import Callback, CALLBACKS
from catalyst.utils.tools.registry import Registry


def _dbs_late_add(r: Registry):
    from . import db as m
    r.add_from_module(m)


DATABASES = Registry("db")
DATABASES.late_add(_dbs_late_add)
Database = DATABASES.add


def _agents_late_add(r: Registry):
    from . import agent as m
    r.add_from_module(m)


AGENTS = Registry("agent")
AGENTS.late_add(_agents_late_add)
Agent = AGENTS.add


def _offpolicy_algorithms_late_add(r: Registry):
    from .offpolicy import algorithms as m
    r.add_from_module(m)


OFFPOLICY_ALGORITHMS = Registry("algorithm")
OFFPOLICY_ALGORITHMS.late_add(_offpolicy_algorithms_late_add)
OffpolicyAlgorithm = OFFPOLICY_ALGORITHMS.add


def _onpolicy_algorithms_late_add(r: Registry):
    from .onpolicy import algorithms as m
    r.add_from_module(m)


ONPOLICY_ALGORITHMS = Registry("algorithm")
ONPOLICY_ALGORITHMS.late_add(_onpolicy_algorithms_late_add)
OnpolicyAlgorithm = ONPOLICY_ALGORITHMS.add


def _env_late_add(r: Registry):
    from . import environment as m
    r.add_from_module(m)


ENVIRONMENTS = Registry("environment")
ENVIRONMENTS.late_add(_env_late_add)
Environment = ENVIRONMENTS.add


def _exploration_late_add(r: Registry):
    from . import exploration as m
    r.add_from_module(m)


EXPLORATION = Registry("exploration")
EXPLORATION.late_add(_exploration_late_add)
Exploration = EXPLORATION.add

__all__ = [
    "Agent",
    "Callback",
    "Criterion",
    "Database",
    "Environment",
    "Exploration",
    "OffpolicyAlgorithm",
    "OnpolicyAlgorithm",
    "Optimizer",
    "Scheduler",
    "Module",
    "Model",
    "Sampler",
    "Transform",
    "AGENTS",
    "CALLBACKS",
    "CRITERIONS",
    "DATABASES",
    "GRAD_CLIPPERS",
    "ENVIRONMENTS",
    "EXPLORATION",
    "MODELS",
    "MODULES",
    "OFFPOLICY_ALGORITHMS",
    "ONPOLICY_ALGORITHMS",
    "OPTIMIZERS",
    "SAMPLERS",
    "SCHEDULERS",
    "TRANSFORMS",
]
