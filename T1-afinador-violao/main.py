import math
import time
import gc
import array
from machine import ADC, Pin

# ---------------------------------------------------------------------------
# Constantes do Sistema
# ---------------------------------------------------------------------------
SAMPLE_RATE = 4000                          # Hz
N = 1024                                    # Número de amostras (potência de 2)
ALPHA = 0.386                               # Coeficiente do filtro IIR (fc=400 Hz, fs=4000 Hz)
SIGNAL_THRESHOLD = 500                      # Limiar de amplitude pico-a-pico (16 bits)
TUNING_TOLERANCE = 1.0                      # Hz
CYCLE_DELAY_MS = 100                        # Intervalo entre ciclos (ms)
BIN_MIN = int(70 * N / SAMPLE_RATE)         # ~36
BIN_MAX = int(350 * N / SAMPLE_RATE)        # ~179

# ---------------------------------------------------------------------------
# Tabela de Afinação Padrão (E2–E4)
# ---------------------------------------------------------------------------
STANDARD_TUNING = [
    ("E2", 82.41),
    ("A2", 110.00),
    ("D3", 146.83),
    ("G3", 196.00),
    ("B3", 246.94),
    ("E4", 329.63),
]


# ---------------------------------------------------------------------------
# FFT Twiddle Factors (stub — implementação completa na tarefa 5.1)
# ---------------------------------------------------------------------------
def precompute_twiddles(n):
    """Pré-calcula twiddle factors cos(2πk/N) e sin(2πk/N) para k=0..N/2-1."""
    half = n // 2
    twiddle_re = [0.0] * half
    twiddle_im = [0.0] * half
    for k in range(half):
        angle = 2.0 * math.pi * k / n
        twiddle_re[k] = math.cos(angle)
        twiddle_im[k] = math.sin(angle)
    return twiddle_re, twiddle_im


def bit_reverse(data_re, data_im, n):
    """Permutação bit-reversal dos índices, operando in-place.

    Reordena os arrays de parte real e imaginária para que cada elemento
    no índice i seja movido para o índice obtido pela reversão dos bits
    de i (considerando log2(n) bits). Passo necessário antes das butterfly
    operations da FFT Cooley-Tukey radix-2 DIT.

    Args:
        data_re: Lista de floats com a parte real (modificada in-place).
        data_im: Lista de floats com a parte imaginária (modificada in-place).
        n: Número de elementos (deve ser potência de 2).
    """
    bits = 0
    temp = n
    while temp > 1:
        bits += 1
        temp >>= 1

    for i in range(n):
        j = 0
        for b in range(bits):
            if i & (1 << b):
                j |= 1 << (bits - 1 - b)
        if i < j:
            data_re[i], data_re[j] = data_re[j], data_re[i]
            data_im[i], data_im[j] = data_im[j], data_im[i]


def fft(data_re, data_im, twiddle_re, twiddle_im, n):
    """FFT Cooley-Tukey radix-2 decimation-in-time (DIT) in-place.

    Aplica a Transformada Rápida de Fourier nos arrays de parte real e
    imaginária, usando twiddle factors pré-calculados. Opera in-place.

    Passos:
        1. Permutação bit-reversal via bit_reverse()
        2. Butterfly operations iterativas em log₂(N) estágios

    Args:
        data_re: Lista de floats com a parte real (modificada in-place).
        data_im: Lista de floats com a parte imaginária (modificada in-place).
        twiddle_re: Lista de floats com cos(2πk/N) para k=0..N/2-1.
        twiddle_im: Lista de floats com sin(2πk/N) para k=0..N/2-1.
        n: Número de elementos (deve ser potência de 2).
    """
    # Step 1: bit-reversal permutation
    bit_reverse(data_re, data_im, n)

    # Step 2: butterfly operations
    size = 2
    while size <= n:
        half_size = size // 2
        step = n // size  # twiddle factor step
        for i in range(0, n, size):
            for k in range(half_size):
                tw_idx = k * step
                tw_re = twiddle_re[tw_idx]
                tw_im = twiddle_im[tw_idx]

                j = i + k
                j_half = j + half_size

                # Butterfly: multiply by twiddle factor
                t_re = data_re[j_half] * tw_re - data_im[j_half] * tw_im
                t_im = data_re[j_half] * tw_im + data_im[j_half] * tw_re

                data_re[j_half] = data_re[j] - t_re
                data_im[j_half] = data_im[j] - t_im
                data_re[j] = data_re[j] + t_re
                data_im[j] = data_im[j] + t_im
        size *= 2


def compute_magnitudes(re, im, magnitudes, n):
    """Calcula as magnitudes do espectro de frequência: |X[k]| = √(re[k]² + im[k]²).

    Processa apenas a primeira metade do espectro (k = 0..N/2-1), pois
    a segunda metade é simétrica para sinais reais. Opera in-place no
    array `magnitudes` pré-alocado.

    Args:
        re: Lista de floats com a parte real da FFT.
        im: Lista de floats com a parte imaginária da FFT.
        magnitudes: Lista pré-alocada para armazenar as magnitudes (in-place).
        n: Número total de pontos da FFT (deve ser potência de 2).
    """
    half = n // 2
    for k in range(half):
        magnitudes[k] = math.sqrt(re[k] * re[k] + im[k] * im[k])


# ---------------------------------------------------------------------------
# Detecção de Pico (PeakDetector)
# ---------------------------------------------------------------------------
def find_peak_frequency(magnitudes, sample_rate, n, bin_min, bin_max):
    """Encontra a frequência de pico no espectro usando interpolação parabólica.

    Busca o bin de maior magnitude na faixa [bin_min, bin_max] e aplica
    interpolação parabólica nos bins vizinhos para refinar a estimativa
    de frequência além da resolução discreta da FFT.

    Args:
        magnitudes: Lista de floats com as magnitudes do espectro (N/2 elementos).
        sample_rate: Taxa de amostragem em Hz.
        n: Número total de pontos da FFT.
        bin_min: Índice mínimo do bin para busca (inclusive).
        bin_max: Índice máximo do bin para busca (inclusive).

    Returns:
        Frequência interpolada em Hz. Retorna 0.0 se todas as magnitudes
        na faixa forem zero.
    """
    # Find bin with maximum magnitude in range
    peak_bin = bin_min
    peak_mag = magnitudes[bin_min]
    for k in range(bin_min + 1, bin_max + 1):
        if magnitudes[k] > peak_mag:
            peak_mag = magnitudes[k]
            peak_bin = k

    # If all magnitudes are zero, no peak found
    if peak_mag == 0.0:
        return 0.0

    # Parabolic interpolation for better precision
    if peak_bin > bin_min and peak_bin < bin_max:
        alpha = magnitudes[peak_bin - 1]
        beta = magnitudes[peak_bin]
        gamma = magnitudes[peak_bin + 1]
        denom = alpha - 2 * beta + gamma
        if abs(denom) > 1e-12:
            p = 0.5 * (alpha - gamma) / denom
        else:
            p = 0.0
    else:
        p = 0.0

    return (peak_bin + p) * sample_rate / n


# ---------------------------------------------------------------------------
# Inicialização do Sistema
# ---------------------------------------------------------------------------
def setup():
    """Configura hardware e pré-aloca todos os arrays para o loop principal."""
    # Hardware
    adc = ADC(26)
    led = Pin(25, Pin.OUT)
    led.value(1)

    # Arrays pré-alocados
    samples = array.array('H', [0] * N)
    signal = [0.0] * N
    filtered = [0.0] * N
    re = [0.0] * N
    im = [0.0] * N
    magnitudes = [0.0] * (N // 2)

    # Twiddle factors pré-calculados
    twiddle_re, twiddle_im = precompute_twiddles(N)

    # Janela de Hanning pré-calculada
    hanning = [0.0] * N
    for i in range(N):
        hanning[i] = 0.5 * (1 - math.cos(2 * math.pi * i / (N - 1)))

    return {
        "adc": adc,
        "led": led,
        "samples": samples,
        "signal": signal,
        "filtered": filtered,
        "re": re,
        "im": im,
        "magnitudes": magnitudes,
        "twiddle_re": twiddle_re,
        "twiddle_im": twiddle_im,
        "hanning": hanning,
    }


# ---------------------------------------------------------------------------
# Captura de Amostras (AudioCapture)
# ---------------------------------------------------------------------------
def capture_samples(adc, samples, sample_rate, n):
    """Lê N amostras do ADC com timing preciso e verifica amplitude do sinal.

    Preenche o array `samples` in-place com leituras de `adc.read_u16()`,
    espaçadas por `1_000_000 // sample_rate` microssegundos.

    Retorna True se a amplitude pico-a-pico (max - min) >= SIGNAL_THRESHOLD,
    indicando sinal suficiente. Retorna False caso contrário.
    """
    interval_us = 1_000_000 // sample_rate

    for i in range(n):
        samples[i] = adc.read_u16()
        time.sleep_us(interval_us)

    # Calcular amplitude pico-a-pico
    min_val = samples[0]
    max_val = samples[0]
    for i in range(1, n):
        if samples[i] < min_val:
            min_val = samples[i]
        if samples[i] > max_val:
            max_val = samples[i]

    return (max_val - min_val) >= SIGNAL_THRESHOLD


# ---------------------------------------------------------------------------
# Processamento do Sinal (SignalProcessor)
# ---------------------------------------------------------------------------
def remove_dc_offset(samples, signal, n):
    """Remove o offset DC subtraindo a média aritmética das amostras.

    Calcula a média das N amostras e subtrai de cada uma, escrevendo
    o resultado in-place no array `signal` pré-alocado.

    Args:
        samples: Array com as amostras brutas do ADC.
        signal: Lista pré-alocada para armazenar o sinal centralizado (in-place).
        n: Número de amostras a processar.
    """
    total = 0
    for i in range(n):
        total += samples[i]
    mean = total / n
    for i in range(n):
        signal[i] = samples[i] - mean


def low_pass_filter(samples, filtered, alpha, n):
    """Aplica filtro passa-baixa IIR de 1ª ordem ao sinal.

    Implementa y[i] = α·x[i] + (1-α)·y[i-1], operando in-place no
    array `filtered` pré-alocado.

    Args:
        samples: Lista de floats com o sinal de entrada (após remoção de DC).
        filtered: Lista pré-alocada para armazenar o sinal filtrado (in-place).
        alpha: Coeficiente do filtro (0 < α ≤ 1). Para fc=400Hz e fs=4000Hz, α≈0.386.
        n: Número de amostras a processar.
    """
    filtered[0] = alpha * samples[0]
    for i in range(1, n):
        filtered[i] = alpha * samples[i] + (1 - alpha) * filtered[i - 1]


def apply_hanning_window(filtered, hanning, n):
    """Aplica janela de Hanning in-place ao sinal filtrado.

    Multiplica cada amostra pelo coeficiente pré-calculado da janela de Hanning,
    reduzindo vazamento espectral na FFT.

    Args:
        filtered: Lista de floats com o sinal filtrado (modificada in-place).
        hanning: Lista pré-calculada com os coeficientes da janela.
        n: Número de amostras a processar.
    """
    for i in range(n):
        filtered[i] *= hanning[i]


# ---------------------------------------------------------------------------
# Identificação de Nota e Feedback (NoteIdentifier)
# ---------------------------------------------------------------------------
def identify_note(frequency):
    """Identifica a nota mais próxima da frequência fornecida.

    Compara a frequência de entrada com as 6 frequências de referência
    da afinação padrão (STANDARD_TUNING) e retorna a nota cuja frequência
    de referência tem a menor diferença absoluta.

    Args:
        frequency: Frequência detectada em Hz.

    Returns:
        Tupla (nome_nota, frequência_referência) da nota mais próxima.
    """
    closest_note = STANDARD_TUNING[0][0]
    closest_freq = STANDARD_TUNING[0][1]
    min_diff = abs(frequency - closest_freq)

    for note, ref_freq in STANDARD_TUNING[1:]:
        diff = abs(frequency - ref_freq)
        if diff < min_diff:
            min_diff = diff
            closest_note = note
            closest_freq = ref_freq

    return (closest_note, closest_freq)


def get_tuning_status(frequency, ref_frequency):
    """Classifica o status de afinação com base no desvio entre a frequência detectada e a referência.

    Calcula o desvio (frequency - ref_frequency) e classifica:
    - "Afinado" se |desvio| ≤ TUNING_TOLERANCE (1.0 Hz)
    - "Sustenido (Sharp)" se desvio > TUNING_TOLERANCE
    - "Bemol (Flat)" se desvio < -TUNING_TOLERANCE

    Args:
        frequency: Frequência detectada em Hz.
        ref_frequency: Frequência de referência da nota mais próxima em Hz.

    Returns:
        Tupla (status, desvio) onde status é uma string e desvio é um float em Hz.
    """
    deviation = frequency - ref_frequency
    if abs(deviation) <= TUNING_TOLERANCE:
        return ("Afinado", deviation)
    elif deviation > 0:
        return ("Sustenido (Sharp)", deviation)
    else:
        return ("Bemol (Flat)", deviation)


def format_output(note, frequency, ref_freq, status, deviation):
    """Formata a string de saída serial com todos os campos do feedback de afinação.

    Gera uma string legível contendo: nota detectada, frequência medida,
    frequência de referência, status da afinação e desvio em Hz com sinal.

    Args:
        note: Nome da nota identificada (ex.: "A2").
        frequency: Frequência medida em Hz.
        ref_freq: Frequência de referência da nota em Hz.
        status: Status da afinação ("Afinado", "Sustenido (Sharp)" ou "Bemol (Flat)").
        deviation: Desvio em Hz (positivo = sustenido, negativo = bemol).

    Returns:
        String formatada, ex.:
        "Nota: A2 | Freq: 111.5 Hz | Ref: 110.0 Hz | Status: Sustenido (+1.5 Hz)"
    """
    sign = "+" if deviation >= 0 else ""
    return "Nota: {} | Freq: {:.1f} Hz | Ref: {:.1f} Hz | Status: {} ({}{:.1f} Hz)".format(
        note, frequency, ref_freq, status, sign, deviation
    )


# ---------------------------------------------------------------------------
# Loop Principal (Integração do Pipeline)
# ---------------------------------------------------------------------------
def main_loop():
    """Loop principal do afinador de guitarra.

    Integra todo o pipeline DSP em um loop contínuo:
    captura → verificação de sinal → remoção DC → filtro → Hanning →
    FFT → magnitudes → pico → nota → status → print.

    Envolvido em try/except para resiliência. gc.collect() e sleep
    executam no finally para garantir estabilidade entre ciclos.
    """
    print("Afinador de Guitarra — Raspberry Pi Pico 2")
    print("Inicializando...")

    ctx = setup()
    adc = ctx["adc"]
    samples = ctx["samples"]
    signal = ctx["signal"]
    filtered = ctx["filtered"]
    re = ctx["re"]
    im = ctx["im"]
    magnitudes = ctx["magnitudes"]
    twiddle_re = ctx["twiddle_re"]
    twiddle_im = ctx["twiddle_im"]
    hanning = ctx["hanning"]

    # Forçar coleta de lixo após inicialização
    gc.collect()

    print("Sistema pronto. LED aceso.")
    print("Toque uma corda para afinar.")
    print("-" * 50)

    while True:
        try:
            # 1. Captura de amostras
            has_signal = capture_samples(adc, samples, SAMPLE_RATE, N)

            if not has_signal:
                print("Sem sinal detectado")
            else:
                # 2. Remoção de DC offset (in-place no array signal)
                remove_dc_offset(samples, signal, N)

                # 3. Filtro passa-baixa IIR
                low_pass_filter(signal, filtered, ALPHA, N)

                # 4. Janela de Hanning (pré-calculada)
                apply_hanning_window(filtered, hanning, N)

                # 5. Preparar arrays para FFT
                for i in range(N):
                    re[i] = filtered[i]
                    im[i] = 0.0

                # 6. FFT
                fft(re, im, twiddle_re, twiddle_im, N)

                # 7. Magnitudes
                compute_magnitudes(re, im, magnitudes, N)

                # 8. Detecção de pico
                freq = find_peak_frequency(magnitudes, SAMPLE_RATE, N, BIN_MIN, BIN_MAX)

                if freq == 0.0:
                    print("Sem sinal detectado")
                else:
                    # 9. Identificação de nota
                    note, ref_freq = identify_note(freq)

                    # 10. Status de afinação
                    status, deviation = get_tuning_status(freq, ref_freq)

                    # 11. Saída formatada
                    print(format_output(note, freq, ref_freq, status, deviation))

        except Exception as e:
            print("Erro: {}".format(e))

        gc.collect()
        time.sleep_ms(CYCLE_DELAY_MS)


if __name__ == "__main__":
    main_loop()
