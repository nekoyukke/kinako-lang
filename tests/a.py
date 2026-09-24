from tests.util import Collector, check, collect, parse, resolve

text = """

fn print(num:int) -> none {
    return none; // 未実装だからしゃーない
}

record Animal {
    var speed: int @owner;
    var age: int @owner;
}

interface AnimalBehavior {
    rq Walk() -> none;
}

class Cat {
    struct use Animal;
    impl use AnimalBehavior {
        def Walk(self:Cat) -> none {
            print(self.Animal.speed);
            return none;
        }
    }
}

let x = 1;
fn main() -> int {
    let y = 1;
    let Taro: Cat @owner;
    Taro.Animal.speed = 1;
    Taro.Animal.age = 18;
    return 0;
}
"""

Collector.clear()
program = parse(text)
ctx = collect(program, text)
ctx = resolve(program, ctx, text)
ctx = check(program, ctx, text)
print(ctx)
