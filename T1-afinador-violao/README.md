# Afinador de Violão — Raspberry Pi Pico 2

Afinador de violão embarcado no Raspberry Pi Pico 2 (RP2350) com MicroPython.
Detecta a nota tocada via microfone e indica se está afinada, sustenida ou bemol.

## Hardware

- Raspberry Pi Pico 2 (RP2350)
- Microfone analógico conectado ao **ADC pino 26**
- LED onboard (pino 25) indica sistema ativo

## Como Usar

1. Copie `main.py` para o Pico via Thonny ou `mpremote cp main.py :main.py`
2. O LED acende ao iniciar
3. Toque uma corda do violão
4. Leia o resultado no terminal serial (USB)

```
Nota: A2 | Freq: 110.2 Hz | Ref: 110.0 Hz | Status: Afinado (+0.2 Hz)
Nota: E2 | Freq: 84.5 Hz | Ref: 82.4 Hz | Status: Sustenido (+2.1 Hz)
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
```

- Taxa de amostragem: 4000 Hz
- 1024 amostras por ciclo (resolução ~3.9 Hz)
- Filtro IIR 1ª ordem (corte 400 Hz)
- FFT radix-2 em MicroPython puro (sem ulab)
- Tolerância de afinação: ±1 Hz

## Testes

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

98 testes unitários cobrindo todo o pipeline DSP. Rodam no PC com mocks do hardware.

## Requisitos

- MicroPython v1.27+ no Pico 2
- Python 3.10+ no PC para testes (pytest + hypothesis)
