# Zakupy: co, gdzie i za ile

Lista na **3 piloty w wersji bazowej + 1 stację dokującą**. Dla innej liczby
przemnóż kolumnę „na pilota". Stan z 10.11.2026, ceny z wyszukiwarki, nie z
koszyków: przed zapłatą sprawdź każdą na stronie sklepu. „netto" znaczy, że
sklep podał cenę bez VAT (do pomnożenia przez 1,23).

Czego nie udało się potwierdzić, jest zaznaczone. Nie zgaduj tam ceny, tylko
sprawdź ją w sklepie.

## Koszyk 1: JLCPCB (płytki)

Wgraj `pcb/gerber/voice-mic-gerber.zip` i `pcb/gerber/voice-mic-dock-gerber.zip`
jako dwa zamówienia w tym samym czasie.

| Parametr | Wartość |
|---|---|
| Warstwy / grubość | 2 / 1,6 mm |
| Wykończenie | HASL |
| Ilość | 5 sztuk (minimum), starczy na 5 pilotów i 5 stacji |
| Montaż | wyłączony (płytki gołe) |

Cena gołych płytek to kilka dolarów, wysyłka i VAT wychodzą w koszyku. Przed
zamówieniem przeczytaj [FAQ JLCPCB o reformie VAT w UE](https://jlcpcb.com/help/article/eu-customs-reform-faq),
bo od lipca 2026 zasady dla przesyłek do UE się zmieniły.

## Koszyk 2: Botland

| Część | Szt. | Cena | Link |
|---|---|---|---|
| Seeed XIAO ESP32-S3 (zwykły, bez „Sense" i „Plus") | 3 | **nie znalazłem ceny** (szacunek 35–45 zł) | [Botland](https://botland.store/moduly-wifi-i-bt-esp32/22878-seeed-xiao-esp32-s3-wifibluetooth-seeedstudio-113991114.html) |
| Tact switch 6×6 mm, 5 mm, THT, 5 szt. | 1 opak. | poniżej 5 zł | [Botland](https://botland.store/tact-switch/3495-tact-switch-6x6mm-5mm-tht-2pin-5pcs-5904422307639.html) |
| Dioda RGB 5 mm, wspólna katoda, 5 szt. | 1 opak. | ok. 1–1,50 | [Botland](https://botland.store/rgb-led/547-led-rgb-5mm-common-cathode-5pcs-5903351243971.html) |

Przy diodzie RGB strona napisała, że oferta jest tylko dla klientów B2B. Jeśli
nie możesz jej kupić jako osoba prywatna, weź to samo w Kamami lub na
AliExpress; liczy się wspólna katoda, bo tak jest zaprojektowana płytka.
Wybierz wersję z matową soczewką, jeśli jest, bo równiej świeci przez obudowę.

## Koszyk 3: Gotronik

| Część | Szt. | Cena | Link |
|---|---|---|---|
| Moduł mikrofonu INMP441 (I2S) | 3 | 12,00 zł brutto (na 2.09.2026) | [Gotronik](https://www.gotronik.pl/cyfrowy-mikrofon-wielokierunkowy-mems-inmp441-i2s-24-bit-kartapdf-14711.html) |

To najtańsza oferta z polskich sklepów, które znalazłem; [Kamami](https://kamami.pl/en/modules-with-microphones-and-sound-detectors/587534-mems-inmp441-microphone-module-5906623475483.html)
ma ten sam moduł za 15,85 zł netto. Sprawdź, czy kupowany moduł jest okrągły
(ok. 14 mm) czy kwadratowy; w obudowie ustawia się to parametrem `mic_shape`.

## Koszyk 4: Kamami (bateria)

| Część | Szt. | Cena | Link |
|---|---|---|---|
| Akyga AKY0823, LP542439, 500 mAh, z zabezpieczeniem, złącze JST 150 mm | 3 | 14,26 zł netto (ok. 17,50 brutto) | [Kamami](https://kamami.pl/en/rechargeable-batteries/1202736-lithium-polymer-battery-akyga-aky0823-lp542439-li-po-3-7v-500mah-pcm-connector-150mm-5906574243384.html) |

To ogniwo ma wymiar 542439 (ok. 5,4 × 24 × 39 mm), a nie 502535, na który
liczyłem w README. Mieści się w obudowie (miejsce ok. 30 × 48 × 6 mm), ale ma
tylko ok. 0,6 mm zapasu na grubość, więc przyklej je cienką taśmą dwustronną.
Wtyk JST musisz odciąć i przylutować przewody do pól `BAT+` i `BAT-`.
Biegunowość sprawdź miernikiem, kolory przewodów w tanich ogniwach bywają
zamienione.

## Koszyk 5: AliExpress lub sklepy specjalistyczne

| Część | Szt. | Uwagi |
|---|---|---|
| Piny pogo ø2 mm, ok. 7 mm długości, do lutowania THT | 2 na stację | **Nie znalazłem w polskich sklepach** pinu o tych wymiarach. Szukaj „pogo pin 2mm spring loaded solder" i zmierz kupiony pin. Jeśli długość lub średnica się różnią, popraw `pogo_body` i `pogo_hole` w `case/voice_mic.scad` i wyeksportuj stację ponownie. |
| Magnes neodymowy walcowy 8 × 3 mm, N35 | 4 (3 piloty + stacja) | Polskie sklepy, które znalazłem, miały inne wymiary lub nie podawały grubości. Pasuje [Supermagnete S-08-03-N](https://www.supermagnete.nl/eng/disc-magnets-neodymium/disc-magnet-8mm-3mm_S-08-03-N) (ceny w euro). Magnesów 8×2 i 3×8 nie bierz. |
| Śruby M3 × 8, łeb kulisty, imbus (ISO 7380), + nakrętki M3 | 6 + 6 | Najłatwiej kupić zestaw M2 i M3 w jednym pudełku. Polskiej ceny pojedynczej śruby nie znalazłem. |
| Wkręty M2 × 12 | 12 | j.w. |
| Wkręty M2 × 5 | 2 | j.w. |

## Koszyk 6: drobnica elektroniczna (TME, Botland, Kamami lub AliExpress)

Nie szukałem cen, to groszowe rzeczy. Kupuj w jednym sklepie, żeby nie płacić
dwa razy za wysyłkę.

| Część | Szt. (3 piloty + zapas) |
|---|---|
| Dioda Schottky'ego SS14 (SMA) | 5 |
| Rezystor 1206: 470 Ω | 5 |
| Rezystor 1206: 220 Ω | 10 |
| Rezystor 1206: 100 kΩ | 5 |
| Rezystor 1206: 470 kΩ | 10 |
| Kondensator 1206: 100 nF | 5 |
| Przewód montażowy cienki (28–30 AWG), kilka kolorów | ok. 2 m |
| Taśma dwustronna cienka / pianka | 1 rolka |

Najtaniej jest wziąć zestaw rezystorów i kondensatorów 1206 (kilkaset sztuk
za kilkanaście złotych) zamiast pojedynczych wartości.

## Stacja dokująca: dodatkowo

Poza pogo i magnesem wyżej potrzebujesz starego kabla USB z wtykiem USB-A,
który obetniesz, albo gniazda USB-C „breakout" z rezystorami 5,1 kΩ. Zasilacz
5 V / 1 A wystarczy na kilka stacji.

## Wersja z głośnikiem: dodatkowo na 1 pilota

| Część | Cena | Uwagi |
|---|---|---|
| Moduł MAX98357A | ok. 10,30 zł brutto ([DFRobot DFR0954 w Gotroniku](https://www.gotronik.pl/modul-wzmacniacza-audio-i2s-3w-klasa-d-dacmax98357-kartapdf-13866.html)) lub ok. 8 € netto ([SparkFun w Botlandzie](https://botland.store/mp3-wav-ogg/13062-max98357a-decoder-stereo-dac-i2s-sparkfun-dev-14809.html)) | **Sprawdź kolejność pinów.** Płytka ma opisy w kolejności jak w module Adafruit (VIN, GND, SD, GAIN, DIN, BCLK, LRC). Moduł DFRobot lub SparkFun może mieć inną, a wtedy trzeba przylutować przewodami albo zmienić płytkę. |
| Głośnik 28 mm, 8 Ω, ok. 1 W | **nie znalazłem pewnej ceny**; kandydat: [TME Loudity LD-SP-2808](https://www.tme.com/us/en-us/details/ld-sp-2808/speakers/loudity/) | Sprawdź średnicę i moc na karcie produktu. RS ma głośnik 28 mm / 2 W za ok. 40 zł, to za drogo. |
| Rezystor 10 kΩ 1206, kondensator 10 µF 1206 | grosze | |

## Podsumowanie znalezionych cen (3 piloty, wersja bazowa)

| | zł |
|---|---|
| Mikrofony INMP441 ×3 | 36,00 |
| Baterie ×3 | ok. 52,50 |
| Moduły XIAO ×3 | **ok. 105–135 (szacunek, nie potwierdzone)** |
| Reszta (płytki, magnesy, śruby, pogo, drobnica, diody) | ok. 60–90 (szacunek) |
| **Razem** | **ok. 255–315** |

Daje to ok. 85–105 zł na pilota razem ze stacją, czyli trochę więcej niż
w README (62–95 zł), głównie dlatego, że tu kupujesz w kilku polskich sklepach
i dochodzą trzy przesyłki.

## Jak zmniejszyć koszty

- Kupuj w jak najmniejszej liczbie sklepów, bo każda przesyłka to kilkanaście
  złotych. Botland sprzedaje większość elektroniki z tego koszyka, TME i
  Kamami mają też drobnicę.
- Najtaniej wychodzi AliExpress dla XIAO, mikrofonu, baterii i wszystkiego
  mechanicznego, ale czekasz 2–4 tygodnie, a części (zwłaszcza moduł
  mikrofonu i pogo) bywają inne niż na zdjęciu.
