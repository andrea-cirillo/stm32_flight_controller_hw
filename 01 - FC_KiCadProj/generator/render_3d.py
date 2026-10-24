import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
d = np.load('/tmp/claude-0/meshH.npz'); T, C = d['T'], d['C']
T = T - np.array([150, -100, 0])             # board centre at origin (STEP: y up)
def view(ax, az, el, title, lim=None):
    a, e = np.radians(az), np.radians(el)
    R1 = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    R2 = np.array([[1, 0, 0], [0, np.cos(e), -np.sin(e)], [0, np.sin(e), np.cos(e)]])
    R = R2 @ R1
    V = T @ R.T
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); n /= (np.linalg.norm(n, axis=1)[:, None] + 1e-12)
    nv = n @ R.T
    light = np.array([0.3, 0.4, 0.85]); light /= np.linalg.norm(light)
    sh = 0.35 + 0.65 * np.abs(nv @ light)
    order = np.argsort(V[:, :, 2].mean(1))
    polys = V[order][:, :, :2]
    cols = np.clip(C[order] * sh[order][:, None], 0, 1)
    ax.add_collection(PolyCollection(polys, facecolors=cols, edgecolors=cols, linewidths=0.2))
    ax.set_aspect('equal'); ax.axis('off'); ax.set_title(title, fontsize=13)
    if lim: ax.set_xlim(*lim[0]); ax.set_ylim(*lim[1])
    else: ax.autoscale_view()
fig, axs = plt.subplots(1, 3, figsize=(24, 8.5))
view(axs[0], 0, 0, 'Top: MCU centred, 1S-6S buck (left), ESC A (rear), ESC B + ELRS (front), 2 Qwiic (right)')
view(axs[1], -35, -60, 'Isometric')
view(axs[2], 0, 180, 'Bottom: passives, flash, 2x4 pogo grid')
plt.tight_layout(); plt.savefig('/home/claude/outFCB/ACwing_FC_A_3D.png', dpi=80)
