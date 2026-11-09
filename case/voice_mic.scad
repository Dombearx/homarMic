// Pilot glosowy - obudowa i stacja dokujaca (OpenSCAD)
//
// Uklad wspolrzednych urzadzenia = uklad plytki: X w prawo (0..32), Y w gore
// (0..62, USB na dole), Z w glab od przedniej scianki (Z=0 lezy na stole drukarki).
//
// Eksport:  openscad -D 'part="tub"' -D speaker=false -o tub.stl voice_mic.scad
//   part = "tub" | "lid" | "button" | "dock" | "assembly"

part    = "assembly";
speaker = false;      // true = wydluzona wersja z glosnikiem 28 mm

/* [Plytka] */
pcb_w = 32; pcb_l = 62; pcb_t = 1.6;
holes = [[2.6, 3.5], [29.4, 3.5], [2.6, 58.5], [29.4, 58.5]];
btn_xy = [16, 33]; led_xy = [16, 42.5]; mic_xy = [16, 53.6];
usb_x = 16;

/* [Obudowa] */
c      = 0.3;    // luz wokol plytki
wall   = 2.2;    // scianki boczne i gorna
bwall  = 4.0;    // scianka dolna (USB, styki, magnes)
front  = 2.0;    // scianka przednia
gap_f  = 7.5;    // przod plytki -> scianka przednia
gap_b  = 8.0;    // tyl plytki -> pokrywa (bateria)
lid_t  = 2.0;
r_in   = 2.2;
ext    = speaker ? 34 : 0;   // przedluzenie na glosnik
spk_d  = 28;     // srednica glosnika
mic_shape = "round";   // "round" (modul okragly 14 mm) | "square" (14 x 14 mm)
mic_d  = 14.6;

/* [Elementy] */
sw_h      = 5.0;   // wysokosc mikroprzycisku 6x6 (od plytki do czubka)
btn_d     = 12;    // otwor na klawisz
led_d     = 5.3;
screw_pilot = 1.7; // otwor pod wkret M2
screw_clear = 2.4;
screw_head  = 4.2;
contact_dx  = 7.5; // styki ladowania: sruby M3 w dolnej sciance, X = usb_x +- contact_dx
pogo_off    = 1.9; // pin pogo trafia w pierscien lba sruby, nie w gniazdo imbusowe
magnet_d = 8.2; magnet_h = 3.2;   // magnes 8 x 3 mm

/* [Stacja] */
pogo_body  = 7.0;  // wysokosc pinu pogo nad plytka stacji (w stanie swobodnym)
pogo_hole  = 3.2;  // otwor w podlodze stacji
pogo_stick = 1.3;  // o ile pin wystaje ponad podloge
dock_pcb = [36, 12];
cup_depth = 16;

$fn = 48;
eps = 0.01;

// ---- wymiary pochodne ----
zp  = front + gap_f;            // przednia powierzchnia plytki
zb  = zp + pcb_t;               // tylna powierzchnia plytki
zc  = zb + gap_b;               // koniec wanny / poczatek pokrywy
ix0 = -c; ix1 = pcb_w + c; iy0 = -c; iy1 = pcb_l + c + ext;
ox0 = ix0 - wall; ox1 = ix1 + wall; oy0 = iy0 - bwall; oy1 = iy1 + wall;
r_out = r_in + wall;
z_contact = zb + 4.0;
z_magnet  = zb + 3.8;
z_usb     = zp - 1.2 - 1.6;      // os gniazda USB-C modulu XIAO
seat_z    = zc + lid_t - 4.3;    // gniazdo lba wkretu M2x12
spk_xy    = [16, pcb_l + c + 3 + spk_d / 2];
top_boss  = [[2.6, iy1 - 2.8], [29.4, iy1 - 2.8]];

module rrect(x0, y0, x1, y1, r) {
    hull() for (x = [x0 + r, x1 - r], y = [y0 + r, y1 - r]) translate([x, y]) circle(r);
}
module outer2d(inset = 0) { rrect(ox0 + inset, oy0 + inset, ox1 - inset, oy1 - inset, r_out - inset); }
module inner2d(inset = 0) { rrect(ix0 + inset, iy0 + inset, ix1 - inset, iy1 - inset, max(0.5, r_in - inset)); }

// walec wzdluz osi Y (do otworow w dolnej sciance)
module ycyl(d, y0, y1) { translate([0, y0, 0]) rotate([-90, 0, 0]) cylinder(d = d, h = y1 - y0); }

module tub() {
    difference() {
        union() {
            difference() {
                hull() {                                   // bryla z fazka na przedniej krawedzi
                    linear_extrude(eps) outer2d(1.2);
                    translate([0, 0, 1.2]) linear_extrude(zc - 1.2) outer2d();
                }
                translate([0, 0, front]) linear_extrude(zc) inner2d();
            }
            // slupki pod plytke
            for (h = holes) translate([h[0], h[1], front - eps]) cylinder(d = 4.6, h = gap_f + eps);
            // podpory krawedzi plytki przy przycisku
            for (x = [ix0, ix1 - 1.6]) translate([x, btn_xy[1] - 2.5, front - eps]) cube([1.6, 5, gap_f + eps]);
            // gniazdo modulu mikrofonu
            translate([mic_xy[0], mic_xy[1], front - eps]) difference() {
                if (mic_shape == "round") cylinder(d = mic_d + 2.4, h = 1.8);
                else translate([-mic_d / 2 - 1.2, -mic_d / 2 - 1.2, 0]) cube([mic_d + 2.4, mic_d + 2.4, 1.8]);
                if (mic_shape == "round") translate([0, 0, -1]) cylinder(d = mic_d, h = 4);
                else translate([-mic_d / 2, -mic_d / 2, -1]) cube([mic_d, mic_d, 4]);
                translate([-4.5, -mic_d, -1]) cube([9, mic_d, 4]);       // wyjscie przewodow
            }
            if (speaker) {
                translate([spk_xy[0], spk_xy[1], front - eps]) difference() {
                    cylinder(d = spk_d + 0.4 + 2.4, h = 3);
                    translate([0, 0, -1]) cylinder(d = spk_d + 0.4, h = 5);
                    translate([-5, -spk_d, -1]) cube([10, spk_d, 5]);
                }
                for (b = top_boss) translate([b[0], b[1], front - eps]) cylinder(d = 5, h = 15 - front);
            }
        }
        // --- otwory ---
        for (h = holes) translate([h[0], h[1], front + 1.5]) cylinder(d = screw_pilot, h = gap_f);
        if (speaker) for (b = top_boss) translate([b[0], b[1], 4]) cylinder(d = screw_pilot, h = 12);
        translate([btn_xy[0], btn_xy[1], -1]) cylinder(d = btn_d, h = front + 2);
        translate([led_xy[0], led_xy[1], -1]) cylinder(d = led_d, h = front + 2);
        // port mikrofonu: maly otwor + komora od srodka
        translate([mic_xy[0], mic_xy[1], -1]) cylinder(d = 2.2, h = front + 2);
        translate([mic_xy[0], mic_xy[1], front - 0.8]) cylinder(d = 7, h = 2);
        // USB-C: otwor na gniazdo + kieszen na obudowe wtyczki
        hull() for (dx = [-2.9, 2.9]) translate([usb_x + dx, 0, z_usb]) ycyl(3.9, oy0 - 1, iy0 + 1);
        hull() for (dx = [-3.0, 3.0]) translate([usb_x + dx, 0, z_usb]) ycyl(7.0, oy0 - 1, oy0 + 2.85);
        // styki ladowania (sruby M3 z lbem kulistym) i magnes
        for (s = [-1, 1]) translate([usb_x + s * contact_dx, 0, z_contact]) {
            ycyl(3.3, oy0 - 1, iy0 + 1);
            ycyl(6.4, oy0 - 1, oy0 + 1.8);
        }
        translate([usb_x, 0, z_magnet]) ycyl(magnet_d, iy0 - magnet_h, iy0 + 1);
        // maskownica glosnika
        if (speaker) for (i = [-5:5], j = [-5:5]) {
            p = [i * 3.2 + (j % 2 == 0 ? 0 : 1.6), j * 2.77];
            if (norm(p) < spk_d / 2 - 2.5) translate([spk_xy[0] + p[0], spk_xy[1] + p[1], -1]) cylinder(d = 2, h = front + 2, $fn = 16);
        }
    }
}

module lid() {
    difference() {
        union() {
            hull() {
                translate([0, 0, zc]) linear_extrude(lid_t - 1.0) outer2d();
                translate([0, 0, zc + lid_t - eps]) linear_extrude(eps) outer2d(1.0);
            }
            // wpust centrujacy (bez dolnej krawedzi - tam sa nakretki stykow)
            translate([0, 0, zc - 2]) linear_extrude(2 + eps) difference() {
                inner2d(0.25); inner2d(1.45);
                translate([3, iy0 - 1]) square([pcb_w - 6, 4]);
            }
            // tuleje dociskajace plytke
            intersection() {
                for (h = holes) translate([h[0], h[1], zb + 0.1]) cylinder(d = 5.6, h = zc - zb);
                translate([0, 0, zb]) linear_extrude(zc) difference() {
                    inner2d(0.25);
                    translate([5.1, iy0 - 1]) square([pcb_w - 10.2, iy1 - iy0 + 2]);
                }
            }
            if (speaker) for (b = top_boss) translate([b[0], b[1], 15.1]) cylinder(d = 5.6, h = zc - 15.1 + eps);
        }
        for (h = concat(holes, speaker ? top_boss : [])) translate([h[0], h[1], 0]) {
            cylinder(d = screw_clear, h = zc + lid_t + 1);
            translate([0, 0, seat_z]) cylinder(d = screw_head, h = 10);
        }
    }
}

module button() {
    // drukowac klawiszem (plaska strona) do stolu
    nub = (zp - sw_h) - front - 0.05 - 1.3 - 0.15;
    translate([btn_xy[0], btn_xy[1], 0]) {
        translate([0, 0, -0.8]) cylinder(d = btn_d - 0.4, h = front + 0.8 + 0.05 + eps);
        translate([0, 0, front + 0.05]) cylinder(d = btn_d + 2, h = 1.3);
        translate([0, 0, front + 1.35 - eps]) cylinder(d = 4, h = nub);
    }
}

// ---- stacja dokujaca: os pionowa = Y urzadzenia; tu Z w gore ----
dev_w = ox1 - ox0; dev_t = zc + lid_t;
floor_t = pogo_body - pogo_stick;
chamber = 8;
dock_w = 58; dock_d = 46;
module dock() {
    // lokalnie: X = X urzadzenia - usb_x ; Y = Z urzadzenia - dev_t/2 ; Z w gore od blatu
    zf = chamber + floor_t;                       // gorna powierzchnia podlogi
    yc = z_contact - dev_t / 2;                   // linia stykow
    difference() {
        hull() {
            linear_extrude(eps) rrect(-dock_w / 2, -dock_d / 2, dock_w / 2, dock_d / 2, 8);
            translate([0, 0, zf + cup_depth - eps]) linear_extrude(eps)
                rrect(-dev_w / 2 - 3.4, -dev_t / 2 - 3.4, dev_w / 2 + 3.4, dev_t / 2 + 3.4, 5);
        }
        // kieszen na pilota
        translate([0, 0, zf]) linear_extrude(cup_depth + 1) rrect(-dev_w / 2 - 0.4, -dev_t / 2 - 0.4, dev_w / 2 + 0.4, dev_t / 2 + 0.4, 1.5);
        // wyciecie z przodu (strona przycisku) - orientacja i chwyt
        translate([-10, -dock_d, zf + 6]) cube([20, dock_d, cup_depth]);
        // piny pogo
        for (s = [-1, 1]) translate([s * (contact_dx + pogo_off), yc, chamber - 1]) cylinder(d = pogo_hole, h = floor_t + 2);
        // magnes od spodu podlogi (zostaje 0,8 mm scianki)
        translate([0, z_magnet - dev_t / 2, chamber - 1]) cylinder(d = magnet_d, h = floor_t - 0.8 + 1);
        // komora plytki + kanal przewodu do tylu
        translate([-dock_pcb[0] / 2 - 0.5, yc - 7.5, -1]) cube([dock_pcb[0] + 1, dock_pcb[1] + 1, chamber + 1]);
        translate([-2.4, yc, -1]) cube([4.8, dock_d, 5.5]);
        // otwory pod wkrety M2 mocujace plytke stacji
        for (s = [-1, 1]) translate([s * 15.5, yc + 1.5, chamber - 1]) cylinder(d = screw_pilot, h = 5);
    }
}

module pcb_dummy() {
    color("green") translate([0, 0, zp]) linear_extrude(pcb_t) rrect(0, 0, pcb_w, pcb_l, 2);
    color("silver") translate([7.1, -1.55, zp - 4.4]) cube([17.8, 22.55, 4.4]);
}

if (part == "tub") tub();
else if (part == "lid") translate([0, 0, zc + lid_t]) rotate([180, 0, 0]) lid();
else if (part == "button") translate([0, 0, front + 1.35]) rotate([180, 0, 0]) button();
else if (part == "dock") dock();
else {
    tub(); pcb_dummy();
    color("orange") button();
    translate([60, 0, 0]) lid();
    translate([-50, 30, 0]) dock();
}
