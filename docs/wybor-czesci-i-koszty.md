# Wybór części, koszty i czas pracy

Ceny są orientacyjne (listopad 2026) i zaokrąglone. Przed zamówieniem sprawdź
aktualne, zwłaszcza kurs dolara i koszt wysyłki z Chin.

## Co wybrałem i dlaczego

### Łączność: Wi-Fi, nie Bluetooth

Komputer z asystentem jest w tej samej sieci, a Wi-Fi ma zasięg całego
mieszkania bez dodatkowych odbiorników. Bluetooth LE wymagałby komputera w
zasięgu kilku metrów albo bramek w każdym pokoju. Wi-Fi zużywa dużo prądu, ale
tylko przez kilka sekund na polecenie; przez resztę czasu układ śpi.

### Mikrokontroler: Seeed XIAO ESP32-S3

| Kandydat | Cena | Dlaczego tak / nie |
|---|---|---|
| **XIAO ESP32-S3** | 30–45 zł | Ładowarka LiPo i USB-C na pokładzie, 21 × 17,8 mm, 8 MB PSRAM, uśpienie 14 µA. PSRAM pozwala nagrywać od pierwszej chwili, zanim połączy się Wi-Fi. |
| XIAO ESP32-C3 | 22–30 zł | Tańszy o kilka złotych, ale bez PSRAM: w RAM mieści się ok. 4–5 s dźwięku, więc początek dłuższego polecenia przepadałby przy wolnym łączeniu z siecią. Jeden port I2S. |
| XIAO ESP32-C6 | 25–35 zł | Antena na płytce, ale też bez PSRAM. |
| XIAO ESP32-S3 Sense | 55–65 zł | Ma mikrofon na pokładzie, ale kosztuje więcej niż zwykły S3 z osobnym INMP441, a nakładka z kamerą pogrubia urządzenie. |
| ESP32 DevKit / „goły" moduł | 15–25 zł | Brak ładowarki i zły prąd uśpienia płytek DevKit; goły moduł ma sens dopiero na własnym PCB (niżej). |
| nRF52840 (BLE) | 30–40 zł | Świetny czas pracy, ale patrz „Łączność". |

### Mikrofon: INMP441 (I2S)

Cyfrowy mikrofon MEMS, stosunek sygnału do szumu 61 dB, powszechnie używany w
satelitach głosowych na ESP32, kosztuje 7–15 zł jako gotowy moduł. Cyfrowe
wyjście oznacza brak przedwzmacniacza i szumów z przetwornika ESP32. Jakość z
odległości 5–30 cm jest w zupełności wystarczająca do transkrypcji modelem
klasy Whisper. Mikrofon jest zasilany z pinu mikrokontrolera, więc w uśpieniu
nie pobiera nic.

Alternatywy: ICS-43434 (nieco lepszy, 2–3 razy droższy jako moduł), mikrofon
analogowy z MAX9814 (tani, ale szumi i wymaga przetwornika).

### Wzmacniacz i głośnik (wariant): MAX98357A + głośnik 28 mm 8 Ω

MAX98357A to wzmacniacz klasy D z wejściem I2S, bez przetwornika po drodze,
do 3 W, z trybem wyłączenia poniżej 1 µA. Dzieli linie zegarowe z mikrofonem,
więc zajmuje tylko dwa dodatkowe piny. Zasilany wprost z baterii.

### Zasilanie i ładowanie

- **Akumulator LiPo 502535, 500 mAh, z płytką zabezpieczającą.** Mieści się
  za płytką (miejsce: 30 × 48 × 6 mm; przy szerokości powyżej 29 mm grubość
  najwyżej 5 mm). Większy 602535 (600 mAh) też wejdzie.
- **Ładowarka** jest w module XIAO (50 mA, czyli ok. 10–11 h do pełna dla
  500 mAh). Wolno, ale pilot i tak stoi w stacji.
- **Stacja na pinach pogo.** Dwa piny sprężynowe w stacji dotykają łbów dwóch
  śrub M3 w spodzie pilota. Śruby są połączone z pinem 5 V modułu przez diodę
  Schottky'ego, więc na odsłoniętych stykach nigdy nie ma napięcia z baterii,
  a odwrotne włożenie niczego nie uszkadza. Magnes dociąga pilota do pinów.
- **Ładowanie indukcyjne (Qi)** odrzuciłem: cewka z odbiornikiem to 15–25 zł
  na sztukę, kilka milimetrów grubości i sporo ciepła przy tak małej baterii.

### Potwierdzenie: zwykła dioda RGB na trzech pinach

Adresowalna dioda WS2812 pobiera ok. 1 mA także wtedy, gdy nie świeci, co
skróciłoby czas czuwania z miesięcy do ok. dwóch tygodni. Zwykła dioda ze
wspólną katodą w uśpieniu nie pobiera nic.

### Gotowe urządzenia, które rozważyłem

- **M5Stack Atom Echo** (ok. 60 zł): mikrofon, głośnik, przycisk i dioda w
  kostce 24 mm, ale bez baterii.
- **M5StickC Plus2** (ok. 100 zł): ma baterię 200 mAh, mikrofon, przycisk,
  ekran i USB-C. To najszybsza droga, jeśli nie chcesz nic lutować; wystarczy
  inny program. Jest jednak droższy, ma małą baterię i nie ma styków do stacji.

## Koszt jednej sztuki (moduł + mała płytka)

| Pozycja | AliExpress | Polskie sklepy |
|---|---|---|
| XIAO ESP32-S3 | 30 zł | 45 zł |
| INMP441 | 7 zł | 15 zł |
| LiPo 500 mAh | 12 zł | 20 zł |
| płytka (5 szt. z wysyłką ok. 30–40 zł) | 7 zł | 7 zł |
| drobnica, śruby, magnes | 4 zł | 6 zł |
| filament | 2 zł | 2 zł |
| **Razem, wersja bazowa** | **ok. 62 zł** | **ok. 95 zł** |
| MAX98357A + głośnik + drobnica | +14 zł | +24 zł |
| **Razem, wersja z głośnikiem** | **ok. 76 zł** | **ok. 119 zł** |
| Stacja dokująca (jedna na kilka pilotów) | 10 zł | 15 zł |

## Kosztorys: pełne własne PCB, 10 sztuk

Wariant, w którym fabryka (JLCPCB, montaż „Economic") lutuje wszystko na
jednej płytce: moduł ESP32-S3-WROOM-1-N8R2, ładowarka LiPo, stabilizator o
małym prądzie spoczynkowym, gniazdo USB-C, mikrofon MEMS, przycisk, dioda.
Tego wariantu **nie zaprojektowałem**; to wycena, żebyś mógł zdecydować.

| Pozycja | Koszt (USD) |
|---|---|
| Części na płytkę: ESP32-S3-WROOM-1-N8R2 ok. 3,3–5,3; mikrofon I2S MEMS ok. 1; ładowarka, stabilizator, USB-C, zabezpieczenia, dioda, przycisk, elementy bierne ok. 1,5 | ok. 6,5 × 10 = 65 |
| Płytki 2-warstwowe, 10 szt. | 5 |
| Opłata za uruchomienie montażu | 8 |
| Szablon | 1,5 |
| Opłaty za części spoza listy podstawowej (ok. 6 typów × 3) | 18 |
| Lutowanie (opłata za punkty) | 1 |
| Wysyłka | 15–20 |
| **Suma netto** | **ok. 115–120** |
| VAT 23% | ok. 27 |
| **Razem** | **ok. 145 USD, czyli ok. 550–600 zł** |

To daje **ok. 55–60 zł za zmontowaną płytkę**. Po doliczeniu baterii, śrub,
magnesu i filamentu: **ok. 75–80 zł za gotowego pilota**. Wersja z głośnikiem:
dodatkowo ok. 2,5 USD na płytkę (MAX98357A i opłata za kolejny typ części)
plus głośnik, razem ok. 90–95 zł za sztukę.

Wnioski:

- Przy 10 sztukach własne PCB **nie jest tańsze** niż gotowy moduł z
  AliExpress (62 zł) i jest porównywalne z zakupami w Polsce. Opłaty stałe
  (uruchomienie, części spoza listy, wysyłka, razem ok. 45 USD) rozkładają
  się dopiero przy 25–30 sztukach i więcej.
- Zyskujesz mniejsze i schludniejsze urządzenie (ok. 30 × 55 × 15 mm) i brak
  ręcznego lutowania.
- Ryzyko: pierwsza wersja własnej płytki z anteną, ładowarką i USB rzadko
  jest bezbłędna. Realnie trzeba liczyć dwa zamówienia, czyli drugie tyle.
- Stawki JLCPCB (uruchomienie ok. 8 USD, ok. 1,5–3 USD za typ części spoza
  listy podstawowej) zmieniają się; sprawdź wycenę na żywo.

Rozsądna kolejność: zbuduj 2–3 sztuki na gotowym module, poużywaj tydzień,
a własne PCB zamów dopiero, gdy będziesz pewien kształtu i funkcji.

## Czas pracy na jednym ładowaniu

To szacunki z danych katalogowych, nie pomiary.

Założenia: bateria 500 mAh, z czego użyteczne ok. 85%; jedno polecenie to ok.
8 s czuwania (budzenie, łączenie z Wi-Fi, 3–5 s mowy, oczekiwanie na
odpowiedź) przy średnio ok. 100 mA, czyli ok. 0,22 mAh. Uśpienie: ok. 20 µA,
czyli ok. 0,5 mAh na dobę. Odpowiedź głosowa: ok. 5 s przy ok. 250 mA, czyli
dodatkowe ok. 0,35 mAh.

| | Wersja bazowa | Z głośnikiem |
|---|---|---|
| Zużycie na polecenie | ok. 0,22 mAh | ok. 0,57 mAh |
| Poleceń na jednym ładowaniu | ok. 1900 | ok. 750 |
| 10 poleceń dziennie | ok. 5 miesięcy | ok. 2 miesiące |
| 30 poleceń dziennie | ok. 2 miesiące | ok. 3–4 tygodnie |
| 100 poleceń dziennie | ok. 3 tygodnie | ok. 1 tydzień |
| Samo leżenie | ponad rok (ogranicza samorozładowanie baterii) | tak samo |

Czas pracy z głośnikiem zależy głównie od długości odpowiedzi i głośności.
Jeśli pilot wraca do stacji choćby raz na kilka dni, bateria praktycznie
nigdy się nie rozładuje.

## Schemat połączeń

```
                    XIAO ESP32-S3
  bateria+ ──┬────── BAT+           5V ───|<|─── DOCK+ (lewa śruba)
             │                           D2 SS14
            R5 470k                 GND ──────── DOCK- (prawa śruba), bateria-
             ├────── D0 (GPIO1)     3V3 ──┬─ R4 100k ─┐
            R6 470k ║ C1 100n             │           │
             │                            │           ├── D1 (GPIO2) ── SW1 ── GND
            GND                                       
                                    D2 (GPIO3) ────── MIC VDD
                                    D3 (GPIO4) ────── MIC SCK,  AMP BCLK
                                    D4 (GPIO5) ────── MIC WS,   AMP LRC
                                    D5 (GPIO6) ────── MIC SD
                                    D6 (GPIO43) ───── AMP DIN
                                    D7 (GPIO44) ──┬── AMP SD
                                                  R7 10k ── GND
                                    D8 (GPIO7) ─ R1 470R ── LED czerwona
                                    D9 (GPIO8) ─ R2 220R ── LED zielona
                                    D10 (GPIO9) ─ R3 220R ─ LED niebieska
                                                            (wspólna katoda → GND)
  MIC GND, MIC L/R → GND        AMP VIN → bateria+ (C2 10µ do GND)     AMP GND → GND
```

| Pin XIAO | GPIO | Sieć | Funkcja |
|---|---|---|---|
| D0 | 1 | BAT_SENSE | pomiar baterii, dzielnik 1:2 |
| D1 | 2 | BTN | przycisk do masy, wybudzanie z uśpienia |
| D2 | 3 | MIC_PWR | zasilanie mikrofonu (wyłączane w uśpieniu) |
| D3 | 4 | I2S_BCLK | zegar bitowy, wspólny dla mikrofonu i wzmacniacza |
| D4 | 5 | I2S_WS | zegar słowa, wspólny |
| D5 | 6 | MIC_SD | dane z mikrofonu |
| D6 | 43 | AMP_DIN | dane do wzmacniacza |
| D7 | 44 | AMP_SD | włączenie wzmacniacza (R7 trzyma go wyłączonego) |
| D8, D9, D10 | 7, 8, 9 | LED_R, LED_G, LED_B | dioda RGB |
| 5V | | VBUS | wejście ładowania ze stacji przez D2 |
| BAT+, BAT- | | VBAT, GND | pady na spodzie modułu, lutowane przez otwory |

## Źródła

- [Seeed Studio: XIAO ESP32-S3, dane techniczne](https://wiki.seeedstudio.com/xiao_esp32s3_getting_started)
- [CNX Software: XIAO ESP32-S3](https://www.cnx-software.com/2023/03/22/xiao-esp32s3-tiny-esp32-s3-wifi-4-and-ble-5-0-module-for-iot-ai-robotics/)
- [esp32.co.uk: XIAO ESP32-S3, zasilanie bateryjne](https://esp32.co.uk/seeed-xiao-esp32-s3-pinout-battery-power-arduino-setup/)
- [Open Electronics: moduł INMP441](https://oe2.open-electronics.org/?p=46708)
- [JLCPCB: cennik montażu](https://jlcpcb.com/help/article/pcb-assembly-price)
- [JLCPCB: montaż prototypów](https://jlcpcb.com/solutions/pcb-prototype-assembly)
- [JLCPCB: ESP32-S3-WROOM-1-N8R2 (C2913204)](https://jlcpcb.com/partdetail/ESP32-S3-WROOM-1-N8R2/C2913204)
- [Elecena: ceny XIAO ESP32-S3 w Polsce](https://elecena.pl/product/23250087/seeed-xiao-esp32s3)
- [Botland: XIAO ESP32-S3](https://botland.store/moduly-wifi-i-bt-esp32/22878-seeed-xiao-esp32-s3-wifibluetooth-seeedstudio-113991114.html)
