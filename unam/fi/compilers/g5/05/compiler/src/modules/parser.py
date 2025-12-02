from rply import ParserGenerator
# from parser.src.modules.tree import *
from nltk.tree import *
from collections import defaultdict
from pathlib import Path
import json
from nltk import Tree as Tree

class Parser:
    def __init__(self):
        self.pg = ParserGenerator(
            # TOKEN NAMES
            [
                # KEYWORDS
                "KW_BREAK","KW_DEFAULT", "KW_FUNC",  
                "KW_CASE", 
                "KW_STRUCT", "KW_ELSE", 
                "KW_PACKAGE", "KW_SWITCH", 
                "KW_IF", "KW_TYPE", "KW_CONTINUE", "KW_FOR", 
                "KW_IMPORT", "KW_RETURN","KW_VAR", 
                # TYPES
                "TYPE_INT", "TYPE_FLOAT32", "TYPE_FLOAT64", 
                "TYPE_BOOL", "TYPE_STR", 
                # LITERALS
                "LIT_FLOAT", "LIT_INT", "LIT_STR", "LIT_BOOL", 
                # OPERATORS
                "OP_PLUSEQ", "OP_PLUSPLUS", "OP_MINUSEQ", "OP_MINUSMINUS", 
                "OP_MULEQ", "OP_DIVEQ", "OP_MODEQ", 
                "OP_ANDEQ", "OP_ANDAND", "OP_ANDNOTEQ",  
                "OP_OREQ", "OP_OROR", "OP_XOREQ", "OP_SHLEQ", "OP_SHREQ", 
                "OP_EQEQ", "OP_NEQ", "OP_LTE", "OP_GTE", "OP_COLONEQ", 
                "OP_PLUS", "OP_MINUS", "OP_MUL", "OP_DIV", 
                "OP_MOD",   
                "OP_EQ", "OP_LT", "OP_GT", "OP_NOT", "OP_DOT", 
                # PUNCTUATION
                "PUNC_LPAREN", "PUNC_RPAREN", "PUNC_LBRACK", "PUNC_RBRACK", 
                "PUNC_LBRACE", "PUNC_RBRACE", "PUNC_COMMA", "PUNC_SEMI", 
                "PUNC_COLON",  "IDENT"

                # MISSING SYNTAX FOR TOKENS
                # KW_INTERFACE, KW_SELECT, KW_DEFER, KW_GO, KW_MAP,
                # KW_CHAN, KW_GOTO, KW_CONST, KW_FALLTHROUGH, KW_RANGE,
                # OP_LEFTARROW, OP_ANDNOT, OP_DOTDOTDOT, OP_SHL, OP_SHR
                # OP_TILDE, "OP_AND", "OP_OR", "OP_XOR",
            
            ], precedence=[
                ("left", ["OP_OROR"]),
                ("left", ["OP_ANDAND"]),
                ("nonassoc", ["OP_EQEQ", "OP_NEQ", "OP_LT", "OP_GT", "OP_LTE", "OP_GTE"]),
                ("left", ["OP_PLUS", "OP_MINUS"]),
                ("left", ["OP_MUL", "OP_DIV", "OP_MOD"]),
                ("right", ["OP_NOT"]),
                ("right", ["KW_ELSE"]), 
            ]
            
        )

        self.parse()
        self.parser = self.pg.build()

    def parse(self):
        '''
        Syntax      = { Production } .
        Production  = production_name "=" [ Expression ] "." .
        Expression  = Term { "|" Term } .
        Term        = Factor { Factor } .
        Factor      = production_name | token [ "…" token ] | Group | Option | Repetition .
        Group       = "(" Expression ")" .
        Option      = "[" Expression "]" .
        Repetition  = "{" Expression "}" .
        SourceFile = PackageClause ";" { ImportDecl ";" } { TopLevelDecl ";" } .
        '''
        ## --------------------------------------------
        # GRAMMAR GRAMMAR
        @self.pg.production("SourceFile : PackageClause PUNC_SEMI ImportDecls TopLevelDecls")
        @self.pg.production("SourceFile : PackageClause ImportDecls TopLevelDecls")
        def source_file(p):
            # normalize list length
            if len(p) == 4:
                return Tree("SourceFile", [p[0], p[2], p[3]])
            else:
                return Tree("SourceFile", [p[0], p[1], p[2]])

        # PACKAGE 
        @self.pg.production("PackageClause : KW_PACKAGE IDENT")
        def package_clause(p):
            return Tree("PackageClause", [Tree("package", []), Tree("Identifier", [p[1].getstr()])])

        # IMPORTS
        @self.pg.production("ImportDecls : ")
        def empty_imports(p):
            return Tree("ImportDecls", [])

        @self.pg.production("ImportDecls : ImportDecls ImportDecl")
        #@self.pg.production("ImportDecls : ImportDecls ImportDecl PUNC_SEMI")
        def import_list(p):
            return Tree("ImportDecls", list(p[0]) + [p[1]])

        @self.pg.production("ImportDecl : KW_IMPORT ImportSpec")
        def import_decl(p):
            return Tree("ImportDecl", [p[1]])

        @self.pg.production("ImportSpec : LIT_STR")
        @self.pg.production("ImportSpec : OP_DOT LIT_STR")  # . "package"
        @self.pg.production("ImportSpec : IDENT LIT_STR")  # alias "package"
        def import_spec(p):
            if len(p) == 1:
                return Tree("ImportSpec", [Tree("path", [p[0].getstr().strip('"')])])
            elif p[0].getstr() == '.':
                return Tree("ImportSpec", [Tree("dot", []), Tree("path", [p[1].getstr()])])
            else:
                return Tree("ImportSpec", [Tree("alias", [p[0].getstr()]), Tree("path", [p[1].getstr()])])
        
        # TOP LEVEL DECLARATIONS
        @self.pg.production("TopLevelDecls : ")
        def empty_top(p):
            return Tree("TopLevelDecls", [])

        @self.pg.production("TopLevelDecls : TopLevelDecls TopLevelDecl")
        #@self.pg.production("TopLevelDecls : TopLevelDecls TopLevelDecl PUNC_SEMI")
        def top_level_list(p):
            return Tree("TopLevelDecls", list(p[0]) + [p[1]])

        @self.pg.production("TopLevelDecl : TypeDecl")
        @self.pg.production("TopLevelDecl : FunctionDecl")
        @self.pg.production("TopLevelDecl : VarDecl")
        @self.pg.production("TopLevelDecl : MethodDecl")
        def top_level_decl(p):
            return Tree("TopLevelDecl", [p[0]])

        @self.pg.production("TypeDecl : KW_TYPE IDENT Type")
        def type_decl(p):
            return Tree("TypeDecl", [
                Tree("Identifier", [p[1].getstr()]), 
                p[2]
            ])

        # FUNCTION DECLARATION
        @self.pg.production("FunctionDecl : KW_FUNC IDENT Signature Block")
        #@self.pg.production("FunctionDecl : KW_FUNC IDENT Signature Type Block")  # Return type
        def function_decl(p):
            if len(p) == 4:
                return Tree("FunctionDecl", [Tree("Identifier", [p[1].getstr()]), p[2], p[3]])
            else:
                return Tree("FunctionDecl", [Tree("Identifier", [p[1].getstr()]), p[2], p[3], p[4]])
        
        # Method declaration
        @self.pg.production("MethodDecl : KW_FUNC Receiver IDENT Signature Block")
        def method_decl(p):
            return ("MethodDecl", p[1], p[2], p[3], p[4])  # Receiver, Name, Sig, Body

        @self.pg.production("Receiver : PUNC_LPAREN ParametersOpt PUNC_RPAREN")
        def receiver(p):
            return ("Receiver", p[1])


        @self.pg.production("TopLevelDecl : error")
        def top_level_error(p):
            print(f"TOP LEVEL ERROR - Unmatched tokens: {p}")
            return Tree("ErrorDecl", [])

        @self.pg.production("Signature : PUNC_LPAREN ParametersOpt PUNC_RPAREN ResultOpt")
        def signature(p):
            return Tree("Signature", [p[1], p[3]])  # Parameters, Result

        # Parameters
        @self.pg.production("ParametersOpt : ")
        def empty_parameters(p):
            return Tree("Parameters", [])

        @self.pg.production("ParametersOpt : ParameterList")
        def parameters(p):
            return p[0]

        @self.pg.production("ParameterList : ParameterDecl")
        def single_parameter(p):
            return Tree("Parameters", [p[0]])

        @self.pg.production("ParameterList : ParameterList PUNC_COMMA ParameterDecl")
        def multiple_parameters(p):
            return Tree("Parameters", list(p[0]) + [p[2]])

        @self.pg.production("ParameterDecl : IDENT Type")
        def parameter_decl(p):
            return Tree("ParameterDecl", [
                Tree("Identifier", [p[0].getstr()]), 
                p[1]
            ])

        # Results
        @self.pg.production("ResultOpt : ")
        def empty_result(p):
            return Tree("Result", [])

        @self.pg.production("ResultOpt : Type")
        def result_type(p):
            return Tree("Result", [p[0]])

        # Assignment operators
        @self.pg.production("AssignOp : OP_EQ")
        @self.pg.production("AssignOp : OP_PLUSEQ")
        @self.pg.production("AssignOp : OP_MINUSEQ")
        @self.pg.production("AssignOp : OP_MULEQ")
        @self.pg.production("AssignOp : OP_DIVEQ")
        @self.pg.production("AssignOp : OP_MODEQ")
        @self.pg.production("AssignOp : OP_ANDEQ")
        @self.pg.production("AssignOp : OP_OREQ")
        @self.pg.production("AssignOp : OP_XOREQ")
        @self.pg.production("AssignOp : OP_SHLEQ")
        @self.pg.production("AssignOp : OP_SHREQ")
        @self.pg.production("AssignOp : OP_ANDNOTEQ")
        @self.pg.production("AssignOp : OP_COLONEQ")
        def assign_op(p):
            return Tree("AssignOp", [p[0].getstr()])
    
        # VAR DECLARATIONS
        @self.pg.production("VarDecl : KW_VAR VarSpecList")
        def var_decl(p):
            return Tree("VarDecl", [p[1]])

        @self.pg.production("VarSpecList : VarSpec")
        def varspeclist_single(p):
            return Tree("VarSpecList", [p[0]])

        @self.pg.production("VarSpecList : VarSpecList PUNC_SEMI VarSpec")
        def varspeclist_multi(p):
            return Tree("VarSpecList", list(p[0]) + [p[2]])

        # VAR SPEC
        @self.pg.production("VarSpec : IDENTList AssignOp ExpressionList")
        def var_spec_untyped(p):
            return Tree("VarSpec", [p[0], Tree("Type", []), p[2]])

        @self.pg.production("VarSpec : IDENTList Type AssignOp ExpressionList")
        def var_spec_typed_init(p):
            return Tree("VarSpec", [p[0], p[1], p[3]])

        @self.pg.production("VarSpec : IDENTList Type")
        def var_spec_typed(p):
            return Tree("VarSpec", [p[0], p[1], Tree("ExpressionList", [])])

        # Mult ident
        @self.pg.production("IDENTList : IDENT")
        def identlist_single(p):
            return Tree("IdentifierList", [Tree("Identifier", [p[0].getstr()])])

        @self.pg.production("IDENTList : IDENTList PUNC_COMMA IDENT")
        def identlist_multi(p):
            return Tree("IdentifierList", list(p[0]) + [Tree("Identifier", [p[2].getstr()])])

        # Mult expr
        @self.pg.production("ExpressionList : Expression")
        def exprlist_single(p):
            return Tree("ExpressionList", [p[0]])

        @self.pg.production("ExpressionList : ExpressionList PUNC_COMMA Expression")
        def exprlist_multi(p):
            return Tree("ExpressionList", list(p[0]) + [p[2]])
                
        #### EXPRESSIONS

        # EXPRESSIONS with manual precedence
        @self.pg.production("Expression : LogicalOrExpression")
        def expression(p):
            return p[0]

        @self.pg.production("LogicalOrExpression : LogicalAndExpression")
        @self.pg.production("LogicalOrExpression : LogicalOrExpression OP_OROR LogicalAndExpression")
        def logical_or(p):
            if len(p) == 1:
                return p[0]
            return Tree("BinaryExpr", [p[0], Tree("Operator", [p[1].getstr()]), p[2]])

        @self.pg.production("LogicalAndExpression : EqualityExpression")
        @self.pg.production("LogicalAndExpression : LogicalAndExpression OP_ANDAND EqualityExpression")
        def logical_and(p):
            if len(p) == 1:
                return p[0]
            return Tree("BinaryExpr", [p[0], Tree("Operator", [p[1].getstr()]), p[2]])

        @self.pg.production("EqualityExpression : RelationalExpression")
        @self.pg.production("EqualityExpression : EqualityExpression OP_EQEQ RelationalExpression")
        @self.pg.production("EqualityExpression : EqualityExpression OP_NEQ RelationalExpression")
        def equality_expression(p):
            if len(p) == 1:
                return p[0]
            return Tree("BinaryExpr", [p[0], Tree("Operator", [p[1].getstr()]), p[2]])

        @self.pg.production("RelationalExpression : AdditiveExpression")
        @self.pg.production("RelationalExpression : RelationalExpression OP_LT AdditiveExpression")
        @self.pg.production("RelationalExpression : RelationalExpression OP_GT AdditiveExpression")
        @self.pg.production("RelationalExpression : RelationalExpression OP_LTE AdditiveExpression")
        @self.pg.production("RelationalExpression : RelationalExpression OP_GTE AdditiveExpression")
        def relational_expression(p):
            if len(p) == 1:
                return p[0]
            return Tree("BinaryExpr", [p[0], Tree("Operator", [p[1].getstr()]), p[2]])

        @self.pg.production("AdditiveExpression : MultiplicativeExpression")
        @self.pg.production("AdditiveExpression : AdditiveExpression OP_PLUS MultiplicativeExpression")
        @self.pg.production("AdditiveExpression : AdditiveExpression OP_MINUS MultiplicativeExpression")
        def additive_expression(p):
            if len(p) == 1:
                return p[0]
            return Tree("BinaryExpr", [p[0], Tree("Operator", [p[1].getstr()]), p[2]])

        @self.pg.production("MultiplicativeExpression : UnaryExpression")
        @self.pg.production("MultiplicativeExpression : MultiplicativeExpression OP_MUL UnaryExpression")
        @self.pg.production("MultiplicativeExpression : MultiplicativeExpression OP_DIV UnaryExpression")
        @self.pg.production("MultiplicativeExpression : MultiplicativeExpression OP_MOD UnaryExpression")
        def multiplicative_expression(p):
            if len(p) == 1:
                return p[0]
            return Tree("BinaryExpr", [p[0], Tree("Operator", [p[1].getstr()]), p[2]])

        @self.pg.production("UnaryExpression : PrimaryExpression")
        @self.pg.production("UnaryExpression : OP_PLUS UnaryExpression")
        @self.pg.production("UnaryExpression : OP_MINUS UnaryExpression")
        @self.pg.production("UnaryExpression : OP_NOT UnaryExpression")
        def unary_expression(p):
            if len(p) == 1:
                return p[0]
            return Tree("UnaryExpr", [Tree("Operator", [p[0].getstr()]), p[1]])

        # Conversion
        @self.pg.production("PrimaryExpression : Type PUNC_LPAREN Expression PUNC_RPAREN")
        def conversion_expr(p):
            return Tree("Conversion", [p[0], p[2]])
        
        # Method expression: T.Method
        @self.pg.production("PrimaryExpression : Type OP_DOT IDENT")
        def method_expr(p):
            return Tree("MethodExpr", [p[0], Tree("Identifier", [p[2].getstr()])])


        @self.pg.production("PrimaryExpression : CompositeLit")
        def primary_composite(p):
            #return p[0] # Type, Elements
            return Tree("PrimaryExpression", [p[0]])
        
        @self.pg.production("QualifiedIdent : IDENT OP_DOT IDENT")
        def qualified_ident(p):
            return Tree("QualifiedIdent", [
                Tree("Identifier", [p[0].getstr()]),
                Tree("Identifier", [p[2].getstr()])
            ])
        
        @self.pg.production("PrimaryExpression : Operand PrimarySuffixList")
        def primary_expression(p):
            base = p[0]
            suffix_list = p[1]
            suffixes = list(suffix_list) if isinstance(suffix_list, Tree) else []

            expr = base
            for suffix in suffixes:
                kind = suffix.label()
                if kind == "SelectorSuffix":
                    expr = Tree("SelectorExpr", [expr] + list(suffix))
                elif kind == "IndexSuffix":
                    expr = Tree("IndexExpr", [expr] + list(suffix))
                elif kind == "CallSuffix":
                    expr = Tree("CallExpr", [expr] + list(suffix))
            return expr

        # Mult suffix
        @self.pg.production("PrimarySuffixList : ")
        def empty_primary_suffix_list(p):
            return Tree("PrimarySuffixList", [])

        @self.pg.production("PrimarySuffixList : PrimarySuffixList PrimarySuffix")
        def primary_suffix_list(p):
            suffix_list = p[0]
            suffix = p[1]
            # Extend existing list
            if isinstance(suffix_list, Tree):
                return Tree("PrimarySuffixList", list(suffix_list) + [suffix])
            else:
                return Tree("PrimarySuffixList", [suffix_list, suffix])

        @self.pg.production("PrimarySuffix : OP_DOT IDENT")
        def selector_suffix(p):
            return Tree("SelectorSuffix", [Tree("Identifier", [p[1].getstr()])])

        @self.pg.production("PrimarySuffix : PUNC_LBRACK Expression PUNC_RBRACK")
        def index_suffix(p):
            return Tree("IndexSuffix", [p[1]])

        @self.pg.production("PrimarySuffix : PUNC_LPAREN ArgumentListOpt PUNC_RPAREN")
        def call_suffix(p):
            return Tree("CallSuffix", [p[1]])
        
        @self.pg.production("PrimarySuffix : PUNC_LBRACK Expression PUNC_COLON Expression PUNC_RBRACK")
        def slice_suffix(p):
            return Tree("SliceSuffix", [p[1], p[3]])

        # Type assertion: x.(Type)
        @self.pg.production("PrimarySuffix : OP_DOT PUNC_LPAREN Type PUNC_RPAREN")
        def type_assert_suffix(p):
            return Tree("TypeAssertSuffix", [p[2]])

        # Composite literal
        @self.pg.production("CompositeLit : Type PUNC_LBRACE ElementListOpt PUNC_RBRACE")
        def composite_literal(p):
            return Tree("CompositeLit", [p[0], p[2]])
 
        # Element list
        @self.pg.production("ElementListOpt : ")
        def element_list_empty(p):
            return Tree("ElementList", [])

        @self.pg.production("ElementListOpt : ElementList")
        def element_list_opt(p):
            return p[0]

        @self.pg.production("ElementList : KeyedElement")
        def element_list_single(p):
            return Tree("ElementList", [p[0]])

        @self.pg.production("ElementList : ElementList PUNC_COMMA KeyedElement")
        def element_list_multiple(p):
            return Tree("ElementList", list(p[0]) + [p[2]])

        # Key-value pairs in struct literals
        @self.pg.production("KeyedElement : Key PUNC_COLON Expression")
        def keyed_element(p):
            return Tree("KeyedElement", [p[0], p[2]])

        @self.pg.production("Key : IDENT")
        def key_ident(p):
            return Tree("Key", [p[0].getstr()])
        
        @self.pg.production("Operand : Literal")
        @self.pg.production("Operand : OperandName")
        def operand_lit(p):
            return p[0]  
        @self.pg.production("Operand : IDENT")  
        def operand_ident(p):
            return Tree("Identifier", [p[0].getstr()])
        ######
        #@self.pg.production("Operand : OperandName")
        #@self.pg.production("Operand : MethodExpr")
        
        @self.pg.production("Operand : PUNC_LPAREN Expression PUNC_RPAREN")
        def operand(p):
            if len(p) == 1:
                return p[0]  # Return Literal or Identifier directly
            else:
                return p[1]        
        
        @self.pg.production("OperandName : QualifiedIdent")
        def operand_qualified_ident(p):
            return p[0]

        # ARGUMENT LISTS
        @self.pg.production("ArgumentListOpt : ")
        def empty_arglist(p):
            return Tree("ArgumentList", [])

        @self.pg.production("ArgumentListOpt : ArgumentList")
        def nonempty_arglist(p):
            return p[0]

        @self.pg.production("ArgumentList : Expression")
        def single_arg(p):
            return Tree("ArgumentList", [p[0]])

        @self.pg.production("ArgumentList : ArgumentList PUNC_COMMA Expression")
        def multiple_args(p):
            return Tree("ArgumentList", list(p[0]) + [p[2]])

        @self.pg.production("Block : PUNC_LBRACE StatementList PUNC_RBRACE")
        def block(p):
            return Tree("Block", [p[1]])

        @self.pg.production("StatementList : ")
        def empty_stmt_list(p):
            return Tree("StatementList", [])

        @self.pg.production("StatementList : StatementList Statement")
        #@self.pg.production("StatementList : StatementList Statement PUNC_SEMI")
        def stmt_list(p):
            return Tree("StatementList", list(p[0]) + [p[1]])

        @self.pg.production("Statement : Expression")
        def stmt_expr(p):
            return Tree("ExprStmt", [p[0]])

        @self.pg.production("Statement : ShortVarDecl")  # Short variable declaration
        def stmt_short_var(p):
            return Tree("ShortVarDecl", [p[0]])

        # SHORT VARIABLE DECLARATION (:=)
        @self.pg.production("ShortVarDecl : IDENTList OP_COLONEQ ExpressionList")
        def short_var_decl(p):
            return Tree("ShortVarDecl", [p[0], p[2]])

        # Statements
        @self.pg.production("Statement : VarDecl")
        @self.pg.production("Statement : TypeDecl")
        @self.pg.production("Statement : FunctionDecl")
        def stmt_decl(p):
            return Tree("DeclStmt", [p[0]])

        @self.pg.production("Statement : ExpressionList AssignOp ExpressionList")
        def stmt_assignment(p):
            return Tree("AssignStmt", [p[0], p[1], p[2]])

        @self.pg.production("Statement : KW_RETURN Expression")
        def stmt_return(p):
            return Tree("ReturnStmt", [p[1]])

        # REEMPLAZAR las tres producciones actuales con:

        # if básico: if (condición) { bloque }
        @self.pg.production("Statement : KW_IF PUNC_LPAREN Expression PUNC_RPAREN Block")
        def if_stmt(p):
            return Tree("IfStmt", [p[2], p[4]])  # Condition, Block

        @self.pg.production("Statement : KW_IF Expression Block")
        def if_stmt_nop(p):
            return Tree("IfStmt", [p[1], p[2]])

        # if-else: if (condición) { bloque } else { bloque }
        @self.pg.production("Statement : KW_IF PUNC_LPAREN Expression PUNC_RPAREN Block KW_ELSE Block")
        def if_else_stmt(p):
            return Tree("IfElseStmt", [p[2], p[4], p[6]])  # Condition, IfBlock, ElseBlock

        # if-else if-else (anidado)
        @self.pg.production("Statement : KW_IF PUNC_LPAREN Expression PUNC_RPAREN Block KW_ELSE Statement")
        def if_else_chain(p):
            # El "Statement" en KW_ELSE Statement puede ser otro if o un bloque
            return Tree("IfElseStmt", [p[2], p[4], p[6]])  # Condition, IfBlock, ElsePart

        # SWITCH / CASE / DEFAULT
        @self.pg.production("Statement : KW_SWITCH Expression PUNC_LBRACE CaseClauses PUNC_RBRACE")
        def switch_stmt(p):
            return Tree("SwitchStmt", [p[1], p[3]])

        @self.pg.production("CaseClauses : ")
        def empty_case_clauses(p):
            return Tree("CaseClauses", [])

        @self.pg.production("CaseClauses : CaseClauses CaseClause")
        def case_clauses(p):
            return Tree("CaseClauses", list(p[0]) + [p[1]])

        @self.pg.production("CaseClause : KW_CASE Expression PUNC_COLON StatementList")
        def case_clause(p):
            return Tree("CaseClause", [p[1], p[3]])

        @self.pg.production("CaseClause : KW_DEFAULT PUNC_COLON StatementList")
        def default_clause(p):
            return Tree("DefaultClause", [p[2]])

        # FOR LOOP
        @self.pg.production("Statement : KW_FOR Block")
        def for_infinite(p):
            return Tree("ForStmt", [Tree("Infinite", []), p[1]])

        # FOR LOOP
        @self.pg.production("Statement : KW_FOR Expression Block")
        def for_loop(p):
            return Tree("ForStmt", [p[1], p[2]])

        @self.pg.production("Statement : KW_FOR ForClause Block")
        def for_with_clause(p):
            return Tree("ForStmt", [p[1], p[2]])

        @self.pg.production("ForClause : InitStmt PUNC_SEMI Expression PUNC_SEMI PostStmt")
        def for_clause(p):
            return Tree("ForClause", [p[0], p[2], p[4]])

        @self.pg.production("InitStmt : SimpleStmt")
        @self.pg.production("InitStmt : ")
        def init_stmt(p):
            if len(p) == 0:
                return Tree("EmptyStmt", [])
            return p[0]

        @self.pg.production("PostStmt : SimpleStmt")
        @self.pg.production("PostStmt : ")
        def post_stmt(p):
            if len(p) == 0:
                return Tree("EmptyStmt", [])
            return p[0]

        # SIMPLE STATEMENTS (can be used in for loops)
        @self.pg.production("SimpleStmt : ShortVarDecl")
        @self.pg.production("SimpleStmt : Expression")
        @self.pg.production("SimpleStmt : IncDecStmt")
        def simple_stmt(p):
            return p[0]

        # INCREMENT/DECREMENT STATEMENTS (i++, i--)
        @self.pg.production("IncDecStmt : Expression OP_PLUSPLUS")
        @self.pg.production("IncDecStmt : Expression OP_MINUSMINUS")
        def inc_dec_stmt(p):
            return Tree("IncDecStmt", [p[0], Tree("Operator", [p[1].getstr()])])

        # BREAK / CONTINUE
        @self.pg.production("Statement : KW_BREAK")
        def break_stmt(p):
            return Tree("BreakStmt", [])

        @self.pg.production("Statement : KW_CONTINUE")
        def continue_stmt(p):
            return Tree("ContinueStmt", [])

        # Type => BuiltinType | IDENT | ArrayType | SliceType | StructType

        @self.pg.production("Type : SimpleType")
        @self.pg.production("Type : StructType")
        @self.pg.production("Type : ArrayType")
        @self.pg.production("Type : SliceType")
        def type_any(p):
            return p[0]

        # Type => BuiltinType | IDENT | ArrayType | SliceType | StructType
        @self.pg.production("SimpleType : TYPE_INT")
        @self.pg.production("SimpleType : TYPE_FLOAT32")
        @self.pg.production("SimpleType : TYPE_FLOAT64")
        @self.pg.production("SimpleType : TYPE_BOOL")
        @self.pg.production("SimpleType : TYPE_STR")
        @self.pg.production("SimpleType : IDENT")
        def simple_type(p):
            token = p[0]
            if token.name.startswith('TYPE_'):
                return Tree("SimpleType", [token.getstr()])
            else:
                return Tree("TypeName", [token.getstr()])

        @self.pg.production("FieldDeclList : ")
        def empty_field_decls(p):
            return Tree("FieldDecls", [])

        @self.pg.production("FieldDeclList : FieldDeclList FieldDecl PUNC_SEMI")
        def field_decl_list(p):
            return Tree("FieldDecls", list(p[0]) + [p[1]])

        @self.pg.production("StructType : KW_STRUCT PUNC_LBRACE StructFieldDecls PUNC_RBRACE")
        def struct_type(p):
            return Tree("StructType", [p[2]])

        @self.pg.production("StructFieldDecls : ")
        def empty_struct_fields(p):
            return Tree("StructFieldDecls", [])

        @self.pg.production("StructFieldDecls : StructFieldDeclList")
        def struct_fields(p):
            return p[0]

        @self.pg.production("StructFieldDeclList : StructFieldDecl")
        def single_struct_field(p):
            return Tree("StructFieldDecls", [p[0]])

        @self.pg.production("StructFieldDeclList : StructFieldDeclList StructFieldDecl")
        def multiple_struct_fields(p):
            return Tree("StructFieldDecls", list(p[0]) + [p[1]])

        @self.pg.production("StructFieldDecl : FieldDecl PUNC_SEMI")
        @self.pg.production("StructFieldDecl : FieldDecl")
        def struct_field_decl(p):
            return Tree("StructFieldDecl", [p[0]])

        @self.pg.production("FieldDecl : IDENTList Type")
        @self.pg.production("FieldDecl : IDENTList Type Tag")
        def field_decl(p):
            if len(p) == 2:
                return Tree("FieldDecl", [p[0], p[1], Tree("Tag", [])])
            else:
                return Tree("FieldDecl", [p[0], p[1], p[2]])
        
        @self.pg.production("Tag : LIT_STR")
        def tag(p):
            return Tree("Tag", [p[0].getstr()])

        # ARRAY AND SLICE TYPES
        @self.pg.production("ArrayType : PUNC_LBRACK Expression PUNC_RBRACK Type")
        def array_type(p):
            return Tree("ArrayType", [p[1], p[3]])

        @self.pg.production("SliceType : PUNC_LBRACK PUNC_RBRACK Type")
        def slice_type(p):
            return Tree("SliceType", [p[2]])

        # Literals
        @self.pg.production("Literal : LIT_INT")
        @self.pg.production("Literal : LIT_FLOAT")
        @self.pg.production("Literal : LIT_STR")
        @self.pg.production("Literal : LIT_BOOL")
        def literal(p):
            token_type = p[0].gettokentype() # Ej: "LIT_INT"
            token_value = p[0].getstr()
            # Guardamos el tipo de literal en el label del sub-árbol
            if token_type == 'LIT_INT':
                return Tree("IntLiteral", [token_value])
            elif token_type == 'LIT_STR':
                return Tree("StringLiteral", [token_value])
            elif token_type == 'LIT_FLOAT':
                return Tree("FloatLiteral", [token_value])
            elif token_type == 'LIT_BOOL':
                return Tree("BoolLiteral", [token_value])
        
        @self.pg.error
        def error_handle(token):
            print("\033[91mERROR SINTACTICO: No se esperaba encontrar el Token '{}' en la línea '{}' columna '{}'".format(token.value,str(token.getsourcepos().lineno),str(token.getsourcepos().colno)))
            raise ValueError(token)
        
        # '''
    
    def get_parser(self):
        return self.parser