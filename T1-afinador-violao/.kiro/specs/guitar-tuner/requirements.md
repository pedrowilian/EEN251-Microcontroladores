# Documento de Requisitos — Afinador de Guitarra

## Introdução

Sistema embarcado de afinador de guitarra executado em um Raspberry Pi Pico 2 com MicroPython. O sistema captura o sinal de áudio de um microfone conectado ao pino ADC 26, processa o sinal com filtro passa-baixa e FFT para detectar a frequência fundamental, e fornece feedback indicando se a corda está afinada, sustenida (sharp) ou bemol (flat) em relação à afinação padrão (E2, A2, D3, G3, B3, E4).

## Glossário

- **Sistema_Afinador**: O software principal executado no Raspberry Pi Pico 2 que realiza a captura, processamento e análise do sinal de áudio.
- **ADC**: Conversor Analógico-Digital (Analog-to-Digital Converter) do Raspberry Pi Pico 2, utilizado no pino 26 para leitura do microfone.
- **LED_Onboard**: LED integrado na placa do Raspberry Pi Pico 2 (pino 25), utilizado como indicador visual de status.
- **Filtro_Passa_Baixa**: Filtro digital aplicado ao sinal de áudio para atenuar frequências acima da faixa de interesse da guitarra.
- **FFT**: Transformada Rápida de Fourier (Fast Fourier Transform), algoritmo utilizado para converter o sinal do domínio do tempo para o domínio da frequência.
- **Frequencia_Fundamental**: A frequência dominante detectada no sinal de áudio, correspondente à nota tocada.
- **Afinacao_Padrao**: Conjunto de frequências de referência para as seis cordas da guitarra em afinação padrão: E2 (82,41 Hz), A2 (110,00 Hz), D3 (146,83 Hz), G3 (196,00 Hz), B3 (246,94 Hz), E4 (329,63 Hz).
- **Tolerancia_Afinacao**: Margem de desvio em Hz aceita para considerar uma corda como "afinada".
- **Taxa_Amostragem**: Frequência com que o ADC realiza leituras do sinal de áudio, medida em amostras por segundo (Hz).

## Requisitos

### Requisito 1: Indicação Visual de Sistema Ativo

**User Story:** Como músico, eu quero que o LED da placa acenda ao iniciar o sistema, para que eu saiba que o afinador está funcionando.

#### Critérios de Aceitação

1. WHEN o script é iniciado, THE Sistema_Afinador SHALL acender o LED_Onboard no pino 25 para indicar que o sistema está em operação.
2. WHILE o Sistema_Afinador estiver em execução, THE LED_Onboard SHALL permanecer aceso continuamente.

### Requisito 2: Captura do Sinal de Áudio

**User Story:** Como músico, eu quero que o sistema capture o som da guitarra pelo microfone, para que a frequência da corda possa ser analisada.

#### Critérios de Aceitação

1. THE Sistema_Afinador SHALL configurar o ADC no pino 26 para leitura do sinal do microfone.
2. THE Sistema_Afinador SHALL coletar amostras de áudio a uma Taxa_Amostragem suficiente para representar frequências até 400 Hz (mínimo de 800 Hz conforme o teorema de Nyquist).
3. THE Sistema_Afinador SHALL coletar um número de amostras que seja potência de 2 (ex.: 1024 ou 2048) para compatibilidade com o algoritmo FFT.

### Requisito 3: Filtragem do Sinal de Áudio

**User Story:** Como músico, eu quero que o sinal de áudio seja filtrado, para que ruídos de alta frequência não interfiram na detecção da nota.

#### Critérios de Aceitação

1. WHEN um conjunto de amostras de áudio é coletado, THE Filtro_Passa_Baixa SHALL atenuar frequências acima de 400 Hz no sinal capturado.
2. THE Filtro_Passa_Baixa SHALL ser implementado como filtro digital executável em MicroPython no Raspberry Pi Pico 2.
3. WHEN o Filtro_Passa_Baixa é aplicado, THE Sistema_Afinador SHALL preservar as componentes de frequência entre 70 Hz e 350 Hz sem atenuação significativa.

### Requisito 4: Detecção de Frequência via FFT

**User Story:** Como músico, eu quero que o sistema detecte a frequência fundamental da corda tocada, para que eu saiba qual nota está sendo produzida.

#### Critérios de Aceitação

1. WHEN o sinal filtrado está disponível, THE Sistema_Afinador SHALL aplicar o algoritmo FFT para transformar o sinal do domínio do tempo para o domínio da frequência.
2. THE Sistema_Afinador SHALL implementar o algoritmo FFT em MicroPython puro, compatível com as limitações de memória e processamento do Raspberry Pi Pico 2.
3. WHEN a FFT é calculada, THE Sistema_Afinador SHALL identificar a Frequencia_Fundamental como o pico de maior magnitude no espectro de frequências dentro da faixa de 70 Hz a 350 Hz.

### Requisito 5: Identificação da Nota Musical

**User Story:** Como músico, eu quero que o sistema identifique qual corda da guitarra está sendo tocada, para que eu saiba qual nota estou afinando.

#### Critérios de Aceitação

1. WHEN a Frequencia_Fundamental é detectada, THE Sistema_Afinador SHALL comparar a frequência com as seis frequências da Afinacao_Padrao: E2 (82,41 Hz), A2 (110,00 Hz), D3 (146,83 Hz), G3 (196,00 Hz), B3 (246,94 Hz) e E4 (329,63 Hz).
2. WHEN a Frequencia_Fundamental é detectada, THE Sistema_Afinador SHALL identificar a nota mais próxima da frequência detectada dentre as seis cordas da Afinacao_Padrao.

### Requisito 6: Feedback de Afinação

**User Story:** Como músico, eu quero receber feedback sobre a afinação da corda, para que eu saiba se preciso ajustar a tensão para cima ou para baixo.

#### Critérios de Aceitação

1. WHEN a nota mais próxima é identificada, THE Sistema_Afinador SHALL classificar a afinação como "Afinado" quando a diferença entre a Frequencia_Fundamental e a frequência de referência for menor ou igual à Tolerancia_Afinacao de 1 Hz.
2. WHEN a Frequencia_Fundamental é maior que a frequência de referência da nota mais próxima por mais de 1 Hz, THE Sistema_Afinador SHALL indicar que a corda está "Sustenido (Sharp)" e exibir a diferença em Hz.
3. WHEN a Frequencia_Fundamental é menor que a frequência de referência da nota mais próxima por mais de 1 Hz, THE Sistema_Afinador SHALL indicar que a corda está "Bemol (Flat)" e exibir a diferença em Hz.
4. THE Sistema_Afinador SHALL exibir o feedback via saída serial (UART/USB) incluindo: a nota detectada, a frequência medida, a frequência de referência e o status da afinação.

### Requisito 7: Operação Contínua

**User Story:** Como músico, eu quero que o afinador funcione continuamente, para que eu possa afinar todas as cordas sem reiniciar o sistema.

#### Critérios de Aceitação

1. THE Sistema_Afinador SHALL operar em loop contínuo, repetindo o ciclo de captura, filtragem, detecção e feedback.
2. IF uma exceção inesperada ocorrer durante o processamento, THEN THE Sistema_Afinador SHALL registrar o erro na saída serial e continuar a operação no próximo ciclo.
3. WHILE o Sistema_Afinador estiver em operação contínua, THE Sistema_Afinador SHALL aguardar um intervalo mínimo de 100 ms entre ciclos de medição para estabilidade.

### Requisito 8: Tratamento de Sinal Insuficiente

**User Story:** Como músico, eu quero que o sistema me avise quando não detectar som suficiente, para que eu saiba que preciso tocar a corda novamente.

#### Critérios de Aceitação

1. WHEN a amplitude do sinal capturado está abaixo de um limiar mínimo, THE Sistema_Afinador SHALL exibir a mensagem "Sem sinal detectado" na saída serial.
2. WHEN nenhum sinal suficiente é detectado, THE Sistema_Afinador SHALL pular a análise FFT e retornar ao início do ciclo de captura.
