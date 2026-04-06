---
inclusion: auto
---

# Steering — Especialista em Sistemas Embarcados, Sinais e MicroPython

## Contexto do Projeto

Este projeto é um afinador de guitarra/violão embarcado no Raspberry Pi Pico 2 (RP2350) rodando MicroPython. O sistema captura áudio via microfone no ADC(26), processa o sinal digitalmente e identifica a nota musical tocada.

## Plataforma e Restrições de Hardware

- **MCU**: Raspberry Pi Pico 2 (RP2350, dual-core ARM Cortex-M33, 150 MHz, 520 KB SRAM)
- **Firmware**: MicroPython (sem NumPy, sem SciPy — tudo em Python puro ou módulos built-in)
- **ADC**: 12 bits (0–4095), pino 26, tensão de referência 3.3V
- **LED onboard**: pino 25 (`Pin(25, Pin.OUT)`)
- **Saída**: Serial via USB (print → console serial)
- **Memória limitada**: evitar alocações grandes; preferir arrays pré-alocados e operações in-place

## Processamento Digital de Sinais — Diretrizes

### Taxa de Amostragem
- A frequência máxima de interesse é ~350 Hz (E4 = 329.63 Hz)
- Pelo teorema de Nyquist, a taxa mínima é 2× a frequência máxima = 700 Hz
- Usar **taxa de amostragem de 4000 Hz** para boa margem e resolução temporal
- Coletar amostras com `time.sleep_us()` para controle preciso do intervalo entre leituras
- Intervalo entre amostras: `1_000_000 // SAMPLE_RATE` microssegundos

### Número de Amostras (N)
- Deve ser potência de 2 para FFT: usar **N = 1024** ou **N = 2048**
- Resolução em frequência: `Δf = SAMPLE_RATE / N`
  - Com 4000 Hz e N=1024: Δf ≈ 3.9 Hz
  - Com 4000 Hz e N=2048: Δf ≈ 1.95 Hz
- **Recomendação**: usar N=2048 para melhor resolução, mas N=1024 se memória for problema
- Pré-alocar o array de amostras: `samples = array('H', [0] * N)` (unsigned short, 16 bits)

### Remoção de Offset DC
- O ADC do Pico retorna valores de 0 a 65535 (16 bits via `read_u16()`) com offset DC em ~32768
- **Sempre subtrair a média** das amostras antes de qualquer processamento:
  ```python
  mean_val = sum(samples) / len(samples)
  samples = [s - mean_val for s in samples]
  ```
- Isso centraliza o sinal em zero, essencial para FFT correta

### Filtro Passa-Baixa Digital
- Implementar como **filtro IIR de primeira ordem** (eficiente em MCU):
  ```python
  # alpha = dt / (RC + dt), onde RC = 1/(2*pi*fc), fc = frequência de corte
  # Para fc = 400 Hz e fs = 4000 Hz:
  # RC = 1/(2*pi*400) ≈ 0.000398
  # dt = 1/4000 = 0.00025
  # alpha = 0.00025 / (0.000398 + 0.00025) ≈ 0.386
  alpha = 0.386
  filtered = [0.0] * len(samples)
  filtered[0] = samples[0] * alpha
  for i in range(1, len(samples)):
      filtered[i] = alpha * samples[i] + (1 - alpha) * filtered[i-1]
  ```
- Alternativa: filtro de média móvel (FIR simples) com janela de 5-10 amostras
- **Não usar filtros de ordem alta** — custo computacional proibitivo em MicroPython

### Janelamento (Windowing)
- Aplicar **janela de Hanning** antes da FFT para reduzir vazamento espectral (spectral leakage):
  ```python
  import math
  for i in range(N):
      w = 0.5 * (1 - math.cos(2 * math.pi * i / (N - 1)))
      filtered[i] *= w
  ```
- Isso é crítico para precisão na detecção de frequência

### FFT (Transformada Rápida de Fourier)
- Implementar **Cooley-Tukey radix-2 DIT** em MicroPython puro
- Usar representação com listas separadas de parte real e imaginária (evitar complex numbers se possível para economia de memória)
- Estrutura do algoritmo:
  1. Bit-reversal permutation dos índices
  2. Butterfly operations iterativas (log2(N) estágios)
  3. Calcular magnitude: `mag[k] = sqrt(re[k]**2 + im[k]**2)`
- **Otimizações importantes**:
  - Pré-calcular twiddle factors (`cos` e `sin`) uma vez e reutilizar
  - Usar `math.sqrt` apenas no cálculo final de magnitude
  - Processar apenas metade do espectro (simetria para sinais reais)
  - Limitar busca de pico à faixa de interesse: bins correspondentes a 70–350 Hz

### Detecção de Pico no Espectro
- Converter índice do bin para frequência: `freq = bin_index * SAMPLE_RATE / N`
- Calcular bins de interesse:
  - `bin_min = int(70 * N / SAMPLE_RATE)`
  - `bin_max = int(350 * N / SAMPLE_RATE)`
- Encontrar o bin com maior magnitude nessa faixa
- **Interpolação parabólica** para melhorar precisão (opcional mas recomendado):
  ```python
  # k = índice do pico, mag = array de magnitudes
  if k > 0 and k < len(mag) - 1:
      alpha_val = mag[k-1]
      beta = mag[k]
      gamma = mag[k+1]
      p = 0.5 * (alpha_val - gamma) / (alpha_val - 2*beta + gamma)
      freq_interpolated = (k + p) * SAMPLE_RATE / N
  ```

### Detecção de Sinal Insuficiente
- Calcular amplitude RMS ou pico-a-pico do sinal
- Se abaixo de um limiar (ex.: amplitude pico-a-pico < 500 em escala de 16 bits), considerar "sem sinal"
- Pular processamento FFT nesse caso para economizar ciclos

## Afinação Padrão do Violão

| Corda | Nota | Frequência (Hz) |
|-------|------|-----------------|
| 6ª    | E2   | 82.41            |
| 5ª    | A2   | 110.00           |
| 4ª    | D3   | 146.83           |
| 3ª    | G3   | 196.00           |
| 2ª    | B3   | 246.94           |
| 1ª    | E4   | 329.63           |

- Tolerância de afinação: ±1 Hz
- Identificar nota mais próxima por menor diferença absoluta

## Boas Práticas para MicroPython no Pico 2

- **Usar `array` module** em vez de listas para dados numéricos grandes (menor uso de memória)
- **Evitar list comprehensions grandes** — preferir loops com arrays pré-alocados
- **`gc.collect()`** entre ciclos de medição para liberar memória
- **`time.sleep_us()`** para timing preciso de amostragem
- **`time.sleep_ms(100)`** entre ciclos para estabilidade
- **Try/except** no loop principal para resiliência — nunca deixar o sistema travar
- **Print formatado** para saída serial legível:
  ```
  Nota: A2 | Freq: 111.5 Hz | Ref: 110.0 Hz | Status: Sustenido (+1.5 Hz)
  ```

## Estrutura Recomendada do Código

```
main.py (ou guitar_tuner.py)
├── Constantes (SAMPLE_RATE, N, frequências de referência, etc.)
├── setup() — configura ADC, LED, variáveis
├── capture_samples() — lê N amostras do ADC
├── remove_dc_offset() — subtrai média
├── low_pass_filter() — aplica filtro IIR
├── apply_window() — janela de Hanning
├── fft() — implementação Cooley-Tukey
├── find_peak_frequency() — busca pico no espectro
├── identify_note() — mapeia frequência para nota
├── get_tuning_status() — calcula desvio e status
├── main_loop() — loop principal com tratamento de erros
└── Ponto de entrada: if __name__ == "__main__"
```

## Cuidados Críticos

1. **Não usar `ulab`** a menos que esteja instalado — assumir MicroPython vanilla
2. **ADC `read_u16()`** retorna 0–65535, não 0–4095 — normalizar adequadamente
3. **Garbage collection** é essencial entre ciclos para evitar fragmentação de memória
4. **Twiddle factors** da FFT devem ser pré-calculados — `math.cos()` e `math.sin()` são lentos
5. **Não alocar memória dentro do loop principal** — pré-alocar tudo no setup
