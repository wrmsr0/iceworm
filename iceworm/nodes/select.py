import enum
import typing as ta

from omnibus import collections as ocol
from omnibus import dataclasses as dc

from ..utils import build_enum_value_map
from .base import Expr
from .base import Identifier
from .base import Integer
from .base import Node
from .func import FunctionCall
from .base import SortItem
from .base import SetQuantifier
from .base import QualifiedNameNode


class Relation(Node, abstract=True):
    pass


class Selectable(Node, abstract=True):
    pass


class InSelect(Expr):
    needle: Expr
    haystack: Selectable
    not_: bool = False


class JoinType(enum.Enum):
    DEFAULT = ''
    INNER = 'inner'
    LEFT = 'left'
    LEFT_OUTER = 'left outer'
    RIGHT = 'right'
    RIGHT_OUTER = 'right outer'
    FULL = 'full'
    FULL_OUTER = 'full outer'
    CROSS = 'cross'
    NATURAL = 'natural'


JOIN_TYPE_MAP: ta.Mapping[str, JoinType] = build_enum_value_map(JoinType)


class Join(Relation):
    left: Relation
    type: JoinType
    right: Relation
    condition: ta.Optional[Expr] = None
    using: ta.Optional[ta.Sequence[Identifier]] = dc.field(None, coerce=lambda o: ocol.frozenlist(o) if o is not None else None)  # noqa


class Pivot(Relation):
    relation: Relation
    func: QualifiedNameNode
    pivot_col: Identifier
    value_col: Identifier
    values: ta.Sequence[Expr] = dc.field(coerce=ocol.frozenlist)


class Unpivot(Relation):
    relation: Relation
    value_col: Identifier
    name_col: Identifier
    pivot_cols: ta.Sequence[Identifier] = dc.field(coerce=ocol.frozenlist)


class Lateral(Relation):
    relation: Relation


class FunctionCallRelation(Relation):
    call: FunctionCall


class Table(Relation):
    name: QualifiedNameNode


class AliasedRelation(Relation):
    relation: Relation
    alias: Identifier
    columns: ta.Sequence[Identifier] = dc.field((), coerce=ocol.frozenlist)


class SelectItem(Node, abstract=True):
    pass


class AllSelectItem(SelectItem):
    pass


class IdentifierAllSelectItem(SelectItem):
    identifier: Identifier


class ExprSelectItem(SelectItem):
    value: Expr
    label: ta.Optional[Identifier] = None


class Grouping(Node, abstract=True):
    pass


class FlatGrouping(Grouping):
    items: ta.Sequence[Expr] = dc.field(coerce=ocol.frozenlist)


class GroupingSet(Node):
    items: ta.Sequence[Expr] = dc.field(coerce=ocol.frozenlist)


class SetsGrouping(Grouping):
    sets: ta.Sequence[GroupingSet] = dc.field(coerce=ocol.frozenlist)


class Select(Selectable):
    items: ta.Sequence[SelectItem] = dc.field(coerce=ocol.frozenlist)
    relations: ta.Sequence[Relation] = dc.field((), coerce=ocol.frozenlist)
    where: ta.Optional[Expr] = None
    top_n: ta.Optional[Integer] = None
    set_quantifier: ta.Optional[SetQuantifier] = None
    group_by: ta.Optional[Grouping] = None
    having: ta.Optional[Expr] = None
    qualify: ta.Optional[Expr] = None
    order_by: ta.Optional[ta.Sequence[SortItem]] = dc.field(None, coerce=lambda o: ocol.frozenlist(o) if o is not None else None)  # noqa
    limit: ta.Optional[int] = None


class Cte(Node):
    name: Identifier
    select: Selectable


class CteSelect(Selectable):
    ctes: ta.Sequence[Cte] = dc.field(coerce=ocol.frozenlist)
    select: Selectable


class SetSelectKind(enum.Enum):
    INTERSECT = 'intersect'
    MINUS = 'minus'
    EXCEPT = 'except'
    UNION = 'union'
    UNION_ALL = 'union all'


SET_SELECT_KIND_MAP: ta.Mapping[str, SetSelectKind] = build_enum_value_map(SetSelectKind)


class SetSelectItem(Node):
    kind: SetSelectKind
    right: Selectable
    set_quantifier: ta.Optional[SetQuantifier] = None


class SetSelect(Selectable):
    left: Selectable
    items: ta.Sequence[SetSelectItem] = dc.field(coerce=ocol.frozenlist)


class SelectExpr(Expr):
    select: Selectable


class SelectRelation(Relation):
    select: Selectable