"""
TODO:
 - newlines delimiting? only one deep

https://golang.org/pkg/reflect/#StructTag lol
/*+ materialization: {wait_time_s: 3600} */
"""
import typing as ta

from omnibus import antlr
from omnibus import check
from omnibus import lang
from omnibus._vendor import antlr4

from ._antlr.MinmlLexer import MinmlLexer
from ._antlr.MinmlParser import MinmlParser
from ._antlr.MinmlVisitor import MinmlVisitor


class NULL(lang.Marker):
    pass


class _ParseVisitor(MinmlVisitor):

    def visit(self, ctx: antlr4.ParserRuleContext):
        check.isinstance(ctx, antlr4.ParserRuleContext)
        return ctx.accept(self)

    def aggregateResult(self, aggregate, nextResult):
        if aggregate is not None:
            check.none(nextResult)
            return aggregate
        else:
            check.none(aggregate)
            return nextResult

    def visitArray(self, ctx: MinmlParser.ArrayContext):
        return [self.visit(e) for e in ctx.value()]

    def visitFalse(self, ctx: MinmlParser.FalseContext):
        return False

    def visitIdentifier(self, ctx:MinmlParser.IdentifierContext):
        return ctx.IDENTIFIER().getText()

    def visitNull(self, ctx: MinmlParser.NullContext):
        return NULL

    def visitNumber(self, ctx: MinmlParser.NumberContext):
        txt = ctx.getText()
        if txt.startswith('0x'):
            return int(txt, 16)
        elif '.' in txt:
            return float(txt)
        else:
            return int(txt)

    def visitObj(self, ctx: MinmlParser.ObjContext):
        return dict(map(self.visit, ctx.pair()))

    def visitPair(self, ctx: MinmlParser.PairContext):
        key = self.visit(ctx.k)
        value = self.visit(ctx.v) if ctx.v is not None else True
        return key, value

    def visitTrue(self, ctx: MinmlParser.TrueContext):
        return True

    def visitString(self, ctx: MinmlParser.StringContext):
        txt = ctx.getText()
        check.state(
            (txt.startswith('"') and txt.endswith('"')) or
            (txt.startswith("'") and txt.endswith("'")))
        return txt[1:-1]


def parse(buf: str) -> ta.Any:
    lexer = MinmlLexer(antlr4.InputStream(buf))
    lexer.removeErrorListeners()
    lexer.addErrorListener(antlr.SilentRaisingErrorListener())

    stream = antlr4.CommonTokenStream(lexer)
    stream.fill()

    parser = MinmlParser(stream)
    parser.removeErrorListeners()
    parser.addErrorListener(antlr.SilentRaisingErrorListener())

    visitor = _ParseVisitor()
    return check.not_none(visitor.visit(parser.root()))
