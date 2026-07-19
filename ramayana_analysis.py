#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lexical-statistical analysis of the Valmiki Ramayana
====================================================
Reproduces every number, table, and figure in the manuscript
"Text Analysis of the Valmiki Ramayana with Computational Linguistic Techniques".

INPUT
    Ramayan_copy.xlsx          raw word-by-kanda frequency workbook
                               (sheet "With repetition"; Harvard-Kyoto transliteration)

OUTPUT (written to ./analysis_out/)
    word_by_kanda_matrix.csv   cleaned frequency matrix (Section 2 of the paper)
    stats_per_kanda.csv        Tables 1 & 5 (all diversity/entropy/Zipf measures)
    top_words.csv              Table 2
    spectrum.csv               Table 3
    heaps.csv                  Table 4
    cosine_raw.csv             Table 6
    cosine_tfidf.csv           Table 7
    jaccard.csv                Table 8
    spearman.csv               (reported in Section 5.1)
    chi_square.txt             Section 5.1 homogeneity test
    fig_sizes.png, fig_zipf.png, fig_coverage.png, fig_cosine.png   Figures 1-4

USAGE
    python ramayana_analysis.py [path/to/Ramayan_copy.xlsx]

Dependencies: pandas, numpy, scipy, matplotlib, openpyxl.
"""

import os, re, sys, json
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ----------------------------------------------------------------------
# 0. Configuration
# ----------------------------------------------------------------------
SRC   = sys.argv[1] if len(sys.argv) > 1 else "Ramayan_copy.xlsx"
OUT   = "analysis_out"
COLS  = ["bal", "ayodya", "arany", "kiskndha", "sundar", "yuddh", "uttar"]
NAMES = {"bal": "Bala", "ayodya": "Ayodhya", "arany": "Aranya",
         "kiskndha": "Kishkindha", "sundar": "Sundara",
         "yuddh": "Yuddha", "uttar": "Uttara"}
os.makedirs(OUT, exist_ok=True)

# ----------------------------------------------------------------------
# 1. Cleaning  (paper, Section 2)
# ----------------------------------------------------------------------
def is_junk(w: str) -> bool:
    """Verse locators (e.g. 1076018c), punctuation/markup, header artefacts."""
    w = str(w)
    if re.fullmatch(r"\d{7}[ac]", w):          # GRETIL verse references
        return True
    if not re.fullmatch(r"[a-zA-Z']+", w):     # symbols, digits
        return True
    if w == "ASCII":                           # e-text header artefact
        return True
    return False


def load_and_clean(path: str) -> pd.DataFrame:
    raw = pd.read_excel(path, sheet_name="With repetition")
    raw = raw.dropna(subset=["Words"]).drop_duplicates()          # (iii) exact dup rows
    raw = raw[~raw["Words"].map(is_junk)]                         # (i)+(ii) junk tokens
    M = raw.groupby("Words")[COLS].max()                          # conflicting dup rows

    # (iv) transliteration "twins": same case-folded form, identical vectors
    #      or vectors agreeing in >= 6 of 7 kanda coordinates -> merge by max.
    M = M.copy()
    M["fold"] = M.index.str.lower()
    rows = {}
    def canonical(ws):        # prefer the variant not ending in mangled 'A'
        return sorted(ws, key=lambda w: (w.endswith("A"), w))[0]
    for _, grp in M.groupby("fold"):
        idx = list(grp.index)
        if len(idx) == 1:
            rows[idx[0]] = grp.loc[idx[0], COLS].values
            continue
        used = set()
        for i, w1 in enumerate(idx):
            if w1 in used:
                continue
            cluster = [w1]
            for w2 in idx[i + 1:]:
                if w2 in used:
                    continue
                eq = (grp.loc[w1, COLS].values == grp.loc[w2, COLS].values).sum()
                if eq >= 6:
                    cluster.append(w2); used.add(w2)
            used.add(w1)
            rows[canonical(cluster)] = grp.loc[cluster, COLS].max().values
    return pd.DataFrame.from_dict(rows, orient="index", columns=COLS).sort_index()


# ----------------------------------------------------------------------
# 2. Lexical statistics  (paper, Section 3)
# ----------------------------------------------------------------------
def lexstats(freqs: np.ndarray) -> dict:
    f = np.array([x for x in freqs if x > 0])
    N, V = int(f.sum()), len(f)
    spec = pd.Series(f).value_counts().sort_index()               # m -> V_m
    V1, V2 = int(spec.get(1, 0)), int(spec.get(2, 0))
    yule_k = 1e4 * (sum(m * m * v for m, v in spec.items()) - N) / N ** 2
    p = f / N
    H = -(p * np.log2(p)).sum()
    simpson = float((p ** 2).sum())
    fs = np.sort(f); n = len(fs)
    gini = (2 * np.arange(1, n + 1) - n - 1).dot(fs) / (n * fs.sum())
    fr = np.sort(f)[::-1]; r = np.arange(1, len(fr) + 1)
    sl, _, rv, _, _ = stats.linregress(np.log10(r), np.log10(fr))          # all ranks
    m5 = fr >= 5
    sl5, _, rv5, _, _ = stats.linregress(np.log10(r[m5]), np.log10(fr[m5]))  # f >= 5
    cum = np.cumsum(fr) / N
    return dict(
        N=N, V=V, V1=V1, V2=V2, hapax_pct=V1 / V, TTR=V / N,
        Guiraud=V / np.sqrt(N), HerdanC=np.log(V) / np.log(N),
        Maas_a2=(np.log(N) - np.log(V)) / np.log(N) ** 2,
        DugastU=np.log(N) ** 2 / (np.log(N) - np.log(V)),
        YuleK=yule_k, Shannon_bits=H, Hmax_bits=np.log2(V),
        Evenness=H / np.log2(V), Perplexity=2 ** H,
        SimpsonD=simpson, InvSimpson=1 / simpson, Gini=gini,
        Zipf_slope=sl, Zipf_R2=rv ** 2, Zipf5_slope=sl5, Zipf5_R2=rv5 ** 2,
        Cov10=cum[9], Cov100=cum[99], Cov1000=cum[999],
        mean=f.mean(), median=float(np.median(f)), sd=f.std(ddof=1),
        skew=stats.skew(f), kurt=stats.kurtosis(f), fmax=int(f.max()),
    )


# ----------------------------------------------------------------------
# 3. Run
# ----------------------------------------------------------------------
def main():
    M = load_and_clean(SRC)
    M.to_csv(f"{OUT}/word_by_kanda_matrix.csv")
    M["total"] = M[COLS].sum(axis=1)
    print(f"Cleaned corpus: {int(M['total'].sum()):,} tokens, {len(M):,} types")

    # ---- per-kanda + whole-corpus statistics (Tables 1 & 5) ----
    res = {NAMES[c]: lexstats(M[c].values) for c in COLS}
    res["Whole corpus"] = lexstats(M["total"].values)
    S = pd.DataFrame(res).T
    S.to_csv(f"{OUT}/stats_per_kanda.csv")

    # ---- top words (Table 2) ----
    M.nlargest(25, "total").to_csv(f"{OUT}/top_words.csv")

    # ---- frequency spectrum (Table 3) ----
    f = M["total"].values
    spec = pd.Series(f).value_counts().sort_index().head(15).rename("Vm").to_frame()
    spec["share_of_types"] = spec.Vm / len(f)
    spec.to_csv(f"{OUT}/spectrum.csv")

    # ---- Heaps' law, canonical order (Table 4) ----
    seen, tot, rows = set(), 0, []
    for c in COLS:
        tot += int(M[c].sum()); seen |= set(M.index[M[c] > 0])
        rows.append((NAMES[c], tot, len(seen)))
    hp = pd.DataFrame(rows, columns=["through", "cumN", "cumV"])
    sl, ic, rv, _, _ = stats.linregress(np.log(hp.cumN), np.log(hp.cumV))
    hp["heaps_pred"] = (np.exp(ic) * hp.cumN ** sl).round(0)
    hp.to_csv(f"{OUT}/heaps.csv", index=False)
    print(f"Heaps: V = {np.exp(ic):.2f} * N^{sl:.4f}   (R2 = {rv**2:.5f})")

    # ---- similarity matrices (Tables 6-8, Section 5) ----
    nm = [NAMES[c] for c in COLS]
    tf = M[COLS].div(M[COLS].sum(axis=0), axis=1)                 # relative frequencies
    idf = np.log(7 / (M[COLS] > 0).sum(axis=1))
    tfidf = tf.mul(idf, axis=0)

    def cosmat(X):
        Xn = X / np.sqrt((X ** 2).sum(axis=0))
        return pd.DataFrame(Xn.T.values @ Xn.values, index=nm, columns=nm)

    cosmat(tf).round(4).to_csv(f"{OUT}/cosine_raw.csv")
    cosmat(tfidf).round(4).to_csv(f"{OUT}/cosine_tfidf.csv")

    jac = pd.DataFrame(np.eye(7), index=nm, columns=nm)
    spr = jac.copy()
    for i, a in enumerate(COLS):
        for j, b in enumerate(COLS):
            if i >= j:
                continue
            A = set(M.index[M[a] > 0]); B = set(M.index[M[b] > 0])
            jac.iloc[i, j] = jac.iloc[j, i] = len(A & B) / len(A | B)
            common = list(A & B)
            rho, _ = stats.spearmanr(M.loc[common, a], M.loc[common, b])
            spr.iloc[i, j] = spr.iloc[j, i] = rho
    jac.round(4).to_csv(f"{OUT}/jaccard.csv")
    spr.round(4).to_csv(f"{OUT}/spearman.csv")

    # ---- chi-square homogeneity, top-50 forms (Section 5.1) ----
    top50 = M.nlargest(50, "total")
    chi2, p, dof, _ = stats.chi2_contingency(top50[COLS].values)
    cram = np.sqrt(chi2 / (top50[COLS].values.sum() * 6))
    with open(f"{OUT}/chi_square.txt", "w") as fh:
        fh.write(f"chi2({dof}) = {chi2:.1f}, p = {p:.3g}, Cramer's V = {cram:.4f}\n")
    print(f"chi2({dof}) = {chi2:.1f}, Cramer's V = {cram:.4f}")

    # ---- Figures 1-4 ----
    Ns = [res[NAMES[c]]["N"] for c in COLS]
    Vs = [res[NAMES[c]]["V"] for c in COLS]

    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=150)             # Figure 1
    x, w = np.arange(7), .38
    ax.bar(x - w / 2, Ns, w, label="Tokens (N)", color="#8B0000")
    ax.bar(x + w / 2, Vs, w, label="Types (V)", color="#C9A227")
    ax.set_xticks(x); ax.set_xticklabels(nm, rotation=20)
    ax.set_title("Corpus size by kanda"); ax.legend(); ax.grid(axis="y", alpha=.3)
    plt.tight_layout(); plt.savefig(f"{OUT}/fig_sizes.png"); plt.close()

    fig, ax = plt.subplots(figsize=(7, 5), dpi=150)               # Figure 2
    fr = np.sort(f)[::-1]
    ax.loglog(np.arange(1, len(fr) + 1), fr, lw=1.8, color="#8B0000", label="Whole corpus")
    for c in COLS:
        fk = np.sort(M[c][M[c] > 0].values)[::-1]
        ax.loglog(np.arange(1, len(fk) + 1), fk, lw=.7, alpha=.55, label=NAMES[c])
    ax.set_xlabel("Rank (log scale)"); ax.set_ylabel("Frequency (log scale)")
    ax.set_title("Rank-frequency (Zipf) profile")
    ax.legend(fontsize=7, ncol=2); ax.grid(alpha=.3, which="both")
    plt.tight_layout(); plt.savefig(f"{OUT}/fig_zipf.png"); plt.close()

    fig, ax = plt.subplots(figsize=(7, 5), dpi=150)               # Figure 3
    cum = np.cumsum(fr) / fr.sum()
    ax.semilogx(np.arange(1, len(fr) + 1), cum * 100, color="#00468B", lw=2)
    for k in (10, 100, 1000):
        ax.axvline(k, ls=":", color="gray", lw=.8)
        ax.annotate(f"top {k}: {cum[k-1]*100:.1f}%", (k, cum[k - 1] * 100),
                    fontsize=8, xytext=(k * 1.3, cum[k - 1] * 100 - 6))
    ax.set_xlabel("Number of most frequent word forms (log scale)")
    ax.set_ylabel("Cumulative % of tokens covered")
    ax.set_title("Vocabulary coverage curve"); ax.grid(alpha=.3)
    plt.tight_layout(); plt.savefig(f"{OUT}/fig_coverage.png"); plt.close()

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), dpi=150)    # Figure 4
    for ax, (mat, t) in zip(axes, [(cosmat(tf), "Cosine (relative frequencies)"),
                                   (cosmat(tfidf), "Cosine (TF-IDF weighted)")]):
        im = ax.imshow(mat.values, cmap="YlOrRd")
        ax.set_xticks(range(7)); ax.set_yticks(range(7))
        ax.set_xticklabels(nm, rotation=45, ha="right", fontsize=8)
        ax.set_yticklabels(nm, fontsize=8)
        for i in range(7):
            for j in range(7):
                ax.text(j, i, f"{mat.values[i, j]:.2f}", ha="center", va="center",
                        fontsize=6.5,
                        color="white" if mat.values[i, j] > .5 * mat.values.max() else "black")
        ax.set_title(t, fontsize=10)
        fig.colorbar(im, ax=ax, fraction=.046)
    plt.tight_layout(); plt.savefig(f"{OUT}/fig_cosine.png"); plt.close()

    print(f"All outputs written to ./{OUT}/")


if __name__ == "__main__":
    main()


# ----------------------------------------------------------------------
# 4. Frame-hypothesis analyses  (paper, Section 5.4)
#    Burrows's Delta, Jensen-Shannon divergence, bootstrap clustering,
#    size-adjusted exclusive shared vocabulary, and G2 keyness.
#    Appended in v1.1; run automatically after main().
# ----------------------------------------------------------------------
def frame_hypothesis_analyses(seed: int = 42, n_boot: int = 200, n_mfw: int = 300):
    from scipy.cluster.hierarchy import linkage, dendrogram
    from scipy.spatial.distance import squareform

    rng = np.random.default_rng(seed)
    M = pd.read_csv(f"{OUT}/word_by_kanda_matrix.csv", index_col=0)
    nm = [NAMES[c] for c in COLS]
    M.columns = nm
    Ntok = M.sum(axis=0)

    # ---- 4.1 Burrows's Delta on the n_mfw most frequent words ----
    def delta_matrix(Mx):
        mfw = Mx.sum(axis=1).nlargest(n_mfw).index
        F = Mx.loc[mfw].div(Mx.sum(axis=0), axis=1)
        Z = F.sub(F.mean(axis=1), axis=0).div(F.std(axis=1, ddof=1), axis=0)
        D = pd.DataFrame(0.0, index=nm, columns=nm)
        for i, a in enumerate(nm):
            for b in nm[i + 1:]:
                D.loc[a, b] = D.loc[b, a] = (Z[a] - Z[b]).abs().mean()
        return D

    Dl = delta_matrix(M)
    Dl.round(4).to_csv(f"{OUT}/delta_mfw{n_mfw}.csv")

    # ---- 4.2 Jensen-Shannon divergence over full distributions ----
    P = M.div(M.sum(axis=0), axis=1)

    def jsd(p, q):
        m = (p + q) / 2
        kl = lambda a, b: (a[a > 0] * np.log2(a[a > 0] / b[a > 0])).sum()
        return 0.5 * kl(p, m) + 0.5 * kl(q, m)

    J = pd.DataFrame(0.0, index=nm, columns=nm)
    for i, a in enumerate(nm):
        for b in nm[i + 1:]:
            J.loc[a, b] = J.loc[b, a] = jsd(P[a].values, P[b].values)
    J.round(4).to_csv(f"{OUT}/jsd.csv")

    # ---- 4.3 Multinomial bootstrap support for the two clusters ----
    def clusters(D):
        Z = linkage(squareform(D.values), method="average")
        members = {i: {i} for i in range(len(nm))}
        out = set()
        for k, (a, b, *_ ) in enumerate(Z):
            s = members[int(a)] | members[int(b)]
            members[len(nm) + k] = s
            out.add(frozenset(nm[i] for i in s))
        return Z, out

    Z0, _ = clusters(Dl)
    hits_bu = hits_vanara = 0
    for _ in range(n_boot):
        Mb = pd.DataFrame(
            np.column_stack([rng.multinomial(int(Ntok[c]), M[c] / Ntok[c]) for c in nm]),
            index=M.index, columns=nm)
        _, cl = clusters(delta_matrix(Mb))
        hits_bu += frozenset({"Bala", "Uttara"}) in cl
        hits_vanara += frozenset({"Kishkindha", "Sundara", "Yuddha"}) in cl
    with open(f"{OUT}/bootstrap_support.txt", "w") as fh:
        fh.write(f"multinomial bootstrap, {n_boot} resamples, Delta({n_mfw} MFW), average linkage\n")
        fh.write(f"{{Bala, Uttara}} cluster support:            {100*hits_bu/n_boot:.0f}%\n")
        fh.write(f"{{Kishkindha, Sundara, Yuddha}} support:     {100*hits_vanara/n_boot:.0f}%\n")
    print(f"Bootstrap support: Bala-Uttara {100*hits_bu/n_boot:.0f}%, "
          f"vanara triad {100*hits_vanara/n_boot:.0f}%")

    # ---- Figure 5: dendrogram ----
    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=150)
    dendrogram(Z0, labels=nm, ax=ax, color_threshold=0, link_color_func=lambda k: "#8B0000")
    ax.set_ylabel(f"Burrows's Delta ({n_mfw} MFW), average linkage")
    ax.set_title("Stylometric clustering of the kandas")
    ax.text(.02, .95, f"bootstrap support: {{Bala,Uttara}} {100*hits_bu/n_boot:.0f}%   "
                      f"{{Kis.,Sun.,Yud.}} {100*hits_vanara/n_boot:.0f}%",
            transform=ax.transAxes, fontsize=8, va="top")
    plt.xticks(rotation=20)
    plt.tight_layout(); plt.savefig(f"{OUT}/fig_dendrogram.png"); plt.close()

    # ---- 4.4 Size-adjusted exclusive shared vocabulary (df = 2) ----
    att = M > 0
    df2 = M.index[att.sum(axis=1) == 2]
    marg = att.loc[df2].sum(axis=0) / (2 * len(df2))
    Zc = sum(marg[a] * marg[b] for i, a in enumerate(nm) for b in nm[i + 1:])
    pairs = {}
    for w in df2:
        ks = tuple(sorted(att.columns[att.loc[w]]))
        pairs[ks] = pairs.get(ks, 0) + 1
    rows = []
    for i, a in enumerate(nm):
        for b in nm[i + 1:]:
            pr = marg[a] * marg[b] / Zc
            o = pairs.get(tuple(sorted((a, b))), 0)
            e = len(df2) * pr
            pv = stats.binomtest(o, len(df2), pr, alternative="greater").pvalue
            rows.append((f"{a}-{b}", o, round(e, 1), round(o / e, 3), pv))
    (pd.DataFrame(rows, columns=["pair", "observed", "expected", "obs_over_exp", "p_greater"])
        .sort_values("obs_over_exp", ascending=False)
        .to_csv(f"{OUT}/exclusive_pairs.csv", index=False))

    # ---- 4.5 Keyness: G2 log-likelihood, (Bala+Uttara) vs core ----
    A = M[["Bala", "Uttara"]].sum(axis=1)
    B = M[["Ayodhya", "Aranya", "Kishkindha", "Sundara", "Yuddha"]].sum(axis=1)
    NA, NB = A.sum(), B.sum()

    def g2(a, b):
        E1, E2 = NA * (a + b) / (NA + NB), NB * (a + b) / (NA + NB)
        t = (a * np.log(a / E1) if a > 0 else 0) + (b * np.log(b / E2) if b > 0 else 0)
        return 2 * t

    key = pd.DataFrame({"frame": A, "core": B})
    key = key[(key.frame + key.core) >= 10]
    key["G2"] = [g2(a, b) for a, b in zip(key.frame, key.core)]
    key["direction"] = np.where(key.frame / NA > key.core / NB, "frame", "core")
    key.sort_values("G2", ascending=False).head(50).to_csv(f"{OUT}/keyness_frame_vs_core.csv")
    print("Frame-hypothesis outputs written.")


if __name__ == "__main__":
    frame_hypothesis_analyses()
