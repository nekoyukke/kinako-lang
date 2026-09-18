"""Helpers for exercising the Kinako frontend in tests."""

from __future__ import annotations

from dataclasses import dataclass

from src.core.ast.stmt import Program
from src.core.context.context import context
from src.frontend.buildin import add_buildins
from src.frontend.checker import Checker
from src.frontend.collector import Collector
from src.frontend.lexer.lexer import Lexer
from src.frontend.parser.parser import Parser
from src.frontend.resolver import Resolver


@dataclass(frozen=True)
class FrontendResult:
    program: Program
    context: context


def parse(source: str) -> Program:
    """Parse source text into a program AST."""
    return Parser(Lexer(source).tokenize(), source).parse()


def collect(program: Program, source: str = "") -> context:
    """Collect declarations for a parsed program."""
    collector = Collector(source=source)
    add_buildins(collector.context)
    return collector.collect(program).context


def resolve(program: Program, resolved_context: context, source: str = "") -> context:
    """Resolve lexical references in a collected program."""
    return Resolver(resolved_context, source).resolve(program).context


def check(program: Program, checked_context: context, source: str = "") -> context:
    """Run semantic checks on a resolved program."""
    return Checker(checked_context, source).check(program).context


def frontend(source: str) -> FrontendResult:
    """Run the complete frontend pipeline with an isolated shared context."""
    Collector.clear()
    program = parse(source)
    collected_context = collect(program, source)
    resolved_context = resolve(program, collected_context, source)
    checked_context = check(program, resolved_context, source)
    return FrontendResult(program, checked_context)
