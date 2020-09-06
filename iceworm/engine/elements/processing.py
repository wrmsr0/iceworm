"""
TODO:
 - add id's
 - add deps
 - find / warn / reject elements with no processors
  - processed_cls_set? optional, enforced if present, warn
 - enforce only modified ids that matched (or added new)
 - ** timing, + detect infinite loops **
  - max iterations?
  - 'aspect_id' tagging equiv - 'ProcessedBy' attribute?
 - ProcessedBy allowed to be updated but only for self, added if not
 - RULES phase - keep? serde already bound lol, can't load any dynamic rule types yet.. *yet*.. nuke serde ctx?
"""
import abc
import typing as ta

from omnibus import check
from omnibus import collections as ocol
from omnibus import dataclasses as dc
from omnibus import lang

from .base import Element
from .collections import ElementSet


class ProcessedBy(dc.Pure):
    processors: ta.AbstractSet['ElementProcessor'] = dc.field(check=lambda o: isinstance(o, ocol.IdentitySet))


class Phase(lang.AutoEnum):
    BOOTSTRAP = ...
    SITES = ...
    RULES = ...
    CONNECTORS = ...
    TARGETS = ...
    FINALIZE = ...


class SubPhase(lang.AutoEnum):
    PRE = ...
    MAIN = ...
    POST = ...


class ElementProcessor(lang.Abstract):

    @abc.abstractmethod
    def processes(self, elements: ElementSet) -> ta.Iterable[Element]:
        raise NotImplementedError

    @abc.abstractmethod
    def process(self, elements: ElementSet) -> ElementSet:
        raise NotImplementedError


class ElementProcessingDriver:

    def __init__(self, processors: ta.Iterable[ElementProcessor]) -> None:
        super().__init__()

        lst = []
        seen = ocol.IdentitySet()
        for ep in processors:
            check.isinstance(ep, ElementProcessor)
            check.not_in(ep, seen)
            lst.append(ep)
            seen.add(ep)
        self._processors: ta.Sequence[ElementProcessor] = lst

    @property
    def processors(self) -> ta.Sequence[ElementProcessor]:
        return self._processors

    def process(self, elements: ta.Iterable[Element]) -> ElementSet:
        elements = ElementSet.of(elements)

        while True:
            dct: ta.MutableMapping[ElementProcessor, ta.AbstractSet[Element]] = ocol.IdentityKeyDict()
            for ep in self._processors:
                epes = ocol.IdentitySet(check.isinstance(e, Element) for e in ep.processes(elements))
                if epes:
                    dct[ep] = epes
            if not dct:
                break

            cur, cures = next(iter(dct.items()))
            expected = [e for e in elements if e not in cures]
            res = ElementSet.of(cur.process(elements))

            missing = [e for e in expected if e not in res]
            if missing:
                raise ValueError(missing)

            swaps: ta.MutableMapping[Element, Element] = ocol.IdentityKeyDict()

            added = [e for e in res if e not in elements]
            removed = [e for e in elements if e not in res]  # noqa
            for e in added:
                pbs = e.meta.get(ProcessedBy)
                if pbs is not None:
                    check.state(check.single(pbs) is cur)
                    continue
                swaps[e] = dc.replace(e, meta={**e.meta, ProcessedBy: ocol.IdentitySet([cur])})
            # TODO: tag matched but unmodified?

            if swaps:
                res = ElementSet.of(swaps.get(e, e) for e in res)

            elements = res

        return elements
