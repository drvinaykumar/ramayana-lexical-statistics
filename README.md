# Lexical Statistics of the Vālmīki Rāmāyaṇa

[![License: MIT](https://img.shields.io/badge/Code-MIT-yellow.svg)](LICENSE)
[![Data: CC BY 4.0](https://img.shields.io/badge/Data-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)

Data and code supplement for:

> Kumar, V. (2026). *Text Analysis of the Vālmīki Rāmāyaṇa with Computational
> Linguistic Techniques.* [journal details to be added on publication]

The repository contains a cleaned word-by-kāṇḍa frequency matrix of the
Vālmīki Rāmāyaṇa (**213,789 tokens; 61,664 distinct surface word forms**) and a
single reproducible Python pipeline that computes every statistic, table, and
figure reported in the paper: lexical diversity measures (TTR, Guiraud, Herdan,
Maas, Yule's K), information-theoretic measures (Shannon entropy, Simpson
concentration, Gini), Zipf's and Heaps' law fits, and inter-kāṇḍa similarity
(cosine on raw and TF–IDF-weighted vectors, Jaccard, Spearman, χ² homogeneity).

## Repository structure

```
.
├── ramayana_analysis.py          # full pipeline: raw workbook → all outputs
├── requirements.txt
├── analysis_out/                 # pre-computed outputs (as used in the paper)
│   ├── word_by_kanda_matrix.csv  # ★ the reconstructed corpus (61,664 forms × 7 kāṇḍas)
│   ├── stats_per_kanda.csv       # paper Tables 1 & 5
│   ├── top_words.csv             # Table 2
│   ├── spectrum.csv              # Table 3
│   ├── heaps.csv                 # Table 4
│   ├── cosine_raw.csv            # Table 6
│   ├── cosine_tfidf.csv          # Table 7
│   ├── jaccard.csv               # Table 8
│   ├── delta_mfw300.csv          # Table 9  (Burrows's Delta, 300 MFW)
│   ├── jsd.csv                   # Section 5.4 (Jensen–Shannon divergence)
│   ├── exclusive_pairs.csv       # Table 10 (size-adjusted exclusive vocabulary)
│   ├── keyness_frame_vs_core.csv # Table 11 (G² keyness, frame vs core)
│   ├── bootstrap_support.txt     # Section 5.4 (cluster support, 200 resamples)
│   ├── spearman.csv              # Section 5.1
│   ├── chi_square.txt            # Section 5.1
│   └── fig_*.png                 # Figures 1–5 (incl. bootstrap dendrogram)
├── CITATION.cff
├── LICENSE
└── README.md
```

## The dataset

`analysis_out/word_by_kanda_matrix.csv` is the corpus described in Section 2 of
the paper. Rows are surface word forms in **Harvard–Kyoto transliteration**
(unlemmatized, sandhi-bound); columns are the seven kāṇḍas:

| column | kāṇḍa | tokens |
|---|---|---|
| `bal` | Bāla | 21,695 |
| `ayodya` | Ayodhyā | 37,444 |
| `arany` | Araṇya | 23,646 |
| `kiskndha` | Kiṣkindhā | 22,447 |
| `sundar` | Sundara | 28,030 |
| `yuddh` | Yuddha | 49,427 |
| `uttar` | Uttara | 31,100 |

**Provenance and reconstruction.** Frequencies derive from the electronic
text of the Baroda Critical Edition (input by Muneo Tokunaga, converted and
revised by John D. Smith), distributed at
<https://bombay.indology.info/ramayana/welcome.html>, tokenized on whitespace. The source spreadsheet stacks seven
per-kāṇḍa frequency lists; within each list only that kāṇḍa's own column is
genuine, because the other columns were filled by a case-insensitive lookup that
conflates Harvard–Kyoto forms differing only in case (e.g. `tasya`/`tasyA`).
`ramayana_analysis.py` therefore rebuilds the matrix from the diagonal blocks,
treating case as significant, and removes verse-locator strings (e.g.
`1076018c`), punctuation, and e-text header tokens. Counts are of surface word
forms, **not lemmata** — see the paper's Section 7 before comparing values
against lemmatized corpora.

**v2.0 note.** Version 1.x used a different cleaning step that read all seven
columns as genuine and merged case-variant forms; it under-counted the corpus by
about 6 %. All outputs in this release supersede v1.x.

## Tokenizing the e-text directly

`tokenize_etext.py` builds the matrix straight from the seven distributed ASCII
files (`Ram01.txt` … `Ram07.txt`) and reports how it differs from the
spreadsheet-derived matrix:

```bash
python tokenize_etext.py path/to/ascii_files analysis_out/word_by_kanda_matrix.csv
```

## Reproducing the paper

```bash
git clone https://github.com/USERNAME/ramayana-lexical-statistics
cd ramayana-lexical-statistics
pip install -r requirements.txt

# Place the raw workbook (not redistributed here) alongside the script, then:
python ramayana_analysis.py Ramayan_copy.xlsx
```

All outputs are rewritten into `analysis_out/`. Without the raw workbook, the
pre-computed outputs committed in `analysis_out/` are the exact files used in
the paper; every downstream statistic can be recomputed from
`word_by_kanda_matrix.csv` alone.

## Key results at a glance

* Corpus: 213,789 tokens; 61,664 types; 70.2 % hapax legomena.
* Zipf slope −0.88 (f ≥ 5, R² = 0.997); Heaps' law V = 2.77·N^0.818 (R² = 0.999).
* Grammatical register nearly uniform across all seven books (Cramér's V ≈ 0.10;
  full-vector cosine 0.87–0.96).
* Content vocabulary partitions the epic into narrative blocks; the disputed
  frame books **Bāla and Uttara show their strongest content affinity with each
  other**, and Kiṣkindhā–Sundara–Yuddha form a cohesive "vānara" cluster.
* The frame-pair affinity holds across independent tests (Section 5.4 of the
  paper): under **Burrows's Delta** Uttara is Bāla's nearest neighbour at every
  feature-set size from 100 to 1,000 most frequent words; the pair clusters
  together in **84–90 % of bootstrap resamples**; and it shows the highest
  vocabulary overlap and the strongest size-adjusted enrichment of
  **exclusively shared vocabulary** (obs/exp = 1.47, p < 10⁻¹²), whose
  **G² keyness profile** is the language of sages, hermitage, and formal address.

## Citing

Please cite the paper (see `CITATION.cff`; GitHub's **Cite this repository**
button generates BibTeX/APA). If you use the dataset independently of the
paper, cite this repository by URL and release tag (v2.0) and acknowledge
the GRETIL source text.

## Licenses

Code: [MIT](LICENSE). Derived data in `analysis_out/`: CC BY 4.0, with
attribution additionally due to the GRETIL e-text (Tokunaga/Smith). The raw
source workbook is not redistributed in this repository.

## Contact

Vinay Kumar — Thapar School of Liberal Arts & Sciences, Thapar Institute of
Engineering & Technology, Patiala, India.
