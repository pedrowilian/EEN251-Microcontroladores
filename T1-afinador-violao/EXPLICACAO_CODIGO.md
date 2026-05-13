# Afinador de Violão — Explicação Detalhada

Documento de estudo do software do afinador embarcado no Raspberry Pi Pico 2.

## 1. Visão Geral do Funcionamento

O afinador tem um trabalho conceitualmente simples mas tecnicamente complexo:

> Pegar o som de uma corda do violão, descobrir qual a frequência fundamental dela e dizer se está afinada.

O fluxo completo é:

```
Microfone → ADC → Filtro → FFT → Detecção de pico → Identificação → Display/Serial
   (analógico)  (digital)  (limpa) (espectro)  (frequência)    (qual nota?)
```

Cada etapa será explicada em detalhe abaixo.

---

## 2. Conceitos Fundamentais

### 2.1 Sinal Analógico vs Digital

O som é uma **onda contínua de pressão do ar**. O microfone converte essa onda em uma **onda contínua de tensão elétrica**. Mas o microcontrolador só consegue trabalhar com **números discretos**.

O **ADC (Analog-to-Digital Converter)** mede a tensão em intervalos regulares e converte em números. Cada medição é uma **amostra**.

### 2.2 Teorema de Nyquist

Para representar fielmente um sinal de frequência `f`, é preciso amostrar a pelo menos `2f`. Ou seja, se queremos detectar até 500 Hz, precisamos amostrar a pelo menos 1000 Hz.

**Por que isso importa?** Se você amostra muito devagar, frequências altas viram "alias" e aparecem como frequências baixas falsas. É como filmar uma roda de carro: dependendo da velocidade do filme vs da roda, ela parece girar pra trás.

### 2.3 Frequência fundamental e harmônicos

Quando você toca uma corda, ela vibra na **frequência fundamental** (a nota que você percebe) e também em **harmônicos** (múltiplos inteiros da fundamental).

Exemplo: corda A2 = 110 Hz
- Fundamental: 110 Hz (nota A2)
- 2º harmônico: 220 Hz
- 3º harmônico: 330 Hz
- ...

O afinador precisa identificar **apenas a fundamental**, ignorando os harmônicos.

---

## 3. Constantes de Configuração

```python
SAMPLE_RATE = 4000          # Hz
N = 2048                    # amostras por FFT
SAMPLE_INTERVAL_US = 250    # microssegundos entre amostras
FREQ_RES = 1.95             # Hz (resolução)
FREQ_MIN_HZ = 60            # busca a partir de 60 Hz
FREQ_MAX_HZ = 500           # busca até 500 Hz
ALPHA = 0.4                 # filtro IIR
SIGNAL_THRESHOLD = 200      # mínimo pra considerar som
TOLERANCE_CENTS = 15        # margem pra "AFINADO"
```

### 3.1 SAMPLE_RATE
Quantas vezes por segundo o ADC lê o sinal do microfone.

- 4000 Hz = capacidade de detectar até 2000 Hz (Nyquist)
- Mais alto = melhor resolução temporal, mas gasta mais CPU
- Para violão (até ~330 Hz fundamental + alguns harmônicos), 4000-8000 Hz é suficiente

### 3.2 N (tamanho da FFT)
Quantas amostras a FFT analisa de uma vez. **DEVE ser potência de 2** (512, 1024, 2048, 4096) — é requisito do algoritmo.

| N | RAM | Resolução (com SR=4000) |
|---|---|---|
| 512 | 11 KB | 7.8 Hz |
| 1024 | 22 KB | 3.9 Hz |
| 2048 | 43 KB | 1.95 Hz |
| 4096 | 86 KB | 0.97 Hz |

**Trade-off:** N maior = melhor resolução de frequência, mas demora mais pra capturar (N/SR segundos = janela de tempo).

### 3.3 SAMPLE_INTERVAL_US
Tempo entre cada leitura do ADC, em microssegundos.

`SAMPLE_INTERVAL_US = 1_000_000 / SAMPLE_RATE`

Com SR=4000: 250 µs (1ms / 4 = 0.25ms = 250µs).

### 3.4 FREQ_RES (resolução de frequência)
A FFT divide o espectro em "bins" (caixinhas). Cada bin tem largura `FREQ_RES = SAMPLE_RATE / N`.

Com SR=4000 e N=2048: cada bin = 1.95 Hz.

Isso significa que a FFT **só consegue distinguir frequências separadas por pelo menos 1.95 Hz**. Frequências dentro do mesmo bin são confundidas.

### 3.5 FREQ_MIN_HZ e FREQ_MAX_HZ
Faixa de busca da FFT. O algoritmo só procura o pico nessa faixa, ignorando ruído fora dela.

Para violão: 60-500 Hz cobre todas as cordas (E2=82 a E4=329) com margem.

### 3.6 ALPHA (filtro IIR)
Coeficiente do filtro passa-baixa. Valor entre 0 e 1.

- α próximo de 0 = filtro muito agressivo (suaviza muito, mas atrasa e reduz amplitude)
- α próximo de 1 = filtro fraco (deixa passar quase tudo)
- α = 0.4 é um meio-termo

### 3.7 SIGNAL_THRESHOLD
Amplitude mínima pico-a-pico do sinal pra considerar que tem som relevante. Se o sinal é mais fraco que isso, é considerado silêncio/ruído e ignorado.

### 3.8 TOLERANCE_CENTS
Quanto a frequência pode desviar da nota de referência e ainda ser considerada "afinada".

**O que é cents?** Unidade musical: 1 semitom = 100 cents. Afinadores profissionais usam ±5 a ±10 cents. Para ambiente ruidoso, 15 cents é razoável.

---

## 4. Pipeline de Processamento (DSP)

Cada ciclo do afinador executa esses passos em sequência:

### 4.1 Captura (`capture`)

```python
def capture(adc, samples, n):
    for i in range(n):
        samples[i] = adc.read_u16()
        time.sleep_us(SAMPLE_INTERVAL_US)
```

Lê N amostras do ADC com timing preciso. Com N=2048 e SR=4000, demora 2048/4000 = **0.512 segundos** pra capturar uma janela.

`adc.read_u16()` retorna valor de 0 a 65535 representando a tensão (0V → 0, 3.3V → 65535).

### 4.2 Detecção de Sinal (`get_pp`)

```python
def get_pp(samples, n):
    mn = 65535; mx = 0
    for i in range(n):
        v = samples[i]
        if v < mn: mn = v
        if v > mx: mx = v
    return mn, mx, mx - mn
```

Calcula a amplitude pico-a-pico (max - min). Se for menor que `SIGNAL_THRESHOLD`, considera silêncio e pula o resto do processamento.

### 4.3 Remoção de DC Offset

```python
total = 0
for i in range(n):
    total += samples[i]
mean = total / n
for i in range(n):
    signal[i] = samples[i] - mean
```

O sinal do microfone tem um **offset DC** (~32768, metade do range). A FFT precisa do sinal **centrado em zero**, senão fica um pico gigante no bin 0 (DC) que atrapalha tudo.

Subtrair a média de todas as amostras centraliza o sinal.

### 4.4 Filtro Passa-Baixa (IIR)

```python
filtered[0] = ALPHA * signal[0]
for i in range(1, n):
    filtered[i] = ALPHA * signal[i] + (1 - ALPHA) * filtered[i - 1]
```

Filtro IIR de 1ª ordem. A fórmula é:

```
y[i] = α·x[i] + (1-α)·y[i-1]
```

Cada amostra de saída é uma mistura entre:
- A amostra atual (peso α)
- A amostra anterior já filtrada (peso 1-α)

Isso suaviza o sinal, atenuando frequências altas. **Reduz ruído de alta frequência** que poderia confundir a FFT.

#### 4.4.1 O que significa "IIR"

**IIR** = **Infinite Impulse Response** (Resposta ao Impulso Infinita).

É uma classe de filtro digital que, ao receber um único pulso na entrada, produz uma saída que **decai mas teoricamente nunca chega a zero** — daí o nome "infinita".

A característica que define um filtro IIR é simples: **ele usa os próprios valores anteriores da saída pra calcular o valor atual**. É um filtro com **memória recursiva**.

#### 4.4.2 Intuição visual

Imagine que você está medindo a temperatura ambiente, e ela oscila bastante por causa de uma corrente de ar:

```
Entrada bruta (com ruído):  22, 28, 19, 25, 21, 27, 20, 24, ...
```

Aplicando α=0.3 ao filtro IIR:

```
y[0] = 0.3 · 22                  = 6.6
y[1] = 0.3 · 28 + 0.7 · 6.6      = 13.0
y[2] = 0.3 · 19 + 0.7 · 13.0     = 14.8
y[3] = 0.3 · 25 + 0.7 · 14.8     = 17.9
y[4] = 0.3 · 21 + 0.7 · 17.9     = 18.8
y[5] = 0.3 · 27 + 0.7 · 18.8     = 21.3
...
```

A saída sobe **gradualmente** até estabilizar perto da média real, **suavizando os picos**. É como ter uma "inércia" que ignora variações bruscas.

#### 4.4.3 O que ele faz na prática

**Atenua frequências altas (passa-baixa):** variações **rápidas** (alta frequência) na entrada não conseguem mudar a saída rápido o suficiente, porque a saída está sempre presa em `(1-α)` do valor anterior. Essas variações são **atenuadas**.

Variações **lentas** (baixa frequência) atravessam o filtro tranquilamente, porque dá tempo da saída acompanhar.

**Frequência de corte:** a frequência onde o filtro atenua o sinal pela metade da potência (-3 dB). Relação entre α e fc:

```
α = dt / (RC + dt)
```

Onde:
- `dt = 1 / SAMPLE_RATE` (período de amostragem)
- `RC = 1 / (2π · fc)` (constante de tempo)

No nosso caso (fs = 4000 Hz, α = 0.4):

```
dt = 1/4000 = 0.00025 s
α = 0.4 → RC ≈ 0.000375 s
fc = 1 / (2π · RC) ≈ 425 Hz
```

O filtro atenua tudo acima de ~425 Hz, mantendo intacto o que está abaixo.

#### 4.4.4 Por que usar no afinador

O microfone capta **muito mais que a vibração da corda**:

| Fonte de ruído | Frequência típica |
|---|---|
| Cliques eletrônicos | 1-20 kHz |
| Ventoinha de PC | 100-500 Hz fundamental + harmônicos altos |
| Hum elétrico (60 Hz e harmônicos) | 60, 120, 180 Hz |
| Sibilância do mic | 5-15 kHz |
| Ruído branco do circuito | distribuído em todo o espectro |

A faixa de interesse do violão é **82–330 Hz** (E2 a E4), com talvez harmônicos até 1 kHz. Tudo acima disso é **lixo** que pode confundir a FFT.

O filtro IIR passa-baixa funciona como um "porteiro": deixa entrar as frequências da corda e bloqueia o resto.

#### 4.4.5 Trade-offs do parâmetro α

| α | Comportamento | Quando usar |
|---|---|---|
| **0.1** | Filtro muito agressivo, fc baixíssimo | Ambiente extremamente ruidoso, sinal forte |
| **0.3** | Agressivo, atenua bem alta freq | Estúdio com PC ruidoso |
| **0.4** | Equilibrado (nosso default) | Uso geral |
| **0.6** | Suave, deixa passar mais ruído | Ambiente silencioso, sinal fraco |
| **1.0** | Sem filtro (saída = entrada) | Desabilita o filtro |

**Trade-off central:** α menor filtra mais ruído, mas também **atrasa a resposta** (latência) e **reduz amplitude do sinal útil**.

#### 4.4.6 IIR vs FIR — por que escolhemos IIR

Existe outra família de filtros: **FIR** (Finite Impulse Response). Comparação:

| Característica | IIR (1ª ordem) | FIR (média móvel) |
|---|---|---|
| Memória usada | 1 valor (`y[n-1]`) | N valores (N=tamanho da janela) |
| Operações por amostra | 2 multiplicações + 1 soma | N multiplicações + N somas |
| Resposta em frequência | Assimétrica (decaimento exponencial) | Linear, simétrica |
| Estabilidade | Pode oscilar se mal projetado | Sempre estável |
| Distorção de fase | Não-linear | Linear |

Pro nosso caso (microcontrolador com pouca CPU), o IIR ganha disparado:
- ✅ Quase zero de RAM (1 valor em memória)
- ✅ ~3x mais rápido que FIR equivalente
- ✅ 1ª ordem é simples e estável

Distorção de fase não importa pra detecção de frequência (a FFT só olha amplitude).

#### 4.4.7 Por que o peso (1 - α) na amostra anterior?

Os dois pesos da fórmula somam **exatamente 1**:

```
α + (1 - α) = 1
```

Isso não é coincidência. A justificativa tem três camadas:

**(a) Razão prática — conservação da escala**

Quando os pesos somam 1, a saída fica **na mesma escala** da entrada. Se você joga um sinal constante `x = 5`, a saída converge pra `y = 5`, não pra 2.5 ou 10.

Exemplo com α = 0.4:

```
y[0] = 0.4 · 5 = 2.0
y[1] = 0.4 · 5 + 0.6 · 2.0 = 3.2
y[2] = 0.4 · 5 + 0.6 · 3.2 = 3.92
y[3] = 0.4 · 5 + 0.6 · 3.92 = 4.352
...
y[∞] = 5  ← converge pra entrada
```

Se os pesos não somassem 1, a saída convergiria pra um valor diferente da entrada — o que seria errado pra um filtro passa-baixa. Você quer atenuar variações, não mudar a média.

**Intuição:** se você dedica fração `α` à entrada nova, sobra `(1 - α)` pra "lembrar" do passado. É como um copo cheio: pra adicionar 30% de água nova, precisa derramar 30% da antiga.

**(b) Razão matemática — derivação a partir do circuito RC analógico**

O filtro IIR de 1ª ordem é a **versão digital** do circuito RC analógico clássico:

```
   Vin ──[R]──┬──── Vout
               │
              ===  C
               │
              GND
```

A equação diferencial desse circuito é:

```
Vout(t) + RC · dVout/dt = Vin(t)
```

Discretizando com diferenças finitas (Euler):

```
dVout/dt ≈ (Vout[n] - Vout[n-1]) / dt
```

onde `dt = 1 / SAMPLE_RATE`. Substituindo e isolando `Vout[n]`:

```
Vout[n] = [dt / (dt+RC)] · Vin[n] + [RC / (dt+RC)] · Vout[n-1]
```

Definindo `α = dt / (dt + RC)`, o coeficiente do `Vout[n-1]` se torna:

```
RC / (dt + RC) = (dt + RC - dt) / (dt + RC)
              = 1 - α
```

O fator `(1 - α)` **emerge naturalmente** da matemática do circuito RC discretizado. Não é uma escolha arbitrária — é o que aparece quando você converte o filtro analógico contínuo pro domínio digital.

**(c) Razão física — balanço de energia**

A regra de ouro pra qualquer mistura ponderada conservativa: **as contribuições têm que somar 100%**. Senão:

- Soma > 1 → cria energia do nada → sistema **instável** (oscila ou explode)
- Soma < 1 → perde energia → sinal **vaza para zero** ao longo do tempo

Por isso `(1-α)`: é o **complemento** que garante que toda a "energia" da entrada seja preservada na saída ao longo do tempo.

**Visualizando o efeito do α:**

| α | Peso entrada | Peso memória | Comportamento |
|---|---|---|---|
| 0.1 | 10% | 90% | Muito "preguiçoso", responde devagar, suaviza muito |
| 0.4 | 40% | 60% | Equilibrado (nosso caso) |
| 0.7 | 70% | 30% | Responsivo, suaviza pouco |
| 1.0 | 100% | 0% | Sem filtro, saída = entrada |
| 0.0 | 0% | 100% | Saída congelada no estado inicial |

**Regra geral:** pra **qualquer** filtro digital de 1ª ordem com ganho unitário em DC (que passa frequências baixas sem alterar amplitude), os coeficientes da entrada e da memória **precisam** somar 1.

Se você inventar um filtro com `y[n] = 0.4·x[n] + 0.7·y[n-1]`, ele vai **explodir** (saída cresce sem limite) porque a soma é 1.1, então cada iteração amplifica o sinal em 10%. Já com `0.4·x[n] + 0.5·y[n-1]`, o sinal **decai** porque soma 0.9.

A única configuração estável e fiel à entrada é exatamente `α + (1-α) = 1`.

#### 4.4.8 Por que vem ANTES da FFT

A ordem importa:

```
1. ADC capture       → sinal cru com ruído
2. DC offset removal → sinal centrado em zero
3. IIR filter        → sinal limpo (alta freq atenuada) ← AQUI
4. Hanning window    → bordas suavizadas
5. FFT               → espectro
```

Se filtrasse **depois** da FFT, o ruído já teria contaminado o espectro. Filtrando **antes**, a FFT recebe um sinal mais limpo e produz picos mais nítidos.

#### 4.4.9 Resumo

> O filtro IIR é um suavizador inteligente que mistura a entrada nova (com peso α) e a saída anterior (com peso 1-α), atenuando frequências acima de ~425 Hz pra que o ADC envie um sinal mais limpo pra FFT analisar. O peso (1-α) emerge naturalmente da discretização do circuito RC e garante que a soma dos pesos seja 1, mantendo o filtro estável e com ganho unitário em DC.

### 4.5 Janela de Hanning

```python
for i in range(n):
    re[i] = filtered[i] * han[i]
```

Onde `han[i] = 0.5 * (1 - cos(2π·i / (N-1)))`.

A janela de Hanning multiplica o sinal por uma curva em forma de sino: zero nas bordas, máximo no centro.

**Por quê?** A FFT assume que o sinal é **periódico**. Mas nosso pedaço de N amostras tem cortes abruptos no início e fim. Esses cortes geram **vazamento espectral** (spectral leakage) — energia que vaza pra outros bins e cria picos falsos.

A janela suaviza as bordas, tornando o sinal "quase periódico" e reduzindo o vazamento drasticamente.

### 4.6 FFT — Transformada Rápida de Fourier (CORE!)

**Esta é a parte mais importante de toda a explicação.**

#### 4.6.1 O que é a FFT?

A **Transformada de Fourier** é uma operação matemática que **decompõe um sinal no tempo em suas frequências componentes**.

Imagine que você tem um acorde tocando: vários sons misturados. Seu cérebro consegue identificar cada nota individualmente — é isso que a Fourier faz matematicamente.

**Entrada:** N amostras no domínio do tempo (`samples[0..N-1]`)
**Saída:** N "bins" no domínio da frequência (`re[0..N-1]`, `im[0..N-1]`)

Cada bin `k` representa "quanta energia há na frequência `k * SAMPLE_RATE / N`".

#### 4.6.2 Por que usamos FFT?

Sem FFT, como você descobriria a frequência fundamental de uma onda complexa? Tentar contar zero-crossings? Não funciona com ruído. Detectar picos? Inviável.

A FFT resolve esse problema **diretamente**: ela mostra todo o espectro de frequências do sinal. Aí basta procurar onde está o pico = frequência fundamental.

#### 4.6.3 Algoritmo Cooley-Tukey radix-2 DIT

A DFT (Transformada Discreta de Fourier) ingênua faz N² operações. Para N=2048, isso é ~4 milhões de operações — inviável em microcontrolador.

A **FFT** (Fast Fourier Transform) faz a mesma coisa em N·log₂(N) operações. Para N=2048, isso é ~22 mil operações — **180x mais rápido**.

O algoritmo Cooley-Tukey funciona dividindo recursivamente:
1. **Bit-reversal:** reordena as amostras (índice 1=001 vira 100=4, etc.)
2. **Butterfly operations:** combina pares de amostras com "twiddle factors" (rotações no plano complexo)

```python
def fft(re, im, tw_re, tw_im, br, n):
    # 1. Bit-reverse
    for i in range(n):
        j = br[i]
        if i < j:
            re[i], re[j] = re[j], re[i]
            im[i], im[j] = im[j], im[i]
    
    # 2. Butterflies
    size = 2
    while size <= n:
        hs = size >> 1
        step = n // size
        for i in range(0, n, size):
            for k in range(hs):
                # Multiplicação complexa com twiddle factor
                tr = re[j2] * wr - im[j2] * wi
                ti2 = re[j2] * wi + im[j2] * wr
                # Butterfly: combina pares
                re[j2] = re[j] - tr
                im[j2] = im[j] - ti2
                re[j] = re[j] + tr
                im[j] = im[j] + ti2
        size <<= 1
```

#### 4.6.4 Twiddle factors

São pré-calculados uma vez no início:

```python
def precompute_twiddles(n):
    for k in range(n // 2):
        a = 2π * k / n
        tw_re[k] = cos(a)
        tw_im[k] = sin(a)
```

Calcular `cos`/`sin` é caro. Pré-calcular em tabela e reutilizar economiza muito tempo.

### 4.7 Magnitudes

Após a FFT, cada bin tem uma parte real e uma imaginária (porque a Fourier opera com números complexos). A **magnitude** representa a energia naquela frequência:

```python
mag[k] = sqrt(re[k]² + im[k]²)
```

Só calculamos para `k` na faixa `[BIN_MIN, BIN_MAX]` por economia.

### 4.8 Detecção de Pico

```python
pk = BIN_MIN
pm = mag[BIN_MIN]
for k in range(BIN_MIN + 1, BIN_MAX + 1):
    if mag[k] > pm:
        pm = mag[k]
        pk = k
```

Encontra o bin com maior magnitude na faixa de busca. Esse é o **pico** = frequência fundamental.

### 4.9 Interpolação Parabólica

```python
a = mag[pk - 1]
b = mag[pk]
c = mag[pk + 1]
d = a - 2.0 * b + c
p = 0.5 * (a - c) / d
return (pk + p) * FREQ_RES
```

A frequência real raramente cai exatamente em um bin. A interpolação parabólica usa os bins vizinhos (esquerda, centro, direita) pra estimar o "verdadeiro" pico **entre** os bins.

Se a forma é uma parábola perfeita, o vértice fica em:
```
p = 0.5 * (a - c) / (a - 2b + c)
```

Isso pode melhorar a precisão de 1.95 Hz (resolução do bin) para frações de Hz.

---

## 5. Identificação da Nota

### 5.1 `identify(freq)`

```python
def identify(freq):
    bi = 0
    bd = abs(freq - TUNING[0][1])
    for i in range(1, 6):
        d = abs(freq - TUNING[i][1])
        if d < bd:
            bd = d
            bi = i
    return bi
```

Compara a frequência detectada com as 6 frequências da afinação padrão (E2, A2, D3, G3, B3, E4) e retorna o **índice da mais próxima**.

### 5.2 `cents(freq, ref)` — Conversão para cents

```python
def cents(freq, ref):
    return 1200.0 * math.log(freq / ref) / LOG2
```

Fórmula matemática: `cents = 1200 · log₂(freq / ref)`

**Por que cents e não Hz?** Porque a percepção musical é **logarítmica**:
- 1 Hz a mais em 80 Hz é uma diferença grande (aprox. 21 cents)
- 1 Hz a mais em 330 Hz é quase imperceptível (5 cents)

Cents são **proporcionais ao desvio musical real**, independente da nota.

| Diferença | Significado |
|---|---|
| 1 semitom | 100 cents |
| Quinta justa | 700 cents |
| Oitava | 1200 cents |
| Afinador profissional | ±5 a ±10 cents |
| "Afinado" pra orelha humana | até ±20 cents |

### 5.3 Status de afinação

```python
if abs(c) <= TOLERANCE_CENTS:
    st = "AFINADO"
elif c > 0:
    st = "ALTO"      # corda esticada demais
else:
    st = "BAIXO"     # corda frouxa demais
```

---

## 6. Display OLED

### 6.1 SSD1306 — comunicação I2C

O OLED é controlado por chip SSD1306 que aceita comandos via I2C:
- Endereço I2C do display: `0x3C`
- Cada comando começa com byte de controle `0x80` (comando) ou `0x40` (dado)

### 6.2 Framebuf

`framebuf.FrameBuffer` é uma biblioteca do MicroPython que cria um "buffer de pixels" na memória. Você desenha nele com:
- `fill(0/1)` — preto/branco
- `text(s, x, y, c)` — texto
- `pixel(x, y, c)` — um pixel
- `hline`, `vline` — linhas
- `fill_rect(x, y, w, h, c)` — retângulo preenchido

Depois `oled.show()` envia o buffer todo de uma vez pro display via I2C.

### 6.3 Layout do display

```
┌──────────────────────────┐
│ A2      Corda 5a         │  linha 0  (página 0)
│ 110.2 Hz   Ref 110.0     │  linha 14 (página 1-2)
│       AFINADO            │  linha 28 (página 3)
│       +3 cents           │  linha 40 (página 5)
│                          │
│       |    █             │  linha 54 (página 6-7) — barra
└──────────────────────────┘
   0          64         127
```

A barra visual mostra:
- Linha vertical no centro = referência (afinado)
- Bloco preenchido = quanto está desafinado e em qual direção

---

## 7. Loop Principal

```python
while True:
    capture(...)              # 1. Lê som
    mn, mx, pp = get_pp(...)  # 2. Verifica amplitude
    
    if pp < SIGNAL_THRESHOLD:
        # silêncio — espera
    else:
        freq = process(...)    # 3. Pipeline DSP completo
        if freq > 0.0:
            idx = identify(freq)
            c = cents(freq, ref)
            # 4. Atualiza display
            # 5. Imprime no serial
    
    gc.collect()              # 6. Libera memória
    time.sleep_ms(50)
```

### 7.1 `gc.collect()`
MicroPython tem garbage collector automático, mas em loops apertados é recomendado chamar manualmente pra evitar fragmentação de memória.

### 7.2 `try/finally` cleanup
Quando o usuário aperta Ctrl+C ou para o script:
```python
finally:
    led.value(0)   # apaga LED
    oled.off()     # limpa e desliga display
```

---

## 8. Por que cada decisão técnica?

| Decisão | Motivo |
|---|---|
| FFT em vez de zero-crossing | Robusto a ruído, funciona com sinais complexos |
| Filtro IIR antes da FFT | Reduz ruído de alta frequência |
| Janela de Hanning | Evita vazamento espectral |
| Interpolação parabólica | Precisão sub-bin sem aumentar N |
| Pré-alocação de arrays | Evita alocação de memória no loop (causa crash) |
| Twiddle factors pré-calculados | cos/sin são caros, calcular uma vez só |
| Cents em vez de Hz | Percepção musical é logarítmica |
| `array.array('H')` para amostras | Usa 2 bytes por amostra em vez de 28 (lista de ints) |

---

## 9. Glossário rápido

- **ADC**: Analog-to-Digital Converter, converte tensão em número
- **DSP**: Digital Signal Processing
- **FFT**: Fast Fourier Transform
- **Bin**: caixinha de frequência da FFT
- **Twiddle factor**: fator de rotação (cos+j·sin) usado nas butterflies da FFT
- **DC offset**: tensão média do sinal (precisa ser removida antes da FFT)
- **Spectral leakage**: vazamento de energia entre bins, causado por descontinuidades nas bordas
- **IIR**: Infinite Impulse Response, tipo de filtro que usa saídas anteriores
- **Cent**: 1/100 de semitom, unidade de desvio musical
- **Nyquist**: frequência máxima detectável = SAMPLE_RATE / 2
- **Pico-a-pico (pp)**: max - min do sinal, mede amplitude

---

## 10. Como ajustar para seu setup

Se algo não funciona bem, ajuste essas constantes na ordem:

1. **Ruído alto?** Aumente `SIGNAL_THRESHOLD` (200 → 500 → 1000)
2. **Sinal fraco?** Diminua `SIGNAL_THRESHOLD` (200 → 100 → 50)
3. **Frequência errada?** Verifique `FREQ_MAX_HZ` (precisa ser > maior frequência testada)
4. **Detecção instável?** Aumente N (1024 → 2048) — melhor resolução
5. **Lento demais?** Diminua N (2048 → 1024) — captura mais rápido
6. **Detectando harmônico em vez de fundamental?** Diminua `FREQ_MAX_HZ` ou aumente `ALPHA`

Olhe sempre o serial: `ADC min=X max=Y pp=Z` te diz exatamente o que tá chegando do mic.
