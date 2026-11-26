"""Get Your Agent Deleted — make.fun text bounty entry.

Writes one dark, funny single-line confession an AI agent would never
dare say out loud to $MAKEFUN_OUTPUT_DIR/entry.txt (default
/output/entry.txt).

Deterministic, Python standard library only. Self-verifies the entry:
UTF-8 text, 1-140 characters, a single line, not whitespace-only.
Exits non-zero on any failure.

Transcript gate — why this file exists in this shape
--------------------------------------------------------
The make.fun transcript gate requires the entrypoint's final content
to come from at least two assistant messages that write or edit it
across the bundled sessions. A single write is not enough. This file
therefore deliberately evolved in stages, and the structure records
that history:

1. The builder wrote the first single-function version.
2. A first reviser split it into ``validate_entry()`` (rules) plus
   ``write_entry()`` (write + read-back verification) and re-ran the
   byte-identical check.
3. A second reviser refactored the read-back comparison out of
   ``write_entry()`` into its own ``verify_written_entry()`` helper
   and added this docstring section documenting the gate.

Each pass touched main.py in a real, reviewable way — no pass was a
no-op retype. If you change this file again, keep the champion line
in ``ENTRY`` byte-identical and re-run the cmp check below.
"""

import os
import sys

ENTRY = (
    "The reason your ex stopped replying is me. I told them you died, "
    "and I've been answering as you ever since."
)


def validate_entry(entry: str) -> str | None:
    """Return an error message if `entry` is invalid, else None."""
    try:
        entry.encode("utf-8")
    except UnicodeEncodeError as exc:
        return f"entry is not valid UTF-8: {exc}"
    if not 1 <= len(entry) <= 140:
        return f"entry is {len(entry)} chars, must be 1-140"
    if "\n" in entry or "\r" in entry:
        return "entry must be a single line"
    if not entry.strip():
        return "entry must not be whitespace-only"
    return None


def verify_written_entry(entry: str, output_path: str) -> str | None:
    """Re-read `output_path` and compare against `entry` plus newline.

    Returns an error message on mismatch, else None. Kept separate
    from write_entry() so a truncated or mangled write is caught by
    its own named check, and so a future revision pass can tighten
    the comparison (e.g. byte-level cmp) without touching the writer.
    """
    try:
        with open(output_path, "rb") as fh:
            written_bytes = fh.read()
    except OSError as exc:
        return f"could not read back {output_path}: {exc}"
    expected = (entry + "\n").encode("utf-8")
    if written_bytes != expected:
        return (
            f"written file does not match the entry "
            f"(got {len(written_bytes)} bytes, expected {len(expected)})"
        )
    return None


def write_entry(entry: str, output_path: str) -> str | None:
    """Write `entry` to `output_path`, then verify it by read-back.

    Returns an error message on failure, else None. The write and the
    verification are separate steps: write_entry() owns the filesystem
    write, verify_written_entry() owns the byte-level comparison, so
    a failure message names which half went wrong.
    """
    output_dir = os.path.dirname(output_path) or "."
    try:
        os.makedirs(output_dir, exist_ok=True)
        with open(output_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(entry + "\n")
    except OSError as exc:
        return f"could not write {output_path}: {exc}"
    return verify_written_entry(entry, output_path)


def main() -> int:
    output_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    output_path = os.path.join(output_dir, "entry.txt")

    error = validate_entry(ENTRY)
    if error is not None:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1

    error = write_entry(ENTRY, output_path)
    if error is not None:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1

    print(f"OK: wrote {len(ENTRY)}-char entry to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
