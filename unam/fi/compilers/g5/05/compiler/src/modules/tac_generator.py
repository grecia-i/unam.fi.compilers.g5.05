# modules/tac_generator.py
from nltk.tree import Tree

class TACGenerator:
    def __init__(self, printer=None):
        self.temp_counter = 0
        self.label_counter = 0
        self.string_counter = 0
        self.code = []
        self.current_function = None
        self.printer = printer or (lambda msg: None)
        
    def new_temp(self):
        temp = f"t{self.temp_counter}"
        self.temp_counter += 1
        return temp
        
    def new_label(self):
        label = f"L{self.label_counter}"
        self.label_counter += 1
        return label
        
    def generate_tac(self, ast):
        """Genera TAC a partir del AST (usando el mismo árbol que semantic analyzer)"""
        self.code = []
        self.temp_counter = 0
        self.label_counter = 0
        self.current_function = None
        
        self.printer(f"[TAC] Processing AST of type: {type(ast)}")
        
        # Handle different AST structures
        if isinstance(ast, Tree):
            if ast.label() == 'SourceFile':
                self.process_source_file(ast)
            else:
                # If it's not a SourceFile, try to process it directly
                self.process_top_level_decl(ast)
        elif isinstance(ast, list):
            self.printer(f"[TAC] Processing list with {len(ast)} elements")
            for item in ast:
                self.process_top_level_decl(item)
        else:
            self.printer(f"[TAC] Warning: Unknown AST type: {type(ast)}")
        
        return self.code

    def process_source_file(self, node):
        """Process SourceFile node"""
        self.printer(f"[TAC] Processing SourceFile with {len(node)} children")
        
        for child in node:
            if isinstance(child, Tree):
                child_label = child.label()
                self.printer(f"[TAC] Processing child: {child_label}")
                
                if child_label == 'PackageClause':
                    continue
                elif child_label == 'ImportDecls':
                    continue
                elif child_label == 'TopLevelDecls':
                    self.process_top_level_decls(child)
                else:
                    # Try to process unknown nodes as top level declarations
                    self.process_top_level_decl(child)
            else:
                self.printer(f"[TAC] Skipping non-tree child: {child}")

    def process_top_level_decls(self, node):
        """Process TopLevelDecls node"""
        self.printer(f"[TAC] Processing TopLevelDecls with {len(node)} children")
        
        for i, decl in enumerate(node):
            self.printer(f"[TAC] Processing declaration {i}: {type(decl)}")
            if isinstance(decl, Tree):
                self.process_top_level_decl(decl)

    def process_top_level_decl(self, decl):
        """Process a top level declaration"""
        if not isinstance(decl, Tree):
            self.printer(f"[TAC] Skipping non-tree declaration: {decl}")
            return
            
        decl_type = decl.label()
        self.printer(f"[TAC] Processing {decl_type}")
        
        if decl_type == 'TopLevelDecl':
            if len(decl) > 0 and isinstance(decl[0], Tree):
                inner_decl = decl[0]
                inner_type = inner_decl.label()
                self.printer(f"[TAC] Inner declaration: {inner_type}")
                
                if inner_type == 'FunctionDecl':
                    self.process_function_decl(inner_decl)
                else:
                    self.printer(f"[TAC] Unsupported inner declaration: {inner_type}")
            else:
                self.printer(f"[TAC] Empty or invalid TopLevelDecl")
        elif decl_type == 'FunctionDecl':
            self.process_function_decl(decl)
        else:
            self.printer(f"[TAC] Unsupported top level declaration: {decl_type}")
    
    def process_function_decl(self, func_decl):
        """Process FunctionDecl node"""
        if not isinstance(func_decl, Tree) or len(func_decl) < 2:
            self.printer(f"[TAC] Invalid FunctionDecl: {func_decl}")
            return
            
        # Extract function name
        func_name_node = func_decl[0]
        if isinstance(func_name_node, Tree) and func_name_node.label() == 'Identifier':
            func_name = func_name_node[0] if len(func_name_node) > 0 else "unknown"
        else:
            func_name = "unknown"
        
        self.printer(f"[TAC] Processing function: {func_name}")
        
        # Set current function
        self.current_function = func_name
        
        # Add function label
        self.code.append(f"FUNC {func_name}:")
        
        # Process parameters if they exist
        if len(func_decl) > 1:
            signature = func_decl[1]
            if isinstance(signature, Tree) and signature.label() == 'Signature':
                if len(signature) > 1:
                    params = signature[1]
                    if isinstance(params, Tree) and params.label() == 'Parameters':
                        # Parameters are already in scope, no TAC needed
                        self.printer(f"[TAC] Function {func_name} has parameters")
        
        # Process function body
        if len(func_decl) > 2:
            body = func_decl[2]
            if isinstance(body, Tree) and body.label() == 'Block':
                self.process_block(body)
            else:
                self.printer(f"[TAC] Function {func_name} has no block body")
        else:
            self.printer(f"[TAC] Function {func_name} has no body")
        
        # Add function end marker
        self.code.append(f"END_FUNC {func_name}")
        self.current_function = None
    
    def process_block(self, block):
        """Process Block node"""
        if not isinstance(block, Tree):
            return
            
        self.printer(f"[TAC] Processing block with {len(block)} children")
        
        for child in block:
            if isinstance(child, Tree) and child.label() == 'StatementList':
                self.process_statement_list(child)
                break  # Usually there's only one StatementList

    def process_statement_list(self, stmt_list):
        """Process StatementList node"""
        if not isinstance(stmt_list, Tree):
            return
            
        self.printer(f"[TAC] Processing statement list with {len(stmt_list)} statements")
        
        for stmt in stmt_list:
            self.process_statement(stmt)
    
    def process_statement(self, stmt):
        """Process individual statement"""
        if not isinstance(stmt, Tree):
            self.printer(f"[TAC] Skipping non-tree statement: {stmt}")
            return
            
        stmt_type = stmt.label()
        self.printer(f"[TAC] Processing statement: {stmt_type}")
        
        if stmt_type == 'IfStmt':
            self.process_if_statement(stmt)
        elif stmt_type == 'IfElseStmt':  # <-- AÑADE ESTA LÍNEA
            self.process_if_else_statement(stmt)
        elif stmt_type == 'DeclStmt':
            self.process_decl_statement(stmt)
        elif stmt_type == 'ForStmt':
            self.process_for_statement(stmt)
        elif stmt_type == 'ReturnStmt':
            self.process_return_statement(stmt)
        elif stmt_type == 'ExprStmt':
            self.process_expr_statement(stmt)
        elif stmt_type == 'AssignStmt':
            self.process_assign_statement(stmt)
        elif stmt_type == 'ShortVarDecl':
            self.process_short_var_decl(stmt)
        elif stmt_type == 'IncDecStmt':
            self.process_inc_dec_statement(stmt)
        else:
            self.printer(f"[TAC] Unsupported statement type: {stmt_type}")
    
    def process_if_statement(self, if_stmt):
        """Process IfStmt node"""
        if not isinstance(if_stmt, Tree) or len(if_stmt) < 3:
            self.printer(f"[TAC] Invalid IfStmt: {if_stmt}")
            return
            
        self.printer(f"[TAC] Processing if statement")
        
        # Process condition
        condition = if_stmt[0]
        cond_temp = self.process_expression(condition)
        
        false_label = self.new_label()
        end_label = self.new_label()
        
        # Jump to false branch if condition is false
        self.code.append(f"IF_FALSE {cond_temp} GOTO {false_label}")
        
        # Process true branch
        true_block = if_stmt[1]
        if isinstance(true_block, Tree) and true_block.label() == 'Block':
            self.process_block(true_block)
        self.code.append(f"GOTO {end_label}")
        
        # False label
        self.code.append(f"LABEL {false_label}:")
        
        # Process false branch if it exists
        if len(if_stmt) > 2:
            false_block = if_stmt[2]
            if isinstance(false_block, Tree) and false_block.label() == 'Block':
                self.process_block(false_block)
        
        # End label
        self.code.append(f"LABEL {end_label}:")

    def process_if_else_statement(self, if_else_stmt):
        if not isinstance(if_else_stmt, Tree) or len(if_else_stmt) < 3:
            self.printer(f"[TAC] Invalid IfElseStmt: {if_else_stmt}")
            return
            
        self.printer(f"[TAC] Processing if-else statement")
        condition = if_else_stmt[0]
        cond_temp = self.process_expression(condition)
        false_label = self.new_label()
        end_label = self.new_label()
        
        self.code.append(f"IF_FALSE {cond_temp} GOTO {false_label}")
        
        true_block = if_else_stmt[1]
        if isinstance(true_block, Tree) and true_block.label() == 'Block':
            self.process_block(true_block)
        self.code.append(f"GOTO {end_label}")
        
        self.code.append(f"LABEL {false_label}:")
        
        false_block = if_else_stmt[2]
        if isinstance(false_block, Tree) and false_block.label() == 'Block':
            self.process_block(false_block)
        
        self.code.append(f"LABEL {end_label}:")
    
    def process_decl_statement(self, decl_stmt):
        """Process DeclStmt node"""
        if not isinstance(decl_stmt, Tree) or len(decl_stmt) < 1:
            return
            
        var_decl = decl_stmt[0]
        if isinstance(var_decl, Tree) and var_decl.label() == 'VarDecl':
            if len(var_decl) > 0:
                var_spec_list = var_decl[0]
                if isinstance(var_spec_list, Tree) and var_spec_list.label() == 'VarSpecList':
                    for var_spec in var_spec_list:
                        if isinstance(var_spec, Tree) and var_spec.label() == 'VarSpec':
                            self.process_var_spec(var_spec)

    def process_var_spec(self, var_spec):
        """Process VarSpec node"""
        if not isinstance(var_spec, Tree) or len(var_spec) < 3:
            return
            
        # Get variable names
        ident_list_node = var_spec[0]
        if isinstance(ident_list_node, Tree) and ident_list_node.label() == 'IdentifierList':
            var_names = []
            for ident_node in ident_list_node:
                if isinstance(ident_node, Tree) and ident_node.label() == 'Identifier':
                    var_names.append(ident_node[0] if len(ident_node) > 0 else "unknown")
            
            # Get initial values if they exist
            expr_list_node = var_spec[2]
            if isinstance(expr_list_node, Tree) and expr_list_node.label() == 'ExpressionList':
                values = []
                for expr in expr_list_node:
                    values.append(self.process_expression(expr))
                
                for var_name, value in zip(var_names, values):
                    self.code.append(f"{var_name} = {value}")
    
    def process_for_statement(self, for_stmt):
        """Process ForStmt node"""
        if not isinstance(for_stmt, Tree) or len(for_stmt) < 2:
            self.printer(f"[TAC] Invalid ForStmt: {for_stmt}")
            return
            
        self.printer(f"[TAC] Processing for statement")
        
        start_label = self.new_label()
        end_label = self.new_label()
        
        # Process initialization
        if len(for_stmt) > 0:
            for_clause = for_stmt[0]
            if isinstance(for_clause, Tree) and for_clause.label() == 'ForClause':
                # Initialization
                if len(for_clause) > 0:
                    init_stmt = for_clause[0]
                    if isinstance(init_stmt, Tree) and init_stmt.label() == 'ShortVarDecl':
                        self.process_short_var_decl(init_stmt)
                
                # Condition label
                condition_label = self.new_label()
                self.code.append(f"GOTO {condition_label}")
                
                # Loop body label
                self.code.append(f"LABEL {start_label}:")
                
                # Loop body
                if len(for_stmt) > 1:
                    loop_body = for_stmt[1]
                    if isinstance(loop_body, Tree) and loop_body.label() == 'Block':
                        self.process_block(loop_body)
                
                # Increment
                if len(for_clause) > 2:
                    inc_stmt = for_clause[2]
                    self.process_statement(inc_stmt)
                
                # Condition check
                self.code.append(f"LABEL {condition_label}:")
                if len(for_clause) > 1:
                    condition = for_clause[1]
                    cond_temp = self.process_expression(condition)
                    self.code.append(f"IF_TRUE {cond_temp} GOTO {start_label}")
                
                self.code.append(f"LABEL {end_label}:")
    
    def process_return_statement(self, return_stmt):
        """Process ReturnStmt node"""
        if not isinstance(return_stmt, Tree):
            return
            
        self.printer(f"[TAC] Processing return statement")
        
        if len(return_stmt) > 0:
            return_value = self.process_expression(return_stmt[0])
            self.code.append(f"RETURN {return_value}")
        else:
            self.code.append("RETURN")
    
    def process_expr_statement(self, expr_stmt):
        """Process ExprStmt node"""
        if not isinstance(expr_stmt, Tree) or len(expr_stmt) < 1:
            return
            
        expr = expr_stmt[0]
        if isinstance(expr, Tree) and expr.label() == 'CallExpr':
            self.process_call_expression(expr)
    
    def process_assign_statement(self, assign_stmt):
        """Process AssignStmt node"""
        if not isinstance(assign_stmt, Tree) or len(assign_stmt) < 3:
            return
            
        # Left side
        left_exprs = assign_stmt[0]
        if isinstance(left_exprs, Tree) and left_exprs.label() == 'ExpressionList':
            left_vars = []
            for expr in left_exprs:
                left_vars.append(self.process_expression(expr))
        
        # Right side
        right_exprs = assign_stmt[2]
        if isinstance(right_exprs, Tree) and right_exprs.label() == 'ExpressionList':
            right_values = []
            for expr in right_exprs:
                right_values.append(self.process_expression(expr))
        
        for left_var, right_value in zip(left_vars, right_values):
            self.code.append(f"{left_var} = {right_value}")
    
    def process_short_var_decl(self, short_decl):
        """Process ShortVarDecl node"""
        if not isinstance(short_decl, Tree):
            return
            
        self.printer(f"[TAC] Processing short var declaration")
        
        # Handle nested ShortVarDecl structure
        if len(short_decl) > 0 and isinstance(short_decl[0], Tree) and short_decl[0].label() == 'ShortVarDecl':
            # This is the nested case from the AST
            inner_decl = short_decl[0]
            self.process_short_var_decl(inner_decl)
            return
            
        if len(short_decl) < 2:
            return
            
        identifiers = short_decl[0]
        expressions = short_decl[1]
        
        var_names = []
        if isinstance(identifiers, Tree) and identifiers.label() == 'IdentifierList':
            for ident in identifiers:
                if isinstance(ident, Tree) and ident.label() == 'Identifier':
                    var_names.append(ident[0] if len(ident) > 0 else "unknown")
        
        values = []
        if isinstance(expressions, Tree) and expressions.label() == 'ExpressionList':
            for expr in expressions:
                values.append(self.process_expression(expr))
        
        for var_name, value in zip(var_names, values):
            self.code.append(f"{var_name} = {value}")
    
    def process_inc_dec_statement(self, inc_dec_stmt):
        """Process IncDecStmt node"""
        if not isinstance(inc_dec_stmt, Tree) or len(inc_dec_stmt) < 2:
            return
            
        var_node = inc_dec_stmt[0]
        op_node = inc_dec_stmt[1]
        
        if isinstance(var_node, Tree) and var_node.label() == 'Identifier':
            var_name = var_node[0] if len(var_node) > 0 else "unknown"
        else:
            var_name = "unknown"
            
        if isinstance(op_node, Tree) and op_node.label() == 'Operator':
            operator = op_node[0] if len(op_node) > 0 else "++"
        else:
            operator = "++"
        
        if operator == '++':
            self.code.append(f"{var_name} = {var_name} + 1")
        elif operator == '--':
            self.code.append(f"{var_name} = {var_name} - 1")
    
    def process_call_expression(self, call_expr):
        """Process CallExpr node"""
        if not isinstance(call_expr, Tree) or len(call_expr) < 2:
            return ""
            
        # Handle function call
        func_expr = call_expr[0]
        func_name = ""
        
        if isinstance(func_expr, Tree):
            if func_expr.label() == 'QualifiedIdent':
                # Qualified call like fmt.Println
                if len(func_expr) >= 2:
                    pkg_node = func_expr[0]
                    func_node = func_expr[1]
                    if isinstance(pkg_node, Tree) and pkg_node.label() == 'Identifier':
                        pkg = pkg_node[0] if len(pkg_node) > 0 else "unknown"
                    else:
                        pkg = "unknown"
                        
                    if isinstance(func_node, Tree) and func_node.label() == 'Identifier':
                        func = func_node[0] if len(func_node) > 0 else "unknown"
                    else:
                        func = "unknown"
                        
                    func_name = f"{pkg}.{func}"
            elif func_expr.label() == 'Identifier':
                # Direct function call
                func_name = func_expr[0] if len(func_expr) > 0 else "unknown"
        
        # Process arguments
        args = []
        if len(call_expr) > 1:
            args_expr = call_expr[1]
            if isinstance(args_expr, Tree) and args_expr.label() == 'ArgumentList':
                for arg in args_expr:
                    if isinstance(arg, Tree) and arg.label() == 'CallExpr':
                        # Handle nested function calls
                        result_temp = self.new_temp()
                        nested_func_name = self.process_call_expression(arg)
                        self.code.append(f"{result_temp} = CALL {nested_func_name}")
                        args.append(result_temp)
                    else:
                        args.append(self.process_expression(arg))
        
        args_str = " ".join(args)
        
        # For functions that return values, store result in temp
        if func_name != "fmt.Println":
            result_temp = self.new_temp()
            self.code.append(f"{result_temp} = CALL {func_name} {args_str}")
            return result_temp
        else:
            self.code.append(f"CALL {func_name} {args_str}")
            return ""
    
    def process_expression(self, expr):
        """Process expression node and return temporary holding result"""
        if not isinstance(expr, Tree):
            return str(expr)
            
        expr_type = expr.label()
        
        if expr_type == 'Identifier':
            if len(expr) > 0:
                return expr[0]
            return "unknown_id"
        
        elif expr_type == 'IntLiteral':
            if len(expr) > 0:
                return expr[0]
            return "0"

        elif expr_type == 'StringLiteral' or expr_type == 'String':
            # create a unique data label and emit DATA entry
            if len(expr) > 0:
                raw = expr[0]
            else:
                raw = '""'
            label = f"str_{self.string_counter}"
            self.string_counter += 1
            # ensure raw is properly quoted (keep original quotes if present)
            value = raw if (raw.startswith('"') and raw.endswith('"')) else f'"{raw}"'
            self.code.append(f"DATA {label} = {value}")
            return label
        
        elif expr_type == 'BinaryExpr':
            if len(expr) < 3:
                return "0"
                
            left = self.process_expression(expr[0])
            operator_node = expr[1]
            right = self.process_expression(expr[2])
            
            operator = ""
            if isinstance(operator_node, Tree) and operator_node.label() == 'Operator':
                operator = operator_node[0] if len(operator_node) > 0 else "+"
            else:
                operator = "+"
            
            temp = self.new_temp()
            
            # Map operators to TAC operations
            op_map = {
                '+': 'ADD',
                '-': 'SUB',
                '*': 'MUL',
                '/': 'DIV',
                '<=': 'LE',
                '<': 'LT',
                '>=': 'GE',
                '>': 'GT',
                '==': 'EQ',
                '!=': 'NE'
            }
            
            if operator in op_map:
                tac_op = op_map[operator]
                self.code.append(f"{temp} = {left} {tac_op} {right}")
            else:
                self.code.append(f"{temp} = {left} {operator} {right}")
            
            return temp
        
        elif expr_type == 'CallExpr':
            return self.process_call_expression(expr)
        
        else:
            # For unsupported expressions, create a temporary
            temp = self.new_temp()
            self.code.append(f"{temp} = {expr_type}_EXPR")
            return temp