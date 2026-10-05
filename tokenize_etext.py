#!/usr/bin/env python3
"""
Tokenize the Ramayana e-text directly from the distributed ASCII files and
compare the result with the spreadsheet-derived matrix used in the paper.

Source: https://bombay.indology.info/ramayana/welcome.html  (ASCII = Harvard-Kyoto)
Files:  Ram01.txt ... Ram07.txt  (one per kanda; Ram00.txt is general information)

Format (per the distribution's own "General information" file):
  * header lines begin with "%"
  * every text line begins with an 8-character locator: book(1) sarga(3)
    verse(3) pada-letter(1), e.g. "1001001a"
  * in tristubh and longer metres a ";" separates the padas within a line

USAGE
    python tokenize_etext.py <dir-with-Ram01..07.txt> [analysis_out/word_by_kanda_matrix.csv]

OUTPUT
    analysis_out/word_by_kanda_matrix_etext.csv   (same layout as the paper's matrix)
    a comparison report on stdout
"""
import re
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

COLS = ["bal", "ayodya", "arany", "kiskndha", "sundar", "yuddh", "uttar"]
LOCATOR = re.compile(r"^\d{7}[a-z]\s+")
HK_WORD = re.compile(r"^[A-Za-z']+$")


def tokenize_file(path: Path):
    counts, odd = Counter(), Counter()
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("%"):
            continue                                  # blank or header line
        if not LOCATOR.match(line):
            odd[line[:40]] += 1                       # report, do not count
            continue
        text = LOCATOR.sub("", line).replace(";", " ")
        for tok in text.split():
            tok = tok.strip("|/.,")                   # defensive: stray punctuation
            if HK_WORD.match(tok):
                counts[tok] += 1
            elif tok:
                odd[tok] += 1
    return counts, odd


def main():
    src = Path(sys.argv[1])
    ref_path = sys.argv[2] if len(sys.argv) > 2 else "analysis_out/word_by_kanda_matrix.csv"
    per_kanda, odd_all = {}, Counter()
    for k, col in enumerate(COLS, start=1):
        counts, odd = tokenize_file(src / f"Ram{k:02d}.txt")
        per_kanda[col] = counts
        odd_all.update(odd)
    M = pd.DataFrame(per_kanda).fillna(0).astype(int).reindex(columns=COLS).sort_index()
    Path("analysis_out").mkdir(exist_ok=True)
    M.to_csv("analysis_out/word_by_kanda_matrix_etext.csv")

    print(f"e-text corpus: {M.values.sum():,} tokens, {len(M):,} types")
    if odd_all:
        print("non-word strings skipped (top 15):", odd_all.most_common(15))

    if Path(ref_path).exists():
        R = pd.read_csv(ref_path, index_col=0, keep_default_na=False)
        print(f"\n{'kanda':10}{'etext N':>10}{'sheet N':>10}{'diff%':>8}{'etext V':>10}{'sheet V':>10}{'diff%':>8}")
        for c in COLS:
            n1, n2 = M[c].sum(), R[c].sum()
            v1, v2 = (M[c] > 0).sum(), (R[c] > 0).sum()
            print(f"{c:10}{n1:>10,}{n2:>10,}{100*(n1-n2)/n2:>7.2f}%{v1:>10,}{v2:>10,}{100*(v1-v2)/v2:>7.2f}%")
        both = M.index.intersection(R.index)
        changed = (M.loc[both, COLS] != R.loc[both, COLS]).any(axis=1).sum()
        print(f"\nforms only in e-text: {len(M.index.difference(R.index)):,}; "
              f"only in sheet: {len(R.index.difference(M.index)):,}; "
              f"shared forms with different counts: {changed:,}")
        print("Re-run ramayana_analysis.py on the new matrix to see whether any result changes.")


if __name__ == "__main__":
    main()
