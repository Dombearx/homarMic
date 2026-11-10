#!/usr/bin/env python3
"""Generator plytek pilota glosowego (KiCad 7+, modul pcbnew).

Uzycie (systemowy Python z KiCadem):
    /usr/bin/python3 gen_pcb.py     # rozmieszczenie, sciezki, wylewki masy, DRC, zapis .kicad_pcb

Wspolrzedne w skrypcie: mm, poczatek w lewym dolnym rogu plytki, os Y w gore,
widok od strony elementow (przod). USB-C modulu XIAO wychodzi przez dolna krawedz.
"""
import os
import sys

import pcbnew
from pcbnew import FromMM, VECTOR2I

HERE = os.path.dirname(os.path.abspath(__file__))
FPLIB = "/usr/share/kicad/footprints"
OUT = os.path.join(HERE, "voice-mic.kicad_pcb")

W, H = 32.0, 62.0          # obrys plytki
XIAO_X0 = 7.1              # lewa krawedz modulu XIAO (szer. 17.8, dl. 21)
TRACK = 0.4
CLEAR = 0.2


def P(x, yup, h=H):
    return VECTOR2I(FromMM(x), FromMM(h - yup))


class Builder:
    def __init__(self, h):
        self.h = h
        self.b = pcbnew.BOARD()
        self.nets = {}
        ds = self.b.GetDesignSettings()
        ds.m_TrackMinWidth = FromMM(0.2)
        ds.m_MinClearance = FromMM(CLEAR)
        ds.m_ViasMinSize = FromMM(0.6)
        ds.m_CopperEdgeClearance = FromMM(0.3)
        nc = ds.m_NetSettings.m_DefaultNetClass
        nc.SetTrackWidth(FromMM(TRACK))
        nc.SetClearance(FromMM(CLEAR))
        nc.SetViaDiameter(FromMM(0.8))
        nc.SetViaDrill(FromMM(0.4))

    def P(self, x, y):
        return P(x, y, self.h)

    def net(self, name):
        if name not in self.nets:
            n = pcbnew.NETINFO_ITEM(self.b, name)
            self.b.Add(n)
            self.nets[name] = n
        return self.nets[name]

    def outline(self, w, h, r=2.0):
        def line(a, c):
            s = pcbnew.PCB_SHAPE(self.b)
            s.SetShape(pcbnew.SHAPE_T_SEGMENT)
            s.SetStart(self.P(*a)); s.SetEnd(self.P(*c))
            s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(FromMM(0.1))
            self.b.Add(s)

        def arc(center, start, end):
            # luk 90 st.; KiCad rysuje zgodnie z ruchem wskazowek (Y w dol)
            s = pcbnew.PCB_SHAPE(self.b)
            s.SetShape(pcbnew.SHAPE_T_ARC)
            s.SetCenter(self.P(*center)); s.SetStart(self.P(*start)); s.SetEnd(self.P(*end))
            s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(FromMM(0.1))
            self.b.Add(s)

        line((r, 0), (w - r, 0)); line((w, r), (w, h - r))
        line((w - r, h), (r, h)); line((0, h - r), (0, r))
        arc((r, r), (r, 0), (0, r))                    # lewy dol
        arc((r, h - r), (0, h - r), (r, h))            # lewa gora
        arc((w - r, h - r), (w - r, h), (w, h - r))    # prawa gora
        arc((w - r, r), (w, r), (w - r, 0))            # prawy dol

    def place(self, lib, name, ref, value, cx, cy, rot=0, nets=None, center=True):
        fp = pcbnew.FootprintLoad(os.path.join(FPLIB, lib + ".pretty"), name)
        fp.SetReference(ref); fp.SetValue(value)
        self.b.Add(fp)
        fp.SetOrientationDegrees(rot)
        fp.SetPosition(self.P(cx, cy))
        if center:  # wysrodkuj wzgledem prostokata opisanego na padach
            xs = [p.GetPosition().x for p in fp.Pads()]
            ys = [p.GetPosition().y for p in fp.Pads()]
            c = VECTOR2I((min(xs) + max(xs)) // 2, (min(ys) + max(ys)) // 2)
            t = self.P(cx, cy)
            fp.Move(VECTOR2I(t.x - c.x, t.y - c.y))
        for pad in fp.Pads():
            n = (nets or {}).get(pad.GetNumber())
            if n:
                pad.SetNet(self.net(n))
        fp.Value().SetVisible(False)
        return fp

    def text(self, s, x, y, size=0.8, layer=pcbnew.F_SilkS, rot=0):
        t = pcbnew.PCB_TEXT(self.b)
        t.SetText(s); t.SetPosition(self.P(x, y)); t.SetLayer(layer)
        t.SetTextSize(VECTOR2I(FromMM(size), FromMM(size)))
        t.SetTextThickness(FromMM(size * 0.16))
        t.SetTextAngleDegrees(rot)
        if layer == pcbnew.B_SilkS:
            t.SetMirrored(True)
        self.b.Add(t)

    def both(self, s, x, y, size=0.8, rot=0):
        self.text(s, x, y, size, pcbnew.F_SilkS, rot)
        self.text(s, x, y, size, pcbnew.B_SilkS, rot)

    def track(self, pts, net, width=0.6, layer=pcbnew.F_Cu):
        for a, c in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(self.b)
            t.SetStart(self.P(*a)); t.SetEnd(self.P(*c))
            t.SetWidth(FromMM(width)); t.SetLayer(layer); t.SetNet(self.net(net))
            self.b.Add(t)

    def gnd_zones(self, w, h):
        for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
            z = pcbnew.ZONE(self.b)
            z.SetLayer(layer); z.SetNet(self.net("GND"))
            o = z.Outline(); o.NewOutline()
            for x, y in ((0, 0), (w, 0), (w, h), (0, h)):
                o.Append(self.P(x, y).x, self.P(x, y).y)
            z.SetLocalClearance(FromMM(0.3))
            z.SetMinThickness(FromMM(0.25))
            z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
            z.SetThermalReliefGap(FromMM(0.3)); z.SetThermalReliefSpokeWidth(FromMM(0.5))
            z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
            self.b.Add(z)
        pcbnew.ZONE_FILLER(self.b).Fill(self.b.Zones())

    def drc(self, path):
        pcbnew.WriteDRCReport(self.b, path, pcbnew.EDA_UNITS_MILLIMETRES, True)
        txt = open(path).read()
        return txt


# --------------------------------------------------------------------------
# Modul XIAO ESP32-S3 montowany na plasko (pady krawedziowe) + 2 otwory pod
# pady baterii na spodzie modulu (lutowane od tylu plytki).
# Wymiary padow wg biblioteki Seeed OPL (XIAO-ESP32-S3-SMD).
XIAO_PINS = {  # numer: (nazwa, lx, u) ; lx od lewej krawedzi modulu, u od krawedzi przeciwnej do USB
    1: ("D0", 0.835, 18.12), 2: ("D1", 0.835, 15.58), 3: ("D2", 0.835, 13.04),
    4: ("D3", 0.835, 10.5), 5: ("D4", 0.835, 7.96), 6: ("D5", 0.835, 5.42),
    7: ("D6", 0.835, 2.88), 8: ("D7", 17.0, 2.88), 9: ("D8", 17.0, 5.42),
    10: ("D9", 17.0, 7.96), 11: ("D10", 17.0, 10.5), 12: ("3V3", 17.0, 13.04),
    13: ("GND", 17.0, 15.58), 14: ("5V", 17.0, 18.12),
}
XIAO_BAT = {23: ("BAT+", 4.445, 10.882), 24: ("BAT-", 4.445, 12.787)}


def xiao_xy(lx, u):
    """Modul obrocony o 180 st.: USB na dolnej krawedzi plytki."""
    return XIAO_X0 + 17.8 - lx, 21.0 - u


def add_xiao(B, nets):
    fp = pcbnew.FOOTPRINT(B.b)
    fp.SetReference("U1"); fp.SetValue("XIAO ESP32-S3")
    fp.SetPosition(B.P(XIAO_X0 + 8.9, 10.5))
    B.b.Add(fp)
    for num, (_, lx, u) in XIAO_PINS.items():
        x, y = xiao_xy(lx, u)
        pad = pcbnew.PAD(fp)
        pad.SetNumber(str(num)); pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
        pad.SetShape(pcbnew.PAD_SHAPE_ROUNDRECT); pad.SetRoundRectRadiusRatio(0.2)
        pad.SetSize(VECTOR2I(FromMM(2.75), FromMM(2.0)))
        pad.SetLayerSet(pad.SMDMask()); pad.SetPosition(B.P(x, y))
        pad.SetNet(B.net(nets[num])); fp.Add(pad); pad.SetLocalCoord()
    for num, (_, lx, u) in XIAO_BAT.items():
        x, y = xiao_xy(lx, u)
        pad = pcbnew.PAD(fp)
        pad.SetNumber(str(num)); pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        pad.SetShape(pcbnew.PAD_SHAPE_OVAL)
        pad.SetSize(VECTOR2I(FromMM(2.4), FromMM(1.4)))
        pad.SetDrillSize(VECTOR2I(FromMM(0.9), FromMM(0.9)))
        pad.SetLayerSet(pad.PTHMask()); pad.SetPosition(B.P(x, y))
        pad.SetNet(B.net(nets[num])); fp.Add(pad); pad.SetLocalCoord()
    # obrys modulu i gniazda USB na opisie
    def rect(x0, y0, x1, y1, layer):
        s = pcbnew.FP_SHAPE(fp); s.SetShape(pcbnew.SHAPE_T_RECT)
        s.SetStart(B.P(x0, y0)); s.SetEnd(B.P(x1, y1))
        s.SetLayer(layer); s.SetWidth(FromMM(0.12)); fp.Add(s); s.SetLocalCoord()
    rect(XIAO_X0, 0.15, XIAO_X0 + 17.8, 21.0, pcbnew.F_SilkS)
    rect(XIAO_X0, 0.0, XIAO_X0 + 17.8, 21.0, pcbnew.F_Fab)
    rect(XIAO_X0 + 4.4, 0.15, XIAO_X0 + 13.4, 6.0, pcbnew.F_SilkS)
    fp.Reference().SetPosition(B.P(XIAO_X0 + 8.9, 17.5))
    fp.Reference().SetTextSize(VECTOR2I(FromMM(0.8), FromMM(0.8)))
    fp.Reference().SetTextThickness(FromMM(0.13))
    fp.Value().SetVisible(False)
    return fp


def keepout_under_xiao(B):
    """Zakaz miedzi na warstwie gornej pod modulem (ma pady testowe na spodzie)."""
    z = pcbnew.ZONE(B.b)
    z.SetIsRuleArea(True)
    z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True); z.SetDoNotAllowCopperPour(True)
    z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
    z.SetLayer(pcbnew.F_Cu)
    o = z.Outline(); o.NewOutline()
    for x, y in ((XIAO_X0 + 2.6, 0), (XIAO_X0 + 15.2, 0), (XIAO_X0 + 15.2, 21.2), (XIAO_X0 + 2.6, 21.2)):
        o.Append(B.P(x, y).x, B.P(x, y).y)
    B.b.Add(z)


R1206 = ("Resistor_SMD", "R_1206_3216Metric_Pad1.30x1.75mm_HandSolder")
C1206 = ("Capacitor_SMD", "C_1206_3216Metric_Pad1.33x1.80mm_HandSolder")
WIRE1 = ("Connector_Wire", "SolderWire-0.5sqmm_1x01_D0.9mm_OD2.1mm")


def build_main():
    B = Builder(H)
    B.outline(W, H)
    xiao_nets = {1: "BAT_SENSE", 2: "BTN", 3: "MIC_PWR", 4: "I2S_BCLK", 5: "I2S_WS",
                 6: "MIC_SD", 7: "AMP_DIN", 8: "AMP_SD", 9: "LED_R", 10: "LED_G",
                 11: "LED_B", 12: "+3V3", 13: "GND", 14: "VBUS", 23: "VBAT", 24: "GND"}
    add_xiao(B, xiao_nets)
    keepout_under_xiao(B)

    for i, (x, y) in enumerate(((2.6, 3.5), (29.4, 3.5), (2.6, 58.5), (29.4, 58.5)), 1):
        B.place("MountingHole", "MountingHole_2.2mm_M2", f"H{i}", "M2", x, y, center=False
                ).Reference().SetVisible(False)

    # przycisk i dioda
    B.place("Button_Switch_THT", "SW_PUSH_6mm_H5mm", "SW1", "6x6x5", 16, 33,
            nets={"1": "BTN", "2": "GND"})
    B.place("LED_THT", "LED_D5.0mm-4_RGB_Staggered_Pins", "D1", "RGB 5mm wsp. katoda", 16, 42.5,
            nets={"1": "LED_RA", "2": "GND", "3": "LED_GA", "4": "LED_BA"})
    # rezystory diody - w pasie miedzy XIAO a przyciskiem
    B.place(*R1206, "R1", "470R", 9.5, 23.5, nets={"1": "LED_R", "2": "LED_RA"})
    B.place(*R1206, "R2", "220R", 9.5, 26.3, nets={"1": "LED_G", "2": "LED_GA"})
    B.place(*R1206, "R3", "220R", 16.0, 23.5, nets={"1": "LED_B", "2": "LED_BA"})
    B.place(*R1206, "R4", "100k", 22.5, 26.3, nets={"1": "+3V3", "2": "BTN"})
    B.place(*R1206, "R7", "10k", 22.5, 23.5, nets={"1": "AMP_SD", "2": "GND"})
    # dzielnik pomiaru baterii - prawy pas obok XIAO (przy D0)
    B.place(*R1206, "R5", "470k", 29.2, 9.5, 90, nets={"1": "BAT_SENSE", "2": "VBAT"})
    B.place(*R1206, "R6", "470k", 29.2, 14.5, 90, nets={"1": "GND", "2": "BAT_SENSE"})
    B.place(*C1206, "C1", "100n", 29.2, 19.5, 90, nets={"1": "GND", "2": "BAT_SENSE"})
    # dioda Schottky'ego: styk stacji -> pin 5V modulu
    B.place("Diode_SMD", "D_SMA_Handsoldering", "D2", "SS14", 2.9, 13.5, 90,
            nets={"1": "VBUS", "2": "DOCK_P"})
    B.place(*C1206, "C2", "10u", 4.0, 39.0, 90, nets={"1": "VBAT", "2": "GND"})
    # pola lutownicze przewodow
    B.place(*WIRE1, "J4", "DOCK+", 2.9, 22.5, nets={"1": "DOCK_P"})
    B.place(*WIRE1, "J5", "DOCK-", 29.2, 24.5, nets={"1": "GND"})
    B.place(*WIRE1, "J3", "BAT+", 3.5, 51.5, nets={"1": "VBAT"})
    B.place(*WIRE1, "J6", "BAT-", 3.5, 46.5, nets={"1": "GND"})
    # mikrofon INMP441 (przewody) i wzmacniacz MAX98357A (modul od tylu plytki)
    B.place("Connector_PinHeader_2.54mm", "PinHeader_1x06_P2.54mm_Vertical", "J1", "INMP441",
            16, 50.5, 90, nets={"1": "MIC_PWR", "2": "GND", "3": "MIC_SD", "4": "I2S_BCLK",
                                "5": "I2S_WS", "6": "GND"})
    B.place("Connector_PinHeader_2.54mm", "PinHeader_1x07_P2.54mm_Vertical", "J2", "MAX98357A",
            16, 58.5, 90, nets={"1": "VBAT", "2": "GND", "3": "AMP_SD", "4": "",
                                "5": "AMP_DIN", "6": "I2S_BCLK", "7": "I2S_WS"})
    return B


def label_main(B):
    for fp in B.b.GetFootprints():
        r = fp.Reference()
        r.SetTextSize(VECTOR2I(FromMM(0.8), FromMM(0.8))); r.SetTextThickness(FromMM(0.13))
        if fp.GetReference()[0] == "J" or fp.GetReference() in ("D1", "SW1"):
            r.SetVisible(False)
    def padxy(ref, num):
        for fp in B.b.GetFootprints():
            if fp.GetReference() == ref:
                for p in fp.Pads():
                    if p.GetNumber() == num:
                        return pcbnew.ToMM(p.GetPosition().x), H - pcbnew.ToMM(p.GetPosition().y)
    for num, name in zip("123456", ("VDD", "GND", "SD", "SCK", "WS", "L/R")):
        x, y = padxy("J1", num)
        B.both(name, x, y - 2.4, 0.8, 90)
    B.both("MIC", 27.5, 50.5, 0.9)
    for num, name in zip("1234567", ("VIN", "GND", "SD", "GAIN", "DIN", "BCLK", "LRC")):
        x, y = padxy("J2", num)
        B.both(name, x, y - 2.7, 0.8, 90)
    B.both("AMP", 27.5, 54.5, 0.9)
    B.both("BAT+", 7.6, 51.5, 0.9); B.both("BAT-", 7.6, 46.5, 0.9)
    B.both("DOCK+", 3.4, 25.0, 0.8); B.both("DOCK-", 28.0, 27.2, 0.8)
    B.text("USB", 16, 3.0, 0.9)
    B.text("PTT", 24.5, 33, 0.8); B.text("RGB", 23.5, 42.5, 0.8)
    B.text("voice-mic r1", 16, 29.2, 0.8)
    B.text("BAT+ / BAT- modulu XIAO:", 16, 15.5, 0.8, pcbnew.B_SilkS)
    B.text("zalac cyna 2 otwory", 16, 13.9, 0.8, pcbnew.B_SilkS)


# --------------------------------------------------------------------------
# Prowadzenie sciezek wlasnym routerem siatkowym (router.py)
ROUTE_ORDER = ["VBAT", "VBUS", "DOCK_P", "BAT_SENSE", "I2S_BCLK", "I2S_WS", "MIC_SD", "BTN", "LED_RA", "LED_GA", "LED_BA",
               "LED_R", "LED_G", "LED_B", "AMP_SD", "MIC_PWR", "AMP_DIN",
               "+3V3", "GND"]


def autoroute(B):
    from router import Router
    R = Router(W, H, track=TRACK, clear=CLEAR)
    for fp in B.b.GetFootprints():
        for p in fp.Pads():
            bb = p.GetBoundingBox()
            x0, y0 = pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop())
            x1, y1 = pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom())
            tht = p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH)
            R.add_pad(p.GetNetname() or None, (0, 1) if tht else (0,), x0, y0, x1, y1)
    R.add_keepout(0, XIAO_X0 + 2.4, H - 21.4, XIAO_X0 + 15.4, H)
    ok = True
    for net in ROUTE_ORDER:
        ok = R.route_net(net) and ok
    for net, layer, a, c in R.segs:
        t = pcbnew.PCB_TRACK(B.b)
        t.SetStart(VECTOR2I(FromMM(a[0]), FromMM(a[1]))); t.SetEnd(VECTOR2I(FromMM(c[0]), FromMM(c[1])))
        t.SetWidth(FromMM(TRACK)); t.SetLayer(pcbnew.F_Cu if layer == 0 else pcbnew.B_Cu)
        t.SetNet(B.net(net)); B.b.Add(t)
    for net, (x, y) in R.vias:
        v = pcbnew.PCB_VIA(B.b)
        v.SetPosition(VECTOR2I(FromMM(x), FromMM(y)))
        v.SetWidth(FromMM(0.8)); v.SetDrill(FromMM(0.4))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(B.net(net)); B.b.Add(v)
    print(f"router: {len(R.segs)} odcinkow, {len(R.vias)} przelotek, komplet={ok}")
    return ok


# --------------------------------------------------------------------------
# Plytka stacji dokujacej: 2 piny pogo + pola przewodow 5 V
DOCK_W, DOCK_H = 36.0, 12.0
POGO_SPACING = 18.8     # = 2 * (contact_dx + pogo_off) z case/voice_mic.scad


def build_dock():
    B = Builder(DOCK_H)
    B.outline(DOCK_W, DOCK_H, 1.5)
    cx = DOCK_W / 2
    fp = pcbnew.FOOTPRINT(B.b); fp.SetReference("P1"); fp.SetValue("pogo x2")
    fp.SetPosition(B.P(cx, 7.0)); B.b.Add(fp)
    for num, dx, net in (("1", -POGO_SPACING / 2, "+5V"), ("2", POGO_SPACING / 2, "GND")):
        pad = pcbnew.PAD(fp); pad.SetNumber(num); pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        pad.SetSize(VECTOR2I(FromMM(3.2), FromMM(3.2)))
        pad.SetDrillSize(VECTOR2I(FromMM(1.3), FromMM(1.3)))
        pad.SetLayerSet(pad.PTHMask()); pad.SetPosition(B.P(cx + dx, 7.0))
        pad.SetNet(B.net(net)); fp.Add(pad); pad.SetLocalCoord()
    fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
    B.place(*WIRE1, "J1", "+5V", cx - 2.5, 3.0, nets={"1": "+5V"}).Reference().SetVisible(False)
    B.place(*WIRE1, "J2", "GND", cx + 2.5, 3.0, nets={"1": "GND"}).Reference().SetVisible(False)
    for i, x in enumerate((cx - 15.5, cx + 15.5), 1):
        B.place("MountingHole", "MountingHole_2.2mm_M2", f"H{i}", "M2", x, 8.5, center=False
                ).Reference().SetVisible(False)
    B.track([(cx - 2.5, 3.0), (cx - POGO_SPACING / 2, 3.0), (cx - POGO_SPACING / 2, 7.0)], "+5V", 0.8)
    B.track([(cx + 2.5, 3.0), (cx + POGO_SPACING / 2, 3.0), (cx + POGO_SPACING / 2, 7.0)], "GND", 0.8)
    B.both("+5V", cx - POGO_SPACING / 2, 10.3, 0.9); B.both("GND", cx + POGO_SPACING / 2, 10.3, 0.9)
    B.both("+", cx - 2.5, 5.3, 0.9); B.both("-", cx + 2.5, 5.3, 0.9)
    B.text("voice-mic dock r1", cx, 1.0, 0.8)
    return B


def finish(B, path, w, h, report):
    """Zapis -> ponowne wczytanie -> wylewki -> DRC (stabilniejsze poza GUI)."""
    pcbnew.SaveBoard(path, B.b)
    print("zapisano", path, flush=True)
    B.b = pcbnew.LoadBoard(path)
    B.nets = {}
    B.net("GND")
    B.b.Remove(B.nets["GND"]); B.nets["GND"] = B.b.FindNet("GND")
    B.gnd_zones(w, h)
    pcbnew.SaveBoard(path, B.b)
    print("wylewki OK", flush=True)
    print(B.drc(report))


def main():
    os.makedirs(os.path.join(HERE, "build"), exist_ok=True)
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("all", "main"):
        B = build_main()
        autoroute(B)
        label_main(B)
        finish(B, OUT, W, H, os.path.join(HERE, "build", "drc-voice-mic.txt"))
    if which in ("all", "dock"):
        D = build_dock()
        finish(D, os.path.join(HERE, "voice-mic-dock.kicad_pcb"), DOCK_W, DOCK_H,
               os.path.join(HERE, "build", "drc-dock.txt"))


if __name__ == "__main__":
    main()
