<div align="center">

```
███████╗███████╗███╗   ██╗    ██████╗ ███████╗ ██╗
██╔════╝██╔════╝████╗  ██║    ╚════██╗██╔════╝███║
█████╗  █████╗  ██╔██╗ ██║     █████╔╝███████╗╚██║
██╔══╝  ██╔══╝  ██║╚██╗██║    ██╔═══╝ ╚════██║ ██║
███████╗███████╗██║ ╚████║    ███████╗███████║ ██║
╚══════╝╚══════╝╚═╝  ╚═══╝    ╚══════╝╚══════╝ ╚═╝
```

# EEN251 — Microcontroladores e Sistemas Embarcados

**Engenharia de Computação · Mauá Institute of Technology**

[![Status](https://img.shields.io/badge/status-em%20andamento-brightgreen?style=flat-square)](.)
[![Ano](https://img.shields.io/badge/Anual-2026-blue?style=flat-square)](.)
[![C](https://img.shields.io/badge/C-A8B9CC?style=flat-square&logo=c&logoColor=black)](.)
[![Raspberry Pi Pico](https://img.shields.io/badge/RPi%20Pico%202-A22846?style=flat-square&logo=raspberrypi&logoColor=white)](.)
[![Raspberry Pi](https://img.shields.io/badge/RPi%204-A22846?style=flat-square&logo=raspberrypi&logoColor=white)](.)
[![Linux](https://img.shields.io/badge/Linux%20Embarcado-FCC624?style=flat-square&logo=linux&logoColor=black)](.)
[![MQTT](https://img.shields.io/badge/MQTT-660066?style=flat-square&logo=eclipse-mosquitto&logoColor=white)](.)
[![IoT](https://img.shields.io/badge/IoT-Ubidots-00C4CC?style=flat-square)](.)

> *"Embedded systems are everywhere — they just don't announce themselves."*

</div>

---

## ◈ Sobre

Este repositório reúne os três projetos desenvolvidos ao longo da disciplina **EEN251 — Microcontroladores e Sistemas Embarcados**, cobrindo desde programação bare-metal em C com a Raspberry Pi Pico 2, passando por Linux embarcado com Raspberry Pi 4, até integração com a nuvem via MQTT e dashboards IoT.

A disciplina evolui em três eixos práticos: **microcontroladores**, **computadores embarcados** e **Internet das Coisas**.

---

## ◈ Projetos

### 🔴 T1 — Afinador de Violão com Raspberry Pi Pico 2
> **Hardware:** Raspberry Pi Pico 2 · **Linguagem:** C · **Arquitetura:** ARM

Desenvolvimento de um afinador de violão embarcado utilizando a Raspberry Pi Pico 2. O sistema captura o sinal sonoro via microfone, realiza análise de frequência em tempo real e indica ao usuário se a corda está afinada, acima ou abaixo da nota alvo — tudo rodando bare-metal em C.

- [ ] Definição do escopo e proposta
- [ ] Captura de áudio via ADC
- [ ] Algoritmo de detecção de frequência (ex: FFT / autocorrelação)
- [ ] Mapeamento das frequências das cordas (E2, A2, D3, G3, B3, E4)
- [ ] Feedback visual ao usuário (display / LEDs)
- [ ] **Apresentação T1**

---

### 🟡 T2 — Projeto com Computador Embarcado
> **Hardware:** Raspberry Pi 4 · **SO:** Linux Embarcado · **Interface:** Node-RED

Desenvolvimento de uma aplicação utilizando a Raspberry Pi 4 com Linux embarcado, trabalhando com periféricos de alto nível e interface com usuário via Node-RED.

- [ ] Instalação e configuração do Linux para embarcados
- [ ] Trabalho com periféricos da Raspberry Pi 4
- [ ] Interface com usuário (Node-RED)
- [ ] **Apresentação T2**

---

### 🟢 T3 — Projeto IoT com Dashboard
> **Protocolo:** MQTT · **Plataforma:** Ubidots · **Interface:** Dashboard em nuvem

Integração de um computador embarcado com a internet, construindo um dashboard interativo via Ubidots e comunicação via protocolo MQTT.

- [ ] Requisições HTTP para a internet
- [ ] Configuração do Ubidots e criação do dashboard
- [ ] Comunicação via protocolo MQTT
- [ ] Integração dashboard ↔ hardware
- [ ] **Apresentação T3**

---

## ◈ Módulos da Disciplina

<details>
<summary><strong>Módulo 1 — Fundamentos de Sistemas Embarcados</strong> <code>semanas 3–8</code></summary>

```
├── Introdução a sistemas embarcados
├── Revisão de programação em C
├── Arquitetura ARM
├── Git e versionamento
├── Sensores e atuadores — GPIO
├── Comunicação Serial — UART
├── Interrupções e modelos de SO (While / Interrupções / SO)
└── Periféricos: Timer e ADC
```

</details>

<details>
<summary><strong>Módulo 2 — Periféricos Avançados & Raspberry Pi Pico 2</strong> <code>semanas 10–17</code></summary>

```
├── ADC e PWM
├── Protocolos I2C e SPI
├── Introdução ao Raspberry Pi Pico
└── Desenvolvimento e apresentação do T1
```

</details>

<details>
<summary><strong>Módulo 3 — Linux Embarcado & Raspberry Pi 4</strong> <code>semanas 23–28</code></summary>

```
├── Raspberry Pi — visão geral
├── Instalação e configuração do Linux para embarcados
├── Trabalhando com periféricos
├── Interface com usuário (Node-RED)
└── Desenvolvimento e apresentação do T2
```

</details>

<details>
<summary><strong>Módulo 4 — IoT & Dashboard em Nuvem</strong> <code>semanas 30–35</code></summary>

```
├── Introdução a HTTP para requisições na internet
├── Internet das Coisas — conceitos
├── Desenvolvimento de dashboards com Ubidots
├── Protocolo MQTT
└── Desenvolvimento e apresentação do T3
```

</details>

---

## ◈ Estrutura do Repositório

```bash
EEN251/
│
├── T1-afinador-violao/          # Raspberry Pi Pico 2 — Afinador de violão
│   ├── src/                     # Código-fonte em C
│   ├── docs/                    # Documentação e esquemáticos
│   └── README.md
│
├── T2-computador-embarcado/     # Raspberry Pi 4 — Linux + Node-RED
│   ├── src/
│   ├── nodered-flows/           # Flows exportados do Node-RED
│   ├── docs/
│   └── README.md
│
├── T3-iot-dashboard/            # MQTT + Ubidots + Dashboard
│   ├── src/
│   ├── dashboard/               # Configurações e capturas do Ubidots
│   ├── docs/
│   └── README.md
│
└── README.md
```

---

## ◈ Entregas

| Entrega | Descrição | Hardware |
|---------|-----------|----------|
| **T1** | Afinador de violão | Raspberry Pi Pico 2 |
| **T2** | Projeto com computador embarcado | Raspberry Pi 4 |
| **T3** | Projeto IoT com dashboard | Raspberry Pi 4 + Nuvem |

---

## ◈ Conceitos-Chave

`Sistemas Embarcados` · `Arquitetura ARM` · `C Bare-metal` · `GPIO` · `UART` · `I2C` · `SPI` · `PWM` · `ADC` · `FFT` · `Timer` · `Interrupções` · `Linux Embarcado` · `Node-RED` · `MQTT` · `IoT` · `Ubidots` · `Raspberry Pi Pico 2` · `Raspberry Pi 4`

---

## ◈ Equipe

<div align="center">

| Nome | Papel |
|------|-------|
| Enzo Oliveira D'Onofrio | Desenvolvedor |
| Leonardo Souza Olivieri | Desenvolvedor |
| Arthur Gama Ruiz | Desenvolvedor |
| João Vitor Morimoto Sesma | Desenvolvedor |
| Pedro Wilian Palumbo Bevilacqua | Desenvolvedor |
| Felipe Fazia da Costa | Desenvolvedor |

**Orientadores**

Prof. Sergio Ribeiro Augusto · Prof. Rodrigo de Marca França

</div>

---

<div align="center">

**EEN251 — Microcontroladores e Sistemas Embarcados**  
Engenharia de Computação · Mauá Institute of Technology · 2026

[![C](https://img.shields.io/badge/-C-A8B9CC?style=flat-square&logo=c&logoColor=black)](.)
[![Raspberry Pi](https://img.shields.io/badge/-Raspberry%20Pi-A22846?style=flat-square&logo=raspberrypi&logoColor=white)](.)
[![Linux](https://img.shields.io/badge/-Linux%20Embarcado-FCC624?style=flat-square&logo=linux&logoColor=black)](.)
[![MQTT](https://img.shields.io/badge/-MQTT-660066?style=flat-square)](.)
[![IoT](https://img.shields.io/badge/-IoT-00C4CC?style=flat-square)](.)

</div>