"""Checker の意味検査を守る回帰テスト。"""

from __future__ import annotations

import unittest

from src.frontend.checker import CheckerError
from tests.util import frontend


class CheckerTest(unittest.TestCase):
    def assert_checker_error(self, source: str, code: str) -> None:
        with self.assertRaises(CheckerError) as raised:
            frontend(source)
        self.assertIn(f"[{code}]", raised.exception.message)

    def test_rejects_moves_to_different_targets_in_if_paths(self) -> None:
        self.assert_checker_error(
            """
            fn main() -> int {
                let source = 1;
                if 1 == 1 { let left move source; }
                else { let right move source; }
                return 0;
            }
            """,
            "K4049",
        )

    def test_rejects_move_in_while_with_zero_iteration_path(self) -> None:
        self.assert_checker_error(
            """
            fn main() -> int {
                let source = 1;
                while 1 == 1 { let destination move source; }
                return 0;
            }
            """,
            "K4049",
        )

    def test_allows_access_to_anonymous_struct_field(self) -> None:
        frontend(
            """
            class Cat {
                struct { var age: int @owner; }
            }
            fn main() -> int {
                let cat: Cat @owner;
                cat.age = 1;
                return 0;
            }
            """
        )

    def test_reports_assignment_to_immutable_value(self) -> None:
        self.assert_checker_error(
            """
            fn main() -> int {
                let value = 1;
                value = 2;
                return value;
            }
            """,
            "K4007",
        )

    def test_reports_use_after_move(self) -> None:
        self.assert_checker_error(
            """
            fn main() -> int {
                let source = 1;
                let destination move source;
                return source;
            }
            """,
            "K4031",
        )


if __name__ == "__main__":
    unittest.main()
