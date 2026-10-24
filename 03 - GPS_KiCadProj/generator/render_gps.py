# ACwing GPS rev A renders: the board alone (top / isometric / bottom) and the stack ESC rev B + FC rev H + GPS rev D
# (M2 standoffs 6 mm, JST SH cable sketched), from the STEP meshes made by genD/step_mesh.py.
import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

G = np.load('/tmp/claude-0/meshGPSD.npz'); F = np.load('/tmp/claude-0/meshH.npz'); S = np.load('/tmp/claude-0/meshESCB.npz')
T_ESC, GAP, T_FC, STANDOFF = 1.0, 5.0, 1.0, 6.0
Z_FC = T_ESC + GAP

def view(ax, T, C, az, el, title, lim=None):
    a, e = np.radians(az), np.radians(el)
    R1 = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    R2 = np.array([[1, 0, 0], [0, np.cos(e), -np.sin(e)], [0, np.sin(e), np.cos(e)]])
    R = R2 @ R1
    V = T @ R.T
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); n /= (np.linalg.norm(n, axis=1)[:, None] + 1e-12)
    light = np.array([0.3, 0.4, 0.85]); light /= np.linalg.norm(light)
    sh = 0.35 + 0.65 * np.abs((n @ R.T) @ light)
    o = np.argsort(V[:, :, 2].mean(1))
    cols = np.clip(C[o] * sh[o][:, None], 0, 1)
    ax.add_collection(PolyCollection(V[o][:, :, :2], facecolors=cols, edgecolors=cols, linewidths=0.2))
    ax.set_aspect('equal'); ax.axis('off'); ax.set_title(title, fontsize=13)
    if lim:
        ax.set_xlim(*lim[0]); ax.set_ylim(*lim[1])
    else:
        ax.autoscale_view()

def centred(d, dz=0.0):
    return d['T'] - np.array([150, -100, -dz]), d['C']

# --- GPS board alone
Tg, Cg = centred(G)
fig, axs = plt.subplots(1, 3, figsize=(21, 7.5))
view(axs[0], Tg, Cg, 0, 0, 'Top: SAM-M10Q (axis-aligned), Qwiic J1 aligned with FC J3, PPS LED')
view(axs[1], Tg, Cg, -35, -60, 'Isometric')
view(axs[2], Tg, Cg, 0, 180, 'Bottom: compass, backup, test pads (nothing above 1.1 mm)')
plt.tight_layout(); plt.savefig('/home/claude/outGPS_RB/ACwing_GPS_A_3D.png', dpi=80); plt.close()

# --- stack: FC + standoffs + GPS board + cable sketch
Ts_, Cs_ = centred(S)
Tf, Cf = centred(F, Z_FC)
Tg2, Cg2 = centred(G, Z_FC + T_FC + STANDOFF)
def cyl(cx, cy, z0, z1, r, col, n=16):
    tris, cols = [], []
    for k in range(n):
        a0, a1 = 2 * np.pi * k / n, 2 * np.pi * (k + 1) / n
        p = [(cx + r * np.cos(a0), cy + r * np.sin(a0)), (cx + r * np.cos(a1), cy + r * np.sin(a1))]
        q = [(p[0][0], p[0][1], z0), (p[1][0], p[1][1], z0), (p[1][0], p[1][1], z1), (p[0][0], p[0][1], z1)]
        tris += [[q[0], q[1], q[2]], [q[0], q[2], q[3]]]; cols += [col, col]
    return tris, cols
extra_T, extra_C = [], []
for hx, hy in ((10, 10), (-10, 10), (-10, -10), (10, -10)):        # grommets (black) and nylon standoffs (white)
    t, c = cyl(hx, hy, T_ESC, Z_FC, 2.0, (0.15, 0.15, 0.15)); extra_T += t; extra_C += c
    t, c = cyl(hx, hy, Z_FC + T_FC, Z_FC + T_FC + STANDOFF, 1.75, (0.93, 0.93, 0.9)); extra_T += t; extra_C += c
# cable sketch (KiCad x, y, z): FC J3 mouth (top, right edge) -> loop outside the right edge -> GPS J1 mouth (rev D: GPS top)
zf, zg = Z_FC + T_FC + 1.4, Z_FC + T_FC + STANDOFF + 1.0 + 1.4
path = [(170.2, 96.4, zf), (172.6, 96.4, zf + 0.6), (174.2, 96.4, zf + 2.4), (174.0, 96.4, zf + 5.0), (172.0, 96.4, zg + 0.6), (168.0, 96.4, zg + 0.3), (165.2, 96.4, zg)]   # GPS J1 right above FC J3 (v = +3.6)
path = np.array([(x - 150, 100 - y, z) for x, y, z in path])
dense = []
for a, b_ in zip(path, path[1:]):
    for s in np.linspace(0, 1, 6, endpoint=False):
        dense.append(a + (b_ - a) * s)
dense.append(path[-1]); dense = np.array(dense)
W = 1.8
for i in range(len(dense) - 1):
    a, b_ = dense[i], dense[i + 1]
    tg = b_ - a; side = np.cross(tg, [0, 0, 1.0])
    side = side / (np.linalg.norm(side) + 1e-9) * W if np.linalg.norm(side) > 1e-6 else np.array([0, W, 0])
    q = [a - side, a + side, b_ + side, b_ - side]
    extra_T += [[q[0], q[1], q[2]], [q[0], q[2], q[3]]]; extra_C += [(0.12, 0.12, 0.12)] * 2
Ts = np.concatenate([Ts_, Tf, Tg2, np.array(extra_T)]); Cs = np.concatenate([Cs_, Cf, Cg2, np.array(extra_C)])
fig, axs = plt.subplots(1, 2, figsize=(20, 9))
view(axs[0], Ts, Cs, -35, -62, 'Stack: ACwing ESC 1S + FC (grommets, 5 mm gap) + GPS (6 mm gap), rev A')
view(axs[1], Ts, Cs, 0, -90, 'Side view (-Y): Qwiic cable FC J3 -> GPS J1, straight up at the right edge')
plt.tight_layout(); plt.savefig('/home/claude/outGPS_RB/ACwing_stack_3D.png', dpi=80); plt.close()
print('renders written')
