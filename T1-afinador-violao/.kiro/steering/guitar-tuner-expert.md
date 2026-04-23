---
inclusion: auto
---

# Steering — Afinador de Violão Embarcado (Raspberry Pi Pico 2 + MicroPython)

## Contexto

Afinador de violão embarcado no Raspberry Pi Pico 2 (RP2350) com MicroPython v1.27+.
Captura áudio via microfone no ADC(26), processa com pipeline DSP (filtro IIR + FFT Cooley-Tukey),
identifica a nota musical e exibe feedback via serial USB.

## Hardware

| Componente | Detalhe |
|---|---|
| MCU | RP2350, dual-core ARM Cortex-M33, 150 MHz, 520 KB SRAM |
| Firmware | MicroPython vanilla (sem ulab, sem NumPy) |
| ADC | Pino 26, `read_u16()` retorna 0–65535 (16 bits) |
| LED onboard | Pino 25, `Pin(25, Pin.OUT)` |
| Saída | `print()` via USB serial |

## Regras de Ouro para MicroPython no Pico 2

### Memória — CRÍTICO
1. **ZERO alocações no loop principal** — toda memória deve ser pré-alocada no `setup()`
2. **Nunca usar list comprehensions** dentro do loop — elas criam listas novas
3. **Nunca usar generators** (`sum(x for x in ...)`) — eles alocam objetos
4. **Usar loops explícitos** com arrays pré-alocados e escrita in-place
5. **`gc.collect()`** obrigatório a cada ciclo, fora do try/except
6. **Usar `array.array('H', ...)`** para dados do ADC (2 bytes por amostra vs 28 bytes por int em lista)
7. **Pré-calcular tudo que for constante**: twiddle factors, janela de Hanning, intervalo de amostragem

### Exemplo — ERRADO vs CERTO
```python
# ERRADO — aloca lista nova a cada ciclo (causa memory allocation failed)
signal = [samples[i] - mean for i in range(n)]

# CERTO — escreve in-place no array pré-alocado
for i in range(n):
    signal[i] = samples[i] - mean

# ERRADO — generator aloca objeto temporário
mean = sum(samples[i] for i in range(n)) / n

# CERTO — loop explícito sem alocação
total = 0
for i in range(n):
    total += samples[i]
mean = total / n
```

## Parâmetros do Sistema

| Parâmetro | Valor | Justificativa |
|---|---|---|
| SAMPLE_RATE | 4000 Hz | Nyquist para 350 Hz com margem |
| N | 1024 | Potência de 2, cabe na memória (~43 KB total) |
| Δf (resolução) | ~3.9 Hz | Suficiente com interpolação parabólica |
| ALPHA (filtro IIR) | 0.386 | fc=400 Hz, fs=4000 Hz, 1ª ordem |
| SIGNAL_THRESHOLD | 500 | Pico-a-pico em escala 16 bits |
| TUNING_TOLERANCE | 1.0 Hz | Margem para "Afinado" |
| CYCLE_DELAY_MS | 100 ms | Estabilidade entre ciclos |

## Pipeline DSP

```
ADC(26) → capture_samples() → remove_dc_offset() → low_pass_filter()
→ apply_hanning_window() → fft() → compute_magnitudes()
→ find_peak_frequency() → identify_note() → get_tuning_status()
→ format_output() → print()
```

### 1. Captura (capture_samples)
- `read_u16()` com `time.sleep_us(250)` entre leituras (4000 Hz)
- Calcula amplitude pico-a-pico; retorna False se < SIGNAL_THRESHOLD

### 2. Remoção DC (remove_dc_offset)
- Calcula média com loop explícito (sem generator)
- Subtrai média in-place no array `signal` pré-alocado

### 3. Filtro IIR Passa-Baixa (low_pass_filter)
- 1ª ordem: `y[i] = α·x[i] + (1-α)·y[i-1]`
- α = 0.386 para corte em 400 Hz
- Opera in-place no array `filtered`

### 4. Janela de Hanning (apply_hanning_window)
- Coeficientes pré-calculados no `setup()` — NÃO chamar `math.cos()` no loop
- Multiplica in-place: `filtered[i] *= hanning[i]`

### 5. FFT Cooley-Tukey (fft)
- Radix-2 DIT com bit-reversal + butterfly operations
- Twiddle factors pré-calculados no `setup()`
- Opera in-place nos arrays `re` e `im`
- Copiar `filtered` → `re` e zerar `im` antes de cada chamada

### 6. Magnitudes (compute_magnitudes)
- `|X[k]| = √(re² + im²)` para k = 0..N/2-1
- Opera in-place no array `magnitudes`

### 7. Detecção de Pico (find_peak_frequency)
- Busca max magnitude na faixa [BIN_MIN, BIN_MAX] (70–350 Hz)
- Interpolação parabólica para precisão sub-bin
- Retorna 0.0 se nenhum pico encontrado

### 8. Identificação e Feedback
- Compara com 6 notas da afinação padrão (E2–E4)
- Classifica: Afinado (±1 Hz), Sustenido (Sharp), Bemol (Flat)
- Formato: `Nota: A2 | Freq: 111.5 Hz | Ref: 110.0 Hz | Status: Sustenido (+1.5 Hz)`

## Afinação Padrão

| Corda | Nota | Frequência (Hz) |
|-------|------|-----------------|
| 6ª | E2 | 82.41 |
| 5ª | A2 | 110.00 |
| 4ª | D3 | 146.83 |
| 3ª | G3 | 196.00 |
| 2ª | B3 | 246.94 |
| 1ª | E4 | 329.63 |

## Estrutura do Código

Arquivo único `main.py` com todas as funções. Todas operam in-place em arrays pré-alocados.
O `setup()` retorna dicionário com todos os recursos; `main_loop()` extrai as referências
e roda o pipeline em loop infinito com `try/except` + `gc.collect()`.

## Testes

- Rodam no **host PC** com CPython + pytest + hypothesis
- `tests/conftest.py` faz mock do módulo `machine` (ADC, Pin, time.sleep_us/ms)
- Fixture `sine_samples(frequency, amplitude)` gera sinais de teste
- Todas as funções DSP são testáveis isoladamente (sem dependência de hardware)

## Armadilhas Conhecidas

1. **`read_u16()` retorna 0–65535**, não 0–4095 — o Pico 2 tem ADC de 12 bits mas MicroPython escala pra 16
2. **`time.sleep_us()` não existe no CPython** — precisa de mock nos testes
3. **Fragmentação de memória** é o inimigo #1 — qualquer alocação no loop eventualmente causa crash
4. **`math.cos()`/`math.sin()` são lentos** — pré-calcular tudo que for constante
5. **Dicionários alocam memória** — ok no setup, mas nunca criar dicts no loop
6. **String formatting aloca** — `format_output()` é a única alocação aceitável no loop (string curta)
