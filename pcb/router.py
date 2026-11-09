"""Prosty dwuwarstwowy router siatkowy (A*) dla malych plytek.

Pracuje na siatce 0,2 mm w ukladzie KiCada (mm, Y w dol). Nie zalezy od pcbnew:
dostaje liste padow, zwraca odcinki sciezek i przelotki. Poprawnosc wyniku
sprawdza potem DRC KiCada.
"""
import heapq
import math

G = 0.2                      # raster siatki [mm]
DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
MULTI = -1


class Router:
    def __init__(self, w, h, track=0.4, clear=0.2, via=0.8, margin=0.1, edge=0.5, corner_r=2.0):
        self.w, self.h = w, h
        self.nx, self.ny = int(round(w / G)) + 1, int(round(h / G)) + 1
        self.track, self.clear, self.via, self.margin = track, clear, via, margin
        self.rt = track / 2 + clear + margin          # srodek sciezki od obcej miedzi
        self.rv = via / 2 + clear + margin            # srodek przelotki od obcej miedzi
        n = self.nx * self.ny
        self.occ_t = [[0] * n, [0] * n]               # [warstwa][komorka] -> id sieci / MULTI
        self.occ_v = [[0] * n, [0] * n]
        self.block = [[False] * n, [False] * n]       # twarde zakazy (krawedz, strefy)
        self.noVia = [False] * n
        self.ids = {}
        self.pads = {}                                # siec -> [(warstwy, x0, y0, x1, y1)]
        self.copper = {}                              # siec -> zbior (x, y, warstwa)
        self.segs, self.vias = [], []
        e = edge + track / 2
        for iy in range(self.ny):
            for ix in range(self.nx):
                x, y = ix * G, iy * G
                bad = x < e or y < e or x > w - e or y > h - e
                cx = min(max(x, corner_r), w - corner_r)
                cy = min(max(y, corner_r), h - corner_r)
                if math.hypot(x - cx, y - cy) > corner_r - e:
                    bad = bad or (cx != x and cy != y)
                if bad:
                    i = iy * self.nx + ix
                    self.block[0][i] = self.block[1][i] = True
                    self.noVia[i] = True

    def nid(self, name):
        return self.ids.setdefault(name, len(self.ids) + 1)

    def _mark(self, arr, i, n):
        v = arr[i]
        if v == 0:
            arr[i] = n
        elif v != n:
            arr[i] = MULTI

    def _paint_rect(self, layer, x0, y0, x1, y1, n):
        for arr, r in ((self.occ_t[layer], self.rt), (self.occ_v[layer], self.rv)):
            for iy in range(max(0, math.ceil((y0 - r) / G)), min(self.ny - 1, math.floor((y1 + r) / G)) + 1):
                for ix in range(max(0, math.ceil((x0 - r) / G)), min(self.nx - 1, math.floor((x1 + r) / G)) + 1):
                    self._mark(arr, iy * self.nx + ix, n)

    def _paint_seg(self, layer, a, b, half, n):
        for arr, r0 in ((self.occ_t[layer], self.rt), (self.occ_v[layer], self.rv)):
            r = r0 + half
            x0, x1 = min(a[0], b[0]) - r, max(a[0], b[0]) + r
            y0, y1 = min(a[1], b[1]) - r, max(a[1], b[1]) + r
            dx, dy = b[0] - a[0], b[1] - a[1]
            L2 = dx * dx + dy * dy
            for iy in range(max(0, math.ceil(y0 / G)), min(self.ny - 1, math.floor(y1 / G)) + 1):
                for ix in range(max(0, math.ceil(x0 / G)), min(self.nx - 1, math.floor(x1 / G)) + 1):
                    px, py = ix * G, iy * G
                    t = 0 if L2 == 0 else max(0, min(1, ((px - a[0]) * dx + (py - a[1]) * dy) / L2))
                    if math.hypot(px - a[0] - t * dx, py - a[1] - t * dy) <= r:
                        self._mark(arr, iy * self.nx + ix, n)

    def add_pad(self, net, layers, x0, y0, x1, y1):
        """net=None -> przeszkoda bez sieci (otwor montazowy)."""
        n = self.nid(net) if net else self.nid(f"__obst{len(self.ids)}")
        for l in layers:
            self._paint_rect(l, x0, y0, x1, y1, n)
        if net:
            self.pads.setdefault(net, []).append((layers, x0, y0, x1, y1))

    def add_keepout(self, layer, x0, y0, x1, y1, vias=True):
        for iy in range(max(0, math.ceil(y0 / G)), min(self.ny - 1, math.floor(y1 / G)) + 1):
            for ix in range(max(0, math.ceil(x0 / G)), min(self.nx - 1, math.floor(x1 / G)) + 1):
                i = iy * self.nx + ix
                self.block[layer][i] = True
                if vias:
                    self.noVia[i] = True

    def _pad_cells(self, pad):
        layers, x0, y0, x1, y1 = pad
        out = set()
        # tylko wnetrze pada (koniec sciezki nie moze wystawac poza miedz)
        m = min(self.track / 2, (x1 - x0) / 2 - 0.01, (y1 - y0) / 2 - 0.01)
        for iy in range(math.ceil((y0 + m) / G - 1e-9), math.floor((y1 - m) / G + 1e-9) + 1):
            for ix in range(math.ceil((x0 + m) / G - 1e-9), math.floor((x1 - m) / G + 1e-9) + 1):
                for l in layers:
                    out.add((ix, iy, l))
        return out

    def _free(self, ix, iy, l, n):
        i = iy * self.nx + ix
        if self.block[l][i]:
            return False
        v = self.occ_t[l][i]
        return v == 0 or v == n

    def _via_ok(self, ix, iy, n):
        i = iy * self.nx + ix
        if self.noVia[i]:
            return False
        return all(self.occ_v[l][i] in (0, n) for l in (0, 1))

    def route_net(self, net, via_cost=12.0, layer_cost=(1.0, 1.0)):
        n = self.nid(net)
        pads = self.pads[net]
        cells = [self._pad_cells(p) for p in pads]
        tree = set(cells[0]) | self.copper.get(net, set())
        todo = list(range(1, len(pads)))
        ok = True
        while todo:
            targets = {}
            for k in todo:
                for c in cells[k]:
                    targets[c] = k
            path = self._astar(tree, targets, n, via_cost, layer_cost)
            if path is None:
                ok = False
                print(f"  !! {net}: brak polaczenia do {len(todo)} padow")
                break
            k = targets[path[-1]]
            todo.remove(k)
            self._commit(net, n, path)
            tree |= set(path) | cells[k]
        self.copper[net] = tree
        return ok

    def _astar(self, sources, targets, n, via_cost, layer_cost):
        tl = list(targets)

        def hfun(ix, iy):
            best = 1e9
            for tx, ty, _ in tl[:: max(1, len(tl) // 24)]:
                dx, dy = abs(tx - ix), abs(ty - iy)
                d = max(dx, dy) + 0.414 * min(dx, dy)
                if d < best:
                    best = d
            return best

        dist, prev, pq = {}, {}, []
        for c in sources:
            s = (c[0], c[1], c[2], -1)
            dist[s] = 0.0
            heapq.heappush(pq, (hfun(c[0], c[1]), 0.0, s))
        while pq:
            _, d, s = heapq.heappop(pq)
            if d > dist.get(s, 1e18):
                continue
            ix, iy, l, dr = s
            if (ix, iy, l) in targets:
                out = []
                while s is not None:
                    out.append((s[0], s[1], s[2]))
                    s = prev.get(s)
                return out[::-1]
            for k, (dx, dy) in enumerate(DIRS):
                jx, jy = ix + dx, iy + dy
                if not (0 <= jx < self.nx and 0 <= jy < self.ny):
                    continue
                if not (self._free(jx, jy, l, n) or (jx, jy, l) in targets):
                    continue
                if dx and dy and not (self._free(ix + dx, iy, l, n) and self._free(ix, iy + dy, l, n)):
                    continue
                step = (1.414 if dx and dy else 1.0) * layer_cost[l]
                if dr != -1 and k != dr:
                    step += 0.6 + (1.5 if (k - dr) % 8 not in (1, 7) else 0)
                t = (jx, jy, l, k)
                nd = d + step
                if nd < dist.get(t, 1e18):
                    dist[t] = nd; prev[t] = s
                    heapq.heappush(pq, (nd + hfun(jx, jy), nd, t))
            ol = 1 - l
            if self._via_ok(ix, iy, n) and (self._free(ix, iy, ol, n) or (ix, iy, ol) in targets):
                t = (ix, iy, ol, -1)
                nd = d + via_cost
                if nd < dist.get(t, 1e18):
                    dist[t] = nd; prev[t] = s
                    heapq.heappush(pq, (nd + hfun(ix, iy), nd, t))
        return None

    def _commit(self, net, n, path):
        run = [path[0]]
        def flush():
            if len(run) >= 2:
                a, b = run[0], run[-1]
                pa, pb = (a[0] * G, a[1] * G), (b[0] * G, b[1] * G)
                self.segs.append((net, a[2], pa, pb))
                self._paint_seg(a[2], pa, pb, self.track / 2, n)
        for p, q in zip(path, path[1:]):
            if p[2] != q[2]:
                flush()
                x, y = p[0] * G, p[1] * G
                self.vias.append((net, (x, y)))
                for l in (0, 1):
                    self._paint_seg(l, (x, y), (x, y), self.via / 2, n)
                run = [q]
                continue
            if len(run) >= 2:
                d0 = (run[-1][0] - run[-2][0], run[-1][1] - run[-2][1])
                d1 = (q[0] - p[0], q[1] - p[1])
                if d0 != d1:
                    last = run[-1]
                    flush()
                    run = [last]
            run.append(q)
        flush()
