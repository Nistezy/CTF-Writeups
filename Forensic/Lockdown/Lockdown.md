# 🔍 Lockdown Lab — CTF Writeup
### CyberDefenders Blue Team Challenge | Análise Forense de Comprometimento IIS · Agent Tesla

---

| **Analista** | Mauricio Robert                                                                                  |
|-----------------------|--------------------------------------------------------------------------------------------------|
| **Organização** | Faculdade Impacta                                                                                |
| **Data do Relatório** | 07/07/2026                                                                                       |
| **Data do Incidente** | 08/07/2026 (Análise de Artefatos)                                                                |
| **Classificação** | CONFIDENCIAL                                                                                       |
| **Caso CTF** | Lockdown Lab — CyberDefenders Blue Team                                                            |
| **Ferramentas** | Wireshark · NetworkMiner · Volatility 3 · VirusTotal · Brave Search                                |

---

## 🔍 Resumo Executivo

Este writeup documenta a investigação forense digital do desafio **Lockdown Lab** (CyberDefenders), focando no comprometimento de um servidor Microsoft IIS após uma série de atividades de reconhecimento e exploração de rede. A análise combinou o exame de tráfego de rede (artefato PCAP) e forense de memória (Memory Dump), permitindo a reconstituição completa da cadeia de ataque (*Kill Chain*).

O invasor iniciou o ataque mapeando o serviço HTTP e os compartilhamentos de rede (SMB). Após identificar permissões mal configuradas, realizou o upload de um web shell (`shell.aspx`) que concedeu Execução de Código Remoto (RCE) no contexto do processo do IIS (`w3wp.exe`). A partir daí, estabeleceu um *reverse shell* e implantou um artefato persistente ofuscado com UPX, pertencente à família **Agent Tesla** (RAT / Infostealer), que passou a se comunicar ativamente com um servidor de Comando e Controle (C2).

---

## 🛠 Ferramentas Utilizadas

| Ferramenta                  | Finalidade                                                                                              |
|--------------------------------|------------------------------------------------------------------------------------------------------------|
| **Wireshark** | Análise aprofundada de pacotes de rede, decodificação de cabeçalhos HTTP e inspeção de requisições Tree Connect SMB. |
| **NetworkMiner** | Extração passiva de arquivos trafegados (web shell) e mapeamento rápido de portas e perfis de hosts da rede. |
| **Volatility 3** | Análise forense de memória volátil para extração do base address do kernel, mapeamento de processos e persistência. |
| **VirusTotal & Search** | Enriquecimento (Threat Intel) para identificação do packer, reputação de domínio C2 e identificação de família de malware. |

---

## 📋 Análise Investigativa — Perguntas e Respostas

### Q1 — Após inundar o host IIS com sondagens rápidas, o invasor revela sua origem. Qual endereço IP gerou esse tráfego de reconhecimento?

> **Resposta: `10.0.2.4`**

**Solução:** A análise inicial do fluxo de rede exibe uma volumosa quantidade de requisições sequenciais originadas do IP `10.0.2.4` direcionadas ao servidor IIS (`10.0.2.15`), caracterizando um comportamento clássico de varredura ativa (*scanning*).

![Origem do Tráfego](/Forensic/Lockdown/images/Attacker_IP_Network(1).png)
*Figura 1 — Captura mostrando as requisições originadas do IP 10.0.2.4 em direção ao alvo.*

---

### Q2 — O invasor está realizando uma enumeração direcionada contra o serviço HTTP no host IIS. Com base nos cabeçalhos de requisição HTTP, qual ferramenta está sendo utilizada?

> **Resposta: `Nmap`**

**Solução:** Ao inspecionar os detalhes dos pacotes HTTP capturados, o campo `User-Agent` contido nos cabeçalhos das requisições revela explicitamente a assinatura de varredura: `User-Agent: Mozilla/5.0 (compatible; Nmap Scripting Engine; https://nmap.org/book/nse.html)\r\n`. Isso confirma o uso dos scripts NSE do Nmap.

![Enumeração Nmap](/Forensic/Lockdown/images/Tool_of_Enumeration_Network(2).png)
*Figura 2 — Cabeçalho HTTP capturado pelo Wireshark revelando o User-Agent do Nmap Scripting Engine.*

---

### Q3 — Durante a revisão do tráfego SMB, observam-se duas requisições consecutivas de Tree Connect que expõem os primeiros compartilhamentos que o intruso sonda no host IIS. Quais são os dois caminhos UNC completos acessados?

> **Resposta: `\\10.0.2.15\Documents, \\10.0.2.15\IPC$`**

**Solução:** No fluxo de pacotes SMB2/SMB3 no Wireshark, foram isoladas as requisições de comando `Tree Connect Request`, revelando que o invasor mapeou e testou acessos primeiro no IPC administrativo e, em seguida, na pasta de Documentos.

![SMB IPC](/Forensic/Lockdown/images/UNIC_Path1-2_Network(3).png)
*Figura 3 — Wireshark exibindo a requisição Tree Connect para o caminho `\\10.0.2.15\IPC$`.*

![SMB Documents](/Forensic/Lockdown/images/UNIC_Path2-2_Network(3).png)
*Figura 4 — Wireshark exibindo a requisição Tree Connect para o caminho `\\10.0.2.15\Documents`.*

---

### Q4 — Dentro do compartilhamento, o invasor planta um payload acessível via web que garantirá a execução remota de código. Qual é o nome do arquivo malicioso que eles enviaram?

> **Resposta: `shell.aspx`**

**Solução:** Cruzando o fluxo TCP no Wireshark (TCP Stream) e a aba "Files" do NetworkMiner, foi possível visualizar o upload de um payload escrito em C# e ASP.NET gravado no servidor, nomeado como `shell.aspx`.

![Payload .aspx](/Forensic/Lockdown/images/Payload_.aspx_Used_in_Attck_Network(4).png)
*Figura 5 — NetworkMiner e Wireshark (Follow TCP Stream) exibindo o conteúdo do arquivo `shell.aspx` carregado no servidor.*

---

### Q5 — O shell recém-plantado faz uma chamada de volta para o invasor por meio de uma porta incomum, mas amigável ao firewall. Qual porta de escuta o invasor usou para o reverse shell?

> **Resposta: `4443`**

**Solução:** O mapeamento de hosts do NetworkMiner indica que, após a execução do web shell, o host do atacante (`10.0.2.4`) estava escutando ativamente (Listening) na porta TCP `4443`, que recebeu o tráfego de saída (conexão reversa) do servidor comprometido.

![Porta de Escuta](/Forensic/Lockdown/images/Listening_Port_Attack_Used_Network(5).png)
*Figura 6 — NetworkMiner mapeando a "Open TCP Port: 4443" no host do atacante (10.0.2.4).*

---

### Q6 — Seu instantâneo (snapshot) de memória captura o kernel do sistema in situ, fornecendo um contexto vital para a violação. Qual é o endereço base do kernel no dump?

> **Resposta: `0xf80079213000`**

**Solução:** A execução do framework de análise de memória Volatility 3 retornou as informações estruturais do arquivo de despejo (`windows.info`), confirmando o `Kernel Base` do sistema operacional.

![Kernel Base](/Forensic/Lockdown/images/Kernel_Base_Address_MemoryDump(1).png)
*Figura 7 — Saída do Volatility exibindo a variável Kernel Base mapeada em 0xf80079213000.*

---

### Q7 — Um serviço confiável inicia um executável desconhecido residente fora da pilha usual do IIS, sinalizando um implante de persistência. Qual é o caminho final completo em disco desse executável?

> **Resposta: `C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup\updatenow.exe`**

**Solução:** Através dos módulos de análise de processos e linha de comando do Volatility (`windows.cmdline`), identificou-se que o atacante implantou um binário anômalo chamado `updatenow.exe` diretamente na pasta global de Inicialização (Startup) do Windows, garantindo persistência na máquina.

![Persistência Startup](/Forensic/Lockdown/images/Full_Path_of_Persistence_MemoryDump(2).png)
*Figura 8 — Volatility listando o full path de persistência do executável malicioso `updatenow.exe`.*

---

### Q8 — O tráfego de saída do reverse shell é tratado por um processo integrado do Windows que também gera o executável implantado. Qual é o nome desse processo e sob qual PID ele roda?

> **Resposta: `w3wp.exe, 4332`**

**Solução:** Ao analisar a árvore de processos (`windows.pstree` e `windows.pslist`), confirmou-se que o `w3wp.exe` (IIS Worker Process) — rodando sob o PID `4332` — foi o processo responsável por despachar a execução do malware de persistência, um comportamento totalmente anômalo para o serviço web.

![Processo e PID](/Forensic/Lockdown/images/PID_Name_Process_Running_Under_MemoryDump(3).png)
*Figura 9 — Volatility exibindo o processo w3wp.exe (PID 4332) ativo na memória durante o incidente.*

---

### Q9 — A inspeção estática revela que o binário foi compactado para dificultar a análise. Qual compactador (packer) foi usado para ofuscá-lo?

> **Resposta: `UPX`**

**Solução:** A análise do binário `updatenow.exe` no VirusTotal e assinaturas YARA identificaram claramente que o executável sofreu empacotamento através do software open-source **UPX** (*Ultimate Packer for eXecutables*) para ofuscação e redução de tamanho.

![Packer UPX](/Forensic/Lockdown/images/Malware_Packer_Used_MalwareSample(1).png)
*Figura 10 — VirusTotal apontando matches de regras YARA para o packer UPX.*

---

### Q10 — A análise de inteligência de ameaças mostra o malware emitindo sinais (beaconing) para seu host de comando e controle. Qual nome de domínio totalmente qualificado (FQDN) ele contata?

> **Resposta: `cp8nl.hyperhost.ua`**

**Solução:** Dados comportamentais em sandbox e consultas de Threat Intelligence do hash investigado (relacionado ao `updatenow.exe`) confirmaram que o artefato realiza resoluções de DNS e conexões externas para o FQDN `cp8nl.hyperhost.ua` visando exfiltração de dados e recebimento de comandos (C2).

![FQDN Contactado](/Forensic/Lockdown/images/FQDN_Malware_Contact_MalwareSample(2).png)
*Figura 11 - Análise comportamental/Threat Intel detalhando a conexão de rede e o beaconing para o FQDN malicioso cp8nl.hyperhost.ua.*

---

### Q11 — O Intel de código aberto associa esse hash a um RAT comercial bem conhecido. A qual família de malware a amostra pertence?

> **Resposta: `Agent Tesla`**

**Solução:** As detecções de engine antivírus no VirusTotal, somadas à pesquisa OSINT (Open Source Intelligence), confirmaram que a amostra maliciosa pertence à clássica família de RATs e Infostealers conhecida como **Agent Tesla**.

![Agent Tesla RAT](/Forensic/Lockdown/images/RAT_Family_Used_in_Attack_MalwareSample(3).png)
*Figura 12 — VirusTotal classificando o artefato como Trojan Win32/AgentTesla, e pesquisa OSINT confirmando a natureza do RAT.*

---

## 🧬 Perfil Completo do Ataque

| Propriedade                       | Valor                                                                       |
|-----------------------------------|-----------------------------------------------------------------------------|
| IP Atacante (Recon & C2)          | `10.0.2.4`                                                                  |
| Alvo (Servidor IIS)               | `10.0.2.15`                                                                 |
| Vetor Inicial                     | Enumeração Nmap (NSE) e Exploração de permissão SMB/HTTP                    |
| Arquivo de Acesso Inicial (RCE)   | `shell.aspx`                                                                |
| Processo Explorado                | `w3wp.exe` (PID `4332`)                                                     |
| Porta de Reverse Shell            | `4443` (TCP)                                                                |
| Caminho de Persistência           | `C:\ProgramData\...\Start Menu\Programs\Startup\updatenow.exe`              |
| Método de Ofuscação               | Empacotamento via `UPX`                                                     |
| Família de Malware                | `Agent Tesla` (RAT / Infostealer)                                           |
| FQDN Comando e Controle (C2)      | `cp8nl.hyperhost.ua`                                                        |
| Kernel Base da Memória            | `0xf80079213000`                                                            |

---

## ✅ Resumo das Flags

| #  | Pergunta                                                          | Flag / Resposta                                  |
|----|-------------------------------------------------------------------|--------------------------------------------------|
| Q1 | IP que gerou tráfego de reconhecimento                            | `10.0.2.4`                                       |
| Q2 | Ferramenta utilizada nos cabeçalhos HTTP                          | `Nmap`                                           |
| Q3 | Dois caminhos UNC acessados (SMB)                                 | `\\10.0.2.15\Documents, \\10.0.2.15\IPC$`        |
| Q4 | Nome do web shell enviado                                         | `shell.aspx`                                     |
| Q5 | Porta de escuta do reverse shell                                  | `4443`                                           |
| Q6 | Endereço base do kernel no Memory Dump                            | `0xf80079213000`                                 |
| Q7 | Caminho completo do executável de persistência                    | `C:\ProgramData\...\Startup\updatenow.exe`       |
| Q8 | Nome e PID do processo integrado do Windows                       | `w3wp.exe, 4332`                                 |
| Q9 | Packer utilizado para ofuscar o malware                           | `UPX`                                            |
| Q10| FQDN do Comando e Controle contatado                              | `cp8nl.hyperhost.ua`                             |
| Q11| Família do malware RAT                                            | `Agent Tesla`                                    |

---

## 📚 Referências

- [CyberDefenders — Lockdown Lab](https://cyberdefenders.org/blueteam-ctf-challenges/lockdown-lab/)
- [Volatility 3 Documentation](https://volatility3.readthedocs.io/)
- [MITRE ATT&CK — T1547: Boot or Logon Autostart Execution](https://attack.mitre.org/techniques/T1547/)
- [MITRE ATT&CK — Agent Tesla (S0331)](https://attack.mitre.org/software/S0331/)

---