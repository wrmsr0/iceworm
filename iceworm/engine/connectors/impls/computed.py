import typing as ta

from omnibus import check
from omnibus import collections as col
from omnibus import dataclasses as dc

from .... import metadata as md
from ....types import Code
from ....types import QualifiedName
from ...utils import parse_simple_select_table
from ..base import Connection as _Connection
from ..base import Connector as _Connector
from ..base import RowSink
from ..base import RowSource
from ..base import Rows


class Table(dc.Pure):
    md_table: md.Table
    fn: Code  # [ta.Callable[[], Rows]]


class ComputedConnector(_Connector['ComputedConnector', 'ComputedConnector.Config']):

    class Config(_Connector.Config):
        tables: ta.Sequence[Table] = dc.field(coerce=col.seq)

    def __init__(self, config: Config) -> None:
        super().__init__(check.isinstance(config, ComputedConnector.Config))

        self._tables_by_name: ta.Mapping[QualifiedName, Table] = {t.md_table.name: t for t in self._config.tables}

    def connect(self) -> 'ComputedConnection':
        return ComputedConnection(self)


class ComputedConnection(_Connection[ComputedConnector]):

    def __init__(self, connector: ComputedConnector) -> None:
        super().__init__(connector)

    def create_row_source(self, query: str) -> RowSource:
        table_name = parse_simple_select_table(query, star=True)
        table = self._ctor._tables_by_name[table_name]
        return ComputedRowSource(table)

    def create_row_sink(self, table: QualifiedName) -> RowSink:
        raise TypeError

    def _reflect(self, names: ta.Optional[ta.Iterable[QualifiedName]] = None) -> ta.Mapping[QualifiedName, md.Object]:
        if names:
            ret = {}
            for name in names:
                try:
                    ret[name] = self._ctor._tables_by_name[name].md_table
                except KeyError:
                    pass
            return ret

        else:
            return {n: t.md_table for n, t in self._ctor._tables_by_name.items()}


class ComputedRowSource(RowSource):

    def __init__(self, table: Table) -> None:
        super().__init__()

        self._table = table

    def produce_rows(self) -> Rows:
        return self._table.fn()
