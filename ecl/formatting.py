"""Text helpers na walang UI: line numbering, severity parsing, line references."""
import re

# Tumatanggap ng "Bug:", "- Bug", "1. Warning", "**Suggestion**" (pagkatapos linisin)
SEVERITY_RE = re.compile(r"^(\W*(?:\d+[.)]\s*)?\W*)(Bug|Warning|Suggestion)\b", re.IGNORECASE)

SEVERITY_TAGS = {"bug": "sev_bug", "warning": "sev_warn", "suggestion": "sev_sugg"}

# "line 42", "Lines 10-15", "linya 7", "line #3 to 9"
LINE_REF_RE = re.compile(
    r"\b(?:lines?|linya)\s*#?\s*(\d+)(?:\s*(?:-|–|to|hanggang)\s*(\d+))?",
    re.IGNORECASE,
)


def number_lines(code):
    lines = code.split("\n")
    width = len(str(len(lines)))
    return "\n".join(f"{i + 1:>{width}} | {ln}" for i, ln in enumerate(lines))


def clean_markdown(line):
    """Tanggalin ang ** at # headings. Naiiwan ang backticks para sa inline code."""
    return re.sub(r"^#{1,6}\s*", "", line.replace("**", ""))


def match_severity(clean_line):
    """Return (prefix, label, rest, tag) o None."""
    m = SEVERITY_RE.match(clean_line)
    if not m:
        return None
    label = m.group(2)
    return m.group(1), label, clean_line[m.end(2):], SEVERITY_TAGS[label.lower()]


def split_line_refs(text):
    """Hatiin ang text sa [(segment, start_line, end_line)]. start_line=None kung hindi reference."""
    out = []
    pos = 0
    for m in LINE_REF_RE.finditer(text):
        if m.start() > pos:
            out.append((text[pos:m.start()], None, None))
        start = int(m.group(1))
        end = int(m.group(2)) if m.group(2) else None
        out.append((m.group(0), start, end))
        pos = m.end()
    if pos < len(text):
        out.append((text[pos:], None, None))
    return out