# TryHackMe — Hackers Holiday CTF
## Level 12 — After Hours

**Categoria:** Forense Digital / WMI Persistence / Malware Analysis
**Dificuldade:** Difícil

---

### 🛎️ Concierge Briefing

> Long after the front desk closes and the pool lights dim, the resort's back-office machines keep humming. Someone, or something, has been logging in during the small hours, well after the night-shift technician has gone home.
> Nothing obvious shows up in Startup, Scheduled Tasks, or the registry Run keys. Whatever's keeping itself alive is hiding somewhere quieter, tucked away in a corner of the system most tools don't think to check.

---

## 🎯 Objetivo

O briefing aponta para um mecanismo de **persistência não convencional**: o malware não está nos locais óbvios (Startup, Scheduled Tasks, Run keys). A frase-chave é *"tucked away in a corner of the system most tools don't think to check"* — uma referência direta ao **repositório WMI (Windows Management Instrumentation)**, um vetor de persistência sofisticado e frequentemente ignorado por ferramentas de análise comuns.

O material do desafio é um conjunto de arquivos do repositório WMI extraídos de uma máquina comprometida:

- `INDEX.BTR` (4.952 KB) — índice do repositório
- `OBJECTS.DATA` (23.632 KB) — dados dos objetos/classes
- `MAPPING1.MAP`, `MAPPING2.MAP`, `MAPPING3.MAP` (78 KB cada) — mapeamentos de páginas

### 🎒 Ferramentas utilizadas

- **`dissect.cim`** (biblioteca Python para parsing de repositórios WMI CIM)
- **Scripts personalizados:** `parse_wmi.py` e `search_objects.py` (fornecidos como parte do desafio)
- **CyberChef** (para decodificação Base64 da flag)

---

## 🔍 Passo 1 — Reconhecendo o material de análise

O desafio entrega os arquivos brutos do repositório WMI — a "base de dados" de configuração do WMI no Windows:

![Arquivos do repositório WMI fornecidos para análise forense](/Hacker%20Holiday%202026%20-%20THM/12º%20Level%20-%20After%20Hours/images/Itens_for_Analyze.png)

```
INDEX.BTR       4,952 KB    — índice B-tree do repositório
OBJECTS.DATA   23,632 KB    — store principal de objetos/classes/instâncias
MAPPING1.MAP       78 KB    — mapeamento de páginas lógicas→físicas (versão 1)
MAPPING2.MAP       78 KB    — mapeamento de páginas lógicas→físicas (versão 2)
MAPPING3.MAP       78 KB    — mapeamento de páginas lógicas→físicas (versão 3)
```

A **persistência via WMI** funciona criando três componentes que trabalham em conjunto dentro do repositório:

1. **Event Filter** (`__EventFilter`) — define a condição que dispara o evento (ex.: a cada X minutos, ao boot, etc.)
2. **Event Consumer** (`__EventConsumer`) — define o que executar quando o filtro disparar (ex.: `CommandLineEventConsumer` para RCE)
3. **Filter-to-Consumer Binding** (`__FilterToConsumerBinding`) — conecta o filtro ao consumer

Nenhum desses três elementos aparece no Registro do Windows, em Scheduled Tasks ou em Startup — eles vivem exclusivamente no repositório WMI, o que os torna invisíveis para a maioria das ferramentas de análise automáticas.

---

## 🔍 Passo 2 — Enumerando o repositório com `parse_wmi.py`

O script `parse_wmi.py` utiliza a biblioteca `dissect.cim` para abrir e percorrer o repositório, listando namespaces e classes disponíveis:

![Enumeração de namespaces e classes do repositório WMI](/Hacker%20Holiday%202026%20-%20THM/12º%20Level%20-%20After%20Hours/images/Enum_Classes.png)

```
Root namespaces:
  <Namespace root\subscription>
  <Namespace root\DEFAULT>
  <Namespace root\CIMV2>
  <Namespace root\msdt>
  ...
  <Namespace root\Hardware>
  <Namespace root\ServiceModel>
  ...
```

O namespace **`root\subscription`** já chama atenção imediatamente — é exatamente o namespace padrão onde são armazenadas as **assinaturas WMI de persistência** (`__FilterToConsumerBinding`, `__EventFilter`, e os consumers).

---

## 🔍 Passo 3 — Encontrando as classes de persistência

Uma segunda execução do script, focada especificamente no namespace `root\subscription`, enumera todas as classes relacionadas à persistência no WMI:

![Classes de persistência encontradas no namespace root\subscription](/Hacker%20Holiday%202026%20-%20THM/12º%20Level%20-%20After%20Hours/images/Properites_of_Classes.png)

```
[CLASS] __EventProviderRegistration
[CLASS] __FilterToConsumerBinding
[CLASS] __EventConsumer
[CLASS] __NamespaceOperationEvent
[CLASS] __EventFilter
[CLASS] __NamespaceDeletionEvent
...
[CLASS] LogFileEventConsumer
[CLASS] ActiveScriptEventConsumer
[CLASS] NTEventLogEventConsumer
[CLASS] SMTPEventConsumer
[CLASS] CommandLineEventConsumer
```

A classe **`CommandLineEventConsumer`** é a mais relevante para execução de código arbitrário — ela executa um comando de linha ao ser acionada pelo filtro vinculado. Mais abaixo, vemos a contagem de instâncias de cada classe crítica:

```
[CLASS] __FilterToConsumerBinding  → [INSTANCE 1]  Total Instances: 1
[CLASS] __EventFilter              → [INSTANCE 1,2] Total Instances: 2
[CLASS] CommandLineEventConsumer   → 1 instância encontrada
```

---

## 🔍 Passo 4 — Examinando as instâncias e suas propriedades

Fazendo o dump das instâncias das classes encontradas:

![Propriedades das instâncias de EventFilter, FilterToConsumerBinding e CommandLineEventConsumer](/Hacker%20Holiday%202026%20-%20THM/12º%20Level%20-%20After%20Hours/images/Functions_of_Properites.png)

Dados extraídos de `__FilterToConsumerBinding`:

```
Consumer: 'NTEventLogEventConsumer.Name="SCM Event Log Consumer"'
Filter:   '__EventFilter.Name="SCM Event Log Filter"'
```

E a instância do `__EventFilter` com nome `EngineTelemetryFilter`:

```
Name:  'EngineTelemetryFilter'
Query: 'SELECT * FROM __InstanceModificationEvent WITHIN 60 WHERE
        TargetInstance ISA "Win32_LocalTime" AND
        TargetInstance.Minute = 30'
```

O filtro dispara **a cada vez que o minuto do relógio é 30** — ou seja, duas vezes por hora, todos os dias, de forma silenciosa. A instância do `CommandLineEventConsumer` vinculada tem a propriedade `CommandLineTemplate` preenchida com um **payload codificado em Base64 passado diretamente ao PowerShell**.

---

## 🔍 Passo 5 — Extraindo e decodificando o payload

A propriedade `CommandLineTemplate` do `CommandLineEventConsumer` contém o payload malicioso completo:

![Payload completo extraído do CommandLineEventConsumer com o comando PowerShell codificado](/Hacker%20Holiday%202026%20-%20THM/12º%20Level%20-%20After%20Hours/images/Enum_Classes_Relationed_Pesistence.png)

```
cmd /C powershell.exe -Sta -Nop -Window Hidden -enc
JAB8AGkAbABBAGMAQgAcGAwaYQB2AGkAAQgAdAZBhAIATwBpAFQBXABjSGAdAIAQgB2...
[base64 longo]
```

A estratégia do malware é clara: `cmd /C powershell.exe -Sta -Nop -Window Hidden -enc <base64>` — a flag `-enc` do PowerShell aceita um payload inteiro em Base64 (UTF-16LE), executando-o completamente em memória, **sem criar arquivos em disco**, e com janela oculta. Combinado com o event filter de timer, isso garante execução silenciosa e periódica.

O script `parse_wmi.py` automatiza toda a pipeline de extração e análise:

1. **Abre o repositório WMI** via `dissect.cim`
2. **Localiza a classe `Win32_HardwareTelemetry`** em `root\CIMV2` e extrai sua propriedade `ConfigData`
3. **Decodifica o Base64** contido em `ConfigData` → `payload_compressed.bin`
4. **Descomprime via raw DEFLATE** → `payload.bin` (4.096 bytes)
5. **Analisa o PE** — confirma header `MZ`, assinatura `PE\x00\x00` válida, PE32
6. **Extrai strings** do binário → `payload_strings.txt`
7. Identifica no output uma string interessante: `c:\net user patch VEhNe1A0dNoX29wM251ZF90aDNfJS2QwMJ9 /add`

---

## 🔍 Passo 6 — Execução do `parse_wmi.py` e descoberta da flag

![Execução completa do parse_wmi.py, identificando o payload PE32 e a string com a flag](/Hacker%20Holiday%202026%20-%20THM/12º%20Level%20-%20After%20Hours/images/Flag.txt.png)

```
======================================================================
 WMI FORENSICS - EngineTelemetry
======================================================================
[+] Verificando arquivos...
    [OK] INDEX.BTR (5,070,848 bytes)
    [OK] OBJECTS.DATA (24,190,976 bytes)
    [OK] MAPPING1.MAP (79,528 bytes)
    [OK] MAPPING2.MAP (79,528 bytes)
    [OK] MAPPING3.MAP (79,528 bytes)

[+] ABRINDO REPOSITÓRIO WMI
[+] WMI repository aberto.

[+] PROCURANDO Win32_HardwareTelemetry
[+] Namespace: <Namespace root\CIMV2>
[+] Classe encontrada: Win32_HardwareTelemetry
[+] Instances: 0
[+] Propriedades:
    - ConfigData
[+] ConfigData encontrada.
[+] Tipo: <class 'str'>
[+] Tamanho: 2212 caracteres

[+] DECODIFICANDO BASE64
[+] Salvo: configdata.b64
[+] Base64 chars: 2212
[+] Decoded bytes: 1658
[+] Header: e5 6f ef 65 45 18 ff de 76 29 65 81 4a c1 00 95...

[+] DESCOMPRIMINDO DEFLATE
[*] zlib falhou: incorrect header check
[+] Tentando raw DEFLATE...
[+] raw DEFLATE OK.
[+] Payload descomprimido: 4096 bytes

[+] ANÁLISE DO PAYLOAD
[+] Tamanho: 4096 bytes
[+] Primeiros 32 bytes: 4d 5a 90 00 03 00 00 00 04 00 00 00 ff ff 00 00...
[+] Header: MZ
[+] Parece ser um executável PE.
[+] PE header offset: 0x80
[+] PE signature: b'PE\x00\x00'
[+] PE válido detectado.
[+] Machine: 0x014C
[+] Sections: 3
[+] Optional Header Magic: 0x010B
[+] PE32

[+] EXTRAINDO STRINGS
[+] ASCII strings: 51
[+] UTF-16LE strings: 21
[+] Strings salvas em: payload_strings.txt

[+] Strings potencialmente interessantes:
      <assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
      ...
      cmd.exe
      c:\net user patch VEhNe1A0dNoX29wM251ZF90aDNfJS2QwMJ9 /add
      Assembly Version
```

A string `c:\net user patch VEhNe1A0dNoX29wM251ZF90aDNfJS2QwMJ9 /add` revela o comportamento final do malware: **criar um usuário chamado `patch`** com a senha `VEhNe1A0dNoX29wM251ZF90aDNfJS2QwMJ9` — que é, na verdade, a **flag em Base64**.

---

## 🔍 Passo 7 — Strings do payload e decodificação da flag

Examinando o arquivo `payload_strings.txt` gerado:

![Strings ASCII e UTF-16LE extraídas do payload PE, incluindo o comando net user com a flag](/Hacker%20Holiday%202026%20-%20THM/12º%20Level%20-%20After%20Hours/images/Payload_Strings.png)

A seção UTF-16LE confirma o comando completo:

```
bytelotusdc
cmd.exe
/c net user patch VEhNe1A0dNoX29wM251ZF90aDNfJS2QwMJ9 /add
Execution halted: Environment mismatch.
```

O assembly .NET, compilado com configuração `asInvoker` (sem elevação de privilégio declarada), tenta criar um usuário local oculto usando como senha exatamente a string Base64. Decodificando essa string no **CyberChef** (`From Base64`):

**Input:**
```
VEhNe1A0dNoX29wM251ZF90aDNfJS2QwMJ9
```

**Output:**
```
THM{P4tch_op3ned_th3_BackD00r}
```

---

## 🚩 Flag

```
THM{P4tch_op3ned_th3_BackD00r}
```

---

## 📝 Resumo da cadeia de investigação

1. **Briefing** → persistência não visível em locais comuns (Startup, Scheduled Tasks, Registry Run keys); aponta para o repositório WMI.
2. **Artefatos forenses entregues** → cinco arquivos do repositório WMI: `INDEX.BTR`, `OBJECTS.DATA`, `MAPPING1-3.MAP`.
3. **Enumeração de namespaces** (`parse_wmi.py` + `dissect.cim`) → namespace `root\subscription` contém o mecanismo de persistência; `root\CIMV2` contém a classe `Win32_HardwareTelemetry` com payload armazenado.
4. **Classes de persistência** → `__FilterToConsumerBinding` (1 instância), `__EventFilter` (2 instâncias, incluindo `EngineTelemetryFilter`), `CommandLineEventConsumer` (payload PowerShell `-enc` base64).
5. **Event Filter** → dispara `a cada minuto = 30` (duas vezes por hora), usando `Win32_LocalTime`, sem deixar rastro em disco.
6. **Classe `Win32_HardwareTelemetry`** em `root\CIMV2` → propriedade `ConfigData` armazena um payload Base64 de 2212 chars.
7. **Decodificação + raw DEFLATE** → binário PE32 de 4096 bytes (assembly .NET).
8. **Extração de strings** → string UTF-16LE revela `cmd.exe /c net user patch <BASE64> /add`.
9. **CyberChef (From Base64)** → decodifica a "senha" → flag.

---