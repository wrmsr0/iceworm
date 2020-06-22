from omnibus import dispatch

from . import nodes as no
from .quoting import quote


def paren(s: str) -> str:
    return '(' + s + ')'


class Renderer(dispatch.Class):
    render = dispatch.property()

    def render(self, node: no.Node) -> str:  # noqa
        raise TypeError(node)

    def render(self, node: no.AliasedRelation) -> str:  # noqa
        return self.render(node.relation) + ((' as ' + self.render(node.alias)) if node.alias is not None else '')

    def render(self, node: no.AllSelectItem) -> str:  # noqa
        return '*'

    def render(self, node: no.BinaryExpr) -> str:  # noqa
        return paren(self.render(node.left)) + ' ' + node.op.value + ' ' + paren(self.render(node.right))

    def render(self, node: no.Case) -> str:  # noqa
        return (
                'case' +
                ((' ' + ' '.join(self.render(i) for i in node.items)) if node.items else '') +
                ((' else ' + self.render(node.default)) if node.items else '') +
                ' end'
        )

    def render(self, node: no.CaseItem) -> str:  # noqa
        return 'when ' + self.render(node.when) + ' then ' + self.render(node.then)

    def render(self, node: no.Cast) -> str:  # noqa
        return self.render(node.value) + ' :: ' + self.render(node.type)

    def render(self, node: no.Cte) -> str:  # noqa
        return self.render(node.name) + ' as ' + paren(self.render(node.select))

    def render(self, node: no.CteSelect) -> str:  # noqa
        return 'with ' + ', '.join(self.render(c) for c in node.ctes) + ' ' + self.render(node.select)

    def render(self, node: no.ExprSelectItem) -> str:  # noqa
        return paren(self.render(node.value)) + ((' as ' + self.render(node.label)) if node.label is not None else '')

    def render(self, node: no.FunctionCall) -> str:  # noqa
        return (
                self.render(node.name) +
                paren(', '.join(paren(self.render(a)) for a in node.args))
                # FIXME: ((' over ' ) ... ) +
        )

    def render(self, node: no.GroupBy) -> str:  # noqa
        return ', '.join(self.render(i) for i in node.items)

    def render(self, node: no.GroupItem) -> str:  # noqa
        return self.render(node.value)

    def render(self, node: no.Identifier) -> str:  # noqa
        return quote(node.name, '"')

    def render(self, node: no.Integer) -> str:  # noqa
        return str(node.value)

    def render(self, node: no.Join) -> str:  # noqa
        return (
                self.render(node.left) +
                ' ' +
                ((node.type.value + ' ') if node.type != no.JoinType.DEFAULT else '') +
                'join ' +
                self.render(node.right) +
                ((' on ' + self.render(node.condition)) if node.condition is not None else '')
        )

    def render(self, node: no.Like) -> str:  # noqa
        return self.render(node.value) + ' like ' + self.render(node.pattern)

    def render(self, node: no.Null) -> str:  # noqa
        return 'null'

    def render(self, node: no.QualifiedName) -> str:  # noqa
        return '.'.join(self.render(i) for i in node.parts)

    def render(self, node: no.Select) -> str:  # noqa
        return (
                'select ' +
                ((node.set_quantifier.value + ' ') if node.set_quantifier is not None else '') +
                ', '.join(self.render(i) for i in node.items) +
                ((' from ' + ', '.join(self.render(r) for r in node.relations)) if node.relations else '') +
                ((' where ' + self.render(node.where)) if node.where is not None else '') +
                ((' group by ' + self.render(node.group_by)) if node.group_by is not None else '') +
                ((' order by ' + ', '.join(self.render(e) for e in node.order_by)) if node.order_by else '')
        )

    def render(self, node: no.SelectExpr) -> str:  # noqa
        return paren(self.render(node.select))

    def render(self, node: no.SelectRelation) -> str:  # noqa
        return paren(self.render(node.select))

    def render(self, node: no.SortItem) -> str:  # noqa
        return self.render(node.value) + ((' ' + node.direction.value) if node.direction is not None else '')

    def render(self, node: no.String) -> str:  # noqa
        return quote(node.value, "'")

    def render(self, node: no.Table) -> str:  # noqa
        return self.render(node.name)

    def render(self, node: no.UnaryExpr) -> str:  # noqa
        return node.op.value + ' ' + paren(self.render(node.value))

    def render(self, node: no.UnionItem) -> str:  # noqa
        return (
                'union ' +
                ((node.set_quantifier.value + ' ') if node.set_quantifier is not None else '') +
                self.render(node.right)
        )

    def render(self, node: no.UnionSelect) -> str:  # noqa
        return (
                self.render(node.left) +
                ((' ' + ' '.join(self.render(i) for i in node.items)) if node.items else '')
        )


def render(node: no.Node) -> str:
    return Renderer().render(node)
