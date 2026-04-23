# Afinador de Violão — Raspberry Pi Pico 2

Afinador de violão embarcado no Raspberry Pi Pico 2 (RP2350) com MicroPython.
Detecta a nota tocada via microfone e indica se está afinada, sustenida ou bemol.
Suporta saída via terminal serial (USB) e display OLED SSD1306.

## Hardware

- Raspberry Pi Pico 2 (RP2350)
- Microfone analógico conectado ao **ADC pino 26**
- LED onboard (pino 25) indica sistema ativo
- **(Opcional)** Display OLED SSD1306 128x64 I2C

## Conexão do Display OLED SSD1306

O display é **opcional**. Se não estiver conectado, o afinador funciona
normalmente pelo terminal serial.

### Pinagem

| Display OLED | Pico (GPIO) | Pino Físico | Descrição        |
|-------------|-------------|-------------|------------------|
| **SDA**     | GP4         | Pino 6      | Dados I2C        |
| **SCL**     | GP5         | Pino 7      | Clock I2C        |
| **VCC**     | 3V3(OUT)    | Pino 36     | Alimentação 3.3V |
| **GND**     | GND         | Pino 38     | Terra            |

### Diagrama de Conexão

```
    Display OLED SSD1306          Raspberry Pi Pico 2
    ┌──────────────┐              ┌──────────────────┐
    │              │              │                  │
    │  VCC ────────┼──────────────┤ 3V3(OUT) (pino 36)
    │  GND ────────┼──────────────┤ GND      (pino 38)
    │  SCL ────────┼──────────────┤ GP5      (pino 7)
    │  SDA ────────┼──────────────┤ GP4      (pino 6)
    │              │              │                  │
    └──────────────┘              │  GP26     (pino 31) ← Microfone
                                  │  LED      (pino 25) ← LED onboard
                                  └──────────────────┘
```

### Notas sobre o Display

- O endereço I2C padrão é **0x3C**. Alguns módulos usam 0x3D — se não funcionar, altere `OLED_ADDR` no código.
- O display usa I2C0 (GP4/GP5). Se precisar usar outros pinos, altere `OLED_SDA`, `OLED_SCL` e `OLED_I2C_ID` no código.
- Displays de 4 pinos (VCC, GND, SCL, SDA) são os mais comuns e compatíveis.
- Se o display não for detectado na inicialização, o código imprime um aviso e continua funcionando apenas pelo terminal serial.

## Arquivos

| Arquivo      | Descrição                                    |
|-------------|----------------------------------------------|
| `main.py`   | Código principal do afinador                 |
| `ssd1306.py`| Driver do display OLED (copiar junto ao Pico)|

## Como Usar

### Sem display (apenas terminal serial)

1. Copie `main.py` para o Pico:
   ```
   mpremote cp main.py :main.py
   ```
2. O LED acende ao iniciar
3. Toque uma corda do violão
4. Leia o resultado no terminal serial (USB)

### Com display OLED

1. Conecte o display conforme a pinagem acima
2. Copie os dois arquivos para o Pico:
   ```
   mpremote cp ssd1306.py :ssd1306.py
   mpremote cp main.py :main.py
   ```
3. Reinicie o Pico
4. O display mostra "AFINADOR VIOLAO Iniciando..."
5. Após calibração, mostra "Toque uma corda..."
6. Ao tocar, mostra a nota, frequência, status e uma barra visual de afinação

### O que aparece no display

```
┌────────────────────────┐
│ E2      Corda 6a       │  ← Nota e corda
│ 82.8Hz   Ref:82.4      │  ← Frequência detectada vs referência
│    * AFINADO *          │  ← Status
│ -[████|██  ]+           │  ← Barra visual (centro = afinado)
│     +0.8 cents          │  ← Desvio em cents
└────────────────────────┘
```

### Saída no terminal serial

A saída serial continua funcionando **sempre**, com ou sem display:

```
Corda 5a (A2) | 110.2 Hz | Ref 110.0 Hz |  ===  AFINADO (+3c)
Corda 6a (E2) | 84.5 Hz | Ref 82.4 Hz |  >>>  ALTO (+43c)
```

## Afinação Padrão

| Corda | Nota | Frequência |
|-------|------|-----------|
| 6ª | E2 | 82.41 Hz |
| 5ª | A2 | 110.00 Hz |
| 4ª | D3 | 146.83 Hz |
| 3ª | G3 | 196.00 Hz |
| 2ª | B3 | 246.94 Hz |
| 1ª | E4 | 329.63 Hz |

## Pipeline DSP

```
Microfone → ADC(26) → Filtro IIR Passa-Baixa → Janela de Hanning
→ FFT Cooley-Tukey → Interpolação Parabólica → Identificação de Nota
→ Terminal Serial + Display OLED
```

- Taxa de amostragem: 4000 Hz
- 1024 amostras por ciclo (resolução ~3.9 Hz)
- Filtro IIR 1ª ordem (corte 400 Hz)
- FFT radix-2 em MicroPython puro (sem ulab)
- Tolerância de afinação: ±10 cents

## Testes

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

98 testes unitários cobrindo todo o pipeline DSP. Rodam no PC com mocks do hardware.

## Requisitos

- MicroPython v1.27+ no Pico 2
- Python 3.10+ no PC para testes (pytest + hypothesis)
