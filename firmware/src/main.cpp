// Pilot glosowy: przytrzymaj przycisk i mow. Po puszczeniu nagranie trafia do
// serwera w sieci Wi-Fi, a dioda potwierdza odbior. Miedzy poleceniami uklad
// spi w trybie deep sleep.
//
// Sprzet: Seeed XIAO ESP32-S3 + INMP441 (+ opcjonalnie MAX98357A), plytka voice-mic r1.
#include <Arduino.h>
#include <limits.h>
#include <WiFi.h>
#include <driver/i2s.h>
#include <driver/rtc_io.h>
#include <esp_sleep.h>

#include "config.h"

#define FW_VERSION "1.0"

// --- wyprowadzenia (XIAO ESP32-S3) ---
static const int PIN_BAT      = 1;   // D0  dzielnik 1:2 napiecia baterii
static const int PIN_BTN      = 2;   // D1  przycisk do masy, wybudzanie
static const int PIN_MIC_PWR  = 3;   // D2  zasilanie mikrofonu
static const int PIN_I2S_BCLK = 4;   // D3
static const int PIN_I2S_WS   = 5;   // D4
static const int PIN_MIC_SD   = 6;   // D5
static const int PIN_AMP_DIN  = 43;  // D6
static const int PIN_AMP_SD   = 44;  // D7  wlaczenie wzmacniacza
static const int PIN_LED_R    = 7;   // D8
static const int PIN_LED_G    = 8;   // D9
static const int PIN_LED_B    = 9;   // D10

static const int SAMPLE_RATE = 16000;
static const uint32_t MIN_PRESS_MS  = 250;    // krotsze nacisniecie = pomylka
static const uint32_t TAIL_MS       = 200;    // dogrywka po puszczeniu przycisku
static const uint32_t WIFI_WAIT_MS  = 10000;
static const uint32_t REPLY_WAIT_MS = 30000;

// dane sieci zapamietane miedzy wybudzeniami - skracaja laczenie do ok. 1 s
RTC_DATA_ATTR static bool    rtcValid = false;
RTC_DATA_ATTR static uint8_t rtcBssid[6];
RTC_DATA_ATTR static int32_t rtcChannel = 0;

static int16_t *recBuf = nullptr;
static size_t recCap = 0;                 // pojemnosc w probkach
static volatile size_t recLen = 0;        // nagrane probki
static volatile bool recRun = false;
static volatile bool recDone = false;
static bool recStarted = false;

// ---------------------------------------------------------------- dioda
enum Color { OFF = 0, RED = 1, GREEN = 2, YELLOW = 3, BLUE = 4, MAGENTA = 5, CYAN = 6, WHITE = 7 };

static void led(Color c) {
  const bool on = LED_COMMON_CATHODE ? HIGH : LOW;
  digitalWrite(PIN_LED_R, (c & 1) ? on : !on);
  digitalWrite(PIN_LED_G, (c & 2) ? on : !on);
  digitalWrite(PIN_LED_B, (c & 4) ? on : !on);
}

static void blink(Color c, int times, int onMs = 120, int offMs = 120) {
  for (int i = 0; i < times; i++) {
    led(c); delay(onMs);
    led(OFF); delay(offMs);
  }
}

// ---------------------------------------------------------------- zasilanie
static int batteryMv() {
  uint32_t sum = 0;
  for (int i = 0; i < 8; i++) sum += analogReadMilliVolts(PIN_BAT);
  return (int)(sum / 8) * 2;
}

static void goToSleep() {
  led(OFF);
  if (recStarted) {                                // najpierw zatrzymaj zadanie nagrywania
    recRun = false;
    while (!recDone) delay(5);
    i2s_driver_uninstall(I2S_NUM_0);
  }
  digitalWrite(PIN_AMP_SD, LOW);
  digitalWrite(PIN_MIC_PWR, LOW);
  WiFi.disconnect(true);
  WiFi.mode(WIFI_OFF);
  // nie zasypiaj z wcisnietym przyciskiem - uklad obudzilby sie od razu
  uint32_t t0 = millis();
  while (digitalRead(PIN_BTN) == LOW && millis() - t0 < 10000) delay(10);
  delay(30);
  esp_sleep_enable_ext0_wakeup((gpio_num_t)PIN_BTN, 0);
  Serial.println("sleep");
  esp_deep_sleep_start();
}

// ---------------------------------------------------------------- nagrywanie
static void micStart() {
  i2s_config_t cfg = {};
  cfg.mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX);
  cfg.sample_rate = SAMPLE_RATE;
  cfg.bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT;
  cfg.channel_format = I2S_CHANNEL_FMT_ONLY_LEFT;
  cfg.communication_format = I2S_COMM_FORMAT_STAND_I2S;
  cfg.intr_alloc_flags = ESP_INTR_FLAG_LEVEL1;
  cfg.dma_buf_count = 8;
  cfg.dma_buf_len = 256;
  i2s_pin_config_t pins = {};
  pins.mck_io_num = I2S_PIN_NO_CHANGE;
  pins.bck_io_num = PIN_I2S_BCLK;
  pins.ws_io_num = PIN_I2S_WS;
  pins.data_out_num = I2S_PIN_NO_CHANGE;
  pins.data_in_num = PIN_MIC_SD;
  i2s_driver_install(I2S_NUM_0, &cfg, 0, nullptr);
  i2s_set_pin(I2S_NUM_0, &pins);
}

static void recordTask(void *) {
  static int32_t raw[256];
  // pierwsze ~60 ms po wlaczeniu mikrofonu to stan nieustalony - pomijamy
  size_t skip = SAMPLE_RATE * 60 / 1000;
  while (recRun) {
    size_t got = 0;
    i2s_read(I2S_NUM_0, raw, sizeof(raw), &got, pdMS_TO_TICKS(100));
    size_t n = got / sizeof(int32_t);
    size_t len = recLen;
    for (size_t i = 0; i < n; i++) {
      if (skip) { skip--; continue; }
      if (len >= recCap) break;
      int32_t v = raw[i] >> MIC_GAIN_SHIFT;
      if (v > 32767) v = 32767;
      if (v < -32768) v = -32768;
      recBuf[len++] = (int16_t)v;
    }
    recLen = len;
  }
  recDone = true;
  vTaskDelete(nullptr);
}

// ---------------------------------------------------------------- siec
static void wifiBegin(bool useCache) {
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  if (useCache && rtcValid) WiFi.begin(WIFI_SSID, WIFI_PASSWORD, rtcChannel, rtcBssid, true);
  else WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
}

static String deviceName() {
  if (strlen(DEVICE_NAME) > 0) return DEVICE_NAME;
  uint8_t mac[6];
  WiFi.macAddress(mac);
  char buf[16];
  snprintf(buf, sizeof(buf), "mic-%02x%02x%02x", mac[3], mac[4], mac[5]);
  return buf;
}

static bool openRequest(WiFiClient &c, int mv) {
  if (!c.connect(SERVER_HOST, SERVER_PORT, 3000)) return false;
  c.setNoDelay(true);
  c.printf("POST %s HTTP/1.1\r\nHost: %s:%d\r\n", SERVER_PATH, SERVER_HOST, SERVER_PORT);
  c.print("Content-Type: application/octet-stream\r\nTransfer-Encoding: chunked\r\nConnection: close\r\n");
  c.printf("X-Audio-Format: pcm_s16le\r\nX-Sample-Rate: %d\r\nX-Channels: 1\r\n", SAMPLE_RATE);
  c.printf("X-Device-Id: %s\r\nX-Battery-Mv: %d\r\nX-Firmware: %s\r\nX-Speaker: %d\r\n",
           deviceName().c_str(), mv, FW_VERSION, HAS_SPEAKER);
  if (strlen(AUTH_TOKEN) > 0) c.printf("X-Auth-Token: %s\r\n", AUTH_TOKEN);
  c.print("\r\n");
  return true;
}

// wysyla probki [sent, upTo) jako kawalki HTTP; zwraca nowa pozycje
static size_t sendChunks(WiFiClient &c, size_t sent, size_t upTo) {
  while (sent < upTo && c.connected()) {
    size_t n = upTo - sent;
    if (n > 2048) n = 2048;
    c.printf("%X\r\n", (unsigned)(n * 2));
    c.write((const uint8_t *)(recBuf + sent), n * 2);
    c.print("\r\n");
    sent += n;
  }
  return sent;
}

struct Reply {
  int status = 0;
  bool audio = false;
  long length = -1;
};

static bool readLine(WiFiClient &c, String &line, uint32_t deadline) {
  line = "";
  while (millis() < deadline) {
    if (c.available()) {
      char ch = c.read();
      if (ch == '\n') return true;
      if (ch != '\r' && line.length() < 200) line += ch;
    } else if (!c.connected()) {
      return false;
    } else {
      delay(2);
    }
  }
  return false;
}

static Reply readReply(WiFiClient &c) {
  Reply r;
  uint32_t deadline = millis() + REPLY_WAIT_MS;
  String line;
  if (!readLine(c, line, deadline)) return r;
  int sp = line.indexOf(' ');
  if (sp > 0) r.status = line.substring(sp + 1, sp + 4).toInt();
  while (readLine(c, line, deadline) && line.length() > 0) {
    line.toLowerCase();
    if (line.startsWith("content-type:") && line.indexOf("audio/") > 0) r.audio = true;
    if (line.startsWith("content-length:")) r.length = line.substring(15).toInt();
  }
  return r;
}

// ---------------------------------------------------------------- glosnik
#if HAS_SPEAKER
static size_t readBytes(WiFiClient &c, uint8_t *dst, size_t n, uint32_t deadline) {
  size_t got = 0;
  while (got < n && millis() < deadline) {
    int a = c.available();
    if (a > 0) got += c.read(dst + got, min((size_t)a, n - got));
    else if (!c.connected()) break;
    else delay(2);
  }
  return got;
}

// odtwarza odpowiedz: WAV, PCM 16 bit, mono, dowolna czestotliwosc
static void playReply(WiFiClient &c, long length) {
  uint32_t deadline = millis() + 60000;
  uint8_t h[12];
  if (readBytes(c, h, 12, deadline) != 12 || memcmp(h, "RIFF", 4) || memcmp(h + 8, "WAVE", 4)) return;
  long left = length > 0 ? length - 12 : LONG_MAX;
  uint32_t rate = 16000, dataLen = 0;
  uint16_t channels = 1;
  while (true) {                                   // szukamy bloku "data"
    if (readBytes(c, h, 8, deadline) != 8) return;
    left -= 8;
    uint32_t sz = h[4] | (h[5] << 8) | (h[6] << 16) | ((uint32_t)h[7] << 24);
    if (!memcmp(h, "data", 4)) { dataLen = sz; break; }
    uint8_t body[64];
    uint32_t todo = sz + (sz & 1);
    bool fmt = !memcmp(h, "fmt ", 4);
    while (todo) {
      size_t n = min((uint32_t)sizeof(body), todo);
      if (readBytes(c, body, n, deadline) != n) return;
      if (fmt) {
        channels = body[2] | (body[3] << 8);
        rate = body[4] | (body[5] << 8) | (body[6] << 16) | ((uint32_t)body[7] << 24);
        fmt = false;
      }
      todo -= n; left -= n;
    }
  }
  if (channels < 1 || channels > 2) return;
  if ((long)dataLen > left) dataLen = left;

  i2s_driver_uninstall(I2S_NUM_0);
  i2s_config_t cfg = {};
  cfg.mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX);
  cfg.sample_rate = rate;
  cfg.bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT;
  cfg.channel_format = I2S_CHANNEL_FMT_RIGHT_LEFT;
  cfg.communication_format = I2S_COMM_FORMAT_STAND_I2S;
  cfg.intr_alloc_flags = ESP_INTR_FLAG_LEVEL1;
  cfg.dma_buf_count = 8;
  cfg.dma_buf_len = 256;
  cfg.tx_desc_auto_clear = true;
  i2s_pin_config_t pins = {};
  pins.mck_io_num = I2S_PIN_NO_CHANGE;
  pins.bck_io_num = PIN_I2S_BCLK;
  pins.ws_io_num = PIN_I2S_WS;
  pins.data_out_num = PIN_AMP_DIN;
  pins.data_in_num = I2S_PIN_NO_CHANGE;
  i2s_driver_install(I2S_NUM_0, &cfg, 0, nullptr);
  i2s_set_pin(I2S_NUM_0, &pins);
  digitalWrite(PIN_AMP_SD, HIGH);

  static uint8_t in[1024];
  static int16_t out[1024];
  const int vol = constrain(SPEAKER_VOLUME, 0, 100) * 256 / 100;
  const size_t frame = 2 * channels;
  while (dataLen >= frame) {
    size_t want = min((uint32_t)sizeof(in), dataLen);
    want -= want % frame;
    size_t got = readBytes(c, in, want, millis() + 3000);
    got -= got % frame;
    if (got == 0) break;
    size_t frames = got / frame;
    for (size_t i = 0; i < frames; i++) {
      int16_t s = (int16_t)(in[i * frame] | (in[i * frame + 1] << 8));
      s = (int16_t)(((int32_t)s * vol) >> 8);
      out[2 * i] = s;
      out[2 * i + 1] = s;
    }
    size_t written;
    i2s_write(I2S_NUM_0, out, frames * 4, &written, portMAX_DELAY);
    dataLen -= got;
  }
  memset(out, 0, sizeof(out));                    // wypchniecie koncowki z bufora DMA
  size_t written;
  for (int i = 0; i < 3; i++) i2s_write(I2S_NUM_0, out, sizeof(out), &written, portMAX_DELAY);
  delay(60);
  digitalWrite(PIN_AMP_SD, LOW);
}
#endif

// ---------------------------------------------------------------- przebieg
static void fail(const char *why) {
  Serial.printf("blad: %s\n", why);
  blink(RED, 3);
  goToSleep();
}

void setup() {
  rtc_gpio_deinit((gpio_num_t)PIN_BTN);            // po wybudzeniu pin nalezy jeszcze do domeny RTC
  pinMode(PIN_BTN, INPUT_PULLUP);
  pinMode(PIN_LED_R, OUTPUT); pinMode(PIN_LED_G, OUTPUT); pinMode(PIN_LED_B, OUTPUT);
  led(OFF);
  pinMode(PIN_AMP_SD, OUTPUT); digitalWrite(PIN_AMP_SD, LOW);
  pinMode(PIN_MIC_PWR, OUTPUT); digitalWrite(PIN_MIC_PWR, HIGH);
  Serial.begin(115200);
#if ARDUINO_USB_CDC_ON_BOOT
  Serial.setTxTimeoutMs(0);                        // bez komputera na USB logi nie moga blokowac
#endif

  const bool byButton = esp_sleep_get_wakeup_cause() == ESP_SLEEP_WAKEUP_EXT0;
  const int mv = batteryMv();
  if (!byButton && digitalRead(PIN_BTN) == HIGH) {
    // wlaczenie zasilania lub reset: pokaz stan baterii i idz spac
    delay(300);
    Serial.printf("voice-mic %s, bateria %d mV\n", FW_VERSION, mv);
    blink(mv < LOW_BATTERY_MV ? RED : WHITE, 2, 150, 150);
    goToSleep();
  }

  // 1. nagrywanie rusza od razu, Wi-Fi laczy sie w tle
  recCap = (size_t)MAX_RECORD_SECONDS * SAMPLE_RATE;
  recBuf = (int16_t *)ps_malloc(recCap * 2);
  if (!recBuf) {                                   // bez PSRAM: krotki bufor w zwyklej pamieci
    recCap = 4 * SAMPLE_RATE;
    recBuf = (int16_t *)malloc(recCap * 2);
  }
  if (!recBuf) fail("pamiec");
  micStart();
  recRun = true;
  recStarted = true;
  xTaskCreatePinnedToCore(recordTask, "rec", 4096, nullptr, 5, nullptr, 1);
  led(BLUE);                                       // niebieski = mow
  const uint32_t tStart = millis();
  wifiBegin(true);

  WiFiClient client;
  bool opened = false, retried = false;
  size_t sent = 0;
  uint32_t tRelease = 0;

  // 2. dopoki przycisk jest wcisniety (plus krotka dogrywka) - nagrywaj i wysylaj na biezaco
  while (true) {
    const uint32_t now = millis();
    if (!tRelease && (digitalRead(PIN_BTN) == HIGH || recLen >= recCap)) {
      tRelease = now;
      if (now - tStart < MIN_PRESS_MS) goToSleep();
    }
    if (tRelease && now - tRelease >= TAIL_MS) break;
    if (WiFi.status() == WL_CONNECTED) {
      if (!opened) opened = openRequest(client, mv);
      if (opened) sent = sendChunks(client, sent, recLen);
    } else if (!retried && now - tStart > 4000) {  // zapamietany kanal/BSSID nieaktualny
      retried = true; rtcValid = false;
      WiFi.disconnect(); wifiBegin(false);
    }
    delay(20);
  }
  recRun = false;
  while (!recDone) delay(5);
  // mikrofon zostaje zasilony do konca: dzieli linie zegarowe I2S ze wzmacniaczem
  led(YELLOW);                                     // zolty = wysylanie / czekam na odpowiedz
  Serial.printf("nagranie %u ms\n", (unsigned)(recLen * 1000 / SAMPLE_RATE));

  // 3. dokoncz wysylke
  const uint32_t tWifi = millis();
  while (WiFi.status() != WL_CONNECTED) {
    if (millis() - tWifi > WIFI_WAIT_MS) fail("wifi");
    if (!retried && millis() - tStart > 4000) {
      retried = true; rtcValid = false;
      WiFi.disconnect(); wifiBegin(false);
    }
    delay(20);
  }
  memcpy(rtcBssid, WiFi.BSSID(), 6);
  rtcChannel = WiFi.channel();
  rtcValid = true;
  if (!opened) opened = openRequest(client, mv);
  if (!opened) fail("serwer nie odpowiada");
  sent = sendChunks(client, sent, recLen);
  if (sent < recLen) fail("zerwane polaczenie");
  client.print("0\r\n\r\n");

  // 4. odpowiedz
  Reply r = readReply(client);
  Serial.printf("HTTP %d audio=%d len=%ld\n", r.status, r.audio, r.length);
  if (r.status < 200 || r.status >= 300) fail("odpowiedz serwera");
  led(GREEN);                                      // zielony = polecenie odebrane
#if HAS_SPEAKER
  if (r.audio) playReply(client, r.length);
  else delay(700);
#else
  delay(700);
#endif
  client.stop();
  led(OFF);
  if (mv < LOW_BATTERY_MV) { delay(200); blink(RED, 2, 400, 200); }   // czas na ladowanie
  goToSleep();
}

void loop() {
  goToSleep();                                     // setup() zawsze konczy sie snem; to tylko zabezpieczenie
}
