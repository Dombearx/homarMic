#!/usr/bin/env python3
"""Serwer odbiorczy pilota glosowego (tylko biblioteka standardowa Pythona).

Pilot wysyla nagranie jako POST /api/voice (surowe PCM 16 bit, 16 kHz, mono,
Transfer-Encoding: chunked). Serwer zapisuje je jako plik WAV i oddaje dalej:

    python3 voice_server.py                          # tylko zapis do ./recordings
    python3 voice_server.py --exec "python3 agent.py"  # po kazdym nagraniu: agent.py <plik.wav>

Polecenie z --exec dostaje sciezke WAV jako ostatni argument oraz zmienne
srodowiskowe VOICE_DEVICE, VOICE_BATTERY_MV. Jesli wypisze na stdout sciezke do
pliku .wav, a pilot ma glosnik, plik ten wraca do pilota jako odpowiedz glosowa.

Mozna tez uzyc tego modulu we wlasnym kodzie:

    from voice_server import serve
    def handle(wav_path, meta):      # meta: device, battery_mv, speaker, seconds
        ...                          # transkrypcja, agent
        return None                  # albo sciezka / bajty WAV z odpowiedzia
    serve(handle, port=8765)
"""
import argparse
import json
import os
import shlex
import subprocess
import sys
import time
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MAX_BYTES = 16000 * 2 * 120          # gorny limit jednego nagrania (2 minuty)


def make_handler(callback, out_dir, token):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def _reply(self, code, body, ctype="application/json"):
            if isinstance(body, (dict, list)):
                body = json.dumps(body).encode()
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(body)
            self.close_connection = True

        def _read_body(self):
            if "chunked" in self.headers.get("Transfer-Encoding", "").lower():
                data = bytearray()
                while True:
                    line = self.rfile.readline(64)
                    if not line:
                        raise ConnectionError("przerwane przesylanie")
                    size = int(line.split(b";")[0].strip() or b"0", 16)
                    if size == 0:
                        while self.rfile.readline(1024) not in (b"\r\n", b"\n", b""):
                            pass
                        return bytes(data)
                    chunk = self.rfile.read(size)
                    if len(chunk) != size:
                        raise ConnectionError("przerwane przesylanie")
                    data += chunk
                    self.rfile.readline(8)
                    if len(data) > MAX_BYTES:
                        raise ValueError("nagranie za dlugie")
            n = int(self.headers.get("Content-Length", "0"))
            if n > MAX_BYTES:
                raise ValueError("nagranie za dlugie")
            return self.rfile.read(n)

        def do_GET(self):
            self._reply(200, {"ok": True, "service": "voice-mic"})

        def do_POST(self):
            if self.path.split("?")[0] != "/api/voice":
                return self._reply(404, {"ok": False, "error": "not found"})
            if token and self.headers.get("X-Auth-Token", "") != token:
                return self._reply(401, {"ok": False, "error": "unauthorized"})
            try:
                pcm = self._read_body()
            except (ValueError, ConnectionError) as e:
                return self._reply(400, {"ok": False, "error": str(e)})
            rate = int(self.headers.get("X-Sample-Rate", "16000"))
            device = "".join(ch for ch in self.headers.get("X-Device-Id", "mic") if ch.isalnum() or ch in "-_")[:32] or "mic"
            meta = {
                "device": device,
                "battery_mv": int(self.headers.get("X-Battery-Mv", "0") or 0),
                "speaker": self.headers.get("X-Speaker", "0") == "1",
                "seconds": round(len(pcm) / 2 / rate, 2),
            }
            os.makedirs(out_dir, exist_ok=True)
            path = os.path.join(out_dir, f"{time.strftime('%Y%m%d-%H%M%S')}_{device}_{int(time.time() * 1000) % 1000:03d}.wav")
            with wave.open(path, "wb") as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
                w.writeframes(pcm[: len(pcm) // 2 * 2])
            print(f"[{time.strftime('%H:%M:%S')}] {device}: {meta['seconds']} s, bateria {meta['battery_mv']} mV -> {path}", flush=True)
            try:
                answer = callback(path, meta) if callback else None
            except Exception as e:                      # blad obslugi = czerwona dioda na pilocie
                print("blad obslugi:", e, file=sys.stderr, flush=True)
                return self._reply(500, {"ok": False, "error": str(e)})
            if isinstance(answer, str) and os.path.isfile(answer):
                with open(answer, "rb") as f:
                    answer = f.read()
            if isinstance(answer, (bytes, bytearray)) and meta["speaker"] and answer[:4] == b"RIFF":
                return self._reply(200, bytes(answer), "audio/wav")
            self._reply(200, {"ok": True, **meta})

        def log_message(self, *a):
            pass

    return Handler


def serve(callback=None, host="0.0.0.0", port=8765, out_dir="recordings", token=""):
    srv = ThreadingHTTPServer((host, port), make_handler(callback, out_dir, token))
    print(f"voice-mic: slucham na {host}:{port}, nagrania w {os.path.abspath(out_dir)}", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


def exec_callback(command):
    def run(path, meta):
        env = dict(os.environ, VOICE_DEVICE=meta["device"], VOICE_BATTERY_MV=str(meta["battery_mv"]))
        r = subprocess.run(shlex.split(command) + [path], env=env, capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            raise RuntimeError(r.stderr.strip() or f"kod wyjscia {r.returncode}")
        last = (r.stdout.strip().splitlines() or [""])[-1].strip()
        return last if last.lower().endswith(".wav") and os.path.isfile(last) else None
    return run


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Serwer odbiorczy pilota glosowego")
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--dir", default="recordings", help="katalog na pliki WAV")
    ap.add_argument("--token", default=os.environ.get("VOICE_TOKEN", ""), help="wymagany naglowek X-Auth-Token")
    ap.add_argument("--exec", dest="command", help="polecenie uruchamiane po kazdym nagraniu (sciezka WAV jako argument)")
    a = ap.parse_args()
    serve(exec_callback(a.command) if a.command else None, a.host, a.port, a.dir, a.token)
