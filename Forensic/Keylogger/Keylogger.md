# 🛡️ Keylogger & RAT Attack — Forensic Analysis

## 📌 Overview

Este writeup apresenta a análise forense de um incidente envolvendo **execução de keylogger, acesso remoto não autorizado (RAT) e persistência**, identificado a partir de evidências coletadas no sistema comprometido.

A investigação revelou comprometimento ativo com coleta de credenciais e controle remoto da máquina.

---

## 🎯 Objetivo

* Identificar vetor de infecção
* Analisar execução do malware
* Detectar persistência
* Identificar comunicação com atacante
* Correlacionar evidências visuais

---

## 🧠 Resumo do Ataque

O atacante executou um fluxo típico de comprometimento:

1. 📥 Execução de script malicioso
2. ⚡ Uso de PowerShell para execução
3. 🐀 Implantação de RAT (AnyDesk)
4. ⌨️ Ativação de Keylogger
5. 🔐 Captura de credenciais
6. ♻️ Persistência no sistema

---

## ⏱️ Timeline do Ataque (Reconstruída)

| Fase          | Evento                          | Evidência                  |
| ------------- | ------------------------------- | -------------------------- |
| Inicial       | Acesso a URL suspeita           | URL utilizada para payload |
| Execução      | Script executado via PowerShell | Código malicioso           |
| Implantação   | Instalação de ferramenta remota | AnyDesk identificado       |
| Monitoramento | Keylogger ativo                 | Captura de senhas          |
| Persistência  | Comando configurado             | Execução automática        |
| Controle      | Comunicação com atacante        | IP externo identificado    |

---

## 🔍 Análise Técnica

### 🌐 Origem do Ataque

![IP do atacante](/Forensic/Keylogger/images/IP%20do%20atacante.png)

* Comunicação com host externo detectada
* Indica possível servidor de controle (C2)

---

### 🔗 Vetor de Infecção

![URL maliciosa](/Forensic/Keylogger/images/URL.png)

* Usuário acessou recurso externo
* Possível download de payload

---

### ⚡ Execução via PowerShell

![Execução PowerShell](/Forensic/Keylogger/images/Code.ink%20no%20PowerShell.png)

* Uso de PowerShell para execução de código
* Técnica comum para evasão e fileless malware

---

### 🧠 Código Malicioso

![Código identificado](/Forensic/Keylogger/images/Codigo.png)

* Script com comportamento suspeito
* Indícios de coleta de dados e execução remota

---

### 🐀 Acesso Remoto (RAT)

![AnyDesk RAT](/Forensic/Keylogger/images/RAT%20no%20Anydesk.png)

* Presença do AnyDesk
* Controle remoto ativo na máquina

---

### ♻️ Persistência

![Persistência](/Forensic/Keylogger/images/Comando%20de%20Persistencia.png)

* Execução automática configurada
* Garante acesso contínuo ao sistema

---

### ⌨️ Keylogger

* Registro de entradas do usuário
* Exposição de credenciais sensíveis

---

### 🧩 Técnicas de Evasão

![LOLbins](/Forensic/Keylogger/images/Lolapps.png)

* Uso de ferramentas legítimas do sistema (Living-off-the-Land)
* Dificulta detecção por antivírus

---

## 📡 Evidências Correlacionadas

* PowerShell → execução inicial
* URL → origem do payload
* AnyDesk → acesso remoto
* Keylogger → exfiltração de dados
* Persistência → manutenção do acesso

---

## 🚨 Indicadores de Comprometimento (IOCs)

* IP externo identificado
* Uso de PowerShell
* Presença de AnyDesk não autorizado
* Scripts suspeitos
* Execução automática (persistência)
* Captura de credenciais