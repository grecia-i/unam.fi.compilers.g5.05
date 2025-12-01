from nltk.tree import Tree

class CCodeGenerator:
    def __init__(self):
        self.code = []
        self.indent_level = 0

    def emit(self, line):
        indentation = "    " * self.indent_level
        self.code.append(indentation + line)

    def get_code(self):
        headers = "#include <stdio.h>\n#include <stdbool.h>\n\n"
        return headers + "\n".join(self.code)

    def visit(self, node):
        if not isinstance(node, Tree):
            return node 
            
        method_name = f'visit_{node.label()}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        res = ""
        for child in node:
            val = self.visit(child)
            if isinstance(val, str):
                res += val
        return res

    # --- GENERAL STRUCTURE ---

    def visit_SourceFile(self, node):
        for child in node:
            if isinstance(child, Tree) and child.label() == "TopLevelDecls":
                self.visit(child)

    def visit_TopLevelDecls(self, node):
        for child in node:
            self.visit(child)

    def visit_TopLevelDecl(self, node):
        self.visit(node[0])

    def visit_FunctionDecl(self, node):
        func_name = node[0][0] # Identifier
        signature = node[1]
        params_node = signature[0]
        result_node = signature[1]
        
        return_type = "void"
        if len(result_node) > 0:
            return_type = self.visit(result_node[0])
        
        if func_name == "main": return_type = "int"

        c_params = []
        if len(params_node) > 0:
            for param in params_node:
                p_name = param[0][0]
                p_type = self.visit(param[1])
                c_params.append(f"{p_type} {p_name}")
        
        self.emit(f"{return_type} {func_name}({', '.join(c_params)}) {{")
        self.indent_level += 1
        
        # The last son is Block
        self.visit(node[-1]) 
        
        self.indent_level -= 1
        self.emit("}")

    def visit_Block(self, node):
        for child in node:
            self.visit(child)

    def visit_StatementList(self, node):
        for child in node:
            self.visit(child)

    #   ---- STATEMENTS ----

    def visit_ExprStmt(self, node):
        val = self.visit(node[0])
        if isinstance(val, str) and val.strip():
            self.emit(f"{val};")

    def visit_ReturnStmt(self, node):
        val = self.visit(node[0])
        self.emit(f"return {val};")

    def visit_IfStmt(self, node):
        cond = self.visit(node[0])
        block = node[1]
        self.emit(f"if ({cond}) {{")
        self.indent_level += 1
        self.visit(block)
        self.indent_level -= 1
        self.emit("}")

    def visit_IfElseStmt(self, node):
        cond = self.visit(node[0])
        block_if = node[1]
        stmt_else = node[2]
        self.emit(f"if ({cond}) {{")
        self.indent_level += 1
        self.visit(block_if)
        self.indent_level -= 1
        self.emit("} else {")
        self.indent_level += 1
        self.visit(stmt_else)
        self.indent_level -= 1
        self.emit("}")

    def visit_ForStmt(self, node):
        child0 = node[0]
        block = node[1]
        
        if child0.label() == "Infinite":
            self.emit("while (true) {")
            self.indent_level += 1
            self.visit(block)
            self.indent_level -= 1
            self.emit("}")
            
        elif child0.label() == "ForClause":
            init = child0[0]
            cond = child0[1]
            post = child0[2]
            
            self.emit("{") 
            self.indent_level += 1
            if init.label() != "EmptyStmt": self.visit(init)
            
            cond_str = self.visit(cond)
            self.emit(f"while ({cond_str}) {{")
            self.indent_level += 1
            self.visit(block)
            
            if post.label() != "EmptyStmt":
                p_str = self.visit(post)
                if p_str and not p_str.endswith(';'): p_str += ";"
                self.emit(p_str)
            
            self.indent_level -= 1
            self.emit("}")
            self.indent_level -= 1
            self.emit("}")
            
        else: 
            cond_str = self.visit(child0)
            self.emit(f"while ({cond_str}) {{")
            self.indent_level += 1
            self.visit(block)
            self.indent_level -= 1
            self.emit("}")

    def visit_IncDecStmt(self, node):
        return f"{self.visit(node[0])}{node[1][0]}"

    # --- VARIABLES ---

    def visit_VarDecl(self, node):
        self.visit(node[0])

    def visit_VarSpecList(self, node):
        for child in node: self.visit(child)

    def visit_VarSpec(self, node):
        ident_list = node[0]
        type_node = node[1]
        expr_list = node[2]

        go_type = "int"
        if isinstance(type_node, Tree) and type_node.label() == "SimpleType":
             go_type = type_node[0]
        c_type = self.map_type(go_type)

        vals = []
        if isinstance(expr_list, Tree) and expr_list.label() == "ExpressionList":
             for expr in expr_list: vals.append(self.visit(expr))
        
        for i, ident in enumerate(ident_list):
            name = ident[0]
            if i < len(vals): self.emit(f"{c_type} {name} = {vals[i]};")
            else: self.emit(f"{c_type} {name};")

    def visit_ShortVarDecl(self, node):
        if len(node) == 1 and isinstance(node[0], Tree) and node[0].label() == 'ShortVarDecl':
             self.visit(node[0])
             return
        ident_list = node[0]
        expr_list = node[1]
        name = ident_list[0][0]
        expr_str = self.visit(expr_list[0])
        
        c_type = "int"
        if expr_str.startswith('"'): c_type = "char*"
        elif "." in expr_str and not expr_str.startswith('"'): c_type = "double"
        
        self.emit(f"{c_type} {name} = {expr_str};")

    def visit_AssignStmt(self, node):
        left_list = node[0]
        right_list = node[2]
        
        left_item = left_list[0]
        name = ""
        if isinstance(left_item, Tree):
             if left_item.label() == 'Identifier': name = left_item[0]
             else: name = self.visit(left_item)
        elif hasattr(left_item, 'getstr'): name = left_item.getstr()
        
        self.emit(f"{name} = {self.visit(right_list[0])};")

    def map_type(self, go_type):
        if go_type == "string": return "char*"
        elif go_type == "float64": return "double"
        elif go_type == "bool": return "bool"
        return "int"

    # --- EXPRESSIONS AND SELECTORS ---

    def visit_CallExpr(self, node):
        func_expr = node[0]
        args_node = node[1]
        
        func_name = self.visit(func_expr)
        
        # Detect fmt.Println
        if func_name in ["fmt.Println", "Println"]:
            if len(args_node) > 0:
                val = self.visit(args_node[0])
                if val.startswith('"'):
                    inner = val.strip('"') 
                    return f'printf("{inner}\\n")'
                else:
                    return f'printf("%d\\n", {val})'
            return 'printf("\\n")'

        return f"{func_name}({self.visit(args_node)})"

    # Maneja: fmt.Println 
    def visit_SelectorExpr(self, node):
        obj = self.visit(node[0]) # fmt
        method = self.visit(node[1]) # Println
        return f"{obj}.{method}"

    def visit_SelectorSuffix(self, node):
        return self.visit(node[0]) # Identifier

    def visit_QualifiedIdent(self, node):
        return f"{self.visit(node[0])}.{self.visit(node[1])}"

    def visit_ArgumentList(self, node):
        args = []
        for child in node:
            val = self.visit(child)
            if val: args.append(str(val))
        return ", ".join(args)

    def visit_ExpressionList(self, node): return self.visit(node[0])
    def visit_Expression(self, node): return self.visit(node[0]) 

    def visit_BinaryExpr(self, node):
        return f"({self.visit(node[0])} {node[1][0]} {self.visit(node[2])})"
    
    def visit_Operand(self, node):
        if len(node) == 1: return self.visit(node[0])
        if len(node) == 3: return f"({self.visit(node[1])})" # ( expr )
        return ""

    # --- HOJAS ---
    def visit_IntLiteral(self, node): return node[0]
    def visit_FloatLiteral(self, node): return node[0]
    def visit_BoolLiteral(self, node): return node[0]
    def visit_Identifier(self, node): return node[0]
    
    def visit_StringLiteral(self, node): 
        val = node[0]
        if not val.startswith('"'):
            return f'"{val}"'
        return val 

    def visit_Literal(self, node):
        val = node[0]
        if isinstance(val, str) and not val.startswith('"') and not val.isdigit():
             return f'"{val}"'
        return val