import numpy as np
from scipy.signal import butter, filtfilt, resample, iirnotch
import soundfile as sf
import noisereduce as nr
import sys
import os

if len(sys.argv) < 2:
    print(f"Usage: {os.path.basename(sys.argv[0])} <input_csv_file>")
    sys.exit(1)

csv_path = sys.argv[1]
print("Loading data...")
data = np.genfromtxt(
    csv_path,
    delimiter=",",
    skip_header=1
)

t = data[:, 0]
v = data[:, 1]

dt = np.median(np.diff(t))
fs = 1.0 / dt
print(f"Fs ≈ {fs:.1f} Hz")

signal = v - np.mean(v)

f_servo = 5210.0
Q = 30.0
bN, aN = iirnotch(f_servo, Q, fs)
signal = filtfilt(bN, aN, signal)

f_low = 100.0
f_high = 5100.0

bBP, aBP = butter(
    6, 
    [f_low / (fs / 2), f_high / (fs / 2)], 
    btype="band"
)
pes = filtfilt(bBP, aBP, signal)

try:
    print("Applying spectral noise reduction...")
    noise_clip = pes[0:5000]
    pes_clean = nr.reduce_noise(y=pes, sr=fs, y_noise=noise_clip, stationary=True)
except Exception as e:
    print(f"Skipping noise reduction (install noisereduce to enable): {e}")
    pes_clean = pes

target_fs = 44100
num_samples = int(len(pes_clean) * target_fs / fs)
audio = resample(pes_clean, num_samples)

peak = np.max(np.abs(audio))
if peak > 0:
    audio = audio / peak * 0.9

base = os.path.splitext(os.path.basename(csv_path))[0]
wav_name = f"{base}.wav"
sf.write(wav_name, audio, target_fs)
print(f"Done: {wav_name}")