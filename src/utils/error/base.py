import traceback

class KinakoRelatedInfo:
    def __init__(self, message: str, line: int, column: int, length: int):
        self.message = message
        self.line = line
        self.column = column
        self.length = length

class KinakoHelp:
    def __init__(self, message: str):
        self.message = message


class KinakoBaseError(Exception):
    RED = "\033[31m"
    YELLOW = "\033[33m"
    RESET = "\033[0m"
    BOLD = "\033[1m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    WHITE = "\033[37m"
    GREEN = "\033[32m"

    def __init__(
        self,
        message: str,
        line: int,
        column: int,
        source: str,
        length: int,
        related: list["KinakoRelatedInfo"] | None = None,
        help: list[KinakoHelp] | None = None
    ):
        self.message = message
        self.line = line
        self.column = column
        self.source = source
        self.length = length
        self.related = related or []
        self.help = help or []
        
        self.stack_frames = traceback.extract_stack()[:-1]
        
        super().__init__(self.__str__())

    @property
    def name(self):
        return self.__class__.__name__
    
    def format_file_only(self) -> str:
        out = ""
        
        for f in self.stack_frames:
                
            out += f'  File "{f.filename}", line {f.lineno}, in {f.name}\n'
            
        return out

    def __str__(self, is_tb: bool = True) -> str:
        tb = self.format_file_only() if is_tb else ""
        
        lines = self.source.splitlines()
        total = len(lines)
        width = len(str(total))

        # --- primary snippet ---
        start = max(1, self.line - 2)
        end = min(total, self.line + 2)

        snippet: list[str] = []
        for i in range(start, end + 1):
            num = str(i).rjust(width)
            line_text = lines[i - 1] if 1 <= i <= total else ""

            if i == self.line:
                col = max(1, min(self.column, len(line_text) + 1))
                tok_len = max(1, self.length)

                before = line_text[:col - 1]
                target = line_text[col - 1: col - 1 + tok_len]
                after = line_text[col - 1 + tok_len:]

                colored = before + self.BG_RED + self.BOLD + target + self.RESET + after
                snippet.append(f"{self.YELLOW}>{num}{self.RESET} {colored}")
            else:
                snippet.append(f" {num} {line_text}")

        # --- related info (note) ---
        related_text = ""
        for r in self.related:
            related_text += f"\n{self.YELLOW}note:{self.RESET} {r.message}\n"
            line_text = lines[r.line - 1] if 1 <= r.line <= total else ""
            num = str(r.line).rjust(width)
            col = max(1, min(r.column, len(line_text) + 1))
            tok_len = max(1, r.length)
            before = line_text[:col - 1]
            target = line_text[col - 1: col - 1 + tok_len]
            after = line_text[col - 1 + tok_len:]
            colored = before + self.BG_RED + self.BOLD + target + self.RESET + after
            related_text += f" {num} {colored}\n"

        # --- help ---
        help_text = ""
        for h in self.help:
            help_text += f"\n{self.GREEN}help:{self.RESET} {self.BG_GREEN}{h.message}{self.RESET}"

        return (
            f"{self.WHITE}\nTraceback (most recent call last):\n"
            f"{tb}"  # 空っぽにならず、呼ばれた順にフレームが並びます
            f'  File "<source>", line {self.line}\n'
            + "\n".join(snippet)
            + f"\n\n{self.RED}{self.name}: {self.message}{self.RESET}\n"
            + related_text
            + help_text
        )