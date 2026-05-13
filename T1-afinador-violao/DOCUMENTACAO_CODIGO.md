# Afinador de Violão Digital — Documentação Técnica

**Plataforma:** Raspberry Pi Pico 2 (RP2350)
**Linguagem:** MicroPython v1.27+
**Versão:** 1.0
**Disciplina:** EEN251 — Microcontroladores

---

## Sumário

1. [Resumo Executivo](#1-resumo-executivo)
2. [Especificações Técnicas](#2-especificações-técnicas)
3. [Arquitetura do Sistema](#3-arquitetura-do-sistema)
4. [Requisitos de Hardware](#4-requisitos-de-hardware)
5. [Instalação e Uso](#5-instalação-e-uso)
6. [Pipeline de Processamento Digital de Sinais](#6-pipeline-de-processamento-digital-de-sinais)
7. [Algoritmo FFT](#7-algoritmo-fft)
8. [Identificação Musical](#8-identificação-musical)
9. [Interface de Usuário](#9-interface-de-usuário)
10. [Parâmetros de Configuração](#10-parâmetros-de-configuração)
11. [Estratégia de Testes](#11-estratégia-de-testes)
12. [Análise de Desempenho](#12-análise-de-desempenho)
13. [Limitações Conhecidas](#13-limitações-conhecidas)
14. [Referências](#14-referências)

---

## 1. Resumo Executivo

Este projeto implementa um afinador de violão digital embarcado no microcontrolador Raspberry Pi Pico 2 utilizando MicroPython puro, sem dependências de bibliotecas externas como NumPy ou ulab. O sistema captura áudio através de um microfone analógico, processa o sinal por meio de um pipeline de DSP (Digital Signal Processing) e identifica a nota musical correspondente à frequência fundamental detectada, fornecendo feedback de afinação em cents (unidade musical logarítmica).

A saída é apresentada em duas formas complementares: terminal serial USB para diagnóstico e um display OLED SSD1306 128×64 pixels para visualização compacta com indicadores gráficos de desafinação.

**Características principais:**

- Detecção de frequência via FFT Cooley-Tukey radix-2 em Python puro
- Resolução de frequência sub-bin via interpolação parabólica
- Pipeline DSP com remoção de offset DC, filtro IIR passa-baixa e janelamento de Hanning
- Identificação automática da nota mais próxima na afinação padrão (E2, A2, D3, G3, B3, E4)
- Feedback em cents (precisão musical logarítmica)
- Operação contínua com tratamento robusto de erros e cleanup de hardware no encerramento

---

## 2. Especificações Técnicas

| Parâmetro | Valor |
|---|---|
| Microcontrolador | RP2350 (dual-core Cortex-M33 @ 150 MHz) |
| Memória SRAM | 520 KB |
| Linguagem | MicroPython v1.27+ |
| Taxa de amostragem | 4 kHz |
| Tamanho da FFT (N) | 2048 amostras |
| Resolução de frequência | 1.95 Hz (com interpolação: ~0.1 Hz) |
| Faixa de busca | 60 Hz – 500 Hz |
| Faixa de afinação | E2 (82.41 Hz) a E4 (329.63 Hz) |
| Tolerância de afinação | ±15 cents (configurável) |
| Latência por ciclo | ~600 ms (captura + processamento) |
| Uso de RAM em runtime | ~110 KB |

---

## 3. Arquitetura do Sistema

O sistema adota uma arquitetura de pipeline sequencial single-core, executando em loop infinito até interrupção do usuário (Ctrl+C). Toda a memória utilizada no loop é pré-alocada na inicialização para evitar fragmentação e falhas de alocação durante operação contínua.

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Microfone  │───▶│   ADC GP26   │───▶│   Captura    │
└──────────────┘    └──────────────┘    │ (2048 amostr)│
                                        └──────┬───────┘
                                               ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Display OLED │◀───│ Identificação│◀───│    Pipeline  │
│   SSD1306    │    │   Musical    │    │      DSP     │
└──────────────┘    └──────────────┘    └──────────────┘
       ▲                    │                    │
┌──────────────┐            │                    ▼
│ Serial USB   │◀───────────┘            ┌──────────────┐
└──────────────┘                         │     FFT      │
                                         │  Cooley-Tukey│
                                         └──────────────┘
```

**Decisões arquiteturais:**

- **Pipeline single-core:** Simplicidade e previsibilidade; o segundo core do RP2350 não é necessário pois o pipeline completo cabe folgadamente em um ciclo.
- **Pré-alocação total:** Todos os arrays de trabalho são alocados na inicialização. O loop principal opera in-place, garantindo zero alocações dinâmicas e evitando o erro `MemoryError: memory allocation failed` característico do MicroPython em loops apertados.
- **MicroPython puro:** Sem `ulab` ou `numpy`. Todo o código DSP é implementado em Python puro, garantindo portabilidade e independência de firmwares customizados.
- **Driver SSD1306 embutido:** O driver do display é parte integrante do `main.py`, eliminando a necessidade de copiar bibliotecas adicionais para o filesystem do Pico.

---

## 4. Requisitos de Hardware

### 4.1 Componentes

| Componente | Descrição |
|---|---|
| Raspberry Pi Pico 2 | Microcontrolador RP2350 com MicroPython instalado |
| Microfone analógico | Módulo eletreto com pré-amplificação (saída 0–3.3V) |
| Display OLED | SSD1306 128×64 monocromático com interface I²C (HW-239A) |
| Cabos jumper | Para conexões físicas |
| Cabo USB | Para alimentação e comunicação serial |

### 4.2 Pinagem

| Função | Pino lógico | Pino físico | Descrição |
|---|---|---|---|
| Microfone (analógico) | GP26 / ADC0 | 31 | Entrada do sinal de áudio |
| LED de status | GP25 | — | LED onboard, aceso = sistema ativo |
| OLED SDA | GP16 | 21 | Linha de dados I²C |
| OLED SCL | GP17 | 22 | Linha de clock I²C |
| Alimentação OLED | 3V3(OUT) | 36 | 3.3V regulado |
| GND comum | GND | 38 | Terra |

> **Nota:** A pinagem I²C do display é configurável via `SoftI2C(sda=Pin(X), scl=Pin(Y))` na função `main()`. O endereço I²C padrão do SSD1306 é `0x3C`; alguns módulos utilizam `0x3D`.

### 4.3 Considerações Elétricas

O ADC do Pico 2 opera com referência de 3.3V e resolução interna de 12 bits, mas o método `read_u16()` do MicroPython escala automaticamente o resultado para 16 bits (0–65535). O sinal do microfone deve estar centrado em ~1.65V (metade da referência) com excursão dentro de 0–3.3V para evitar saturação ou clipping.

---

## 5. Instalação e Uso

### 5.1 Pré-requisitos

1. MicroPython v1.27 ou superior instalado no Raspberry Pi Pico 2
2. Hardware conectado conforme [seção 4.2](#42-pinagem)
3. Ferramenta de transferência de arquivos: `mpremote`, Thonny ou similar

### 5.2 Instalação

```bash
# Conecte o Pico via USB e identifique a porta serial
# No Windows: COMx, no Linux/Mac: /dev/ttyACMx

# Copie o arquivo principal usando mpremote
mpremote connect auto fs cp main.py :main.py

# Reinicie o Pico
mpremote connect auto reset
```

### 5.3 Operação

Ao energizar o Pico:

1. O LED onboard (GP25) acende, indicando inicialização
2. O display OLED exibe a tela de splash "AFINADOR — Iniciando..."
3. Após pré-cálculo de twiddle factors e janela de Hanning (~1 segundo), o display mostra "Toque uma corda!"
4. Tocar uma corda do violão a até ~30 cm do microfone
5. O sistema exibe a nota detectada, frequência medida, status de afinação e desvio em cents

### 5.4 Encerramento

Pressionar `Ctrl+C` no terminal serial dispara o cleanup graceful:

```python
finally:
    led.value(0)   # apaga LED
    oled.off()     # limpa e desliga display
```

---

## 6. Pipeline de Processamento Digital de Sinais

O pipeline DSP é executado a cada ciclo de medição. As etapas operam in-place sobre arrays pré-alocados.

### 6.1 Captura de Amostras

```python
def capture(adc, samples, n):
    for i in range(n):
        samples[i] = adc.read_u16()
        time.sleep_us(SAMPLE_INTERVAL_US)
```

**Função:** Coletar N amostras do ADC com intervalo temporal preciso.

**Considerações:**
- A precisão do timing depende do `time.sleep_us()`, que tem resolução de ~1 µs no RP2350
- Com SAMPLE_RATE=4000 e N=2048, a janela temporal é de 512 ms
- O array `samples` usa `array.array('H', ...)` (unsigned short, 2 bytes/elemento), economizando memória vs lista de inteiros Python

### 6.2 Detecção de Atividade

```python
def get_pp(samples, n):
    mn = 65535; mx = 0
    for i in range(n):
        v = samples[i]
        if v < mn: mn = v
        if v > mx: mx = v
    return mn, mx, mx - mn
```

**Função:** Calcular amplitude pico-a-pico para decidir se há sinal suficiente.

Se `pp < SIGNAL_THRESHOLD` (default: 200), o ciclo é abortado para economia computacional.

### 6.3 Remoção de Offset DC

O sinal do microfone tem componente DC ~32768 (meio do range do ADC). A FFT requer sinal centrado em zero — caso contrário, o bin 0 (DC) recebe energia espúria que pode dominar o espectro.

```python
total = sum(samples[i] for i in range(n))
mean = total / n
for i in range(n):
    signal[i] = samples[i] - mean
```

### 6.4 Filtro IIR Passa-Baixa de 1ª Ordem

```python
filtered[0] = ALPHA * signal[0]
for i in range(1, n):
    filtered[i] = ALPHA * signal[i] + (1 - ALPHA) * filtered[i - 1]
```

**Equação:** `y[n] = α · x[n] + (1 - α) · y[n-1]`

**Frequência de corte:** Para α=0.4 e fs=4000 Hz, fc ≈ 425 Hz (suficiente para preservar a faixa de interesse de 60–500 Hz).

**Justificativa:** Filtro IIR oferece ótima atenuação de alta frequência com complexidade computacional O(N) e zero overhead de memória adicional.

### 6.5 Janelamento de Hanning

```python
han[i] = 0.5 * (1 - cos(2π·i / (N-1)))   # pré-calculado
filtered[i] *= han[i]                     # aplicado a cada ciclo
```

**Função:** Suavizar as bordas do bloco de N amostras antes da FFT, eliminando descontinuidades artificiais que causariam **vazamento espectral** (spectral leakage).

A janela de Hanning oferece bom compromisso entre largura do lóbulo principal (resolução de frequência) e atenuação dos lóbulos laterais (-31 dB).

### 6.6 Aplicação da FFT

Detalhada na seção 7.

### 6.7 Cálculo de Magnitudes

```python
for k in range(BIN_MIN, BIN_MAX + 1):
    mag[k] = sqrt(re[k]² + im[k]²)
```

Apenas a faixa de interesse (60–500 Hz, correspondente a bins ~30–256) é processada, economizando tempo de CPU.

### 6.8 Detecção de Pico

Busca o bin com maior magnitude na faixa permitida. Esse pico, em condições ideais, corresponde à frequência fundamental da corda.

### 6.9 Interpolação Parabólica

```python
a, b, c = mag[pk-1], mag[pk], mag[pk+1]
d = a - 2b + c
p = 0.5 * (a - c) / d                  # offset sub-bin (-0.5 a +0.5)
freq = (pk + p) * SAMPLE_RATE / N      # frequência interpolada
```

**Função:** Estimar o pico verdadeiro entre dois bins adjacentes ajustando uma parábola pelos três pontos do entorno do bin de máximo.

**Ganho de precisão:** Sem interpolação, a precisão é limitada à largura do bin (1.95 Hz). Com interpolação parabólica, a precisão melhora para frações de Hz.

---

## 7. Algoritmo FFT

A FFT (Fast Fourier Transform) é o núcleo computacional do afinador. Esta seção descreve a implementação utilizada.

### 7.1 Motivação

A DFT (Discrete Fourier Transform) ingênua tem complexidade O(N²): para N=2048, isso são ~4.2 milhões de multiplicações complexas — inviável em microcontrolador.

A FFT reduz a complexidade para **O(N · log₂N)**: para N=2048, são ~22 mil multiplicações, **~190× mais rápido**.

### 7.2 Algoritmo Cooley-Tukey radix-2 DIT

Implementado em duas fases:

**Fase 1 — Permutação Bit-Reversal:**
Reordena os índices de entrada de modo que o algoritmo butterfly opere sobre dados consecutivos em memória. Os índices bit-revertidos são pré-calculados em uma tabela:

```python
def precompute_br(n):
    bits = log2(n)
    return [reverse_bits(i, bits) for i in range(n)]
```

**Fase 2 — Butterfly Iterativo:**
log₂(N) estágios, cada um operando sobre `N` elementos:

```python
size = 2
while size <= n:
    half = size // 2
    step = n // size
    for i in range(0, n, size):
        for k in range(half):
            wr = tw_re[k * step]    # twiddle factor (cos)
            wi = tw_im[k * step]    # twiddle factor (sin)
            j  = i + k
            j2 = j + half

            tr = re[j2] * wr - im[j2] * wi
            ti = re[j2] * wi + im[j2] * wr

            re[j2] = re[j] - tr
            im[j2] = im[j] - ti
            re[j]  = re[j] + tr
            im[j]  = im[j] + ti
    size *= 2
```

### 7.3 Twiddle Factors

São rotações no plano complexo: `W_N^k = cos(2πk/N) - j·sin(2πk/N)`.

Pré-calculados na inicialização e armazenados em duas listas (parte real e imaginária separadas) para evitar chamadas repetidas a `math.cos()` e `math.sin()`, que são caras em MicroPython.

### 7.4 Saída

Após a execução da FFT, os arrays `re[k]` e `im[k]` (k = 0..N/2) representam o conteúdo espectral. A magnitude `|X[k]| = sqrt(re[k]² + im[k]²)` corresponde à energia na frequência `f_k = k · fs / N`.

---

## 8. Identificação Musical

### 8.1 Tabela de Afinação Padrão

| Corda | Nota | Frequência (Hz) |
|---|---|---|
| 6ª (mais grossa) | E2 | 82.41 |
| 5ª | A2 | 110.00 |
| 4ª | D3 | 146.83 |
| 3ª | G3 | 196.00 |
| 2ª | B3 | 246.94 |
| 1ª (mais fina) | E4 | 329.63 |

### 8.2 Identificação por Distância Mínima

```python
def identify(freq):
    return argmin(|freq - TUNING[i]| for i in range(6))
```

A nota retornada é aquela com menor diferença absoluta em Hz da frequência detectada.

### 8.3 Cálculo de Desvio em Cents

```python
def cents(freq, ref):
    return 1200 * log₂(freq / ref)
```

**Por que cents?** A percepção musical é logarítmica:

- 1 Hz a mais em E2 (82 Hz) → desvio de ~21 cents (audível)
- 1 Hz a mais em E4 (330 Hz) → desvio de ~5 cents (quase imperceptível)

Cents são proporcionais ao desvio musical real, independente da frequência absoluta.

| Diferença | Cents |
|---|---|
| 1 semitom | 100 |
| Quinta justa | 700 |
| Oitava | 1200 |

**Tolerância de "afinado":** Configurável via `TOLERANCE_CENTS` (default: 15 cents). Afinadores profissionais utilizam 3–10 cents.

### 8.4 Classificação

```python
if abs(c) <= TOLERANCE_CENTS:  → "AFINADO"
elif c > 0:                     → "ALTO"  (corda esticada demais)
else:                            → "BAIXO" (corda frouxa demais)
```

---

## 9. Interface de Usuário

### 9.1 Display OLED

Layout de 4 áreas funcionais em 128×64 pixels:

```
┌──────────────────────────────────┐
│ E2          Corda 6a             │  ← Nota e número da corda
│ 82.4 Hz       Ref 82.4           │  ← Frequência medida vs referência
│         AFINADO                  │  ← Status de afinação
│         +3 cents                 │  ← Desvio numérico
│            │                     │
│      ──────█──────               │  ← Barra visual de afinação
└──────────────────────────────────┘
```

A barra visual:
- Linha vertical no centro = referência exata
- Bloco preenchido cresce para a esquerda (BAIXO) ou direita (ALTO) proporcionalmente ao desvio
- Bloco centrado quando dentro da tolerância (AFINADO)

### 9.2 Saída Serial

Cada ciclo com sinal válido produz uma linha:

```
E2 6a 82.4Hz ref=82.4 +3c AFINADO
A2 5a 112.5Hz ref=110.0 +39c ALTO
```

A cada 10 ciclos, o sistema também imprime um diagnóstico do ADC para auxiliar troubleshooting:

```
ADC min=31200 max=33800 pp=2600
```

### 9.3 LED de Status

| Estado | LED |
|---|---|
| Sistema ativo, com sinal | Aceso fixo |
| Sistema ativo, sem sinal | Aceso fixo |
| Sistema parado (Ctrl+C) | Apagado |

---

## 10. Parâmetros de Configuração

Todos os parâmetros são definidos como constantes no início do `main.py` e podem ser ajustados sem alterar a lógica:

| Parâmetro | Default | Função | Quando alterar |
|---|---|---|---|
| `SAMPLE_RATE` | 4000 Hz | Frequência de amostragem | Aumentar para detectar frequências > 1.5 kHz |
| `N` | 2048 | Tamanho da FFT | 1024 = mais rápido, menos preciso; 4096 = mais preciso, mais lento |
| `FREQ_MIN_HZ` | 60 | Limite inferior da busca | Reduzir para notas graves abaixo de E2 |
| `FREQ_MAX_HZ` | 500 | Limite superior da busca | Aumentar para notas/harmônicos acima de E4 |
| `ALPHA` | 0.4 | Coeficiente do filtro IIR | Reduzir (0.2–0.3) para ambientes ruidosos |
| `SIGNAL_THRESHOLD` | 200 | Detecção mínima de sinal | Calibrar com base no ruído ambiente do mic |
| `TOLERANCE_CENTS` | 15 | Margem de "afinado" | 5–10 para afinador exigente; 20–25 para ambiente ruidoso |

---

## 11. Estratégia de Testes

O projeto adota uma estratégia de teste híbrida executada no host PC:

### 11.1 Testes Unitários

Validação de funções isoladas com casos específicos: FFT de senoide, identificação de nota exata, conversão para cents, etc.

### 11.2 Testes de Integração

Validação do pipeline DSP completo com sinais sintéticos das 6 cordas mais 430 Hz (frequência de referência ABNT/ISO).

### 11.3 Mocks de Hardware

O módulo `tests/conftest.py` substitui `machine` e `framebuf` por implementações mock, permitindo importação e teste do `main.py` em CPython sem hardware real.

### 11.4 Execução

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

**Cobertura atual:** 32 testes cobrindo FFT, pipeline DSP completo, identificação de nota, conversão de cents e infraestrutura.

---

## 12. Análise de Desempenho

### 12.1 Uso de Memória

| Estrutura | Bytes |
|---|---|
| `samples` (uint16) | 4096 |
| `signal`, `filtered`, `re`, `im` (4×float) | 65 536 |
| `mag` (float, N/2) | 8192 |
| `tw_re`, `tw_im` (2×float, N/2) | 16 384 |
| `han` (float) | 8192 |
| `br` (uint16, N) | 4096 |
| Buffer OLED | 1024 |
| Driver, código, GC | ~10 000 |
| **Total** | **~117 KB** |

Com 520 KB de SRAM disponíveis, o sistema utiliza cerca de **22%** da memória.

### 12.2 Tempo por Ciclo

Medido empiricamente no Pico 2 a 150 MHz:

| Etapa | Tempo (ms) |
|---|---|
| Captura (2048 amostras @ 4 kHz) | 512 |
| Pipeline DSP (DC, IIR, Hanning) | ~80 |
| FFT 2048 pontos | ~250 |
| Detecção de pico + identificação | ~5 |
| Atualização do display I²C | ~30 |
| **Total por ciclo** | **~880 ms** |

### 12.3 Precisão de Frequência

- **Resolução do bin:** 1.95 Hz (= 4000/2048)
- **Com interpolação parabólica:** ~0.1 Hz em sinais limpos
- **Equivalente em cents @ E2 (82 Hz):** ~2 cents
- **Equivalente em cents @ E4 (330 Hz):** ~0.5 cents

---

## 13. Limitações Conhecidas

### 13.1 Latência

A captura de 2048 amostras a 4 kHz consome 512 ms. O ciclo total fica em torno de 1 segundo, o que torna o feedback responsivo mas não instantâneo. Reduzir N para 1024 corta a latência pela metade ao custo de menor resolução.

### 13.2 Sensibilidade a Ruído

O microfone analógico capta ruído ambiente, ventoinhas, vibrações da mesa, etc. O filtro IIR + Hanning + threshold de amplitude mitigam, mas não eliminam, falsas detecções em ambientes muito ruidosos.

### 13.3 Detecção de Harmônicos

Em alguns casos, o algoritmo pode bloquear no segundo harmônico em vez da fundamental, especialmente quando este é mais energético (corda excitada perto da ponte). Não há lógica de detecção de pitch baseada em sub-harmônicos (HPS — Harmonic Product Spectrum) implementada.

### 13.4 Dependência de Pino I²C

A pinagem do display OLED é definida no código (`SoftI2C(sda=Pin(16), scl=Pin(17))`). Mudanças físicas exigem alteração do código.

---

## 14. Referências

1. Cooley, J. W.; Tukey, J. W. **An Algorithm for the Machine Calculation of Complex Fourier Series.** Mathematics of Computation, vol. 19, 1965.
2. Smith, J. O. **Spectral Audio Signal Processing.** W3K Publishing, 2011. https://ccrma.stanford.edu/~jos/sasp/
3. Harris, F. J. **On the Use of Windows for Harmonic Analysis with the Discrete Fourier Transform.** Proceedings of the IEEE, 1978.
4. Raspberry Pi Foundation. **RP2350 Datasheet.** https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf
5. MicroPython Documentation. **machine — functions related to the hardware.** https://docs.micropython.org/en/latest/library/machine.html
6. SSD1306 Datasheet. **128×64 Dot Matrix OLED/PLED Segment/Common Driver with Controller.** Solomon Systech.
