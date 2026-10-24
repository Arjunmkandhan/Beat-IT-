"""Creates small test sounds so you can try the language without any audio files.
Run once:  python make_demo_sounds.py"""
import math, random, struct, wave
from pathlib import Path

RATE = 44100

def write(path, samples):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, x)) * 32000)) for x in samples))

def tone(freq, secs, decay):
    n = int(RATE * secs)
    return [math.sin(2 * math.pi * freq * i / RATE) * math.exp(-decay * i / n) for i in range(n)]

def noise(secs, level, decay):
    n = int(RATE * secs)
    return [random.uniform(-1, 1) * level * math.exp(-decay * i / n) for i in range(n)]

write("sounds/kick.wav", tone(70, 0.40, 5))
write("sounds/snare.wav", noise(0.25, 0.8, 6))
write("sounds/noise/rain.wav", noise(1.00, 0.3, 0.5))
write("birdsounds/chirp.wav", tone(2200, 0.50, 4))
print("Created sounds/, sounds/noise/ and birdsounds/")
