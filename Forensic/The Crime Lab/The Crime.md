# 🔍 138-The-Crime — CTF Writeup
### CyberDefenders Blue Team Challenge | Forense Mobile & Análise de Artefatos Android

---

| **Analista**          | Mauricio Robert                                                          |
|-----------------------|--------------------------------------------------------------------------|
| **Organização**       | Faculdade Impacta                                                        |
| **Data do Relatório** | 15/06/2026                                                               |
| **Data do Incidente** | 20/09/2023                                                               |
| **Classificação**     | CONFIDENCIAL                                                             |
| **Ferramentas**       | Autopsy 4.23.1 (CriminalLab) · ALEAPP 3.2.5                            |
| **Arquivo**           | Imagem de dispositivo Android — `138-The-Crime`                         |

---

## 🔍 Resumo Executivo

A análise forense mobile do dispositivo Android de **Mohamed Ahmed** revelou um trader que investiu todas as suas economias via aplicativo **Olymp Trade** e contraiu dívidas com terceiros. Em **20/09/2023**, pressionado por ameaças SMS do cobrador **Shady Wahab** (+20 117 213 7258) exigindo **250.000 EGP**, Mohamed deixou sua residência sem avisar a família e se hospedou no **The Nile Ritz-Carlton, Cairo**. Comunicações via **Discord** entre os usuários `inform0_o` (vítima) e `rob1ns0n.` revelaram o plano de se encontrarem no **The Mob Museum** em Las Vegas — destino confirmado por uma passagem aérea da **Egypt Airlines** (Voo 310, 01/10/2023, Cairo → Las Vegas) encontrada na memória do dispositivo.

---

## 🛠 Ferramentas Utilizadas

| Ferramenta                    | Finalidade                                                                                                         |
|-------------------------------|--------------------------------------------------------------------------------------------------------------------|
| **Autopsy 4.23.1 (CriminalLab)** | Análise do sistema de arquivos Android — navegação de diretórios, extração de mensagens (MMS/SMS), contatos, metadados, hashes MD5/SHA-256 e aplicativos instalados |
| **ALEAPP 3.2.5**              | Extração e análise de artefatos Android — Discord Chats, histórico do Chrome, geolocalização, Firebase Cloud Messaging e metadados de dispositivo |

---

## 📋 Perguntas e Respostas

### Q1 — Qual é o SHA-256 do aplicativo de trading utilizado pela vítima?

> **Resposta: `4f188a77235b2f83a1c49e78c1548d7c2c6c05106d8b9feb823fdc3466e8df32`**

**Solução:** A navegação pelo sistema de arquivos Android no Autopsy revelou, em:

```
/data/app/com.ticno.olymptrade-IKDfBXc8qLNF9F2eXSyBwg==/
```

o arquivo `base.apk` (38.512.633 bytes, MIME: `application/vnd.android.package-archive`). A aba **File Metadata** exibe os hashes:

```
MD5:     7623f52f97c57a0731ef534e6b38102f
SHA-256: 4f188a77235b2f83a1c49e78c1548d7c2c6c05106d8b9feb823fdc3466e8df32
Hash Lookup Result: UNKNOWN
```

O identificador `com.ticno.olymptrade` confirma que o aplicativo é o **Olymp Trade** — plataforma de trading online de opções binárias e forex, alinhada ao contexto de investimentos e dívidas relatado pelas testemunhas.

![SHA-256 Olymptrade](/Forensic/The%20Crime%20Lab/images/SHA%20256_App_of_Trade(1).png)

---

### Q2 — Qual é o valor da dívida que a vítima deve ao cobrador?

> **Resposta: `250,000 EGP`**

**Solução:** A análise das mensagens no Autopsy, filtradas pelo banco de dados `mmssms.db`, revelou uma mensagem SMS recebida em `2023-09-20 13:09:45 PDT`, com direção `Incoming` e origem `+201172137258`. O conteúdo extraído exibe a ameaça completa:

```
"It's time for you to pay back the money you owe me, but you're not picking
up my calls. You better think twice about not paying, because it won't end
well for you. Prepare the sum of 250,000 EGP and I'll expect your call
within an hour at most."
```

O trecho **`Prepare the sum of 250,000 EGP`** está destacado no campo de texto da mensagem, revelando com precisão o valor exigido: **250.000 libras egípcias**.

![Valor da Divida](/Forensic/The%20Crime%20Lab/images/Value_of_Owe_to_Person(2).png)

---

### Q3 — Qual é o nome da pessoa a quem a vítima deve dinheiro?

> **Resposta: `Shady Wahab`**

**Solução:** A análise dos **Contacts** no Autopsy, extraídos do `contacts2.db`, apresentou 6 contatos. O destaque em azul aponta:

```
Nome:   Shady Wahab
Número: +20 117 213 7258
```

A janela de propriedades do `mmssms.db` confirma que o campo `From Phone Number` da mensagem de ameaça (`+201172137258`) pertence exatamente ao contato **Shady Wahab**, conectando o número de telefone do remetente das ameaças ao nome na agenda de contatos da vítima.

![Nome do Cobrador](/Forensic/The%20Crime%20Lab/images/Name_of_The_Colletor(3).png)

---

### Q4 — Onde a vítima estava em 20 de setembro de 2023?

> **Resposta: `The Nile Ritz-Carlton`**

**Solução:** A análise de geolocalização via **ALEAPP** (relatório exportado em `C:/Users/ForenseAnalyst/Documents/CriminalLab/ModuleOutput/`) revelou uma captura do **Google Maps** mostrando a localização da vítima em 20/09/2023. O mapa exibe o Cairo com um marcador (pin azul) posicionado diretamente sobre:

```
The Nile Ritz-Carlton, Cairo
(فندق نايل ريتز كارلتون)
```

O hotel está situado às margens do Rio Nilo, próximo ao Museu Egípcio no Tahrir Square — confirmando que Mohamed Ahmed estava hospedado no **The Nile Ritz-Carlton** ao sair de sua residência sem comunicar a família. A reserva foi feita por 10 dias (20/09 a 01/10/2023), coincidindo com a data do voo para Las Vegas.

![GEO da Vitima 20/09](/Forensic/The%20Crime%20Lab/images/Locate_of_Victim_20-09(4).png)

---

### Q5 — Qual é o destino de viagem planejado pela vítima?

> **Resposta: `Las Vegas`**

**Solução:** A análise do diretório de mídia no Autopsy, em:

```
/data/media/0/Download/
```

revelou o arquivo `Plane Ticket.png` (159.713 bytes, MD5: `332d749be579fa5268a9b6874c84e0be`). A visualização na aba **Application** exibe a passagem aérea completa:

```
Companhia:      EGYPT AIRLINES
Passageiro:     MOHAMED AHMED
Data:           01.10.2023
Origem:         Cairo
Destino:        Las Vegas
Embarque:       09:00 AM
Portão:         08 | Voo: 310 | Assento: 20 | Classe: C
```

A passagem comprova que Mohamed Ahmed havia planejado viajar de **Cairo para Las Vegas** em 01/10/2023 — exatamente 10 dias após deixar a residência.

![Destino da Vitima](/Forensic/The%20Crime%20Lab/images/Next_Location_of_Victm(5).png)

---

### Q6 — Qual é o local do encontro combinado no Discord?

> **Resposta: `The Mob Museum`**

**Solução:** A análise das conversas Discord via **ALEAPP 3.2.5** (relatório "ALEAPP - Discord Chats report") revelou duas mensagens no Channel ID `1153848030269804606`, em 20/09/2023:

**Mensagem 1** — Usuário `inform0_o` (`2023-09-20T00:57:26`):
```
"Hey mate. Some changes have occurred in the plan. I have booked my ticket
for 01/10 at 9:00 AM. Where am I supposed to meet you?"
```

**Mensagem 2** — Usuário `rob1ns0n.` (`2023-09-20T20:46:02`, Avatar: `bd09719d0f`):
```
"What a wonderful news! Well meet at **The Mob Museum**.
I'll await your call when you arrive. Enjoy your flight bro ❤"
```

O usuário `rob1ns0n.` confirma o local de encontro em **`The Mob Museum`** (National Museum of Organized Crime and Law Enforcement), localizado em **Las Vegas, Nevada** — consistente com o destino na passagem aérea encontrada no dispositivo.

![Local de Encontro](/Forensic/The%20Crime%20Lab/images/Discord_Chat_The_Mob_Museum(6).png)

---

## ⛓ Linha do Tempo de Eventos

```
[20/09/2023 00:57 UTC] COMUNICAÇÃO DISCORD
    inform0_o (Mohamed Ahmed) pergunta a rob1ns0n. onde se encontrar
    Confirma voo reservado para 01/10 às 9:00 AM
    ↓
[20/09/2023 manhã] FUGA DA RESIDÊNCIA
    Mohamed deixa sua casa sem avisar a família
    Check-in no The Nile Ritz-Carlton, Cairo (reserva de 10 dias)
    ↓
[20/09/2023 13:09 PDT] AMEAÇA DO COBRADOR
    Shady Wahab (+20 117 213 7258) envia SMS de ameaça
    Exige pagamento de 250.000 EGP em até 1 hora
    Vítima não atende chamadas
    ↓
[20/09/2023 20:46 UTC] RESPOSTA DISCORD
    rob1ns0n. confirma encontro no The Mob Museum, Las Vegas
    "I'll await your call when you arrive"
    ↓
[01/10/2023 09:00] VOO PLANEJADO
    Egypt Airlines Voo 310 — Cairo → Las Vegas
    Passageiro: MOHAMED AHMED | Gate 08 | Seat 20 | Class C
    ↓
[01/10/2023 — previsto] ENCONTRO EM LAS VEGAS
    The Mob Museum, Las Vegas, Nevada
    Rob1ns0n. aguardaria ligação na chegada
```

---

## 🗺 Mapeamento Investigativo

| Pergunta | Fonte de Evidência | Artefato |
|----------|-------------------|----------|
| App de trading | Autopsy → `/data/app/com.ticno.olymptrade/` | `base.apk` (SHA-256) |
| Valor da dívida | Autopsy → Messages → `mmssms.db` | SMS de ameaça — 250.000 EGP |
| Nome do cobrador | Autopsy → Contacts → `contacts2.db` | Shady Wahab (+20 117 213 7258) |
| Localização 20/09 | ALEAPP → Google Maps geolocation | The Nile Ritz-Carlton, Cairo |
| Destino da viagem | Autopsy → `/data/media/0/Download/` | `Plane Ticket.png` — Las Vegas |
| Local do encontro | ALEAPP → Discord Chats | Mensagem de `rob1ns0n.` — The Mob Museum |

---

## 🚨 Artefatos e Indicadores Identificados (IOCs)

| Tipo | Indicador | Contexto |
|------|-----------|----------|
| Identidade | Mohamed Ahmed | Vítima / passageiro — confirmado na passagem aérea |
| Aplicativo | `com.ticno.olymptrade` (Olymp Trade) | App de trading primário — base.apk (38,5 MB) |
| SHA-256 | `4f188a77235b2f83a1c49e78c1548d7c2c6c05106d8b9feb823fdc3466e8df32` | Hash SHA-256 do `base.apk` (Olymp Trade) |
| MD5 App | `7623f52f97c57a0731ef534e6b38102f` | Hash MD5 do `base.apk` |
| Dívida | 250.000 EGP | Valor exigido por Shady Wahab via SMS em 20/09 |
| Cobrador | Shady Wahab (`+20 117 213 7258`) | Remetente das ameaças SMS — contato na agenda |
| Localização 20/09 | The Nile Ritz-Carlton, Cairo | Localização via Google Maps extraído pelo ALEAPP |
| Passagem Aérea | Egypt Airlines Voo 310 — Cairo → Las Vegas, 01/10/2023 | `Plane Ticket.png` em `/data/media/0/Download/` |
| MD5 Passagem | `332d749be579fa5268a9b6874c84e0be` | Hash MD5 do `Plane Ticket.png` |
| Discord (vítima) | `inform0_o` | Username da vítima no Discord |
| Discord (cúmplice) | `rob1ns0n.` (Avatar: `bd09719d0f`) | Contato planejando encontro em Las Vegas |
| Canal Discord | `1153848030269804606` | Canal onde o encontro foi planejado |
| Local Encontro | The Mob Museum (Las Vegas, Nevada) | Confirmado em mensagem Discord de `rob1ns0n.` |
| BD Mensagens | `mmssms.db` | Banco de dados SMS/MMS Android — fonte das ameaças |
| BD Contatos | `contacts2.db` | Banco de dados de contatos Android — identificação de Shady Wahab |

---

## ✅ Resumo das Flags

| # | Pergunta | Flag / Resposta |
|---|----------|-----------------|
| Q1 | SHA-256 do app de trading | `4f188a77235b2f83a1c49e78c1548d7c2c6c05106d8b9feb823fdc3466e8df32` |
| Q2 | Valor da dívida | `250,000 EGP` |
| Q3 | Nome do cobrador | `Shady Wahab` |
| Q4 | Localização da vítima em 20/09/2023 | `The Nile Ritz-Carlton` |
| Q5 | Destino de viagem planejado | `Las Vegas` |
| Q6 | Local do encontro no Discord | `The Mob Museum` |

---

## 📚 Referências

- [CyberDefenders — 138-The-Crime CTF](https://cyberdefenders.org/)
- [Autopsy Digital Forensics Platform](https://www.autopsy.com/)
- [ALEAPP — Android Logs Events and Protobuf Parser](https://github.com/abrignoni/ALEAPP)
- [Olymp Trade (com.ticno.olymptrade)](https://olymptrade.com/)
- [The Mob Museum, Las Vegas](https://themobmuseum.org/)
- [The Nile Ritz-Carlton, Cairo](https://www.ritzcarlton.com/cairo)

---