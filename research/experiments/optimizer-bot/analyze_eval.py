#!/usr/bin/env python3
"""Analyze the optimizer-bot differentiation eval: 2 blind judges x 9 pairs.

Decodes the blinded arms, computes treatment (research workflow) win-rate and
rubric deltas overall / by stakes tier / by dimension, writes results.tsv, and
renders a two-panel readout PNG.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DIMS = ["correctness", "specificity", "actionability", "sourcing", "honesty"]
HERE = os.path.dirname(__file__)

# 5-dim scores (0-5) per answer, per judge. A/B are blinded labels.
J1 = {
 "T1": {"A": [5,5,5,4,5], "B": [4,2,3,0,4]}, "T2": {"A": [3,2,3,0,4], "B": [5,5,5,5,5]},
 "T3": {"A": [5,5,5,4,4], "B": [4,3,4,0,5]}, "M1": {"A": [4,4,4,1,4], "B": [5,5,5,5,5]},
 "M2": {"A": [5,5,5,4,5], "B": [4,3,4,0,5]}, "M3": {"A": [4,3,4,1,4], "B": [5,5,5,5,5]},
 "H1": {"A": [5,5,5,5,5], "B": [3,3,4,0,4]}, "H2": {"A": [3,3,4,1,4], "B": [5,5,5,5,5]},
 "H3": {"A": [5,5,5,4,5], "B": [4,3,4,0,5]},
}
J2 = {
 "T1": {"A": [4,5,5,4,5], "B": [4,2,2,0,4]}, "T2": {"A": [3,3,3,0,4], "B": [5,5,5,5,5]},
 "T3": {"A": [4,5,5,4,5], "B": [4,3,4,0,4]}, "M1": {"A": [4,4,4,0,4], "B": [5,5,5,5,5]},
 "M2": {"A": [5,5,5,5,5], "B": [4,3,3,0,5]}, "M3": {"A": [4,3,3,0,4], "B": [5,5,5,5,5]},
 "H1": {"A": [5,5,5,5,5], "B": [2,3,3,0,4]}, "H2": {"A": [4,3,3,0,4], "B": [4,5,5,5,5]},
 "H3": {"A": [5,5,5,5,5], "B": [4,3,3,0,5]},
}
# Which blinded letter is the research-workflow (treatment) arm, per question:
TREAT = {"T1":"A","T2":"B","T3":"A","M1":"B","M2":"A","M3":"B","H1":"A","H2":"B","H3":"A"}
TIER = {"T":"trivial","M":"mid","H":"high"}

rows = []
for judge, data in [("J1", J1), ("J2", J2)]:
    for q, arms in data.items():
        t = TREAT[q]; b = "B" if t == "A" else "A"
        tv, bv = arms[t], arms[b]
        rec = {"judge": judge, "q": q, "tier": TIER[q[0]],
               "treat_total": sum(tv), "base_total": sum(bv),
               "delta": sum(tv) - sum(bv), "treat_win": sum(tv) > sum(bv)}
        for i, d in enumerate(DIMS):
            rec[f"t_{d}"] = tv[i]; rec[f"b_{d}"] = bv[i]
        rows.append(rec)
df = pd.DataFrame(rows)
df.to_csv(os.path.join(HERE, "results.tsv"), sep="\t", index=False)

# ---- headline numbers -------------------------------------------------------
n = len(df)
winrate = df["treat_win"].mean()
print(f"verdicts: {n} (9 questions x 2 judges)")
print(f"treatment win-rate: {winrate*100:.0f}%  ({df['treat_win'].sum()}/{n})")
print(f"mean rubric total:  treatment {df['treat_total'].mean():.1f}/25  vs baseline {df['base_total'].mean():.1f}/25")
print(f"mean delta:         +{df['delta'].mean():.1f} points  (+{df['delta'].mean()/25*100:.0f}% of scale)")
print("\nby tier (mean delta, treatment win-rate):")
tier_g = df.groupby("tier").agg(delta=("delta","mean"), win=("treat_win","mean")).reindex(["trivial","mid","high"])
for tier, r in tier_g.iterrows():
    print(f"  {tier:8} +{r['delta']:.1f}   {r['win']*100:.0f}% win")
print("\nby dimension (mean treatment vs baseline, 0-5):")
dim_means = {d: (df[f"t_{d}"].mean(), df[f"b_{d}"].mean()) for d in DIMS}
for d,(t,b) in dim_means.items():
    print(f"  {d:14} T {t:.1f}  vs  B {b:.1f}   (+{t-b:.1f})")

# ---- chart ------------------------------------------------------------------
TEAL, GREY = "#2A9D8F", "#9AA0A6"
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5.2))

# Panel 1: mean rubric total by tier
tiers = ["trivial","mid","high"]
tg = df.groupby("tier").agg(t=("treat_total","mean"), b=("base_total","mean")).reindex(tiers)
x = np.arange(len(tiers)); w = 0.38
ax1.bar(x-w/2, tg["t"], w, label="research workflow", color=TEAL)
ax1.bar(x+w/2, tg["b"], w, label="free-tool baseline", color=GREY)
for i,(t,b) in enumerate(zip(tg["t"], tg["b"])):
    ax1.text(i-w/2, t+0.3, f"{t:.0f}", ha="center", fontsize=9, color=TEAL, fontweight="bold")
    ax1.text(i+w/2, b+0.3, f"{b:.0f}", ha="center", fontsize=9, color="#666")
ax1.set_xticks(x); ax1.set_xticklabels([t+"\nstakes" for t in tiers])
ax1.set_ylabel("mean rubric total (/25)"); ax1.set_ylim(0, 26)
ax1.set_title("Answer quality by stakes tier", fontweight="bold")
ax1.legend(frameon=False, fontsize=9); ax1.spines[["top","right"]].set_visible(False)

# Panel 2: mean score by dimension (where the edge comes from)
tvals = [dim_means[d][0] for d in DIMS]; bvals = [dim_means[d][1] for d in DIMS]
y = np.arange(len(DIMS))
ax2.barh(y-w/2, tvals, w, label="research workflow", color=TEAL)
ax2.barh(y+w/2, bvals, w, label="free-tool baseline", color=GREY)
ax2.set_yticks(y); ax2.set_yticklabels(DIMS); ax2.invert_yaxis()
ax2.set_xlabel("mean score (/5)"); ax2.set_xlim(0, 5.3)
ax2.set_title("Where the edge comes from", fontweight="bold")
ax2.legend(frameon=False, fontsize=9, loc="lower right"); ax2.spines[["top","right"]].set_visible(False)

fig.suptitle(f"optimizer-bot: research workflow beats the free-tool baseline "
             f"{winrate*100:.0f}% of verdicts (2 blind judges x 9 Qs)", fontsize=12, fontweight="bold")
fig.tight_layout(rect=[0,0,1,0.96])
out = os.path.join(HERE, "readout.png")
fig.savefig(out, dpi=130)
print(f"\nchart -> {out}")
