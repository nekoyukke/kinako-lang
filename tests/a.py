from tests.util import *

text = """
let x = 1;
fn main() -> int {
    let y = 1;
    return 0;
}
"""

program = parse(text)
ctx = collect(program, text)
ctx = resolve(program, ctx, text)
print(ctx)