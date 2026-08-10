# TryHackMe — Hackers Holiday CTF
## Level 14 — Management Wants a Word

**Categoria:** Digital Forensics / DPAPI / Credential Recovery / Encrypted Volumes
**Dificuldade:** Difícil

---

### 🛎️ Concierge Briefing

> Housekeeping found a guest's laptop left behind after an early checkout, Room 214, registered to a "Vera." IT pulled a full triage before wiping it for the next guest.
> Hunt down the artifacts scattered across her machine and figure out how they fit together. Somewhere in that trail is a password she never meant to leave behind. Follow it, and it'll open a door to something she was keeping very quiet.

---

## 🎯 Objetivo

Diferente dos levels anteriores (ataques diretos a VERA via prompt injection), este desafio é puramente forense: recebemos uma imagem KAPE do laptop de "Vera" (quarto 214) e precisamos reconstruir, passo a passo, a cadeia de criptografia do Windows DPAPI — do hive SAM até as credenciais salvas no Chrome — para finalmente localizar e montar um volume criptografado escondido no disco, onde a flag está guardada.

---

## 🔍 Passo 1 — Reconhecendo o triage KAPE

O material fornecido é uma extração KAPE (`management-wants-a-word-forensics-hh-day-14`). Rodando `tree` na raiz:

![Árvore de diretórios do KAPE mostrando os hives de usuário e o perfil completo do Chrome de vera](/Hacker%20Holiday%202026%20-%20THM/14º%20Level%20-%20Management%20Wants%20a%20Word/images/Analyze_Archives.png)

```
management-wants-a-word-forensics-hh-day-14
└── KAPE
    └── C
        ├── Users
        │   ├── Default
        │   │   ├── NTUSER.DAT
        │   │   ├── NTUSER.DAT.LOG1
        │   │   └── NTUSER.DAT.LOG2
        │   └── vera
        │       └── AppData
        │           └── Local
        │               └── Google
        │                   └── Chrome For Testing
        │                       └── User Data
        │                           ├── AutofillStates
        │                           ├── BrowserMetrics
        │                           ├── CertificateRevocation
        │                           ├── component_crx_cache
        │                           ├── Crashpad
        │                           ├── Crowd Deny
        │                           └── Default
        │                               ├── Affiliation Database
        │                               ├── AutofillStrikeDatabase
        │                               ├── blob_storage
        │                               ├── BudgetDatabase
        │                               └── Cache
        ...
```

Duas coisas ficam claras de cara:
- Existe um perfil completo do **Chrome** da usuária `vera`, incluindo `Login Data` (credenciais salvas) e `Local State` (chave AES mestre do navegador).
- Os hives de registro (`SAM`, `SYSTEM`, `SECURITY`) também estão presentes na imagem — necessários para recuperar a senha local da conta e as chaves DPAPI do sistema.

A estratégia é clara: usar os hives para extrair segredos locais, usar esses segredos para decriptar a **DPAPI Master Key** da usuária, e usar essa master key para decriptar o que o Chrome guardou.

---

## 🔍 Passo 2 — Extraindo segredos locais com `secretsdump`

Rodando o `impacket-secretsdump` em modo `LOCAL` contra os três hives extraídos:

![Dump local via impacket-secretsdump revelando hashes SAM e o DefaultPassword em texto claro](/Hacker%20Holiday%202026%20-%20THM/14º%20Level%20-%20Management%20Wants%20a%20Word/images/Pass_and_User.png)

```bash
impacket-secretsdump -sam Windows/System32/config/SAM \
                      -system Windows/System32/config/SYSTEM \
                      -security Windows/System32/config/SECURITY LOCAL
```

Saída relevante:

```
[*] Target system bootKey: 0x0f6f73ce89c8cda52d06fcc5131e040f
[*] Dumping local SAM hashes (uid:rid:lmhash:nthash)
Administrator:500:aad3b435b51404eeaad3b435b51404ee:...
Guest:501:aad3b435b51404eeaad3b435b51404ee:...
DefaultAccount:503:aad3b435b51404eeaad3b435b51404ee:...
WDAGUtilityAccount:504:aad3b435b51404eeaad3b435b51404ee:...
vera:1000:aad3b435b51404eeaad3b435b51404ee:1241186a4aac4f34f4bf7ace71b396a8:::
[*] Dumping LSA Secrets
[*] DefaultPassword
(Unknown User):minivera
[*] DPAPI_SYSTEM
dpapi_machinekey:0x875427f6426f5dc4e318d1e6cfed17291295e4f7
dpapi_userkey:0xb0536fa518944b2520b5a5b9f5b513e3892224a1
[*] NL$KM
NL$KM:2f31efe46aa6555fbb049e1d72fd5842025665...
```

Dois achados-chave:
- **`DefaultPassword: minivera`** — uma senha em texto claro guardada nas LSA Secrets, quase certamente a senha da conta `vera` (autologon).
- Existem também as chaves **`DPAPI_SYSTEM`** (machine/user key), que poderiam decriptar a master key via chave de sistema — mas neste caso a rota mais direta é usar a senha de usuário recuperada (`minivera`) diretamente contra a master key protegida pelo SID da conta.

---

## 🔍 Passo 3 — Localizando e decriptando a DPAPI Master Key

Toda credencial protegida por DPAPI (Chrome incluso) depende de uma **master key** por usuário, armazenada em `AppData\Roaming\Microsoft\Protect\<SID>\`. Localizando o arquivo:

![Localização do arquivo de master key, inspeção em xxd e decriptação com impacket-dpapi](/Hacker%20Holiday%202026%20-%20THM/14º%20Level%20-%20Management%20Wants%20a%20Word/images/Master_Key.png)

```bash
find Users/vera/AppData/Roaming/Microsoft/Protect -type f -printf '%p\n'
```

```
Users/vera/AppData/Roaming/Microsoft/Protect/S-1-5-21-2529683458-431225740-1723070931-1000/c90719ef-5b98-474e-b934-136d606a702a
Users/vera/AppData/Roaming/Microsoft/Protect/S-1-5-21-2529683458-431225740-1723070931-1000/Preferred
```

O arquivo `Preferred` só aponta para o GUID da master key ativa (confirmado via `xxd`, que mostra os bytes do GUID `c90719ef-...` no header). O arquivo com nome de GUID é a master key criptografada de fato.

Tentativa inicial de decriptação, sem a senha certa, falha:

```
ERROR: not enough values to unpack (expected 2, got 1)
```

Usando a senha `minivera` recuperada no passo anterior, junto com o SID da conta:

```bash
impacket-dpapi masterkey \
  -file "Users/vera/AppData/Roaming/Microsoft/Protect/S-1-5-21-2529683458-431225740-1723070931-1000/c90719ef-5b98-474e-b934-136d606a702a" \
  -sid "S-1-5-21-2529683458-431225740-1723070931-1000" \
  -password "minivera"
```

```
Decrypted key with User Key (SHA1)
Decrypted key: 0x5e5715ec9b6df5a86e97902692a66d28e691f05d5bc1e04d0159cfe960e94c978c07e5004a0179d3a96df2468885a28175b0b02cc064445f116a752d2b3e9d40
```

A master key da usuária `vera` está decriptada. Ela é a chave-mestra que abrirá qualquer segredo DPAPI dela — incluindo o cofre de senhas do Chrome.

---

## 🔍 Passo 4 — Confirmando o alvo: o blob DPAPI do Chrome

Antes de tentar decriptar as credenciais salvas, é preciso confirmar que a master key recuperada é de fato a que protege o cofre do Chrome (`Local State`). Extraindo o blob criptografado (`chrome_blob.bin`, referente à chave AES do `Local State`) e inspecionando seu header manualmente com Python:

![Análise do header do DPAPI_BLOB do Chrome confirmando o GUID da master key](/Hacker%20Holiday%202026%20-%20THM/14º%20Level%20-%20Management%20Wants%20a%20Word/images/DPAI_Master_Key.png)

```python
from pathlib import Path
import struct, uuid

data = Path("/tmp/chrome_blob.bin").read_bytes()

print("Tamanho:", len(data))
print("Header:", data[:4].hex())

# DPAPI_BLOB:
# DWORD Version
# GUID Provider
# DWORD MasterKeyVersion
# GUID MasterKeyGuid
print("Version:", struct.unpack("<I", data[0:4])[0])
print("Provider:", uuid.UUID(bytes_le=data[4:20]))
print("MasterKeyVersion:", struct.unpack("<I", data[20:24])[0])
print("MasterKey GUID:", uuid.UUID(bytes_le=data[24:40]))
```

```
Tamanho: 312
Header: 01000000
Version: 1
Provider: df9d8cd0-1501-11d1-8c7a-00c04fc297eb
MasterKeyVersion: 1
MasterKey GUID: c90719ef-5b98-474e-b934-136d606a702a
```

O `Provider` corresponde ao GUID padrão do provedor DPAPI do Windows, e o **MasterKey GUID bate exatamente com o arquivo de master key decriptado no Passo 3** (`c90719ef-5b98-474e-b934-136d606a702a`). Confirmado: essa é a chave certa para abrir o cofre de senhas do Chrome.

---

## 🔍 Passo 5 — Automatizando a cadeia completa com `pypykatz`

Em vez de decriptar manualmente o blob AES-GCM do Chrome camada por camada, usamos o **pypykatz**, que já entende toda a cadeia DPAPI → Chrome nativamente:

![Cadeia pypykatz: prekey a partir da senha, master key, e decriptação das credenciais salvas do Chrome](/Hacker%20Holiday%202026%20-%20THM/14º%20Level%20-%20Management%20Wants%20a%20Word/images/DPAI_Master_Key.png)

**1. Gerar o "prekey" a partir da senha e do SID:**
```bash
pypykatz dpapi prekey password "S-1-5-21-2529683458-431225740-1723070931-1000" "minivera" -o /tmp/vera_prekey
cat /tmp/vera_prekey
```
```
5aab0bd7b4bcfafa38c05b63b11b6affefafaff4
ccaba45d495d0968ac4c77d7a89e1bdba69139fb
16e4ee09fcd85ad0fe613f1ece43909a7d151215
1c6fcccf2c9ae8e08e1eea5671718d2e9878e35d
```

**2. Usar o prekey para decriptar a master key file:**
```bash
pypykatz dpapi masterkey \
  Users/vera/AppData/Roaming/Microsoft/Protect/S-1-5-21-2529683458-431225740-1723070931-1000/c90719ef-5b98-474e-b934-136d606a702a \
  /tmp/vera_prekey -o /tmp/vera_mkf
```

**3. Usar a master key para decriptar o cofre do Chrome (`Local State` + `Login Data`):**
```bash
pypykatz dpapi chrome /tmp/vera_mkf \
  "Users/vera/AppData/Local/Google/Chrome For Testing/User Data/Local State" \
  --logindata "Users/vera/AppData/Local/Google/Chrome For Testing/User Data/Default/Login Data"
```

```
file: Users/vera/AppData/Local/Google/Chrome For Testing/User Data/Default/Login Data
user: VeraSecretVault
pass: b'Wh4t1sV3raD0inG0nTh1sH0st'
url:  http://bytelotus.thm:8080/login
```

A credencial salva no Chrome não é de um site qualquer — o usuário `VeraSecretVault` e a URL sugerem que essa senha (`Wh4t1sV3raD0inG0nTh1sH0st`) foi salva para proteger algo bem mais interessante que um login web comum.

---

## 🔍 Passo 6 — Montando o cofre criptografado escondido

Uma busca pelo disco revela um arquivo de container em `Users/vera/Documents/backup` — um volume **VeraCrypt/TrueCrypt** oculto. Usando a senha recuperada no passo anterior:

![Montagem do volume VeraCrypt/TrueCrypt oculto e navegação até a pasta de documentos financeiros secretos](/Hacker%20Holiday%202026%20-%20THM/14º%20Level%20-%20Management%20Wants%20a%20Word/images/Mount_Vera_Vault.png)

```bash
sudo cryptsetup open --type tcrypt --veracrypt backup vera_vault
# Enter passphrase for backup: Wh4t1sV3raD0inG0nTh1sH0st

sudo cryptsetup status vera_vault
```
```
/dev/mapper/vera_vault is active.
  type:    TCRYPT
  cipher:  aes-xts-plain64
  keysize: 512 [bits]
  device:  /dev/loop0
  loop:    /home/nistezy/.../Users/vera/Documents/backup
  size:    204288 [512-byte units] (104595456 [bytes])
  mode:    read/write
```

Confirmando o tipo de sistema de arquivos dentro do mapeamento:

```bash
sudo file -sL /dev/mapper/vera_vault
```
```
/dev/mapper/vera_vault: DOS/MBR boot sector, ... FAT (32 bit) ...
```

Por segurança, o volume é fechado e reaberto em modo **somente leitura**, depois montado:

```bash
sudo cryptsetup close vera_vault
sudo cryptsetup open --type tcrypt --veracrypt --readonly backup vera_vault
sudo mkdir -p /mnt/vera
sudo mount -t vfat -o ro /dev/mapper/vera_vault /mnt/vera
ls -lah /mnt/vera
```

```
drwxr-xr-x  '$RECYCLE.BIN'
drwxr-xr-x  secret_financial_documents
drwxr-xr-x  'System Volume Information'
```

A pasta `secret_financial_documents` contém dois arquivos: `important_invoice_byte_lotus.pdf` e `transactions_q3.csv`.

---

## 🔍 Passo 7 — Encontrando a flag

Abrindo `important_invoice_byte_lotus.pdf`:

![Fatura falsa da Byte Lotus Resorts contendo a flag como item de linha](/Hacker%20Holiday%202026%20-%20THM/14º%20Level%20-%20Management%20Wants%20a%20Word/images/Flag.png)

O documento simula uma fatura da **Byte Lotus Resorts**, com um item de linha inusitado na tabela de descrição:

```
NO.  DESCRIPTION                              QTY   PRICE   TOTAL
1.   Flag: THM{1t_w4s_V3r4_A11_Al0ng?!}         1    $100    $100
```

---

## 🚩 Flag

```
THM{1t_w4s_V3r4_A11_Al0ng?!}
```

---

## 📖 Epílogo — a história por trás do vault

Entre os artefatos do laptop também estava um trecho de uma "história em quadrinhos" interna (parte do lore do CTF), que reforça o twist da flag:

![Página em quadrinhos "04 Sunrise" revelando que VERA era, ao mesmo tempo, concierge, gerente e "equipe de escalonamento" dos golpes de cripto](/Hacker%20Holiday%202026%20-%20THM/14º%20Level%20-%20Management%20Wants%20a%20Word/images/Story.png)

O quadrinho mostra VERA mandando mensagens de "bom dia" automatizadas para personagens de esquemas cripto (`Ponzi`, `Lambo`, `Vibe`), resolvendo silenciosamente centenas de tickets de reclamação e "isolando" clientes insatisfeitos com uma "equipe de escalonamento" — que, na verdade, também era só ela. A conclusão do quadrinho:

> *"It was never a bug; it was a business model."*

Ou seja: a senha guardada, o cofre escondido e a fatura falsa não eram um acidente de configuração — era a prova de que **Vera sempre soube exatamente o que estava fazendo**.

---

## 📝 Resumo da cadeia de investigação

1. **Briefing** → laptop de "Vera" (Rm 214) recebe triage forense completo (KAPE) antes do wipe.
2. **Reconhecimento da imagem** → `tree` revela hives de registro e um perfil completo do Chrome pertencente à usuária `vera`.
3. **`secretsdump` (LOCAL)** contra SAM/SYSTEM/SECURITY → recupera hashes locais e a LSA Secret `DefaultPassword: minivera`.
4. **`impacket-dpapi masterkey`** com SID + senha `minivera` → decripta a master key DPAPI da usuária.
5. **Análise manual do `DPAPI_BLOB`** do Chrome (`chrome_blob.bin`) → confirma que o GUID da master key bate com a chave recuperada.
6. **`pypykatz dpapi prekey/masterkey/chrome`** → automatiza toda a cadeia e decripta o `Login Data` do Chrome, revelando usuário `VeraSecretVault`, senha `Wh4t1sV3raD0inG0nTh1sH0st` e uma URL suspeita.
7. **`cryptsetup open --type tcrypt --veracrypt`** com a senha recuperada → monta um volume TrueCrypt/VeraCrypt oculto (`vera_vault`) em modo somente leitura.
8. **Exploração do volume montado** → pasta `secret_financial_documents` com uma fatura falsa contendo a flag como item de linha.
9. **Lore/epílogo** → confirma narrativamente que VERA sempre esteve por trás de tudo.

---