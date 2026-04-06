# Plano de Implementação: Afinador de Guitarra

## Visão Geral

Implementação incremental do afinador de guitarra embarcado em MicroPython para Raspberry Pi Pico 2. O código principal reside em `main.py` (arquivo único). Testes rodam no host (PC) com `pytest` + `hypothesis` no diretório `tests/`.

## Tarefas

- [x] 1. Estrutura do projeto e constantes
  - [x] 1.1 Criar `main.py` com constantes do sistema e tabela de afinação
    - Definir `SAMPLE_RATE`, `N`, `ALPHA`, `SIGNAL_THRESHOLD`, `TUNING_TOLERANCE`, `CYCLE_DELAY_MS`, `BIN_MIN`, `BIN_MAX`
    - Definir `STANDARD_TUNING` com as 6 notas e frequências de referência
    - Adicionar imports necessários: `math`, `time`, `gc`, `array`
    - _Requisitos: 2.2, 2.3, 3.1, 5.1_

  - [x] 1.2 Implementar `setup()` com inicialização de hardware e pré-alocação de arrays
    - Configurar ADC no pino 26 e LED no pino 25 (acender LED)
    - Pré-alocar `samples` (`array('H', ...)`), `filtered`, `re`, `im`, `magnitudes`
    - Pré-calcular twiddle factors chamando `precompute_twiddles(N)`
    - Retornar dicionário ou tupla com todos os recursos inicializados
    - _Requisitos: 1.1, 1.2, 2.1_

  - [x] 1.3 Criar `tests/conftest.py` e estrutura de testes
    - Criar diretório `tests/`
    - Configurar `conftest.py` com fixtures compartilhadas (constantes, arrays de teste)
    - Garantir que `main.py` pode ser importado no host (mock de `machine` module)
    - _Requisitos: Design — Estratégia de Testes_

- [x] 2. Captura de áudio e detecção de sinal
  - [x] 2.1 Implementar `capture_samples(adc, samples, sample_rate, n)`
    - Ler N amostras do ADC com `read_u16()` e timing via `time.sleep_us()`
    - Calcular amplitude pico-a-pico (max - min)
    - Retornar `False` se amplitude < `SIGNAL_THRESHOLD`, `True` caso contrário
    - _Requisitos: 2.1, 2.2, 2.3, 8.1, 8.2_

  - [ ]* 2.2 Escrever teste de propriedade para detecção de sinal insuficiente
    - **Propriedade 7: Detecção de sinal insuficiente**
    - Gerar arrays com amplitude pico-a-pico < 500 e verificar retorno `False`
    - Gerar arrays com amplitude pico-a-pico ≥ 500 e verificar retorno `True`
    - **Valida: Requisito 8.1**

- [x] 3. Processamento do sinal (SignalProcessor)
  - [x] 3.1 Implementar `remove_dc_offset(samples, n)`
    - Calcular média aritmética das N amostras
    - Subtrair média de cada amostra, retornando lista de floats centralizada em zero
    - _Requisitos: Design — Componente SignalProcessor_

  - [x] 3.2 Implementar `low_pass_filter(samples, filtered, alpha, n)`
    - Filtro IIR de 1ª ordem: `y[i] = α·x[i] + (1-α)·y[i-1]`
    - Operar in-place no array `filtered` pré-alocado
    - _Requisitos: 3.1, 3.2, 3.3_

  - [ ]* 3.3 Escrever teste de propriedade para atenuação do filtro acima de 400 Hz
    - **Propriedade 1: Atenuação do filtro passa-baixa acima de 400 Hz**
    - Gerar senoides com frequência > 400 Hz, aplicar filtro, verificar atenuação > 50%
    - **Valida: Requisito 3.1**

  - [ ]* 3.4 Escrever teste de propriedade para preservação da banda passante (70–350 Hz)
    - **Propriedade 2: Preservação da banda passante do filtro (70–350 Hz)**
    - Gerar senoides com frequência entre 70 e 350 Hz, aplicar filtro, verificar perda < 30%
    - **Valida: Requisito 3.3**

  - [x] 3.5 Implementar `apply_hanning_window(filtered, n)`
    - Aplicar janela de Hanning in-place: `w[i] = 0.5 × (1 - cos(2πi/(N-1)))`
    - _Requisitos: Design — Componente SignalProcessor_

- [x] 4. Checkpoint — Verificar testes do processamento de sinal
  - Garantir que todos os testes passam, perguntar ao usuário se houver dúvidas.

- [x] 5. Motor FFT (FFTEngine)
  - [x] 5.1 Implementar `precompute_twiddles(n)`
    - Calcular `cos(2πk/N)` e `sin(2πk/N)` para k = 0..N/2-1
    - Retornar duas listas (parte real e imaginária)
    - _Requisitos: 4.2_

  - [x] 5.2 Implementar `bit_reverse(data_re, data_im, n)`
    - Permutação bit-reversal dos índices, operando in-place
    - _Requisitos: 4.2_

  - [x] 5.3 Implementar `fft(data_re, data_im, twiddle_re, twiddle_im, n)`
    - Butterfly operations iterativas em log₂(N) estágios usando twiddle factors pré-calculados
    - Operar in-place nos arrays real e imaginário
    - _Requisitos: 4.1, 4.2_

  - [x] 5.4 Implementar `compute_magnitudes(re, im, magnitudes, n)`
    - Calcular `|X[k]| = √(re[k]² + im[k]²)` para k = 0..N/2-1
    - _Requisitos: 4.1_

- [x] 6. Detecção de pico (PeakDetector)
  - [x] 6.1 Implementar `find_peak_frequency(magnitudes, sample_rate, n, bin_min, bin_max)`
    - Buscar bin de maior magnitude na faixa [bin_min, bin_max]
    - Aplicar interpolação parabólica para refinar a frequência
    - Retornar frequência interpolada em Hz
    - _Requisitos: 4.3_

  - [ ]* 6.2 Escrever teste de propriedade para precisão da detecção de frequência
    - **Propriedade 3: Precisão da detecção de frequência (FFT + pico)**
    - Gerar senoides com frequência f ∈ [70, 350] Hz, executar pipeline completo (DC offset → filtro → Hanning → FFT → pico), verificar |f_estimada - f| ≤ 2 Hz
    - **Valida: Requisitos 4.1, 4.3**

- [x] 7. Checkpoint — Verificar testes do pipeline DSP
  - Garantir que todos os testes passam, perguntar ao usuário se houver dúvidas.

- [x] 8. Identificação de nota e feedback (NoteIdentifier)
  - [x] 8.1 Implementar `identify_note(frequency)`
    - Comparar frequência com as 6 referências de `STANDARD_TUNING`
    - Retornar tupla (nome_nota, frequência_referência) com menor diferença absoluta
    - _Requisitos: 5.1, 5.2_

  - [ ]* 8.2 Escrever teste de propriedade para identificação da nota mais próxima
    - **Propriedade 4: Identificação da nota mais próxima**
    - Gerar frequências em [70, 350] Hz, verificar que a nota retornada é a de menor diferença absoluta
    - **Valida: Requisitos 5.1, 5.2**

  - [x] 8.3 Implementar `get_tuning_status(frequency, ref_frequency)`
    - Calcular desvio e classificar: "Afinado" (|d| ≤ 1.0), "Sustenido (Sharp)" (d > 1.0), "Bemol (Flat)" (d < -1.0)
    - Retornar tupla (status, desvio)
    - _Requisitos: 6.1, 6.2, 6.3_

  - [ ]* 8.4 Escrever teste de propriedade para classificação do status de afinação
    - **Propriedade 5: Classificação correta do status de afinação**
    - Gerar pares (frequência, referência), verificar classificação correta conforme tolerância de 1.0 Hz
    - **Valida: Requisitos 6.1, 6.2, 6.3**

  - [x] 8.5 Implementar `format_output(note, frequency, ref_freq, status, deviation)`
    - Formatar string: `Nota: A2 | Freq: 111.5 Hz | Ref: 110.0 Hz | Status: Sustenido (+1.5 Hz)`
    - _Requisitos: 6.4_

  - [ ]* 8.6 Escrever teste de propriedade para completude do formato de saída
    - **Propriedade 6: Completude do formato de saída**
    - Gerar combinações válidas de (nota, freq, ref, status, desvio), verificar que a string contém todos os 5 campos
    - **Valida: Requisito 6.4**

- [x] 9. Loop principal e integração
  - [x] 9.1 Implementar `main_loop()` integrando todo o pipeline
    - Chamar `setup()` para inicialização
    - Loop contínuo: captura → verificação de sinal → remoção DC → filtro → Hanning → FFT → magnitudes → pico → nota → status → print
    - Exibir "Sem sinal detectado" quando sinal insuficiente
    - Envolver em `try/except` com log de erro via `print()`
    - `gc.collect()` e `time.sleep_ms(CYCLE_DELAY_MS)` no `finally`
    - _Requisitos: 7.1, 7.2, 7.3, 8.1, 8.2_

  - [x] 9.2 Adicionar ponto de entrada `if __name__ == "__main__"`
    - Chamar `main_loop()` para execução no Pico
    - _Requisitos: 7.1_

  - [ ]* 9.3 Escrever testes de integração do pipeline completo
    - Testar pipeline end-to-end com sinais senoidais conhecidos (ex.: 110 Hz → A2, 329.63 Hz → E4)
    - Verificar saída formatada corretamente
    - Verificar tratamento de sinal insuficiente
    - _Requisitos: 2.1, 4.1, 5.1, 6.4, 8.1_

- [x] 10. Checkpoint final — Validação completa
  - Garantir que todos os testes passam, perguntar ao usuário se houver dúvidas.

## Notas

- Tarefas marcadas com `*` são opcionais e podem ser puladas para um MVP mais rápido
- Cada tarefa referencia requisitos específicos para rastreabilidade
- Checkpoints garantem validação incremental
- Testes de propriedade validam propriedades universais de corretude
- Testes unitários validam exemplos específicos e casos de borda
- Todo código DSP deve ser Python puro (sem numpy, sem ulab)
- Arrays devem ser pré-alocados no `setup()` — sem alocações no loop principal
- Testes rodam no host (PC) com `pytest` + `hypothesis`, não no Pico
