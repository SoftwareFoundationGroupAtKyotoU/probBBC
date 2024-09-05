import sys
import os
import numpy as np
from matplotlib import pyplot as plt

# Gaussian process regression

stat_file = sys.argv[1]
baseline_file = sys.argv[2]
output_file = sys.argv[3]
true_value = float(sys.argv[4])
if len(sys.argv) > 5:
    xlimit = int(sys.argv[5])
else:
    xlimit = 0

if len(sys.argv) > 6:
    xtarget = int(sys.argv[6])
else:
    xtarget = None

if len(sys.argv) > 7:
    uniform_smc_file = sys.argv[7]
else:
    uniform_smc_file = None

if len(sys.argv) > 9:
    ymin = float(sys.argv[8])
    ymax = float(sys.argv[9])
else:
    ymin = None
    ymax = None


# stat file of our method
# 0-round 1-probability 2-round' 3-#-of-queries 4-#-of-steps
probbbc_prob_data = np.loadtxt(stat_file, usecols=1, dtype="float")
probbbc_step_data = np.loadtxt(stat_file, usecols=4, dtype="int64")
if len(probbbc_prob_data) != len(probbbc_step_data):
    print(f"stat file of our method is broken : {stat_file}")
    exit()

# stat file of baseline method
# 0-#-of-steps, 1-probability
baseline_prob_data = np.loadtxt(baseline_file, usecols=1, dtype="float")
baseline_step_data = np.loadtxt(baseline_file, usecols=0, dtype="int64")
if len(baseline_prob_data) != len(baseline_step_data):
    print(f"stat file of baseline method is broken : {baseline_file}")
    exit()

plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["mathtext.fontset"] = "stix"  # math fontの設定
plt.rcParams["font.size"] = 15
# plt.rcParams['figure.dpi'] = 300
plt.rcParams["figure.figsize"] = (6.5, 3.5)

fig = plt.figure()
ax = fig.add_subplot(111)
# plot data of baseline method
ax.plot(
    baseline_step_data,
    baseline_prob_data,
    color="#F92816",
    alpha=0.2,
    marker="o",
    markersize=0.5,
    linestyle="",
    label="baseline method",
)
(label_baseline,) = ax.plot(
    [-1000_0000],
    [0],
    color="#F92816",
    marker="o",
    linestyle="",
    label="baseline method",
)
# plot data of our method
# green : 0CC94B or 079C29, blue : 091DF4 or 040EC6
ax.plot(
    probbbc_step_data,
    probbbc_prob_data,
    color="#091DF4",
    alpha=0.6,
    marker="o",
    markersize=0.5,
    linestyle="",
    label="our method",
)
(label_probbbc,) = ax.plot(
    [-1000_0000], [0], color="#091DF4", marker="o", linestyle="", label="our method"
)
# plot true value
label_true = ax.axhline(true_value, ls="-.", color="k")

ax.set_xlabel(r"Number of executed steps on the SUT")
ax.set_ylabel(r"Probability $p$")
if xlimit > 0:
    ax.set_xlim(0, xlimit)
else:
    ax.set_xlim(0, max(probbbc_step_data.max(), baseline_step_data.max()))
if ymin and ymax:
    ax.set_ylim(ymin, ymax)
# else:
#   ax.set_ylim(-0.02)


ax.legend(handles=[label_probbbc, label_baseline])  # 凡例

# Gaussian process regression
# print(f'GPR : fiting our method (sample size : {len(probbbc_step_data)})')
# xpoints = np.linspace(0, xlimit, num=1000).reshape(-1, 1)
# kernel = 0.4 * RBF(length_scale=1) + WhiteKernel(noise_level=1)
# gp_probbbc = GaussianProcessRegressor(kernel=kernel)
# gp_probbbc.fit(probbbc_step_data.reshape(-1,1), probbbc_prob_data)
# mean_predictions_gpr, std_predictions_gpr = gp_probbbc.predict(
#     xpoints,
#     return_std=True,
# )
# ax.fill_between(
#     xpoints.ravel(),
#     mean_predictions_gpr - std_predictions_gpr,
#     mean_predictions_gpr + std_predictions_gpr,
#     color="#091DF4",
#     alpha=0.4,
# )
# training_size = len(probbbc_step_data)
# print(f'GPR : fitting baseline method (sample size : {training_size})')
# kernel = 1.0 * RBF(length_scale=1) + WhiteKernel(noise_level=1)
# gp_baseline = GaussianProcessRegressor(kernel=kernel)
# baseline_data = np.loadtxt(baseline_file)
# rng = np.random.default_rng()
# baseline_data = rng.choice(baseline_data, size=training_size)
# gp_baseline.fit(baseline_data[:,0].reshape(-1,1), baseline_data[:,1])
# mean_predictions_gpr, std_predictions_gpr = gp_baseline.predict(
#     xpoints,
#     return_std=True,
# )
# ax.fill_between(
#     xpoints.ravel(),
#     mean_predictions_gpr - std_predictions_gpr,
#     mean_predictions_gpr + std_predictions_gpr,
#     color="#F92816",
#     alpha=0.4,
# )

plt.show()

fig.savefig(output_file, bbox_inches="tight", pad_inches=0.05)

plt.clf()

if xtarget:
    # plt.rcParams['figure.dpi'] = 300
    plt.rcParams["figure.figsize"] = (3.5, 3.5)
    # boxplot data of our method
    xtarget_diff = 100000
    probbbc_data = np.loadtxt(stat_file, usecols=[1, 4])
    # probbbc_data = probbbc_data[np.any((probbbc_data > xtarget - xtarget_diff) & (probbbc_data < xtarget + xtarget_diff), axis=1)]
    index = np.argsort(np.abs(probbbc_data[:, 1] - xtarget))
    probbbc_data = probbbc_data[index]
    probbbc_data = probbbc_data[:, 0]
    probbbc_data = probbbc_data[:60]
    print(f"boxplot data of our method has {len(probbbc_data)} data")

    # boxplot data of baseline method
    baseline_data = np.loadtxt(baseline_file)
    # baseline_data = baseline_data[np.any((baseline_data > xtarget - xtarget_diff) & (baseline_data < xtarget + xtarget_diff), axis=1)]
    index = np.argsort(np.abs(baseline_data[:, 0] - xtarget))
    baseline_data = baseline_data[index]
    baseline_data = baseline_data[:, 1]
    baseline_data = baseline_data[:60]
    print(f"boxplot data of baseline method has {len(baseline_data)} data")

    fig = plt.figure()
    ax = fig.add_subplot(111)

    if uniform_smc_file:
        uniform_data = np.loadtxt(uniform_smc_file)
        ax.boxplot([probbbc_data, baseline_data, uniform_data], widths=[0.5, 0.5, 0.5])
        ax.set_xticklabels(["ProbBBC", "baseline", "uniform"])
    else:
        ax.boxplot([probbbc_data, baseline_data], widths=[0.5, 0.5])
        ax.set_xticklabels(["our method", "baseline method"])
    ax.axhline(true_value, ls="--")
    # ax.set_ylim(0.29, 0.52)
    plt.ylabel(r"Probability $p$")

    plt.show()

    fig.savefig(
        os.path.splitext(output_file)[0] + "_boxplot.eps",
        bbox_inches="tight",
        pad_inches=0.05,
    )
