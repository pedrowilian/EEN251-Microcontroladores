"""
Afinador de Violão com FFT - MicroPython (RP2040 / Pico)
Microfone: KY-037 no pino ADC GP26
"""

from machine import ADC, Pin
import time
import math

# ─── Hardware ────────────────────────────────────────────────────────────────
adc = ADC(26)
led = Pin(25, Pin.OUT)

# ─── Notas das 6 cordas do violão (afinação padrão) ──────────────────────────
NOTAS = {
    "E2 (6a)": 82.41,
    "A2 (5a)": 110.00,
    "D3 (4a)": 146.83,
    "G3 (3a)": 196.00,
    "B3 (2a)": 246.94,
    "E4 (1a)": 329.63,
}

NOME_CURTO = {
    "E2 (6a)": "Mi grave (E2)",
    "A2 (5a)": "La      (A2)",
    "D3 (4a)": "Re      (D3)",
    "G3 (3a)": "Sol     (G3)",
    "B3 (2a)": "Si      (B3)",
    "E4 (1a)": "Mi agudo(E4)",
}

# ─── Parâmetros de captura ────────────────────────────────────────────────────
N_SAMPLES   = 512
SAMPLE_RATE = 4000
INTERVALO   = 1_000_000 // SAMPLE_RATE

# Magnitude mínima para considerar que tem sinal (evita ruído de fundo)
MAG_MINIMA  = 500

# ─── Janela de Hann ──────────────────────────────────────────────────────────
JANELA_HANN = [
    0.5 * (1.0 - math.cos(2.0 * math.pi * i / (N_SAMPLES - 1)))
    for i in range(N_SAMPLES)
]

# ─── FFT Cooley-Tukey ─────────────────────────────────────────────────────────
def fft(x_real, x_imag):
    n = len(x_real)
    if n <= 1:
        return x_real, x_imag
    er, ei  = fft(x_real[0::2], x_imag[0::2])
    or_, oi = fft(x_real[1::2], x_imag[1::2])
    tr, ti  = [0.0]*n, [0.0]*n
    half = n // 2
    for k in range(half):
        ang = -2.0 * math.pi * k / n
        wr  =  math.cos(ang)
        wi  =  math.sin(ang)
        re  =  wr * or_[k] - wi * oi[k]
        im  =  wr * oi[k]  + wi * or_[k]
        tr[k]        = er[k] + re
        ti[k]        = ei[k] + im
        tr[k + half] = er[k] - re
        ti[k + half] = ei[k] - im
    return tr, ti

# ─── Captura de amostras ──────────────────────────────────────────────────────
def capturar():
    data = []
    t = time.ticks_us()
    for _ in range(N_SAMPLES):
        data.append(adc.read_u16())
        t += INTERVALO
        while time.ticks_diff(t, time.ticks_us()) > 0:
            pass
    return data

# ─── Filtro Butterworth passa-baixa 2a ordem ─────────────────────────────────
B0, B1, B2 =  0.0674552,  0.1349104,  0.0674552
A1, A2     = -1.1429805,  0.4127513

def filtro_pb(data):
    out = [0.0] * len(data)
    x1 = x2 = y1 = y2 = 0.0
    for i, x0 in enumerate(data):
        y0 = B0*x0 + B1*x1 + B2*x2 - A1*y1 - A2*y2
        out[i] = y0
        x2, x1 = x1, x0
        y2, y1 = y1, y0
    return out

# ─── Detecção de frequência via FFT ──────────────────────────────────────────
def detectar_freq_fft(data):
    media = sum(data) / len(data)
    xr = [(data[i] - media) * JANELA_HANN[i] for i in range(N_SAMPLES)]
    xi = [0.0] * N_SAMPLES

    fr, fi = fft(xr, xi)

    half = N_SAMPLES // 2
    mag  = [math.sqrt(fr[i]*fr[i] + fi[i]*fi[i]) for i in range(1, half)]

    mag_max = max(mag)

    # Sinal fraco demais = silencio, ignora
    if mag_max < MAG_MINIMA:
        return 0.0, 0.0

    pico_idx = mag.index(mag_max) + 1
    freq = pico_idx * SAMPLE_RATE / N_SAMPLES
    return freq, mag_max

# ─── Conversão Hz para Cents ─────────────────────────────────────────────────
def hz_para_cents(freq, ref):
    if freq <= 0 or ref <= 0:
        return 0.0
    return 1200.0 * math.log(freq / ref, 1)

# ─── Identifica nota mais próxima ────────────────────────────────────────────
def identificar_nota(freq):
    if freq <= 0:
        return None, 0.0, 0.0

    melhor      = None
    menor_cents = 9999.0

    for nome, val in NOTAS.items():
        c = abs(hz_para_cents(freq, val))
        if c < menor_cents:
            menor_cents = c
            melhor = nome

    if melhor is None:
        return None, 0.0, 0.0

    cents_rel = hz_para_cents(freq, NOTAS[melhor])
    return melhor, menor_cents, cents_rel

# ─── Barra ASCII de afinação ─────────────────────────────────────────────────
def barra(cents, largura=21):
    centro = largura // 2
    pos = int(cents / 50.0 * (centro - 1))
    pos = max(-(centro-1), min(centro-1, pos))
    linha = ['-'] * largura
    linha[centro] = '|'
    linha[centro + pos] = 'O'
    return ''.join(linha) + '  {:+.1f}c'.format(cents)

# ─── Feedback LED ────────────────────────────────────────────────────────────
def feedback_led(afinado):
    led.value(1 if afinado else 0)

# ─── Loop principal ───────────────────────────────────────────────────────────
print("==============================")
print("  AFINADOR DE VIOLAO  FFT")
print("==============================")

while True:
    try:
        sinal      = capturar()
        sinal_filt = filtro_pb(sinal)
        freq, mag  = detectar_freq_fft(sinal_filt)

        # Sem sinal detectado
        if freq <= 0 or mag <= 0:
            feedback_led(False)
            print("Aguardando sinal... (toque uma corda)")
            print("------------------------------")
            time.sleep(0.4)
            continue

        nota, cents_abs, cents_rel = identificar_nota(freq)

        # Seguranca extra: nota nao identificada
        if nota is None:
            print("Nota nao identificada, freq:", round(freq, 2))
            print("------------------------------")
            time.sleep(0.4)
            continue

        afinado = abs(cents_rel) <= 8
        feedback_led(afinado)

        print("Freq : {} Hz  |  Mag: {}".format(round(freq, 2), round(mag)))
        print("Nota : {}  ({} Hz)".format(NOME_CURTO[nota], round(NOTAS[nota], 2)))
        print("Barra: {}".format(barra(cents_rel)))

        if afinado:
            print(">>> AFINADO! <<<")
        elif cents_rel > 0:
            print(">>> Afrouxe a corda (agudo)")
        else:
            print(">>> Aperte a corda (grave)")

        print("------------------------------")

    except Exception as e:
        print("Erro:", e)
        time.sleep(0.5)

    time.sleep(0.4)