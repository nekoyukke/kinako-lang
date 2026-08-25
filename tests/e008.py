from tests.util import *

source = """
fn main() {
    let a = 1;

    {
        let a = 2;
        return a;
    }
}
"""

program = parser(source)
ctx = builtin()
collector(source, program, context=ctx)
resolver(source, program, ctx,)

print(ctx)