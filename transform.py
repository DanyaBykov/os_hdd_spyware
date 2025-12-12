import numpy as np
from scipy.signal import butter, filtfilt, resample
import soundfile as sf
import sys
import os

if len(sys.argv) < 2:
	print(f"Usage: {os.path.basename(sys.argv[0])} <input_csv_file>")
	sys.exit(1)

csv_path = sys.argv[1]

data = np.genfromtxt(csv_path, delimiter=",", skip_header=1)
t = data[:, 0]
v = data[:, 1]

dt = np.median(np.diff(t))
fs = 1.0 / dt
print("Fs ≈", fs, "Hz")

thr = 0.5 * (v.min() + v.max())
bits = (v > thr).astype(float)

fc = 3000.0
b, a = butter(4, fc / (fs / 2), btype="low")
pes = filtfilt(b, a, bits)

pes = pes - np.mean(pes)
pes = pes / np.max(np.abs(pes))

target_fs = 44100
num_samples = int(len(pes) * target_fs / fs)
audio = resample(pes, num_samples)

audio = audio / np.max(np.abs(audio)) * 0.9

sf.write("room_audio.wav", audio, target_fs)
print("Saved: room_audio.wav")