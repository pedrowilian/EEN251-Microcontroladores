import math
import time
import gc
import array
from machine import ADC, Pin, I2C

# ===================================================================
# CONSTANTES
# ===================================================================
SAMPLE_RATE = 4000
N = 1024
ALPHA = 0.386                    # IIR fc=400Hz fs=4000Hz
CYCLE_DELAY_MS = 80
SAMPLE_INTERVAL_US = 250         # 1_000_000 // 4000
BIN_MIN = 18                     # int(70 * 1024 / 4000)
BIN_MAX = 89                     # int(350 * 1024 / 4000)
FREQ_RES = 3.90625               # 4000 / 1024
TOLERANCE_CENTS = 10
LOG2 = 0.6931471805599453        # math.log(2) pre-calculado
ONE_MINUS_ALPHA = 0.614          # 1.0 - 0.386

# Afinacao padrao — tupla de tuplas (imutavel, sem alocacao)
TUNING = (
    ("E2", 82.41),
    ("A2", 110.00),
    ("D3", 146.83),
    ("G3", 196.00),
    ("B3", 246.94),
    ("E4", 329.63),
)
CORDAS = ("6a", "5a", "4a", "3a", "2a", "1a")

# ===================================================================
# DISPLAY OLED SSD1306 (128x64, I2C)
# ===================================================================
# Conexao:
#   SDA -> GP4 (pino fisico 6)
#   SCL -> GP5 (pino fisico 7)
#   VCC -> 3V3 (pino fisico 36)
#   GND -> GND (pino fisico 38)
#
# Se o display nao estiver conectado, o afinador funciona
# normalmente apenas pelo terminal serial (print).
# ===================================================================

OLED_WIDTH = 128
OLED_HEIGHT = 64
OLED_SDA = 4    # GP4
OLED_SCL = 5    # GP5
OLED_ADDR = 0x3C
OLED_I2C_ID = 0

# Barra de afinacao: posicao central e limites
BAR_Y = 40
BAR_H = 10
BAR_CENTER_X = 64
BAR_WIDTH = 100   # largura total da barra (50 pra cada lado)


def init_display():
    """Tenta inicializar o display OLED. Retorna (oled, True) ou (None, False)."""
    try:
        i2c = I2C(OLED_I2C_ID, sda=Pin(OLED_SDA), scl=Pin(OLED_SCL),
                   freq=400_000)
        devices = i2c.scan()
        if OLED_ADDR not in devices:
            print("[OLED] Display nao encontrado no endereco 0x{:02X}".format(
                OLED_ADDR))
            print("[OLED] Dispositivos I2C encontrados: {}".format(
                ["0x{:02X}".format(d) for d in devices]))
            return None, False

        from ssd1306 import SSD1306_I2C
        oled = SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, i2c, addr=OLED_ADDR)
        oled.fill(0)
        oled.text("AFINADOR", 28, 8, 1)
        oled.text("VIOLAO", 36, 24, 1)
        oled.text("Iniciando...", 16, 48, 1)
        oled.show()
        print("[OLED] Display inicializado com sucesso!")
        return oled, True
    except Exception as e:
        print("[OLED] Falha ao inicializar: {}".format(e))
        print("[OLED] Continuando sem display.")
        return None, False


def oled_show_idle(oled):
    """Tela de espera — aguardando sinal."""
    oled.fill(0)
    oled.text("AFINADOR", 28, 0, 1)
    oled.hline(0, 10, 128, 1)
    oled.text("Toque uma", 24, 24, 1)
    oled.text("corda...", 32, 36, 1)
    oled.show()


def oled_show_calibrating(oled):
    """Tela de calibracao."""
    oled.fill(0)
    oled.text("CALIBRANDO", 20, 16, 1)
    oled.text("ruido...", 32, 32, 1)
    oled.text("Silencio!", 28, 48, 1)
    oled.show()


def oled_show_tuning(oled, corda, note, freq, ref, cents, status):
    """Tela principal de afinacao com barra visual."""
    oled.fill(0)

    # Linha 1: nota e corda (fonte grande simulada com 2x)
    oled.text(note, 0, 0, 1)
    oled.text("Corda " + corda, 48, 0, 1)

    # Linha 2: frequencia detectada vs referencia
    oled.text("{:.1f}Hz".format(freq), 0, 14, 1)
    oled.text("Ref:{:.1f}".format(ref), 64, 14, 1)

    # Linha 3: status
    if status == "AFINADO":
        oled.text("* AFINADO *", 16, 26, 1)
    elif status == "ALTO":
        oled.text("ALTO  +{:.0f}c".format(abs(cents)), 16, 26, 1)
    else:
        oled.text("BAIXO  -{:.0f}c".format(abs(cents)), 16, 26, 1)

    # Barra de afinacao visual
    # Fundo da barra
    half_w = BAR_WIDTH // 2
    bar_x0 = BAR_CENTER_X - half_w
    bar_x1 = BAR_CENTER_X + half_w
    oled.rect(bar_x0, BAR_Y, BAR_WIDTH, BAR_H, 1)

    # Marca central (referencia)
    oled.vline(BAR_CENTER_X, BAR_Y, BAR_H, 1)

    # Indicador de posicao: cents mapeado pra pixels
    # ±50 cents = ±half_w pixels
    max_cents = 50.0
    clamped = max(-max_cents, min(max_cents, cents))
    indicator_x = int(BAR_CENTER_X + (clamped / max_cents) * half_w)

    # Desenha indicador (retangulo preenchido 5px de largura)
    ind_w = 5
    ix = max(bar_x0, min(bar_x1 - ind_w, indicator_x - ind_w // 2))
    oled.fill_rect(ix, BAR_Y + 1, ind_w, BAR_H - 2, 1)

    # Labels da barra
    oled.text("-", bar_x0 - 8, BAR_Y + 1, 1)
    oled.text("+", bar_x1 + 2, BAR_Y + 1, 1)

    # Linha 5: desvio em cents
    sign = "+" if cents >= 0 else ""
    oled.text("{}{:.1f} cents".format(sign, cents), 20, 55, 1)

    oled.show()


# ===================================================================
# FFT ENGINE
# ===================================================================

def precompute_twiddles(n):
    half = n >> 1
    tw_re = [0.0] * half
    tw_im = [0.0] * half
    for k in range(half):
        a = 6.283185307179586 * k / n
        tw_re[k] = math.cos(a)
        tw_im[k] = math.sin(a)
    return tw_re, tw_im


def precompute_bit_reverse_table(n):
    bits = 0
    t = n
    while t > 1:
        bits += 1
        t >>= 1
    tbl = [0] * n
    for i in range(n):
        j = 0
        for b in range(bits):
            if i & (1 << b):
                j |= 1 << (bits - 1 - b)
        tbl[i] = j
    return tbl


def bit_reverse(re, im, tbl, n):
    for i in range(n):
        j = tbl[i]
        if i < j:
            re[i], re[j] = re[j], re[i]
            im[i], im[j] = im[j], im[i]


def fft(re, im, tw_re, tw_im, br, n):
    bit_reverse(re, im, br, n)
    size = 2
    while size <= n:
        hs = size >> 1
        step = n // size
        for i in range(0, n, size):
            for k in range(hs):
                ti = k * step
                wr = tw_re[ti]
                wi = tw_im[ti]
                j = i + k
                j2 = j + hs
                tr = re[j2] * wr - im[j2] * wi
                ti2 = re[j2] * wi + im[j2] * wr
                re[j2] = re[j] - tr
                im[j2] = im[j] - ti2
                re[j] = re[j] + tr
                im[j] = im[j] + ti2
        size <<= 1


def compute_magnitudes(re, im, mag, n):
    half = n >> 1
    _sqrt = math.sqrt
    for k in range(half):
        mag[k] = _sqrt(re[k] * re[k] + im[k] * im[k])


# ===================================================================
# DETECCAO DE PICO
# ===================================================================

def find_peak_frequency(mag, bmin, bmax):
    pk = bmin
    pm = mag[bmin]
    for k in range(bmin + 1, bmax + 1):
        if mag[k] > pm:
            pm = mag[k]
            pk = k
    if pm == 0.0:
        return 0.0
    p = 0.0
    if pk > bmin and pk < bmax:
        a = mag[pk - 1]
        b = mag[pk]
        c = mag[pk + 1]
        d = a - 2.0 * b + c
        if d < -1e-12 or d > 1e-12:
            p = 0.5 * (a - c) / d
    return (pk + p) * FREQ_RES


# ===================================================================
# CAPTURA
# ===================================================================

def capture_samples(adc, samples, n):
    _sleep = time.sleep_us
    _iv = SAMPLE_INTERVAL_US
    for i in range(n):
        samples[i] = adc.read_u16()
        _sleep(_iv)


def check_signal(samples, n, noise_floor):
    """Verifica se ha sinal acima do piso de ruido.

    Retorna amplitude pico-a-pico. Sinal valido se pp > noise_floor * 3.
    """
    mn = 65535
    mx = 0
    for i in range(n):
        v = samples[i]
        if v < mn:
            mn = v
        if v > mx:
            mx = v
    return mx - mn


# ===================================================================
# PROCESSAMENTO DE SINAL
# ===================================================================

def remove_dc_offset(samples, signal, n):
    total = 0
    for i in range(n):
        total += samples[i]
    mean = total / n
    for i in range(n):
        signal[i] = samples[i] - mean


def low_pass_filter(signal, filtered, n):
    _a = ALPHA
    _oma = ONE_MINUS_ALPHA
    filtered[0] = _a * signal[0]
    for i in range(1, n):
        filtered[i] = _a * signal[i] + _oma * filtered[i - 1]


def apply_hanning(filtered, hanning, n):
    for i in range(n):
        filtered[i] *= hanning[i]


# ===================================================================
# IDENTIFICACAO DE NOTA
# ===================================================================

def identify_note(freq):
    bi = 0
    bd = abs(freq - TUNING[0][1])
    for i in range(1, 6):
        d = abs(freq - TUNING[i][1])
        if d < bd:
            bd = d
            bi = i
    return bi


def cents_deviation(freq, ref):
    """Desvio em cents sem math.log — usa aproximacao rapida.

    cents = 1200 * log2(freq/ref)
    log2(x) = log(x) / log(2)

    Para evitar alocacao, usa constante LOG2 pre-calculada.
    """
    if ref <= 0.0 or freq <= 0.0:
        return 0.0
    return 1200.0 * math.log(freq / ref) / LOG2


# ===================================================================
# CALIBRACAO DE RUIDO
# ===================================================================

def calibrate_noise(adc, samples, n):
    """Le amostras em silencio e retorna o piso de ruido (pico-a-pico).

    Faz 3 leituras e pega o maximo como referencia.
    """
    worst = 0
    _sleep = time.sleep_us
    _iv = SAMPLE_INTERVAL_US
    for _ in range(3):
        for i in range(n):
            samples[i] = adc.read_u16()
            _sleep(_iv)
        pp = check_signal(samples, n, 0)
        if pp > worst:
            worst = pp
        time.sleep_ms(50)
    # Margem de seguranca: 2x o ruido medido, minimo 300
    result = worst * 2
    if result < 300:
        result = 300
    return result


# ===================================================================
# SETUP
# ===================================================================

def setup():
    adc = ADC(26)
    led = Pin(25, Pin.OUT)
    led.value(1)

    samples = array.array('H', (0 for _ in range(N)))
    signal = [0.0] * N
    filtered = [0.0] * N
    re = [0.0] * N
    im = [0.0] * N
    mag = [0.0] * (N >> 1)

    tw_re, tw_im = precompute_twiddles(N)
    br = precompute_bit_reverse_table(N)

    han = [0.0] * N
    for i in range(N):
        han[i] = 0.5 * (1.0 - math.cos(6.283185307179586 * i / (N - 1)))

    return (adc, led, samples, signal, filtered, re, im, mag,
            tw_re, tw_im, br, han)


# ===================================================================
# FORMATACAO DE SAIDA (terminal serial)
# ===================================================================

def get_tuning_status(cents):
    """Retorna (status, indicador) baseado no desvio em cents."""
    ac = abs(cents)
    if ac <= TOLERANCE_CENTS:
        return "AFINADO", "  ===  "
    elif cents > 0:
        if ac > 30:
            ind = " >>>>> "
        elif ac > 15:
            ind = "  >>>  "
        else:
            ind = "   >>  "
        return "ALTO", ind
    else:
        if ac > 30:
            ind = " <<<<< "
        elif ac > 15:
            ind = "  <<<  "
        else:
            ind = "  <<   "
        return "BAIXO", ind


def format_output(corda, note, freq, ref, ind, st, cents):
    """Formata a string de saida para o terminal serial."""
    sign = "+" if cents >= 0 else ""
    return "Corda {} ({}) | {:.1f} Hz | Ref {:.1f} Hz |{}{} ({}{:.0f}c)".format(
        corda, note, freq, ref, ind, st, sign, cents)


# ===================================================================
# LOOP PRINCIPAL
# ===================================================================

def main_loop():
    print("=" * 55)
    print("  AFINADOR DE VIOLAO - Raspberry Pi Pico 2")
    print("  FFT {} pts | {} Hz | MicroPython".format(N, SAMPLE_RATE))
    print("=" * 55)
    print("Inicializando...")

    (adc, led, samples, signal, filtered, re, im, mag,
     tw_re, tw_im, br, han) = setup()

    # Tenta inicializar display OLED
    oled, has_display = init_display()

    gc.collect()
    print("Memoria livre: {} bytes".format(gc.mem_free()))
    print("Resolucao: {:.2f} Hz | Tolerancia: {} cents".format(
        FREQ_RES, TOLERANCE_CENTS))
    print("")
    print("Calibrando ruido ambiente...")

    if has_display:
        oled_show_calibrating(oled)

    noise_floor = calibrate_noise(adc, samples, N)
    print("Piso de ruido: {} (pico-a-pico)".format(noise_floor))
    print("-" * 55)
    print("Pronto! Toque uma corda.")
    print("")

    if has_display:
        oled_show_idle(oled)

    # Estado para estabilidade de leitura
    last_note = -1
    same_count = 0
    CONFIRM_COUNT = 2  # precisa detectar mesma nota 2x seguidas

    idle = 0
    display_idle_shown = True  # ja mostramos a tela idle acima

    while True:
        try:
            # 1. Captura
            capture_samples(adc, samples, N)
            pp = check_signal(samples, N, noise_floor)

            if pp < noise_floor:
                # Sem sinal — pisca LED devagar
                idle += 1
                if idle % 15 == 0:
                    led.value(0)
                elif idle % 15 == 8:
                    led.value(1)
                last_note = -1
                same_count = 0

                # Mostra tela idle no display (so 1 vez)
                if has_display and not display_idle_shown:
                    oled_show_idle(oled)
                    display_idle_shown = True
            else:
                led.value(1)
                idle = 0
                display_idle_shown = False

                # 2. Pipeline DSP
                remove_dc_offset(samples, signal, N)
                low_pass_filter(signal, filtered, N)
                apply_hanning(filtered, han, N)

                for i in range(N):
                    re[i] = filtered[i]
                    im[i] = 0.0

                fft(re, im, tw_re, tw_im, br, N)
                compute_magnitudes(re, im, mag, N)

                # 3. Pico
                freq = find_peak_frequency(mag, BIN_MIN, BIN_MAX)

                if freq > 0.0:
                    idx = identify_note(freq)

                    # Estabilidade: so mostra se mesma nota 2x seguidas
                    if idx == last_note:
                        same_count += 1
                    else:
                        last_note = idx
                        same_count = 1

                    if same_count >= CONFIRM_COUNT:
                        ref = TUNING[idx][1]
                        note = TUNING[idx][0]
                        corda = CORDAS[idx]
                        c = cents_deviation(freq, ref)

                        # Status e indicador
                        st, ind = get_tuning_status(c)

                        # Saida serial (sempre funciona)
                        print(format_output(corda, note, freq, ref,
                                            ind, st, c))

                        # Saida display OLED
                        if has_display:
                            oled_show_tuning(oled, corda, note, freq,
                                             ref, c, st)

        except Exception as e:
            print("! {}".format(e))

        gc.collect()
        time.sleep_ms(CYCLE_DELAY_MS)


if __name__ == "__main__":
    main_loop()
