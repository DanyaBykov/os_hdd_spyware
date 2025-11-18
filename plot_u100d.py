import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import welch
import os

LOG_FILE = "U100D_output_v6.log"  

DURATION_SEC = 60
PLOT_LIMIT_LOW_FREQ = 50
SAVE_DIR = "plots"
SHOW_PLOTS = True
os.makedirs(SAVE_DIR, exist_ok=True)

def hex_to_signed16(h):
    v = int(h, 16)
    if v >= 0x8000:
        v -= 0x10000
    return v


indices = []
pes_min = []
pes_avg = []
pes_max = []

with open(LOG_FILE, "r") as f:
    for line in f:
        parts = line.strip().split()
        hex_candidates = [
            p for p in parts
            if len(p) == 4 and all(c in "0123456789ABCDEFabcdef" for c in p)
        ]
        if len(hex_candidates) >= 3:
            mn, av, mx = hex_candidates[:3]
            pes_min.append(hex_to_signed16(mn))
            pes_avg.append(hex_to_signed16(av))
            pes_max.append(hex_to_signed16(mx))
            indices.append(len(indices))


pes_min = np.array(pes_min, dtype=float)
pes_avg = np.array(pes_avg, dtype=float)
pes_max = np.array(pes_max, dtype=float)

N = len(pes_avg)
Fs = N / DURATION_SEC

print(f"[INFO] Loaded {N} PES rows")
print(f"[INFO] Estimated sampling rate: {Fs:.3f} Hz")


t = np.linspace(0, DURATION_SEC, N)
pes_avg_dc = pes_avg - np.mean(pes_avg)


def sliding_rms(x, win):
    out = []
    for i in range(0, len(x), win):
        out.append(np.sqrt(np.mean(x[i:i+win] ** 2)))
    return np.array(out)


rms_win = int(Fs * 1.0) if Fs > 1 else 1
rms_vals = sliding_rms(pes_avg_dc, rms_win)
rms_t = np.linspace(0, DURATION_SEC, len(rms_vals))


f_fft = np.fft.rfftfreq(N, 1/Fs)
fft_mag = np.abs(np.fft.rfft(pes_avg_dc))
fw, pw = welch(pes_avg_dc, Fs, nperseg=min(2048, N))


def save_plot(name):
    path = os.path.join(SAVE_DIR, name)
    plt.savefig(path, dpi=200, bbox_inches="tight")
    if SHOW_PLOTS:
        plt.show()
    else:
        plt.close()


plt.figure(figsize=(14, 6))
plt.plot(t, pes_avg_dc)
plt.title("PES AVG — raw (DC removed)")
plt.xlabel("Time (s)")
plt.ylabel("PES avg")
plt.grid(True)
save_plot("pes_avg_raw.png")

plt.figure(figsize=(14, 5))
plt.plot(rms_t, rms_vals, '-o')
plt.title("RMS vibration level")
plt.xlabel("Time (s)")
plt.ylabel("RMS")
plt.grid(True)
save_plot("pes_rms.png")

plt.figure(figsize=(14, 6))
plt.semilogy(f_fft, fft_mag)
plt.xlim(0, PLOT_LIMIT_LOW_FREQ)
plt.title(f"FFT low-frequency spectrum (0–{PLOT_LIMIT_LOW_FREQ} Hz)")
plt.xlabel("Frequency (Hz)")
plt.ylabel("Magnitude")
plt.grid(True)
save_plot("fft_low_freq.png")

plt.figure(figsize=(14, 6))
plt.semilogy(fw, pw)
plt.xlim(0, PLOT_LIMIT_LOW_FREQ)
plt.title("PSD (Welch) low-frequency")
plt.xlabel("Frequency (Hz)")
plt.ylabel("Power")
plt.grid(True)
save_plot("psd_low_freq.png")

plt.figure(figsize=(14, 5))
plt.hist(pes_avg_dc, bins=50)
plt.title("Histogram of PES avg")
plt.xlabel("PES avg")
plt.ylabel("Count")
plt.grid(True)
save_plot("histogram_pes_avg.png")

plt.figure(figsize=(14, 6))
plt.imshow(np.vstack([pes_min, pes_avg, pes_max]),
           aspect='auto', cmap='viridis')
plt.title("MIN / AVG / MAX heatmap")
plt.yticks([0,1,2], ["MIN", "AVG", "MAX"])
plt.colorbar(label="PES value")
save_plot("heatmap_min_avg_max.png")
