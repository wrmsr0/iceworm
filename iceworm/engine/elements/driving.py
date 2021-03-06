"""
TODO:
 - cross-phase dep tracking..
 - ** some kind of rudimentary priority, internal only, prob read-only **
  - ** enforcements - enforce after every pass all refs resolve * and to correct type * **
  - *** NO - EAGER ANALYSES ***
 - ** honor analysis deps **
 - ** phase *RANGE* not frozen - cannot be added before, frozen after **
 - make processors only have to return what they modified? cann no longer sort
 - find / warn / reject elements with no processors
  - processed_cls_set? optional, enforced if present, warn
 - ** timing, + detect infinite loops **
  - max iterations?
  - 'aspect_id' tagging equiv - '_ProcessedBy' attribute?
 - _ProcessedBy allowed to be updated but only for self, added if not
 - RULES phase - keep? serde already bound lol, can't load any dynamic rule types yet.. *yet*.. nuke serde ctx?
 - class Phase(dc.Pure): name: str, mutable_element_types: ta.AbstractSet[type], ...
 - decompose? need to setup ctors before instantiating next phases lol..
 - secrets processor - url: str, url_secret: Secret = dc.field(metadata={els.SecretField: 'url')
 - overlap w/ tree xforms? passes? no cuz flat?
 - ** enforce origin propagation somehow - require for ids? auto-add for ids? **
 - if mem is an issue strip origins unless explicitly kept
"""
import itertools
import logging
import random
import typing as ta
import weakref

from omnibus import check
from omnibus import collections as ocol
from omnibus import dataclasses as dc
from omnibus import lang

from .base import Dependable
from .base import Element
from .base import Frozen
from .collections import Analysis
from .collections import ElementSet
from .phases import PHASES
from .phases import Phase
from .phases import Phases
from .processors import ElementProcessor
from .validations import Validation


log = logging.getLogger(__name__)


class _ProcessedBy(dc.Pure):
    processors: ta.AbstractSet['ElementProcessor'] = dc.field(
        coerce=lambda o: ocol.IdentitySet(check.not_isinstance(o, str)) if not isinstance(o, ocol.IdentitySet) else o,
        check=lambda o: isinstance(o, ocol.IdentitySet) and all(isinstance(e, ElementProcessor) for e in o))

    EMPTY: ta.ClassVar['_ProcessedBy']


_ProcessedBy.EMPTY = _ProcessedBy([])


def _coerce_phase_range(o):
    if isinstance(o, Phase):
        return (Phases.BOOTSTRAP, o)
    elif isinstance(o, ta.Sequence):
        l, r = o
        return (l, r)
    else:
        raise TypeError(o)


class PhaseFrozen(dc.Pure):
    range: ta.Tuple[Phase, Phase] = dc.field(
        coerce=_coerce_phase_range,
        check=lambda t: len(t) == 2 and all(isinstance(e, Phase) for e in t) and t[0] <= t[1])


_PHASE_FROZEN_CACHE = weakref.WeakKeyDictionary()


def _phase_frozen(cls: type) -> ta.Optional[ta.Tuple[Phase, Phase]]:
    try:
        return _PHASE_FROZEN_CACHE[cls]
    except KeyError:
        check.issubclass(cls, Element)
        pfi = dc.metadatas_dict(cls).get(PhaseFrozen)
        if pfi is not None:
            pf = check.isinstance(pfi, PhaseFrozen).range
        else:
            pf = None
        _PHASE_FROZEN_CACHE[cls] = pf
        return pf


def has_processed(ep: 'ElementProcessor', e: Element) -> bool:
    check.isinstance(ep, ElementProcessor)
    check.isinstance(e, Element)
    try:
        pb = e.meta[_ProcessedBy]
    except KeyError:
        return False
    else:
        return ep in check.isinstance(pb, _ProcessedBy).processors


DriverItem = ta.Union[ElementProcessor, ta.Type[Validation]]
DriverItemFactory = ta.Callable[[Phase, ta.Optional[ElementSet]], ta.Iterable[DriverItem]]


class ElementProcessingDriver:

    class Config(dc.Pure):
        max_iterations: int = 1000

        step_shuffle: bool = False
        step_shuffle_seed: ta.Optional[int] = dc.field(None, check_type=(int, None))

    def __init__(
            self,
            factory: DriverItemFactory,
            *,
            config: Config = Config(),
    ) -> None:
        super().__init__()

        self._factory = check.callable(factory)
        self._config = check.isinstance(config, self.Config)

    @classmethod
    def build_factory(cls, processors: ta.Iterable[ElementProcessor]) -> DriverItemFactory:
        lst = []
        seen = ocol.IdentitySet()
        by_phase = {}
        for ep in processors:
            check.isinstance(ep, ElementProcessor)
            check.not_in(ep, seen)
            lst.append(ep)
            for p in set(type(ep).phases()):
                check.isinstance(p, Phase)
                by_phase.setdefault(p, []).append(ep)
            seen.add(ep)
        processor_seqs_by_phase: ta.Mapping[Phase, ta.Sequence[ElementProcessor]] = by_phase
        return lambda phase, es: processor_seqs_by_phase.get(phase, [])

    def _build_steps(
            self,
            items: ta.Sequence[ta.Union[ElementProcessor, ta.Type[Analysis]]],
            phase: Phase,
    ) -> ta.Sequence[ta.AbstractSet[ElementProcessor]]:
        if not items:
            return []

        deps_dct = {}
        ep_seqs_by_cls = {}
        for e in items:
            if isinstance(e, ElementProcessor):
                cls = type(e)
                check.in_(phase, cls.phases())
                ep_seqs_by_cls.setdefault(type(e), []).append(e)
            elif isinstance(e, type) and issubclass(e, Analysis):
                cls = e
            else:
                raise TypeError(e)
            deps_dct[cls] = {check.issubclass(d, Dependable) for d in e.cls_dependencies()}

        todo = set(deps_dct)
        while todo:
            cur = todo.pop()
            try:
                deps = deps_dct[cur]
            except KeyError:
                deps = deps_dct[cur] = cur.cls_dependencies()
            for dep in deps:
                if dep in deps_dct:
                    continue
                check.issubclass(dep, Dependable)
                if not issubclass(dep, Analysis) and issubclass(dep, lang.Final):
                    raise Exception(f'Can only implicitly dep final analyses, not {dep}')
                todo.add(dep)

        sets_by_mro_cls = {}
        for c in deps_dct:
            for mro_cls in c.__mro__:
                sets_by_mro_cls.setdefault(mro_cls, set()).add(c)

        ep_deps = {
            e: {mdep for dep in deps for mdep in check.not_empty(sets_by_mro_cls[dep])}
            for e, deps in deps_dct.items()
        }
        steps = list(ocol.toposort(ep_deps))

        return [
            {e for c in step if issubclass(c, ElementProcessor) for e in ep_seqs_by_cls[c]}
            for step in steps
        ]

    def _sort_step(self, step: ta.Iterable[ElementProcessor]) -> ta.Sequence[ElementProcessor]:
        ep_sets_by_cls = {}

        for ep in step:
            ep_sets_by_cls.setdefault(type(ep), ocol.IdentitySet()).add(ep)
        cls_by_qn = ocol.unique_dict((cls.__qualname__, cls) for cls in ep_sets_by_cls)

        ret = []
        for _, cls in sorted(cls_by_qn.items(), key=lambda t: t[0]):
            kws_by_ep: ta.Mapping[ElementProcessor, ta.Mapping[str, ta.Any]] = ocol.IdentityKeyDict(
                (ep, dict(check.isinstance(ep.key, ta.Mapping))) for ep in ep_sets_by_cls[cls])
            kw_keys = sorted({check.isinstance(k, str) for kw in kws_by_ep.values() for k in kw})
            eps_by_kwt = ocol.unique_dict((tuple(kw.get(k) for k in kw_keys), ep) for ep, kw in kws_by_ep.items())
            ret.extend([ep for _, ep in sorted(list(eps_by_kwt.items()), key=lambda t: t[0])])

        if self._config.step_shuffle:
            if self._config.step_shuffle_seed is not None:
                r = random.Random(self._config.step_shuffle_seed)
            else:
                r = random.random
            random.shuffle(ret, r)

        return ret

    def _run_processor(
            self,
            processor: ElementProcessor,
            matches: ta.AbstractSet[Element],
            elements: ElementSet,
            phase: Phase,
    ) -> ElementSet:
        expected = [e for e in elements if e not in matches]
        res = ElementSet.of(processor.process(elements))

        missing = [e for e in expected if e not in res]
        if missing:
            raise ValueError(missing)

        leftover = [e for e in matches if e in res and Frozen not in e.meta]
        if leftover:
            raise ValueError(leftover)

        swaps: ta.MutableMapping[Element, Element] = ocol.IdentityKeyDict()

        added = [e for e in res if e not in elements]
        removed = [e for e in elements if e not in res]  # noqa

        check.empty([e for e in removed if Frozen in e.meta])

        for e in itertools.chain(added, removed):
            pf = _phase_frozen(type(e))
            if pf is not None and not (pf[0] <= phase <= pf[1]):
                raise ValueError(e, pf)

        for e in added:
            pbs = e.meta.get(_ProcessedBy)
            if pbs is not None:
                npbs = check.isinstance(pbs, _ProcessedBy).processors
                if processor in npbs:
                    continue
            else:
                npbs = []
            swaps[e] = dc.replace(
                e,
                meta={
                    **e.meta,
                    _ProcessedBy: _ProcessedBy([*npbs, processor]),
                },
            )

        if swaps:
            res = ElementSet.of(swaps.get(e, e) for e in res)

        return res

    def _strip_meta(self, eles: ta.Iterable[Element]) -> ElementSet:
        return ElementSet.of(dc.replace(e, meta={**e.meta, _ProcessedBy: None}) for e in eles)

    def process(self, elements: ta.Iterable[Element]) -> ElementSet:
        elements = self._strip_meta(elements)

        for phase in PHASES:
            items = list(self._factory(phase, elements))
            eps, items = ocol.partition(items, lambda e: isinstance(e, ElementProcessor))
            vals, items = ocol.partition(items, lambda e: isinstance(e, type) and issubclass(e, Validation))
            check.empty(items)

            steps = self._build_steps(eps, phase)
            steps = [self._sort_step(step) for step in steps]

            count = 0
            history = []
            while True:
                count += 1
                check.state(count <= self._config.max_iterations)
                if log.isEnabledFor(logging.DEBUG):
                    log.debug(f'phase={phase} count={count}')

                dct: ta.MutableMapping[ElementProcessor, ta.AbstractSet[Element]] = ocol.IdentityKeyDict()
                for step in steps:
                    for processor in step:
                        matches = ocol.IdentitySet(check.isinstance(e, Element) for e in processor.match(elements))
                        if matches:
                            dct[processor] = matches
                    if dct:
                        break
                if not dct:
                    break

                processor, matches = next(iter(dct.items()))
                history.append(processor)
                if log.isEnabledFor(logging.DEBUG):
                    log.debug(processor)

                elements = self._run_processor(processor, matches, elements, phase)

                for val in vals:
                    elements.analyze(val)

            elements = ElementSet.of([
                dc.replace(e, meta={**e.meta, Frozen: Frozen})
                if pf is not None and phase == pf[1] and Frozen not in e.meta else e
                for e in elements
                for pf in [_phase_frozen(type(e))]
            ])

        return self._strip_meta(elements)
