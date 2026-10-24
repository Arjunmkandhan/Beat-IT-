"""PHASE 1 - Lexical analysis.
Turns source text into tokens. Because Beat It is indentation based, the lexer
also emits INDENT / DEDENT tokens (exactly like Python's tokenizer)."""
import re
from dataclasses import dataclass
from errors import BeatItError

KEYWORDS = {
    "import", "from", "as", "for", "in", "while", "return",
    "volume", "play", "play_async", "sleep", "range",
    "int", "double", "string", "void",
}
TAB_WIDTH = 4


@dataclass
class Token:
    kind: str      # INT DOUBLE STRING IDENT KEYWORD OP NEWLINE INDENT DEDENT EOF
    value: object
    line: int


TOKEN_RE = re.compile(r'''
    (?P<WS>[ \t]+)
  | (?P<DOUBLE>\d+\.\d+)
  | (?P<INT>\d+)
  | (?P<STRING>"[^"\n]*"|'[^'\n]*')
  | (?P<IDENT>[A-Za-z_][A-Za-z_0-9]*)
  | (?P<OP>\+=|==|!=|<=|>=|[+\-*/<>=()\[\],:.])
''', re.VERBOSE)


def strip_comments(src):
    """Remove // and /* */ comments (but not inside strings). Newlines are kept
    so that line numbers in error messages stay correct."""
    out, i, n, quote = [], 0, len(src), None
    while i < n:
        c = src[i]
        if quote:
            out.append(c)
            if c == quote or c == "\n":
                quote = None
            i += 1
        elif c in "\"'":
            quote = c
            out.append(c)
            i += 1
        elif src.startswith("//", i):
            while i < n and src[i] != "\n":
                i += 1
        elif src.startswith("/*", i):
            end = src.find("*/", i + 2)
            if end == -1:
                raise BeatItError("Unterminated /* comment", src.count("\n", 0, i) + 1)
            out.append("\n" * src.count("\n", i, end))
            i = end + 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def tokenize(source):
    source = strip_comments(source)
    tokens, indents, depth = [], [0], 0
    lineno = 0
    for lineno, raw in enumerate(source.split("\n"), start=1):
        raw = raw.rstrip("\r")
        if raw.strip() == "":
            continue

        if depth == 0:
            expanded = raw.expandtabs(TAB_WIDTH)
            width = len(expanded) - len(expanded.lstrip(" "))
            if width > indents[-1]:
                indents.append(width)
                tokens.append(Token("INDENT", None, lineno))
            else:
                while width < indents[-1]:
                    indents.pop()
                    tokens.append(Token("DEDENT", None, lineno))
                if width != indents[-1]:
                    raise BeatItError("Inconsistent indentation", lineno)

        pos = 0
        while pos < len(raw):
            m = TOKEN_RE.match(raw, pos)
            if not m:
                raise BeatItError(f"Unexpected character {raw[pos]!r}", lineno)
            pos, kind, text = m.end(), m.lastgroup, m.group()
            if kind == "WS":
                continue
            if kind == "INT":
                tokens.append(Token("INT", int(text), lineno))
            elif kind == "DOUBLE":
                tokens.append(Token("DOUBLE", float(text), lineno))
            elif kind == "STRING":
                tokens.append(Token("STRING", text[1:-1], lineno))
            elif kind == "IDENT":
                tokens.append(Token("KEYWORD" if text in KEYWORDS else "IDENT", text, lineno))
            else:
                if text in "([":
                    depth += 1
                elif text in ")]":
                    depth -= 1
                    if depth < 0:
                        raise BeatItError(f"Unmatched {text!r}", lineno)
                tokens.append(Token("OP", text, lineno))

        if depth == 0:
            tokens.append(Token("NEWLINE", None, lineno))

    if depth > 0:
        raise BeatItError("Unclosed '(' or '['", lineno)
    while len(indents) > 1:
        indents.pop()
        tokens.append(Token("DEDENT", None, lineno))
    tokens.append(Token("EOF", None, lineno))
    return tokens