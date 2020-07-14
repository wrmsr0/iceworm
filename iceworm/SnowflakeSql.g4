grammar SnowflakeSql;


singleStatement
    : statement ';'? EOF
    ;

statement
    : select
    ;

select
    : cteSelect
    ;

cteSelect
    : (WITH cte (',' cte)*)? unionSelect
    ;

cte
    : identifier AS '(' select ')'
    ;

unionSelect
    : primarySelect unionItem*
    ;

unionItem
    : UNION setQuantifier? primarySelect
    ;

primarySelect
    : SELECT topN? setQuantifier? selectItem (',' selectItem)*
      (FROM relation (',' relation)*)?
      (WHERE where=booleanExpression)?
      (GROUP BY groupBy)?
      (HAVING having=booleanExpression)?
      (ORDER BY sortItem (',' sortItem)*)?
    ;

topN
    : TOP number
    ;

selectItem
    : '*'                           #allSelectItem
    | identifier '.' '*'            #identifierAllSelectItem
    | expression (AS? identifier)?  #expressionSelectItem
    ;

expression
    : booleanExpression
    ;

booleanExpression
    : valueExpression predicate[$valueExpression.ctx]?   #predicatedBooleanExpression
    | op=NOT booleanExpression                           #unaryBooleanExpression
    | booleanExpression op=(AND | OR) booleanExpression  #binaryBooleanExpression
    | booleanExpression '::' identifier                  #castBooleanExpression
    ;

predicate[ParserRuleContext value]
    : cmpOp right=valueExpression                   #cmpPredicate
    | IS NOT? NULL                                  #isNullPredicate
    | NOT? IN '(' expression (',' expression)* ')'  #inListPredicate
    | NOT? IN '(' select ')'                        #inSelectPredicate
    | NOT? IN JINJA                                 #inJinjaPredicate
    | NOT? LIKE expression                          #likePredicate
    | NOT? ILIKE expression                         #ilikePredicate
    ;

valueExpression
    : primaryExpression                                      #primaryValueExpression
    | op=unaryOp valueExpression                             #unaryValueExpression
    | left=valueExpression op=arithOp right=valueExpression  #arithValueExpression
    ;

primaryExpression
    : functionCall                                                     #functionCallExpression
    | CASE (val=expression)? caseItem* (ELSE default=expression)? END  #caseExpression
    | INTERVAL expression                                              #intervalExpression
    | '(' select ')'                                                   #selectExpression
    | '(' expression ')'                                               #parenExpression
    | JINJA                                                            #jinjaExpression
    | simpleExpression                                                 #simplePrimaryExpression
    ;

simpleExpression
    : qualifiedName
    | number
    | string
    | null
    | true
    | false
    ;

functionCall
    : qualifiedName '(' (expression (',' expression)*)? ')' over?  #expressionFunctionCall
    | qualifiedName '(' kwarg (',' kwarg)* ')' over?               #kwargFunctionCall
    | qualifiedName '(' '*' ')' over?                              #starFunctionCall
    ;

kwarg
    : identifier '=>' expression
    ;

caseItem
    : WHEN expression THEN expression
    ;

over
    : OVER '(' (PARTITION BY part=expression)? (ORDER BY sortItem (',' sortItem)*)? ')'
    ;

sortItem
    : expression direction=(ASC | DESC)?
    ;

relation
    : relation AS? identifier                                                      #aliasedRelation
    | left=relation ty=joinType? JOIN right=relation (ON cond=booleanExpression)?  #joinRelation
    | relation PIVOT '('
      func=qualifiedName '(' pc=identifier ')'
      FOR vc=identifier IN '(' (expression (',' expression)*)? ')' ')'             #pivotRelation
    | relation UNPIVOT '('
      vc=identifier
      FOR nc=identifier IN '(' identifierList? ')' ')'                             #unpivotRelation
    | LATERAL relation                                                             #lateralRelation
    | functionCall                                                                 #functionCallRelation
    | '(' select ')'                                                               #selectRelation
    | '(' relation ')'                                                             #parenRelation
    | JINJA                                                                        #jinjaRelation
    | qualifiedName                                                                #tableRelation
    ;

groupBy
    : expression (',' expression)*
    ;

qualifiedName
    : identifier ('.' identifier)*
    ;

identifierList
    : identifier (',' identifier)*
    ;

identifier
    : unquotedIdentifier
    | quotedIdentifier
    ;

quotedIdentifier
    : QUOTED_IDENTIFIER
    ;

number
    : INTEGER_VALUE  #integerNumber
    | DECIMAL_VALUE  #decimalNumber
    | FLOAT_VALUE    #floatNumber
    ;

string
    : STRING
    ;

null
    : NULL
    ;

true
    : TRUE
    ;

false
    : FALSE
    ;

setQuantifier
    : DISTINCT
    | ALL
    ;

joinType
    : INNER
    | LEFT
    | LEFT OUTER
    | RIGHT
    | RIGHT OUTER
    | FULL
    | FULL OUTER
    | CROSS
    | NATURAL
    ;

cmpOp
    : '='
    | '!='
    | '<>'
    | '<'
    | '<='
    | '>'
    | '>='
    ;

arithOp
    : '+'
    | '-'
    | '*'
    | '/'
    | '%'
    | '||'
    ;

unaryOp
    : '+'
    | '-'
    ;

unquotedIdentifier
    : IDENTIFIER

    | LEFT
    | RIGHT

    ;

ALL: 'all';
AND: 'and';
AS: 'as';
ASC: 'asc';
BY: 'by';
CASE: 'case';
CROSS: 'cross';
DESC: 'desc';
DISTINCT: 'distinct';
ELSE: 'else';
END: 'end';
FALSE: 'false';
FOR: 'for';
FROM: 'from';
FULL: 'full';
GROUP: 'group';
HAVING: 'having';
ILIKE: 'ilike';
IN: 'in';
INNER: 'inner';
INTERVAL: 'interval';
IS: 'is';
JOIN: 'join';
LATERAL: 'lateral';
LEFT: 'left';
LIKE: 'like';
NATURAL: 'natural';
NOT: 'not';
NULL: 'null';
ON: 'on';
OR: 'or';
ORDER: 'order';
OUTER: 'outer';
OVER: 'over';
PARTITION: 'partition';
PIVOT: 'pivot';
RIGHT: 'right';
SELECT: 'select';
THEN: 'then';
TOP: 'top';
TRUE: 'true';
UNION: 'union';
UNPIVOT: 'unpivot';
WHEN: 'when';
WHERE: 'where';
WITH: 'with';

STRING
    : '\'' (~'\'' | '\'\'')* '\''
    ;

INTEGER_VALUE
    : DIGIT+
    ;

DECIMAL_VALUE
    : DIGIT+ '.' DIGIT*
    | '.' DIGIT+
    ;

FLOAT_VALUE
    : DIGIT+ ('.' DIGIT*)? EXPONENT
    | '.' DIGIT+ EXPONENT
    ;

IDENTIFIER
    : (LETTER | '_') (LETTER | DIGIT | '_' | '@' | ':' | '$')*
    ;

QUOTED_IDENTIFIER
    : '"' (~'"' | '""')* '"'
    ;

JINJA
    : '{{' .*? '}}'
    ;

fragment EXPONENT
    : [Ee] [+-]? DIGIT+
    ;

fragment DIGIT
    : [0-9]
    ;

fragment LETTER
    : [A-Za-z]
    ;

COMMENT
    : '--' ~[\r\n]* '\r'? '\n'? -> channel(HIDDEN)
    ;

BLOCK_COMMENT
    : '/*' .*? '*/' -> channel(HIDDEN)
    ;

WS
    : [ \t\n\r]+ -> skip
    ;
