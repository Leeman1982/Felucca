#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""NightShift: take the few Open Samples sounds the SAMPLE and DRUM engines use into assets/samples-os/.

Open Samples (https://github.com/pumodi/open-samples, Jeffrey "Pumodi" Brice and contributors) is under the Open
Samples Permissive Use Public License, not CC0: free to use in music and sound playback, commercial or not, but not to
be resold as a sample product, and not for training AI models. So the excerpts are not kept in this tree (assets/
samples-os/ holds only ATTRIBUTION.txt); this script makes them from the original files, and a firmware built with
them must not be sold as a sample product (NOTICE in README.md). tools/gen_samples.py builds without them (the sets
stay, as names that play a sine: SAMPLE's missing-sample sound).

The originals: a local checkout (OPEN_SAMPLES=path, or ../open-samples next to this repository), else each file is
downloaded from the repository (about 25 MB). Each JV-2080 / M1 file holds one note a C, held, every 7.2 s (C2, C3,
C4 ..; 4pole_Bass from C1); the LinnDrum is a Kontakt monolith of 17 one-shot WAVs, taken out by their RIFF headers.

What is taken (a mono 16-bit excerpt from each note's onset):
  101BASS   Roland JV-2080 "101_Bass"      C2 C3 C4    SH-101 style synth bass, steady (looped by gen_samples.py)
  4PBASS    Roland JV-2080 "4pole_Bass"    C1 C2 C3    a four-pole ladder bass, round (its file starts at C1)
  JUNOSTR   Roland JV-2080 "JUNO_Strings"  C2 C3 C4    Juno string ensemble (the attack is the engine's ATK)
  LINN      LinnDrum (Kontakt monolith)    eight hits on the DRUM lanes' GM notes: kick 36, snare 38, clap 39,
            closed hat 42, open hat 46, tom 45, rim 37, cowbell 56 (the monolith's hits are unnamed: picked by their
            spectra, see LINN_HITS)

  tools/fetch_open_samples.py            make assets/samples-os/
"""
import os
import struct
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sampleio import read_any_wav  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "assets" / "samples-os"
RAW = "https://raw.githubusercontent.com/pumodi/open-samples/main/"
JV = "Synthesizers/RolandSynthesizers/Roland JV-2080/Samples/"

# set dir: (source file, [(note index in the file (0 = C2), MIDI root)], seconds kept)
NOTE_SETS = {
    "101BASS": (JV + "101_Bass.wav", [(0, 36), (1, 48), (2, 60)], 1.4),
    "4PBASS": (JV + "4pole_Bass.wav", [(0, 24), (1, 36), (2, 48)], 1.4),   # (this one starts at C1)
    "JUNOSTR": (JV + "JUNO_Strings.wav", [(0, 36), (1, 48), (2, 60)], 1.6),
}
NOTE_PITCH = 7.2                    # s from one note to the next in these files
LINN = "Synthesizers/Linn/LinnDrum/LinnDrum.nbkt"
# the monolith's WAVs in file order (vsm_linndrum-005 .. -017, -001 .. -004) -> the lane each one plays, by its
# spectrum and envelope: -003 the kick (all below 400 Hz), -002 the snare (a 130 Hz body under a bright burst, gated
# at 0.18 s), -006 the clap (a burst in several hits, 1..3 kHz), -012 the closed hat (0.13 s, 8 kHz), -013 the open
# hat (0.9 s), -015 a tom (141 Hz, its stick noise), -001 the rim (a click ringing near 1 kHz), -007 the cowbell (its
# partials 0.6 .. 3 kHz, 0.15 s)
LINN_HITS = {"003": ("kick", 36), "002": ("snare", 38), "006": ("clap", 39), "012": ("hatcl", 42),
             "013": ("hatop", 46), "015": ("tom", 45), "001": ("rim", 37), "007": ("bell", 56)}


def source(rel):
    """the original file's bytes: the local checkout, else the repository"""
    base = os.environ.get("OPEN_SAMPLES") or str(ROOT.parent / "open-samples")
    p = Path(base) / rel
    if p.exists():
        return p.read_bytes()
    print(f"  downloading {rel}")
    with urllib.request.urlopen(RAW + urllib.parse.quote(rel)) as r:
        return r.read()


def write_wav(path, sr, x):
    """mono float -> 16-bit PCM WAV, peak at -0.5 dBFS"""
    pk = max(1e-9, max(abs(v) for v in x))
    g = 0.944 / pk
    data = struct.pack("<%dh" % len(x), *(max(-32768, min(32767, int(round(v * g * 32767)))) for v in x))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"RIFF" + struct.pack("<I", 36 + len(data)) + b"WAVEfmt " +
                     struct.pack("<IHHIIHH", 16, 1, 1, sr, sr * 2, 2, 16) + b"data" + struct.pack("<I", len(data)) + data)


def onset_from(x, start, rel=0.02):
    """the first sample from `start` above rel x the peak of the next second (a note's attack), less 2 ms"""
    seg = x[start:start + 44100]
    pk = max(1e-9, max(abs(v) for v in seg))
    i = next((i for i, v in enumerate(seg) if abs(v) > rel * pk), 0)
    return max(start, start + i - 88)


def notes():
    for d, (rel, picks, keep) in NOTE_SETS.items():
        tmp = DEST / ".src.wav"
        tmp.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_bytes(source(rel))
        sr, x = read_any_wav(tmp)
        tmp.unlink()
        for k, (n, root) in enumerate(picks):
            a = onset_from(x, int(n * NOTE_PITCH * sr))
            write_wav(DEST / d / f"{k:02d}_{root}.wav", sr, x[a:a + int(keep * sr)])
        print(f"  {d}: {len(picks)} notes from {rel.rsplit('/', 1)[1]}")


def linn():
    d = source(LINN)
    names = []
    for i in range(0, 13056, 2):                     # the table of contents: UTF-16 names before the first WAV
        if d[i:i + 26] == "vsm_linndrum-".encode("utf-16-le"):
            names.append(d[i + 26:i + 32].decode("utf-16-le"))
    offs = []
    i = d.find(b"RIFF")
    while i >= 0:
        offs.append(i)
        i = d.find(b"RIFF", i + 8)
    n = 0
    for name, o in zip(names, offs):
        if name not in LINN_HITS:
            continue
        size = struct.unpack_from("<I", d, o + 4)[0]
        tmp = DEST / ".src.wav"
        tmp.write_bytes(d[o:o + 8 + size])
        sr, x = read_any_wav(tmp)
        tmp.unlink()
        role, key = LINN_HITS[name]
        a = onset_from(x, 0)
        write_wav(DEST / "LINN" / f"{key}_{role}.wav", sr, x[a:])
        n += 1
    if n != len(LINN_HITS):
        sys.exit(f"LinnDrum: {n} of {len(LINN_HITS)} hits found")
    print(f"  LINN: {n} hits from {LINN.rsplit('/', 1)[1]}")


if __name__ == "__main__":
    notes()
    linn()
