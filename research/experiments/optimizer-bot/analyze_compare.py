#!/usr/bin/env python3
"""Compare round 1 (workflow vs no-tools default) with round 2 (vs strong browsing).

Same 9 questions, 2 blind judges each round. Computes win/tie/loss and rubric
deltas per round and per dimension, and charts where the edge went.
Tie rule: |treat_total - base_total| <= 1 (matches the judges' stated ~1pt tie rule).
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DIMS = ["correctness","specificity","actionability","sourcing","honesty"]
HERE = os.path.dirname(__file__)
TREAT = {"T1":"A","T2":"B","T3":"A","M1":"B","M2":"A","M3":"B","H1":"A","H2":"B","H3":"A"}
TIE = 1

# ---- Round 1 (vs no-tools default) -----------------------------------------
R1_J1 = {
 "T1":{"A":[5,5,5,4,5],"B":[4,2,3,0,4]},"T2":{"A":[3,2,3,0,4],"B":[5,5,5,5,5]},
 "T3":{"A":[5,5,5,4,4],"B":[4,3,4,0,5]},"M1":{"A":[4,4,4,1,4],"B":[5,5,5,5,5]},
 "M2":{"A":[5,5,5,4,5],"B":[4,3,4,0,5]},"M3":{"A":[4,3,4,1,4],"B":[5,5,5,5,5]},
 "H1":{"A":[5,5,5,5,5],"B":[3,3,4,0,4]},"H2":{"A":[3,3,4,1,4],"B":[5,5,5,5,5]},
 "H3":{"A":[5,5,5,4,5],"B":[4,3,4,0,5]}}
R1_J2 = {
 "T1":{"A":[4,5,5,4,5],"B":[4,2,2,0,4]},"T2":{"A":[3,3,3,0,4],"B":[5,5,5,5,5]},
 "T3":{"A":[4,5,5,4,5],"B":[4,3,4,0,4]},"M1":{"A":[4,4,4,0,4],"B":[5,5,5,5,5]},
 "M2":{"A":[5,5,5,5,5],"B":[4,3,3,0,5]},"M3":{"A":[4,3,3,0,4],"B":[5,5,5,5,5]},
 "H1":{"A":[5,5,5,5,5],"B":[2,3,3,0,4]},"H2":{"A":[4,3,3,0,4],"B":[4,5,5,5,5]},
 "H3":{"A":[5,5,5,5,5],"B":[4,3,3,0,5]}}
# ---- Round 2 (vs strong browsing baseline) ---------------------------------
R2_J1 = {
 "T1":{"A":[4,5,4,4,4],"B":[4,4,5,4,5]},"T2":{"A":[5,4,4,5,5],"B":[5,5,5,4,4]},
 "T3":{"A":[5,5,5,4,4],"B":[5,4,4,4,5]},"M1":{"A":[5,4,5,5,5],"B":[5,5,5,5,4]},
 "M2":{"A":[5,5,5,4,5],"B":[4,4,4,5,5]},"M3":{"A":[4,4,4,4,5],"B":[5,5,5,4,5]},
 "H1":{"A":[5,5,5,4,5],"B":[4,4,5,5,5]},"H2":{"A":[5,5,5,5,5],"B":[5,5,4,4,5]},
 "H3":{"A":[5,5,5,4,5],"B":[4,4,4,5,5]}}
R2_J2 = {
 "T1":{"A":[4,5,4,4,5],"B":[5,4,4,3,5]},"T2":{"A":[5,5,4,4,5],"B":[4,5,5,4,4]},
 "T3":{"A":[5,5,5,4,3],"B":[5,4,4,4,5]},"M1":{"A":[5,5,4,4,5],"B":[5,5,5,5,5]},
 "M2":{"A":[5,5,5,4,5],"B":[4,4,4,4,4]},"M3":{"A":[3,4,4,4,4],"B":[5,5,4,4,5]},
 "H1":{"A":[5,5,5,5,5],"B":[4,4,4,5,4]},"H2":{"A":[5,5,5,5,5],"B":[5,5,5,4,5]},
 "H3":{"A":[5,5,5,4,5],"B":[4,4,4,4,5]}}

def frame(rounds):
    rows = []
    for rnd, judges in rounds.items():
        for judge, data in judges.items():
            for q, arms in data.items():
                t = TREAT[q]; b = "B" if t == "A" else "A"
                tv, bv = arms[t], arms[b]
                d = sum(tv) - sum(bv)
                rec = {"round": rnd, "judge": judge, "q": q, "tier": {"T":"trivial","M":"mid","H":"high"}[q[0]],
                       "delta": d, "outcome": "win" if d > TIE else ("loss" if d < -TIE else "tie")}
                for i, dim in enumerate(DIMS):
                    rec[f"d_{dim}"] = tv[i] - bv[i]
                rows.append(rec)
    return pd.DataFrame(rows)

df = frame({"R1": {"J1": R1_J1, "J2": R1_J2}, "R2": {"J1": R2_J1, "J2": R2_J2}})
df.to_csv(os.path.join(HERE, "results_compare.tsv"), sep="\t", index=False)

for rnd, label in [("R1","Round 1  (vs no-tools default)"), ("R2","Round 2  (vs strong browsing)")]:
    d = df[df["round"] == rnd]
    oc = d["outcome"].value_counts()
    print(f"\n{label}  — {len(d)} verdicts")
    print(f"  win/tie/loss: {oc.get('win',0)} / {oc.get('tie',0)} / {oc.get('loss',0)}")
    print(f"  mean rubric delta (treat-base): +{d['delta'].mean():.1f} / 25")
    print(f"  per-dimension delta: " + ", ".join(f"{dim} {d['d_'+dim].mean():+.1f}" for dim in DIMS))

# ---- chart ------------------------------------------------------------------
TEAL, GREY, RED = "#2A9D8F", "#B8BdC2", "#E45756"
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 5.2))

# Panel 1: win/tie/loss per round (stacked)
rounds = ["R1","R2"]; labels = ["Round 1\nvs no-tools\ndefault", "Round 2\nvs strong\nbrowsing"]
wins = [ (df[(df["round"]==r)]["outcome"]=="win").sum() for r in rounds ]
ties = [ (df[(df["round"]==r)]["outcome"]=="tie").sum() for r in rounds ]
loss = [ (df[(df["round"]==r)]["outcome"]=="loss").sum() for r in rounds ]
x = np.arange(len(rounds))
ax1.bar(x, wins, 0.55, label="workflow wins", color=TEAL)
ax1.bar(x, ties, 0.55, bottom=wins, label="tie", color=GREY)
ax1.bar(x, loss, 0.55, bottom=np.array(wins)+np.array(ties), label="workflow loses", color=RED)
for i in range(len(rounds)):
    if wins[i]: ax1.text(i, wins[i]/2, str(wins[i]), ha="center", va="center", color="white", fontweight="bold")
    if ties[i]: ax1.text(i, wins[i]+ties[i]/2, str(ties[i]), ha="center", va="center", color="#333", fontweight="bold")
    if loss[i]: ax1.text(i, wins[i]+ties[i]+loss[i]/2, str(loss[i]), ha="center", va="center", color="white", fontweight="bold")
ax1.set_xticks(x); ax1.set_xticklabels(labels)
ax1.set_ylabel("verdicts (9 Qs x 2 judges)"); ax1.set_ylim(0,19)
ax1.set_title("Workflow win-rate collapses vs the real competitor", fontweight="bold", fontsize=11)
ax1.legend(frameon=False, fontsize=9, loc="upper right"); ax1.spines[["top","right"]].set_visible(False)

# Panel 2: per-dimension mean delta, R1 vs R2
r1d = [df[df["round"]=="R1"]["d_"+dim].mean() for dim in DIMS]
r2d = [df[df["round"]=="R2"]["d_"+dim].mean() for dim in DIMS]
y = np.arange(len(DIMS)); w = 0.38
ax2.barh(y-w/2, r1d, w, label="Round 1", color="#4C78A8")
ax2.barh(y+w/2, r2d, w, label="Round 2", color=TEAL)
ax2.axvline(0, color="#888", lw=0.8)
ax2.set_yticks(y); ax2.set_yticklabels(DIMS); ax2.invert_yaxis()
ax2.set_xlabel("workflow advantage per dimension (treat − base, /5)")
ax2.set_title("The whole edge was 'it cited sources'", fontweight="bold", fontsize=11)
ax2.legend(frameon=False, fontsize=9, loc="lower right"); ax2.spines[["top","right"]].set_visible(False)

fig.suptitle("optimizer-bot: the answer-quality moat is thin once the baseline can browse",
             fontsize=12.5, fontweight="bold")
fig.tight_layout(rect=[0,0,1,0.95])
out = os.path.join(HERE, "readout_compare.png")
fig.savefig(out, dpi=130); print(f"\nchart -> {out}")
