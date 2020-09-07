import typing as ta

from omnibus import check
from omnibus import dataclasses as dc

from .. import elements as els
from ... import datatypes as dt
from ... import metadata as md
from ...types import QualifiedName
from ..utils import parse_simple_select_table
from .connectors import Connection
from .connectors import Connector
from .connectors import RowGen
from .connectors import RowSink
from .connectors import RowSource


TABLE = md.Table(
    ['dual'],
    [
        md.Column('dummy', dt.String()),
    ]
)


class DualConnector(Connector['DualConnector', 'DualConnector.Config']):

    class Config(Connector.Config):
        id: els.Id = dc.field('dual', check=lambda s: isinstance(s, els.Id) and s)

    def __init__(self, config: Config) -> None:
        super().__init__(check.isinstance(config, DualConnector.Config))

    def connect(self) -> 'DualConnection':
        return DualConnection(self)


class DualConnection(Connection[DualConnector]):

    def __init__(self, connector: DualConnector) -> None:
        super().__init__(connector)

    def create_row_source(self, query: str) -> RowSource:
        table_name = parse_simple_select_table(query, star=True)
        if table_name != TABLE.name:
            raise NameError(table_name)
        return DualRowSource()

    def create_row_sink(self, table: QualifiedName) -> RowSink:
        raise TypeError

    def _reflect(self, names: ta.Optional[ta.Iterable[QualifiedName]] = None) -> ta.Mapping[QualifiedName, md.Object]:
        if TABLE.name in names:
            return {TABLE.name: TABLE}
        else:
            return {}


class DualRowSource(RowSource):

    def produce_rows(self) -> RowGen:
        return [{'dummy': 'x'}]