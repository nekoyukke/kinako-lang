from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any, cast
from enum import Enum
from abc import ABC

from src.core.contract.policy.policy import Policy
from src.core.contract.right.right import Right
from src.core.contract.type.type import TypeDef

@dataclass
class Identifier(ABC):
    pass

@dataclass
class Generic_Identifier(Identifier):
    generic: Identifier
    expr: Identifier

@dataclass
class Union_Identifier(Identifier):
    identifiers: list[Identifier]

@dataclass
class Real_Identifier(Identifier):
    name:str

@dataclass
class Contract:
    type: Identifier | None
    right: Identifier | None
    policy: Identifier | None

    type_id: TypeDef | None = None
    right_id: Right | None = None
    policy_id: Policy | None = None


from src.core.symbol.symbol import Symbol
@dataclass
class Parameter:
    name: str
    contract: Contract
    symbol: Symbol | None = None
    
        
@dataclass
class ASTNode(ABC):
    """
    ASTノードの基底
    """
    line: int
    col: int
    len: int

    def _format_repr(self, indent: int = 0) -> str:
        """再帰的に整形されたAST表現を生成する"""
        indent_str = "  " * indent
        next_indent_str = "  " * (indent + 1)
        
        class_name = self.__class__.__name__
        
        # フィールドを取得
        try:
            node_fields = fields(self)
        except TypeError:
            # dataclassではない場合は標準のreprを返す
            return object.__repr__(self)
        
        if not node_fields:
            return f"{class_name}()"
        
        field_strs: list[str] = []
        for f in node_fields:
            # line, column, len フィールドをスキップ
            
            value = getattr(self, f.name)
            formatted_value = self._format_value(value, indent + 1)
            
            # 値が複数行の場合は改行を入れる
            if "\n" in formatted_value:
                field_strs.append(f"{f.name}=\n{next_indent_str}{formatted_value}")
            else:
                field_strs.append(f"{f.name}={formatted_value}")
        
        # フィールド数が多い場合は各フィールドを改行する
        if len(field_strs) > 2 or any("\n" in fs for fs in field_strs):
            fields_str = f",\n{next_indent_str}".join(field_strs)
            return f"{class_name}(\n{next_indent_str}{fields_str}\n{indent_str})"
        else:
            return f"{class_name}({', '.join(field_strs)})"
    
    def _format_value(self, value: list[Any] | Any, indent: int) -> str:
        """値を適切にフォーマットする"""
        indent_str = "  " * indent
        next_indent_str = "  " * (indent + 1)
        
        # None
        if value is None:
            return "None"
        
        # ASTNode（再帰）
        if isinstance(value, ASTNode):
            return value._format_repr(indent=indent)
        
        # Enum
        if isinstance(value, Enum):
            return f"{value.__class__.__name__}.{value.name}"
        
        # リスト
        if isinstance(value, list):
            if not value:
                return "[]"
            nvalue: list[Any] = cast(list[Any], value)
            # 要素が複数またはASTNodeを含む場合は改行
            formatted_items: list[str] = [self._format_value(item, indent + 1) for item in nvalue]
            if len(nvalue) > 2 or any(isinstance(v, ASTNode) for v in nvalue):
                items_str = f",\n{next_indent_str}".join(formatted_items)
                return f"[\n{next_indent_str}{items_str}\n{indent_str}]"
            else:
                return f"[{', '.join(formatted_items)}]"
        
        # 文字列
        if isinstance(value, str):
            return repr(value)
        
        # 数値、真偽値など
        return repr(value)
    
    def __repr__(self) -> str:
        return self._format_repr(indent=0)
    
    def get_child(self) -> list[ASTNode]:
        try:
            node_fields = fields(self)
        except TypeError:
            return []
        result:list[ASTNode] = []
        for i in node_fields:
            value  = getattr(self, i.name)
            if isinstance(value, ASTNode):
                result.append(value)
            elif hasattr(value, "__iter__") and not isinstance(value, (str, bytes)):
                for item in value:
                    if isinstance(item, ASTNode):
                        result.append(item)
        return result
