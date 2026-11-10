// Skopiuj ten plik jako config.h i uzupelnij. config.h nie trafia do repozytorium.
#pragma once

#define WIFI_SSID      "nazwa-sieci"
#define WIFI_PASSWORD  "haslo"

// Komputer z asystentem (adres IP lub nazwa) i port serwera odbiorczego
#define SERVER_HOST    "192.168.1.10"
#define SERVER_PORT    8765
#define SERVER_PATH    "/api/voice"
// Wspolny sekret wysylany w naglowku X-Auth-Token (pusty = bez naglowka)
#define AUTH_TOKEN     ""

// Nazwa pilota widoczna po stronie serwera; pusta = "mic-" + koncowka adresu MAC
#define DEVICE_NAME    ""

// 1 = wersja z glosnikiem (MAX98357A): odtwarza odpowiedz WAV z serwera
#define HAS_SPEAKER    0
#define SPEAKER_VOLUME 60        // 0..100

// 1 = dioda RGB ze wspolna katoda (domyslnie), 0 = ze wspolna anoda
#define LED_COMMON_CATHODE 1

#define MAX_RECORD_SECONDS 30    // limit jednego polecenia
#define MIC_GAIN_SHIFT     14    // mniejsza liczba = glosniej (13..16)
#define LOW_BATTERY_MV     3500
