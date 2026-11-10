#!/usr/bin/env python3
"""Udaje pilota: wysyla plik WAV (16 bit, mono) albo ton testowy tak samo jak firmware.

    python3 fake_mic.py                      # 1 s tonu 440 Hz na localhost:8765
    python3 fake_mic.py nagranie.wav --host 192.168.1.10 --speaker
"""
import argparse
import math
import socket
import struct
import wave

ap = argparse.ArgumentParser()
ap.add_argument("wav", nargs="?")
ap.add_argument("--host", default="127.0.0.1")
ap.add_argument("--port", type=int, default=8765)
ap.add_argument("--token", default="")
ap.add_argument("--speaker", action="store_true", help="udawaj wersje z glosnikiem")
a = ap.parse_args()

if a.wav:
    with wave.open(a.wav) as w:
        assert w.getsampwidth() == 2 and w.getnchannels() == 1, "potrzebny WAV 16 bit mono"
        rate, pcm = w.getframerate(), w.readframes(w.getnframes())
else:
    rate = 16000
    pcm = b"".join(struct.pack("<h", int(8000 * math.sin(2 * math.pi * 440 * i / rate))) for i in range(rate))

s = socket.create_connection((a.host, a.port), timeout=10)
head = (f"POST /api/voice HTTP/1.1\r\nHost: {a.host}:{a.port}\r\nContent-Type: application/octet-stream\r\n"
        f"Transfer-Encoding: chunked\r\nConnection: close\r\nX-Audio-Format: pcm_s16le\r\nX-Sample-Rate: {rate}\r\n"
        f"X-Channels: 1\r\nX-Device-Id: fake-mic\r\nX-Battery-Mv: 3900\r\nX-Speaker: {int(a.speaker)}\r\n")
if a.token:
    head += f"X-Auth-Token: {a.token}\r\n"
s.sendall(head.encode() + b"\r\n")
for i in range(0, len(pcm), 4096):
    chunk = pcm[i:i + 4096]
    s.sendall(f"{len(chunk):X}\r\n".encode() + chunk + b"\r\n")
s.sendall(b"0\r\n\r\n")
reply = b""
while True:
    part = s.recv(65536)
    if not part:
        break
    reply += part
head, _, body = reply.partition(b"\r\n\r\n")
print(head.decode(errors="replace"))
print(body.decode(errors="replace") if b"application/json" in head else f"<{len(body)} bajtow audio>")
