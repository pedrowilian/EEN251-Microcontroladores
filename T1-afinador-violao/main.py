import math
import time
import gc
import array
import framebuf
from machine import ADC, Pin, SoftI2C


# ===================================================================
# SSD1306 EMBUTIDO
# ===================================================================
class SSD1306_I2C:
    def __init__(self, width, height, i2c, addr=0x3C):
        self.width = width
        self.height = height
        self.i2c = i2c
        self.addr = addr
        self.pages = height // 8
        self.buffer = bytearray(self.pages * width)
        self.framebuf = framebuf.FrameBuffer(
            self.buffer, width, height, framebuf.MONO_VLSB)
        self._cmd = bytearray(2)
        self._head = bytearray(b'\x40')
        self._init()

    def _wc(self, c):
        self._cmd[0] = 0x80
        self._cmd[1] = c
        self.i2c.writeto(self.addr, self._cmd)

    def _init(self):
        for c in (
            0xAE, 0x20, 0x00, 0x40, 0xA1, 0xC8,
            0xA8, self.height - 1, 0xD3, 0x00,
            0xDA, 0x02 if self.height == 32 else 0x12,
            0xD5, 0x80, 0xD9, 0xF1, 0xDB, 0x30,
            0x81, 0xFF, 0xA4, 0xA6, 0x8D, 0x14, 0xAF,
        ):
            self._wc(c)
        self.fill(0)
        self.show()

    def show(self):
        self._wc(0x21); self._wc(0); self._wc(self.width - 1)
        self._wc(0x22); self._wc(0); self._wc(self.pages - 1)
        self.i2c.writevto(self.addr, [self._head, self.buffer])

    def fill(self, c):          self.framebuf.fill(c)
    def text(self, s, x, y, c=1): self.framebuf.text(s, x, y, c)
    def hline(self, x, y, w, c):  self.framebuf.hline(x, y, w, c)
    def vline(self, x, y, h, c):  self.framebuf.vline(x, y, h, c)
    def fill_rect(self, x, y, w, h, c): self.framebuf.fill_rect(x, y, w, h, c)
    def rect(self, x, y, w, h, c): self.framebuf.rect(x, y, w, h, c)

    def off(self):
        self.fill(0)
        self.show()
        self._wc(0xAE)


# ===================================================================
# CONSTANTES
# ===================================================================
# CONSTANTES — AJUSTE AQUI
# ===================================================================

# --- AMOSTRAGEM ---
# Quantas leituras do ADC por segundo.
# Maior = captura mais rapido, mas gasta mais CPU.
# Precisa ser pelo menos 2x a maior frequencia que quer detectar (Nyquist).
# Ex: pra 500 Hz, minimo 1000. Recomendado: 4000-8000.
SAMPLE_RATE = 4000

# Quantas amostras por medicao. TEM QUE SER POTENCIA DE 2 (512, 1024, 2048, 4096).
# Maior = melhor precisao de frequencia, mas usa mais RAM e demora mais.
# 1024 = ~43KB RAM, resolucao ~7.8 Hz (com SR=8000)
# 2048 = ~86KB RAM, resolucao ~3.9 Hz (com SR=8000) <-- recomendado
# 4096 = ~172KB RAM, resolucao ~1.95 Hz (pode faltar RAM)
N = 2048

# Intervalo entre leituras do ADC em microsegundos.
# = 1_000_000 / SAMPLE_RATE. Se mudar SAMPLE_RATE, mude isso tambem.
SAMPLE_INTERVAL_US = 1_000_000 // SAMPLE_RATE  # 125 us pra 8000 Hz

# Resolucao de frequencia da FFT em Hz.
# = SAMPLE_RATE / N. Calculado automaticamente.
FREQ_RES = SAMPLE_RATE / N

# --- FAIXA DE FREQUENCIA ---
# Faixa de busca da FFT em Hz. So procura pico nessa faixa.
# BIN_MIN = frequencia minima (Hz). E2 = 82 Hz, entao 60 Hz da margem.
# BIN_MAX = frequencia maxima (Hz). E4 = 330 Hz, mas 500 Hz pra pegar harmonicos.
# Se voce ta testando com 430 Hz do YouTube, precisa BIN_MAX >= 430.
FREQ_MIN_HZ = 60
FREQ_MAX_HZ = 500
BIN_MIN = int(FREQ_MIN_HZ * N / SAMPLE_RATE)
BIN_MAX = int(FREQ_MAX_HZ * N / SAMPLE_RATE)

# --- FILTRO PASSA-BAIXA ---
# Coeficiente do filtro IIR. Valor entre 0 e 1.
# Menor = filtra mais ruido, mas pode perder sinal fraco.
# Maior = deixa mais sinal passar, mas tambem mais ruido.
# 0.3 = agressivo (bom pra ambiente ruidoso)
# 0.5 = moderado
# 0.7 = suave (bom pra ambiente silencioso)
ALPHA = 0.4
ONE_MINUS_ALPHA = 1.0 - ALPHA

# --- DETECCAO DE SINAL ---
# Amplitude minima pico-a-pico do ADC pra considerar que tem som.
# ADC retorna 0-65535. Se o mic ta com muito ruido, aumente.
# Se o mic ta com sinal fraco, diminua.
# 100 = muito sensivel (pega tudo, inclusive ruido)
# 500 = moderado
# 1000 = so pega sinal forte
# DICA: olhe o debug "ADC min=X max=Y pp=Z" no serial.
#       Em silencio, anote o pp. Coloque SIGNAL_THRESHOLD um pouco acima.
SIGNAL_THRESHOLD = 200

# --- AFINACAO ---
# Tolerancia em cents pra considerar "afinado".
# 1 semitom = 100 cents. Afinadores profissionais usam 5-10 cents.
# 10 = preciso (afinador bom)
# 15 = tolerante (bom pra ambiente ruidoso)
# 25 = muito tolerante
TOLERANCE_CENTS = 15

# --- ESTABILIZACAO POR MEDIANA MOVEL ---
# Quantas leituras de frequencia manter no buffer circular para
# calcular a mediana. A mediana descarta outliers (ex: harmonico
# detectado errado) e estabiliza a leitura mostrada no display.
# 3 = menos latencia (~1s pra estabilizar), suaviza menos
# 5 = sweet spot (~1.8s, bom equilibrio) <-- recomendado
# 7 = mais estavel (~2.5s), mais latencia
HISTORY_SIZE = 5

# --- CONSTANTES MATEMATICAS (nao mexer) ---
TWO_PI = 6.283185307179586
LOG2 = 0.6931471805599453

# --- NOTAS DO VIOLAO ---
TUNING = (
    ("E2", 82.41),    # 6a corda (mais grossa)
    ("A2", 110.00),   # 5a corda
    ("D3", 146.83),   # 4a corda
    ("G3", 196.00),   # 3a corda
    ("B3", 246.94),   # 2a corda
    ("E4", 329.63),   # 1a corda (mais fina)
)
CORDAS = ("6a", "5a", "4a", "3a", "2a", "1a")


# ===================================================================
# FFT
# ===================================================================

def precompute_twiddles(n):
    half = n >> 1
    tw_re = [0.0] * half
    tw_im = [0.0] * half
    for k in range(half):
        a = TWO_PI * k / n
        tw_re[k] = math.cos(a)
        tw_im[k] = math.sin(a)
    return tw_re, tw_im


def precompute_br(n):
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


def fft(re, im, tw_re, tw_im, br, n):
    """
    Calcula a Transformada Rapida de Fourier (FFT) in-place usando o
    algoritmo Cooley-Tukey radix-2 decimation-in-time (DIT).

    A entrada deve ter parte imaginaria zerada (sinal real). Os arrays
    re e im sao modificados in-place: ao retornar, contem a parte real
    e imaginaria da DFT do sinal de entrada.

    A frequencia correspondente ao bin k e: f_k = k * SAMPLE_RATE / n
    Para sinais reais, apenas os bins 0..n/2 sao informativos (simetria
    conjugada complexa: X[k] = conj(X[N-k])).

    Complexidade: O(n * log2(n)) operacoes de butterfly.

    Args:
        re:    Lista de N floats (parte real do sinal de entrada).
               Modificada in-place: contem Re(X[k]) na saida.
        im:    Lista de N floats (parte imaginaria do sinal de entrada,
               geralmente zerada). Modificada in-place: contem Im(X[k]).
        tw_re: Tabela pre-calculada de cos(2*pi*k/N) para k=0..N/2-1.
               Use precompute_twiddles(n) para gerar.
        tw_im: Tabela pre-calculada de sin(2*pi*k/N) para k=0..N/2-1.
        br:    Tabela de bit-reversal pre-calculada via precompute_br(n).
        n:     Tamanho da FFT. DEVE ser potencia de 2 (512, 1024, 2048, 4096).

    Pre-condicoes:
        - len(re) == len(im) == n
        - n e potencia de 2
        - len(tw_re) == len(tw_im) == n // 2
        - len(br) == n

    Pos-condicoes:
        - re[k] e im[k] contem a parte real e imaginaria do bin k
        - A magnitude e sqrt(re[k]**2 + im[k]**2)
        - A fase e atan2(im[k], re[k])

    Exemplo:
        >>> re = [math.sin(2 * math.pi * 100 * i / 1024) for i in range(1024)]
        >>> im = [0.0] * 1024
        >>> tw_re, tw_im = precompute_twiddles(1024)
        >>> br = precompute_br(1024)
        >>> fft(re, im, tw_re, tw_im, br, 1024)
        # re[100] e im[100] agora contem o componente espectral em 100 Hz
        # (assumindo SAMPLE_RATE=1024 nesse exemplo)

    Referencia:
        Cooley & Tukey (1965). "An Algorithm for the Machine Calculation
        of Complex Fourier Series." Math. Comp. 19, 297-301.
    """
    for i in range(n):
        j = br[i]
        if i < j:
            re[i], re[j] = re[j], re[i]
            im[i], im[j] = im[j], im[i]
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


# ===================================================================
# DSP
# ===================================================================

def capture(adc, samples, n):
    _sleep = time.sleep_us
    for i in range(n):
        samples[i] = adc.read_u16()
        _sleep(SAMPLE_INTERVAL_US)


def get_pp(samples, n):
    """Retorna min, max, pico-a-pico."""
    mn = 65535
    mx = 0
    for i in range(n):
        v = samples[i]
        if v < mn: mn = v
        if v > mx: mx = v
    return mn, mx, mx - mn


def process(samples, signal, filtered, han, re, im, mag, tw_re, tw_im, br, n):
    """
    Pipeline DSP completo: converte amostras brutas do ADC em frequencia
    fundamental detectada (em Hz).

    Executa as seguintes etapas em sequencia, todas in-place:
        1. Remocao de offset DC (centraliza o sinal em zero)
        2. Filtro IIR passa-baixa de 1a ordem (atenua alta frequencia)
        3. Janelamento de Hanning (reduz vazamento espectral)
        4. FFT Cooley-Tukey radix-2 DIT
        5. Calculo de magnitudes |X[k]| na faixa BIN_MIN..BIN_MAX
        6. Deteccao de pico (bin de maior magnitude na faixa)
        7. Interpolacao parabolica para precisao sub-bin

    Args:
        samples:  array.array('H') com N amostras brutas do ADC (uint16).
                  Usado apenas como entrada; nao modificado.
        signal:   Lista pre-alocada de N floats. Buffer de trabalho usado
                  para armazenar o sinal apos remocao de DC offset.
        filtered: Lista pre-alocada de N floats. Buffer de trabalho usado
                  para o sinal apos filtro IIR.
        han:      Lista pre-calculada de N floats com a janela de Hanning:
                  han[i] = 0.5 * (1 - cos(2*pi*i/(N-1)))
        re:       Lista pre-alocada de N floats. Recebe a parte real da FFT.
        im:       Lista pre-alocada de N floats. Recebe a parte imaginaria.
        mag:      Lista pre-alocada de N/2 floats. Recebe magnitudes.
                  Apenas posicoes BIN_MIN..BIN_MAX sao preenchidas (otimizacao).
        tw_re:    Twiddle factors (cosseno) pre-calculados.
        tw_im:    Twiddle factors (seno) pre-calculados.
        br:       Tabela bit-reversal pre-calculada.
        n:        Tamanho da FFT. Deve ser potencia de 2.

    Returns:
        float: Frequencia fundamental detectada em Hz, com precisao
        sub-bin via interpolacao parabolica. Retorna 0.0 se nenhum pico
        for encontrado na faixa de busca (caso degenerado de espectro
        vazio).

    Faixa de busca:
        Configurada pelas constantes globais BIN_MIN e BIN_MAX,
        correspondentes a FREQ_MIN_HZ e FREQ_MAX_HZ. Picos fora dessa
        faixa sao ignorados.

    Complexidade:
        Dominada pela FFT: O(n * log2(n)).

    Notas de implementacao:
        - Zero alocacao de memoria: todos os buffers sao pre-alocados pelo caller.
        - As referencias locais (_a, _oma, _sqrt) sao usadas para reduzir
          lookups de atributos no loop, otimizacao especifica de MicroPython.
        - A interpolacao parabolica usa tres pontos (pico e vizinhos) para
          ajustar uma parabola e estimar o vertice (frequencia verdadeira).

    Pre-condicoes:
        - Todos os buffers tem tamanho compativel com n
        - n e potencia de 2
        - tw_re, tw_im, br foram gerados com o mesmo n via funcoes precompute_*
        - han foi pre-calculado para o mesmo n
        - BIN_MIN < BIN_MAX < n/2

    Exemplo de uso:
        # Inicializacao (uma vez)
        samples = array.array('H', [0] * N)
        signal = [0.0] * N
        filtered = [0.0] * N
        re, im = [0.0] * N, [0.0] * N
        mag = [0.0] * (N // 2)
        tw_re, tw_im = precompute_twiddles(N)
        br = precompute_br(N)
        han = [0.5 * (1 - math.cos(2*math.pi*i/(N-1))) for i in range(N)]

        # Loop principal
        capture(adc, samples, N)
        freq_hz = process(samples, signal, filtered, han,
                          re, im, mag, tw_re, tw_im, br, N)
        if freq_hz > 0:
            print("Frequencia: {:.1f} Hz".format(freq_hz))
    """
    # DC offset
    total = 0
    for i in range(n):
        total += samples[i]
    mean = total / n
    for i in range(n):
        signal[i] = samples[i] - mean

    # Filtro IIR
    _a = ALPHA
    _oma = ONE_MINUS_ALPHA
    filtered[0] = _a * signal[0]
    for i in range(1, n):
        filtered[i] = _a * signal[i] + _oma * filtered[i - 1]

    # Hanning + copia pra FFT
    for i in range(n):
        re[i] = filtered[i] * han[i]
        im[i] = 0.0

    # FFT
    fft(re, im, tw_re, tw_im, br, n)

    # Magnitudes (so na faixa de interesse)
    _sqrt = math.sqrt
    for k in range(BIN_MIN, BIN_MAX + 1):
        mag[k] = _sqrt(re[k] * re[k] + im[k] * im[k])

    # Pico
    pk = BIN_MIN
    pm = mag[BIN_MIN]
    for k in range(BIN_MIN + 1, BIN_MAX + 1):
        if mag[k] > pm:
            pm = mag[k]
            pk = k

    if pm == 0.0:
        return 0.0

    # Interpolacao parabolica
    p = 0.0
    if pk > BIN_MIN and pk < BIN_MAX:
        a = mag[pk - 1]
        b = mag[pk]
        c = mag[pk + 1]
        d = a - 2.0 * b + c
        if d < -1e-12 or d > 1e-12:
            p = 0.5 * (a - c) / d

    return (pk + p) * FREQ_RES


def identify(freq):
    bi = 0
    bd = abs(freq - TUNING[0][1])
    for i in range(1, 6):
        d = abs(freq - TUNING[i][1])
        if d < bd:
            bd = d
            bi = i
    return bi


def cents(freq, ref):
    if ref <= 0.0 or freq <= 0.0:
        return 0.0
    return 1200.0 * math.log(freq / ref) / LOG2


# ===================================================================
# MAIN
# ===================================================================

def main():
    # Hardware
    adc = ADC(26)
    led = Pin(25, Pin.OUT)
    led.value(1)

    i2c = SoftI2C(sda=Pin(16), scl=Pin(17), freq=400000)
    oled = SSD1306_I2C(128, 64, i2c)
    oled.fill(0)
    oled.text("AFINADOR", 28, 10, 1)
    oled.text("Iniciando...", 16, 35, 1)
    oled.show()

    print("=== AFINADOR DE VIOLAO ===")
    print("SR={} N={} Res={:.2f}Hz".format(SAMPLE_RATE, N, FREQ_RES))

    # Pre-alocacoes
    samples = array.array('H', (0 for _ in range(N)))
    signal = [0.0] * N
    filtered = [0.0] * N
    re = [0.0] * N
    im = [0.0] * N
    mag = [0.0] * (N >> 1)
    tw_re, tw_im = precompute_twiddles(N)
    br = precompute_br(N)
    han = [0.0] * N
    for i in range(N):
        han[i] = 0.5 * (1.0 - math.cos(TWO_PI * i / (N - 1)))

    gc.collect()
    print("Mem: {}".format(gc.mem_free()))
    time.sleep_ms(1000)

    oled.fill(0)
    oled.text("Toque uma", 20, 20, 1)
    oled.text("corda!", 36, 35, 1)
    oled.show()

    cycle = 0

    # Buffer circular para mediana movel da frequencia detectada.
    # Estabiliza a leitura descartando outliers (ex: harmonico ocasional).
    freq_history = [0.0] * HISTORY_SIZE
    hist_idx = 0
    hist_filled = 0  # warm-up: quantas posicoes ja foram preenchidas

    try:
        while True:
            # Captura
            capture(adc, samples, N)
            mn, mx, pp = get_pp(samples, N)

            # Debug ADC a cada 10 ciclos
            cycle += 1
            if cycle % 10 == 1:
                print("ADC min={} max={} pp={}".format(mn, mx, pp))

            if pp < SIGNAL_THRESHOLD:
                # Sem sinal suficiente — reseta buffer da mediana
                hist_filled = 0
                hist_idx = 0
                if cycle % 30 == 0:
                    oled.fill(0)
                    oled.text("Aguardando", 16, 20, 1)
                    oled.text("sinal...", 28, 35, 1)
                    oled.show()
            else:
                # Processar
                freq = process(samples, signal, filtered, han,
                               re, im, mag, tw_re, tw_im, br, N)

                if freq > 0.0:
                    # === MEDIANA MOVEL ===
                    # Adiciona ao buffer circular
                    freq_history[hist_idx] = freq
                    hist_idx = (hist_idx + 1) % HISTORY_SIZE
                    if hist_filled < HISTORY_SIZE:
                        hist_filled += 1

                    # Calcula mediana das leituras validas
                    if hist_filled >= 3:
                        valid = list(freq_history[:hist_filled])
                        valid.sort()
                        freq_smooth = valid[hist_filled // 2]
                    else:
                        freq_smooth = freq  # warm-up

                    idx = identify(freq_smooth)
                    ref = TUNING[idx][1]
                    note = TUNING[idx][0]
                    corda = CORDAS[idx]
                    c = cents(freq_smooth, ref)
                    ac = abs(c)

                    if ac <= TOLERANCE_CENTS:
                        st = "AFINADO"
                    elif c > 0:
                        st = "ALTO"
                    else:
                        st = "BAIXO"

                    # === DISPLAY ===
                    oled.fill(0)

                    # Nota e corda
                    oled.text(note, 0, 0, 1)
                    oled.text("Corda " + corda, 48, 0, 1)

                    # Frequencia medida
                    fi = int(freq_smooth)
                    fd = int((freq_smooth - fi) * 10) % 10
                    oled.text("{}.{} Hz".format(fi, fd), 0, 14, 1)

                    # Referencia
                    ri = int(ref)
                    rd = int((ref - ri) * 10) % 10
                    oled.text("Ref {}.{}".format(ri, rd), 68, 14, 1)

                    # Status
                    oled.text(st, 36, 28, 1)

                    # Cents
                    sign = "+" if c >= 0 else ""
                    ci = int(ac)
                    oled.text("{}{} cents".format(sign, ci), 28, 40, 1)

                    # Barra visual
                    center = 64
                    oled.vline(center, 54, 10, 1)
                    offset = int(c * 1.0)
                    if offset > 50: offset = 50
                    if offset < -50: offset = -50
                    if ac <= TOLERANCE_CENTS:
                        oled.fill_rect(center - 3, 56, 7, 6, 1)
                    elif offset > 0:
                        oled.fill_rect(center + 1, 56, offset, 5, 1)
                    else:
                        oled.fill_rect(center + offset, 56, -offset, 5, 1)

                    oled.show()

                    # Serial
                    print("{} {} {}.{}Hz ref={}.{} {}{}c {}".format(
                        note, corda, fi, fd, ri, rd, sign, ci, st))

            gc.collect()
            time.sleep_ms(50)

    except KeyboardInterrupt:
        print("Parando...")
    finally:
        # CLEANUP: desliga LED e limpa display
        led.value(0)
        oled.off()
        print("LED off, display off.")


if __name__ == "__main__":
    main()
