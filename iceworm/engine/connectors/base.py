"""
TODO:
 - virtual vs physical tables
 - physical tables requiring refresh
 - incremental vs total physical tables
 - materialized vs unmaterialized virtuals
 - ** dataclass interop ** - dc->tbl, query
  - just return object refs? jsonize?
  - support snowflake json garbage on objects
 - piecewise conf? csv mounts? ...
  - *no*, but could have a csv_mount rule before ctor phase that rewrites the sole ctor cfg ele
 - ctors/conns as ctxmgrs?
 - HeapConnector - writable
 - simpler dumber connector? where does sf query jit live?
  - conns that support sql pushdown vs not..
 - 'union'? 'overlay'? wrap one by heap/pg to give txns?

Def conns:
 - sql - snow + pg (+ incl internal state storage pg, 'self')
 - kafka
 - dynamo
 - system - conns, nodes, running ops, etc
 - mongo
 - redis

Alt conns:
 - salesforce
 - pagerduty
 - jira
 - gsheets
 - slack
 - github
 - pandas? :/
"""
import abc
import typing as ta

from omnibus import check
from omnibus import configs as cfgs
from omnibus import dataclasses as dc
from omnibus import defs
from omnibus import lang
from omnibus.serde import mapping as sm

from .. import elements as els
from ... import metadata as md
from ...types import QualifiedName


ConnectorT = ta.TypeVar('ConnectorT', bound='Connector')
ConnectorConfigT = ta.TypeVar('ConnectorConfigT', bound='Connector.Config')

Row = ta.Mapping[str, ta.Any]
Rows = ta.Iterable[Row]


class RowSource(lang.Abstract):

    @abc.abstractmethod
    def produce_rows(self) -> Rows:
        raise NotImplementedError


class RowSink(lang.Abstract):

    @abc.abstractmethod
    def consume_rows(self, rows: ta.Iterable[Row]) -> None:
        raise NotImplementedError


class ListRowSource(RowSource):

    def __init__(self, rows: ta.Iterable[Row]) -> None:
        super().__init__()

        self._rows = list(rows)

    @property
    def rows(self) -> ta.List[Row]:
        return self._rows

    def produce_rows(self) -> Rows:
        yield from self._rows


class ListRowSink(RowSink):

    def __init__(self, rows: ta.Optional[ta.List[Row]] = None) -> None:
        super().__init__()

        self._rows = rows if rows is not None else []

    @property
    def rows(self) -> ta.List[Row]:
        return self._rows

    def __iter__(self) -> ta.Iterator[Row]:
        return iter(self._rows)

    def consume_rows(self, rows: ta.Iterable[Row]) -> None:
        self._rows.extend(rows)


class Connector(ta.Generic[ConnectorT, ConnectorConfigT], cfgs.Configurable[ConnectorConfigT], lang.Abstract):

    class Config(els.Element, cfgs.Config, abstract=True):

        dc.metadata({
            els.PhaseFrozen: els.PhaseFrozen(els.Phases.CONNECTORS),
            sm.Name: lambda cls: lang.decamelize(cfgs.get_impl(cls).__name__),
        })

        id: els.Id = dc.field(check=lambda s: isinstance(s, els.Id) and s)

    def __init__(self, config: ConnectorConfigT) -> None:
        super().__init__(config)

    defs.repr('id')

    @property
    def config(self) -> ConnectorConfigT:
        return self._config

    @property
    def id(self) -> els.Id:
        return self._config.id

    def close(self) -> None:
        pass

    @abc.abstractmethod
    def connect(self) -> 'Connection[ConnectorT]':
        raise NotImplementedError

    @classmethod
    def of(cls, obj: ta.Union['Connector', Config]) -> 'Connector':
        if isinstance(obj, Connector):
            return obj
        elif isinstance(obj, Connector.Config):
            return check.isinstance(check.issubclass(cfgs.get_impl(obj), cls)(obj), Connector)
        else:
            raise TypeError(obj)


class Connection(lang.Abstract, ta.Generic[ConnectorT]):

    def __init__(self, ctor: ConnectorT) -> None:
        super().__init__()

        self._ctor: ConnectorT = check.isinstance(ctor, Connector)

        self._reflect_cache: ta.MutableMapping[QualifiedName, ta.Optional[md.Object]] = {}

    defs.repr('ctor')

    @property
    def ctor(self) -> ConnectorT:
        return self._ctor

    def close(self) -> None:
        pass

    @abc.abstractmethod
    def create_row_source(self, query: str) -> RowSource:
        raise NotImplementedError

    @abc.abstractmethod
    def create_row_sink(self, table: QualifiedName) -> RowSink:
        raise NotImplementedError

    def reflect(self, names: ta.Optional[ta.Iterable[QualifiedName]] = None) -> ta.Mapping[QualifiedName, md.Object]:
        if names is not None:
            check.not_isinstance(names, (str, QualifiedName))
            ret = {}
            missing = set()

            for name in names:
                check.isinstance(name, QualifiedName)
                try:
                    obj = self._reflect_cache[name]
                except KeyError:
                    missing.add(name)
                else:
                    if obj is not None:
                        ret[name] = obj

            if missing:
                new = self._reflect(missing)
                for name, obj in new.items():
                    check.not_in(name, ret)
                    check.not_in(name, self._reflect_cache)
                    ret[name] = self._reflect_cache[name] = obj

            return ret

        else:
            raise NotImplementedError

    @abc.abstractmethod
    def _reflect(self, names: ta.Optional[ta.Iterable[QualifiedName]] = None) -> ta.Mapping[QualifiedName, md.Object]:
        raise NotImplementedError
