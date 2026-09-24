"""backend LLVM IR を `.ll` テキストへ出力する。"""
from __future__ import annotations
from pathlib import Path
from src.backend.llvm import ir

class LLVMEmissionError(ValueError): pass

class LLVMEmitter:
    def emit(self, module: ir.Module) -> str:
        lines = [f"; ModuleID = '{module.name}'", 'source_filename = "kinako"']
        lines += [self.struct(item) for item in module.type_declarations]
        if module.type_declarations: lines.append("")
        lines += [f"@{item.name} = global {self.ty(item.type)} {self.val(item.initializer)}" for item in module.globals]
        if module.globals: lines.append("")
        lines += [
            f"declare {self.ty(item.type.result)} @{item.name}("
            + ", ".join(self.ty(parameter) for parameter in item.type.parameters)
            + ")"
            for item in module.external_functions
        ]
        if module.external_functions: lines.append("")
        for function in module.functions:
            if len(lines) > 2: lines.append("")
            params = ", ".join(f"{self.ty(p.value.type)} %{p.value.name}" for p in function.parameters)
            lines.append(f"define {self.ty(function.type.result)} @{function.name}({params}) {{")
            for block in function.blocks:
                if block.terminator is None: raise LLVMEmissionError(f"unterminated block: {block.label}")
                lines.append(f"{block.label}:")
                lines += ["  " + self.inst(x) for x in block.instructions]
                lines.append("  " + self.term(block.terminator))
            lines.append("}")
        return "\n".join(lines) + "\n"
    def struct(self, node: ir.StructDeclaration) -> str:
        if node.fields is None: return f"%{node.name} = type opaque"
        return f"%{node.name} = type {{ {', '.join(self.ty(x) for x in node.fields)} }}"
    def ty(self, value: ir.LLVMType) -> str:
        if isinstance(value, ir.IntegerType): return f"i{value.bits}"
        if isinstance(value, ir.FloatType): return value.name
        if isinstance(value, ir.PointerType): return "ptr"
        if isinstance(value, ir.VoidType): return "void"
        if isinstance(value, ir.NamedStructType): return "%" + value.name
        raise LLVMEmissionError(f"unsupported type: {type(value).__name__}")
    def val(self, value: ir.Value) -> str:
        if isinstance(value, ir.LocalValue): return "%" + value.name
        if isinstance(value, ir.GlobalValue): return "@" + value.name
        if isinstance(value, ir.IntegerConstant): return str(value.value)
        if isinstance(value, ir.FloatConstant): return str(value.value)
        if isinstance(value, ir.NullConstant): return "null"
        if isinstance(value, ir.UndefValue): return "undef"
        raise LLVMEmissionError(f"unsupported value: {type(value).__name__}")
    def inst(self, node: ir.Instruction) -> str:
        if isinstance(node, ir.Alloca): return f"%{node.result.name} = alloca {self.ty(node.allocated_type)}"
        if isinstance(node, ir.Load): return f"%{node.result.name} = load {self.ty(node.result.type)}, ptr {self.val(node.address)}"
        if isinstance(node, ir.Store): return f"store {self.ty(node.value.type)} {self.val(node.value)}, ptr {self.val(node.address)}"
        if isinstance(node, ir.Binary): return f"%{node.result.name} = {node.op.value} {self.ty(node.result.type)} {self.val(node.left)}, {self.val(node.right)}"
        if isinstance(node, ir.Compare): return f"%{node.result.name} = icmp {node.op.value} {self.ty(node.left.type)} {self.val(node.left)}, {self.val(node.right)}"
        if isinstance(node, ir.Cast): return f"%{node.result.name} = {node.op.value} {self.ty(node.value.type)} {self.val(node.value)} to {self.ty(node.result.type)}"
        if isinstance(node, ir.Call):
            args = ", ".join(f"{self.ty(x.type)} {self.val(x)}" for x in node.arguments)
            if not isinstance(node.callee.type, ir.FunctionType):
                raise LLVMEmissionError(f"Unkonwn error")
            text = f"call {self.ty(node.callee.type.result)} @{node.callee.name}({args})"
            return text if node.result is None else f"%{node.result.name} = {text}"
        if isinstance(node, ir.InlineAsm):
            effect = " sideeffect" if node.side_effect else ""
            template = node.template.replace('\\', '\\\\').replace('"', '\\"')
            constraints = node.constraints.replace('\\', '\\\\').replace('"', '\\"')
            return f'call void asm{effect} "{template}", "{constraints}"()'
        if isinstance(node, ir.GetElementPtr):
            indices = ", ".join(f"{self.ty(x.type)} {self.val(x)}" for x in node.indices)
            return f"%{node.result.name} = getelementptr {self.ty(node.element_type)}, ptr {self.val(node.address)}, {indices}"
        raise LLVMEmissionError(f"unsupported instruction: {type(node).__name__}")
    def term(self, node: ir.Terminator) -> str:
        if isinstance(node, ir.Return): return "ret void" if node.value is None else f"ret {self.ty(node.value.type)} {self.val(node.value)}"
        if isinstance(node, ir.Branch): return f"br label %{node.target}"
        if isinstance(node, ir.ConditionalBranch): return f"br i1 {self.val(node.condition)}, label %{node.then_target}, label %{node.else_target}"
        raise LLVMEmissionError(f"unsupported terminator: {type(node).__name__}")

def emit_llvm(module: ir.Module) -> str: return LLVMEmitter().emit(module)
def write_llvm(module: ir.Module, path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(emit_llvm(module), encoding="utf-8", newline="\n")
