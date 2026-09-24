from tests.util import Collector, check, collect, parse, resolve

text = """

fn main() -> int {
    return 0;
}
"""

Collector.clear()
program = parse(text)
ctx = collect(program, text)
ctx = resolve(program, ctx, text)
ctx = check(program, ctx, text)

print(ctx)