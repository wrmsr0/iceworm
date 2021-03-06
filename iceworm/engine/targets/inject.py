from omnibus import check
from omnibus import inject as inj

from . import infer
from . import joins
from . import reflect
from .. import elements as els


def _install_elements(binder: inj.Binder) -> inj.Binder:
    check.isinstance(binder, inj.Binder)

    els.inject.bind_element_processor(binder, infer.InferTableProcessor, els.Phases.TARGETS)
    els.inject.bind_element_processor(binder, joins.JoinSplittingProcessor, els.Phases.TARGETS)
    els.inject.bind_element_processor(binder, reflect.ReflectReferencedTablesProcessor, els.Phases.TARGETS)
    els.inject.bind_element_processor(binder, reflect.ReflectTablesProcessor, els.Phases.TARGETS)

    return binder


def install(binder: inj.Binder) -> inj.Binder:
    check.isinstance(binder, inj.Binder)

    els.inject.bind_elements_module(binder, _install_elements)

    return binder
