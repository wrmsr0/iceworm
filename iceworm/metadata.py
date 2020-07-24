"""
TODO:
 - *load and treat derived tables as table funcs*
  - transform jinja exprs to params
   - inJinjaPredicate -> array arg + contains pred
 - pk awareness
 - partition / clustering
 - slow vs fast changing
  - refresh interval awareness
 - alchemy reflection bidir adapter
 - serde
 - external tables from files
 - permanence
  - file? multi-git + merge? db?
  - versioning? hash? dumb autoinc?
 - exfiltration?
 - *record all statements as executed w/ pk/partition ranges -> use interval ops for persisted lineage*
"""
import typing as ta

from omnibus import dataclasses as dc
from omnibus import properties

from .datatypes import Datatype
from .types import QualifiedName
from .utils import unique_dict


class Column(dc.Pure):
    name: str
    type: Datatype


class Table(dc.Frozen, final=True, allow_setattr=True, reorder=True):
    name: str
    schema: ta.Optional[str] = dc.field(None, kwonly=True)
    catalog: ta.Optional[str] = dc.field(None, kwonly=True)

    columns: ta.Sequence[Column]

    def __post_init__(self) -> None:
        self._columns_by_name: ta.Mapping[str, Column] = unique_dict((c.name, c) for c in self.columns)

    @property
    def columns_by_name(self) -> ta.Mapping[str, Column]:
        return self._columns_by_name

    @properties.cached
    def qualified_name(self) -> QualifiedName:
        return QualifiedName(*filter(None, [self.catalog, self.schema, self.name]))


class Catalog(dc.Frozen, final=True, allow_setattr=True):
    tables: ta.Sequence[Table]

    def __post_init__(self) -> None:
        self._tables_by_name: ta.Mapping[str, Table] = unique_dict((t.name, t) for t in self.tables)

    @property
    def tables_by_name(self) -> ta.Mapping[str, Table]:
        return self._tables_by_name
