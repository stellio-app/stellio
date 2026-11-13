@@@ Home | Início
# Wiki do Stellio
{{img:dashboard}}


O **Stellio** é o gestor de arquivos 3D para makers e proprietários de impressoras 3D. Centraliza a sua biblioteca (STL, 3MF, OBJ, STEP, PLY, AMF), automatiza as tarefas repetitivas e integra-se no seu fluxo de impressão.

> 🔒 **Filosofia**: os seus dados ficam consigo. Tudo funciona localmente; por predefinição, nada sai do seu computador.

## Por onde começar?

| Quero… | Página |
|---|---|
| Instalar o Stellio | [Instalação](pt-Installation) |
| Dar os primeiros passos | [Primeiros passos](pt-Getting-Started) |
| Gerir os meus arquivos 3D | [Biblioteca](pt-Library) |
| Ligar as minhas impressoras | [Impressoras](pt-Printers) |
| Acompanhar as minhas bobinas | [Filamento](pt-Filament) |
| Transferir modelos | [Transferências](pt-Downloads) |
| Usar a IA e o S.O.S Print | [Inteligência artificial](pt-AI) |
| Calcular custos, orçamentos, faturas | [Custos e gestão](pt-Costs-and-Management) |
| Aceder pelo telemóvel | [Acesso remoto e móvel](pt-Remote-Access) |
| Instalar no Raspberry Pi / Proxmox | [Edição servidor](pt-Server-Edition) |
| Configurar, fazer cópias, perceber os meus dados | [Definições e dados](pt-Settings-and-Data) |
| Resolver um problema | [Resolução de problemas](pt-Troubleshooting) |
| Contribuir para o projeto | [Contribuir](pt-Contributing) |

## Ligações úteis

- 🌐 Site: [stellio-app.com](https://stellio-app.com) — ▶ [demonstração online (só leitura)](https://demo.stellio-app.com)
- 📦 [Transferências (Releases)](https://github.com/stellio-app/stellio/releases)
- 🐛 [Reportar um erro](https://github.com/stellio-app/stellio/issues) · 💡 [Propor uma ideia](https://github.com/stellio-app/stellio/discussions) · 💬 [Discord](https://discord.gg/ySxpHvS6bd)
- 📜 Licença **AGPL v3**

@@@ Installation | Instalação
# Instalação

| Plataforma | Ficheiro / método | Modo |
|---|---|---|
| 🪟 Windows | `Stellio-Setup-<version>.exe` | Aplicação de secretária |
| 🪟 Windows portátil | `Stellio-v<version>-portable-win64.zip` | Aplicação de secretária, sem instalação |
| 🍎 macOS | `.dmg` (Apple Silicon `arm64` ou Intel `x86_64`) | Aplicação de secretária |
| 🐧 Linux | `Stellio-v<version>-x86_64.AppImage` | Aplicação de secretária |
| 🍓 Raspberry Pi / Linux | `install-pi.sh` | Servidor (navegador) |
| 🖥️ Proxmox VE | `stellio-lxc.sh` | Contentor LXC com um só comando |
| 📲 Android | APK complementar | Ver [Acesso remoto e móvel](pt-Remote-Access) |

Todos os ficheiros estão na página [Releases](https://github.com/stellio-app/stellio/releases), cada um com uma soma de verificação `.sha256`.

## Windows

1. Transfira o instalador a partir das Releases.
2. Execute `Stellio-Setup-<version>.exe`.
3. Pronto.

**Versão portátil**: descompacte em qualquer lugar (disco, pen USB) e execute `Stellio.exe`. Os seus dados ficam na pasta `data` junto do executável (mantenha o ficheiro `portable.flag`).

> ⚠️ O instalador **não está assinado**: o Windows SmartScreen pode mostrar um aviso. Verifique o `.sha256` se quiser; a atualização integrada confirma-o antes de instalar.

## macOS

Abra o `.dmg` e arraste o Stellio para Aplicações. Escolha o ficheiro adequado ao seu Mac: `arm64` (M1, M2, M3…) ou `x86_64` (Intel). As versões não são notarizadas: no primeiro arranque, clique com o botão direito → **Abrir**.

> Se o ecrã ficar branco: a porta 5000 pode estar ocupada pelo «Recetor AirPlay» do macOS. O Stellio escolhe então automaticamente outra porta livre. Ver [Resolução de problemas](pt-Troubleshooting).

## Linux (AppImage)

```bash
chmod +x Stellio-v*-x86_64.AppImage
./Stellio-v*-x86_64.AppImage
```
O AppImage inclui as suas informações de atualização (`.zsync`).

## Raspberry Pi / servidor Linux

Modo **servidor sem interface**: o Stellio funciona em segundo plano e usa-se a partir de um navegador. Detalhes em [Edição servidor](pt-Server-Edition).

```bash
curl -O https://raw.githubusercontent.com/stellio-app/stellio/main/install-pi.sh
chmod +x install-pi.sh
./install-pi.sh
```

## Proxmox VE

Na **Shell do anfitrião Proxmox**:
```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/stellio-app/stellio/main/stellio-lxc.sh)"
```
Detalhes em [Edição servidor](pt-Server-Edition).

## Atualizações

- **Secretária**: o Stellio deteta novas versões no GitHub e aplica um patch `.zip` (o mesmo mecanismo no Windows, macOS e Linux). O widget «Atualização» do painel abre a janela de atualização.
- **Servidor**: a mesma atualização automática, ou `update-stellio` (contentor LXC) / `./install-pi.sh` (Raspberry Pi).
- No primeiro arranque de cada versão, os módulos em falta (orçamentos PDF, importação de folhas de cálculo, notificações…) são transferidos automaticamente.

@@@ Getting-Started | Primeiros passos
# Primeiros passos
{{img:library}}


## 1. Primeiro arranque
O Stellio mostra uma **visita guiada** e uma lista «Primeiros passos». Pode reiniciar a visita a qualquer momento nas Definições.

## 2. Criar a sua conta
As contas são **locais**: palavra-passe + código de recuperação + pergunta secreta. A reposição da palavra-passe é 100 % local, sem e-mail nem internet.

## 3. Adicionar as suas fontes
Uma **fonte** é uma pasta ou partilha que contém os seus modelos:
- pasta local, ficheiro avulso, partilha **SMB** ou **NFS**;
- as pastas 3D detetadas no seu computador são-lhe **sugeridas** e adicionam-se com um clique;
- para cada fonte, escolhe os tipos de ficheiro apresentados.

O Stellio analisa então os seus ficheiros e gera as miniaturas 3D em segundo plano.

## 4. Adicionar uma impressora (opcional)
Abra a página **Impressoras**: a descoberta de rede propõe as máquinas detetadas. Ver [Impressoras](pt-Printers).

## 5. Escolher o seu slicer
O Stellio deteta automaticamente os slicers instalados (OrcaSlicer, Bambu Studio, PrusaSlicer, Cura…). O botão de envio abre o ficheiro diretamente no slicer.

## Painel
A página inicial reúne impressões em curso, stock baixo, impressões recentes e ficheiros recentes. Os **widgets** (cerca de vinte) reordenam-se arrastando e largando e podem ser ocultados: impressões em curso, stock baixo, últimos S.O.S Print, sugestões, instâncias do Stellio, projetos concluídos, galeria, orçamentos…

## Ferramentas do dia a dia
- **Paleta de comandos** `Ctrl+K`: navegar, executar uma ação, encontrar um ficheiro, uma etiqueta, uma bobina ou um perfil.
- **Centro de notificações** (sino): fim de impressão, falha, manutenção, stock baixo, secagem de bobinas.
- **Widget flutuante** com o progresso da impressão em curso, visível em todas as páginas.
- **Atalhos de teclado**: ver [Definições e dados](pt-Settings-and-Data).

@@@ Library | Biblioteca
# Biblioteca
{{img:library}}


## Fontes e miniaturas
- Várias fontes: pastas locais, ficheiros, partilhas SMB/NFS.
- **Miniaturas 3D automáticas** (PyRender, ou um renderizador por CPU de recurso) com pré-visualização ampliada ao passar o rato.
- A geração **faz pausa assim que usa a aplicação** e retoma depois.
- Definição **Desempenho das miniaturas**: Automático / Eco / Normal / Rápido.
- Formatos: STL, 3MF (incluindo multiplaca e PrusaSlicer), OBJ, STEP/STP, PLY, AMF (convertidos para STL para os slicers que não os leem) e arquivos compactados (ZIP, RAR, 7z, TAR) que se podem explorar diretamente.

## Organizar
- **Etiquetas** coloridas, com etiquetagem automática por IA; etiquetar vários ficheiros com um clique.
- **Favoritos**, filtros avançados (tipo, tamanho, peso, estado de impressão), **filtros guardados**.
- Filtros de estado: «Enviado ao slicer», «Já impresso», «Já bem-sucedido», «Já falhado».
- **Filtro «Stock de filamento»**: mantém apenas os ficheiros imprimíveis com as bobinas que possui.
- A ordenação, a pesquisa e os filtros são **memorizados** ao reabrir a aplicação.
- Fila **«Imprimir em breve»**, reordenável e enviável ao slicer.
- **Renomeação em massa** (procurar/substituir, prefixo, sufixo, numeração) com pré-visualização.
- **Anular eliminações** (`Ctrl+Z`) graças a uma reciclagem temporária de 5 minutos; vale também para etiquetas, projetos e fontes.
- Seleção rápida: `Shift+clique` para um intervalo, setas + `Enter`.
- **Deteção de duplicados** (exatos e de geometria semelhante).
- **Origem do modelo**: ligação de origem, autor, licença, notas, data de transferência.
- **Arrastar e largar** ficheiros 3D a partir do explorador, também através do navegador.

## Pesquisa
- Pesquisa clássica e **pesquisa semântica por IA** («procuro um suporte para…»), com as pesquisas recentes memorizadas.
- **Coleções inteligentes**.

## Projetos / montagens
Agrupe vários ficheiros para um mesmo objeto.
- 3MF **multiplaca**: ao adicioná-lo a um projeto, é dividido num 3MF por placa (6 placas = 6 ficheiros), guardados numa pasta oculta.
- Ação **«Dividir placas»** no menu ⋯ de um ficheiro.
- Cartão de projeto: clique na miniatura = visualizador 3D; o filtro «Todos / Em curso / Concluídos» é memorizado; **Custo do projeto** com um botão.

{{img:projects}}

## Visualizador 3D e ferramentas
- **Visualizador 3D** (Three.js, funciona offline), navegação entre placas.
- **Disposição automática** na mesa (rectpack, ou silhueta real com shapely).
- **Reparação de malha** (trimesh + pymeshfix) com comparação antes/depois.
- **Conversor** STL ↔ 3MF ↔ OBJ.
- **Análise de imprimibilidade** (saliências) e **orientações sugeridas**.
- **Verificação de integridade** (ficheiros corrompidos ou em falta).
- **Estatísticas** detalhadas (formatos, plataformas, fiabilidade dos perfis).

{{img:viewer}}

## Histórico e fotos
- **Histórico** paginado por semanas, com avaliação sucesso/falha (que alimenta a IA), botões **Ver ficheiro** e **Reimprimir**, filtros por plataforma, resultado e datas.
- **Galeria de fotos** de impressão. A foto de fim de impressão é depois marcada como *Sucesso* ou *Falha* com um clique.
- **Os meus G-codes**: G-codes ligados a um ficheiro, transferência e botão **Abrir no slicer**.
- **Cópia de segurança** da biblioteca: ver [Definições e dados](pt-Settings-and-Data).

@@@ Printers | Impressoras
# Impressoras
{{img:printers}}


## Marcas suportadas

| Marca | Modelos | Ligação |
|---|---|---|
| **Bambu Lab** | X1/X1C/X1E, X2D, P1P/P1S, P2S, A1/A1 mini, H2D/H2S/H2C | MQTT (LAN + nuvem): acompanhamento, AMS, câmara, descoberta SSDP |
| **Prusa** | MK4, MK3.9, MK3.5, MINI+, XL, CORE One | PrusaLink (HTTP) |
| **Creality** | Séries K1/K2, Ender-3 V3, Hi | WebSocket: acompanhamento, CFS, descoberta UDP |
| **Elegoo** | Centauri Carbon 1 e 2, séries de resina Saturn/Mars | SDCP (WebSocket) |
| **FlashForge** | Adventurer 5M/5M Pro, AD5X | API proprietária |
| **Klipper / Moonraker** | Qualquer máquina Klipper (Voron…) | HTTP: acompanhamento, envio, câmara, horas exatas |
| **OctoPrint** | Qualquer impressora controlada pelo OctoPrint | HTTP |

Os outros modelos que falam o mesmo protocolo costumam funcionar. Diga-nos no GitHub se o seu funciona.

## Adicionar uma impressora
- **Descoberta automática** da rede local (SSDP, difusão UDP, sondagens dirigidas): as impressoras detetadas adicionam-se com um clique.
- Caso contrário, introdução manual (tipo, modelo, endereço, chave de acesso).
- Indique o **volume de impressão** (X, Y, Z): o Stellio avisa antes do envio se a peça for demasiado grande.

## Acompanhamento
- Temperatura, progresso, câmara em direto; miniatura e nome do ficheiro em curso no cartão.
- Contador automático de horas de impressão.
- **Widget flutuante** de progresso; fica à esquerda da seta «subir» quando esta aparece.

## Enviar ao slicer / à impressora
- Janela de envio com **pré-visualização rápida** (peso, tempo estimado), **escolha da bobina** e calibrações recordadas.
- **Verificação antes da impressão**: bobina que precisa de secagem, filamento abrasivo (aconselha-se bico de aço endurecido), calibração em falta, volume de impressão, material suficiente.
- **Reimprimir como da última vez** a partir do histórico.
- **Modo colaborativo leve**: avisa se outro dispositivo estiver a ver o ficheiro ou antes de um envio duplicado.
- **Abrir no slicer** a partir de «Os meus G-codes».

## Durante a impressão
- **Tomada inteligente** (Shelly, Tasmota, Home Assistant): o Stellio lê os watts e regista o consumo real (kWh) e o custo.
- **Consumo real de filamento**, registado após a impressão.
- **Foto de fim de impressão** tirada quando a impressão chega aos **100 %** (a peça ainda está na mesa), uma única foto para avaliar *Sucesso/Falha*.
- **Vigilância de falhas por IA** (Ollama com visão, 100 % local): alerta perante esparguete ou peça descolada, **nunca uma paragem automática**.
- **Timelapse** automático (câmara → vídeo MP4, requer ffmpeg).
- **Ligações de partilha do estado**, só de leitura.

## Manutenção
- **Manutenção preditiva** com tarefas próprias de cada marca.
- **Peças de desgaste** (bicos, placas, correias…) com alertas de stock, ligadas às tarefas de manutenção.
- **Calibrações** (fluxo, pressure advance, temperaturas) por filamento e impressora.

@@@ Filament | Filamento
# Filamento

## Fontes de inventário
| Fonte | Detalhes |
|---|---|
| **Spoolman** | Deteção automática na rede. O Stellio **já não lhe escreve** o consumo (evita a contagem a dobrar). |
| **Manual** | Bobinas introduzidas à mão, importação Excel/CSV. |
| **TigerTag** | Identificação NFC/RFID. Início de sessão com e-mail e palavra-passe (só se guarda um token cifrado) ou reutilização de uma sessão do TigerTag Studio. **Só leitura.** |
| **OpenPrintTag** | Norma aberta de etiquetas NFC: importação/exportação de ficheiros `.bin`, leitura/escrita a partir da app Android, peso consumido sempre atualizado. |
| **Bambu AMS / Creality CFS** | Leitura dos slots. |

**Open Filament Database**: procure uma bobina por marca, material e cor e crie-a com um clique (peso, diâmetro e densidade preenchidos).

## No dia a dia
- **Consumo automático** ao enviar ao slicer, com verificação de compatibilidade (há material suficiente?).
- **Alertas de stock baixo** no arranque, limite ajustável, caixa «A encomendar» e ligação de compra.
- **Voltar a comprar uma bobina**: primeiro a loja do fabricante (Arianeplast, Bambu Lab, Polymaker, eSUN, Sunlu…), depois lojas gerais; o stock é verificado automaticamente quando o site o permite.
- **Secagem**: registo, estado (seca / precisa de secagem) consoante o material, temperatura e duração sugeridas, lembretes.
- **Ficha da bobina**: impressões, gramas, custo e diferença não acompanhada.

## Pesagem e previsão
O bloco **Pesagem e previsão de filamento** estima a **data de esgotamento** de cada bobina a partir do seu consumo diário.
- O peso restante vem de uma pesagem manual ou do TigerTag.
- Os pesos do TigerTag alimentam **apenas a previsão**: só aparecem aqui para uma bobina **prestes a acabar** (14 dias ou menos). O resto está no inventário.
- Um formulário de pesagem manual está sempre disponível.

{{img:filament}}

## Previsão de consumo
A biblioteca pode mostrar um **aviso de reposição** quando o stock não chega para os seus favoritos.

@@@ Downloads | Transferências
# Transferências

Transfira modelos diretamente para as suas fontes a partir de várias plataformas:

| Plataforma | Início de sessão |
|---|---|
| **Printables** | API GraphQL |
| **MakerWorld** | Início de sessão Bambu Lab em 2 passos |
| **Thingiverse** | Chave de API |
| **Nexprint** (Elegoo) | E-mail e palavra-passe da conta, guardados cifrados |
| **Creality Cloud** | Nas Definições (credenciais cifradas; início de sessão com Google não suportado) |
| **Snapmaker Space** | Igual |

- **Ctrl+N** abre uma nova transferência.
- O ficheiro chega à fonte que escolher e a **origem do modelo** (ligação, autor, licença) é guardada.
- **Nova versão**: todos os dias, o Stellio verifica se os modelos transferidos (Printables, MakerWorld, Thingiverse) foram atualizados.
- **Os meus gostos / As minhas criações**: as contas ligadas são testadas em cada arranque do ambiente de secretária (a cada 24 h no servidor).
- **Ligações úteis**: lojas, fabricantes, sites de modelos e recursos, em secções recolhíveis.

@@@ AI | Inteligência artificial
# Inteligência artificial

## IA local (Ollama)
Por predefinição, a IA funciona **100 % localmente** com o [Ollama](https://ollama.com/). Pode ser desativada.

Funções:
- **Etiquetagem automática** e **descrição** dos modelos;
- **Pesquisa semântica** em linguagem natural;
- **Análise de imprimibilidade** e **orientações sugeridas**;
- **Recomendação de perfil de slicer** (geometria + histórico de sucessos);
- **Estimativa do tempo de impressão** antes do fatiamento;
- **Vigilância de falhas** (modelo de visão).

O endereço do servidor Ollama define-se nas Definições (`ollama_url`): pode apontar para uma máquina remota mais potente (útil num Raspberry Pi).

## IA online (edição servidor, opcional)
Em vez do Ollama, use o **Claude** (Anthropic), o **ChatGPT** (OpenAI) ou o **Gemini** (Google) com a **sua própria chave de API** (Definições → Inteligência artificial).
- A chave é cifrada no servidor e nunca é devolvida ao navegador.
- Os pedidos (nomes de ficheiros, etiquetas, descrições, fotos do S.O.S Print) vão para o fornecedor escolhido e são faturados na sua chave.
- O Ollama continua a ser a opção predefinida.

## S.O.S Print
Diagnóstico **adaptativo** de uma falha de impressão:
1. Descreve o problema (foto possível em cada passo) e, se quiser, as definições usadas (temperaturas, velocidades, retração…).
2. O Stellio faz **uma pergunta de cada vez** (4 no máximo) e reduz em direto uma lista de hipóteses.
3. Apresenta um **diagnóstico final**.

As conversas são guardadas: reabra-as ou marque-as como resolvidas.

> ℹ️ Os resultados «Sucesso / Falha» que avalia no histórico melhoram as recomendações.

@@@ Costs-and-Management | Custos e gestão
# Custos e gestão
{{img:management}}


## Cálculo do custo de impressão
Material, eletricidade, desgaste da máquina (por hora), custos fixos, margem em % e quantidade: preço unitário e total ao cêntimo.
- A **margem predefinida** define-se uma vez em *Definições → Preços de impressão*; o histórico mostra o **preço de venda** junto ao custo, enquanto as estatísticas mantêm o custo real.
- **Custo do projeto**: o mesmo cálculo para todos os ficheiros de um projeto.
- **Tomada inteligente**: a potência medida substitui a estimativa de eletricidade.
- **Pegada de CO₂** das suas impressões (material + eletricidade).

## Orçamentos PDF
Gerados a partir da calculadora: cliente, designação, notas; cabeçalho configurável (nome/empresa, logótipo, morada, telefone, e-mail, site, NIF) e avisos legais no rodapé. Cada orçamento é conservado (cópia PDF) e consultável no widget **Orçamentos**.

## Ecrã «Gestão»
Visível quando a opção *Ativar as funções de custos, orçamentos e faturação* está marcada:
- **Orçamentos de clientes**: uma **ligação de acompanhamento** permite ao cliente ver, aceitar ou recusar o orçamento online; a aceitação cria a tarefa de impressão e mostra os seus dados de sinal. **O Stellio não processa qualquer pagamento.** As ligações são sempre externas; se o acesso remoto estiver desativado, o ecrã propõe ativá-lo com um clique.
- **Contabilidade**: exportação mensal ZIP (CSV dos documentos, PDF das faturas, totais por mês).
- **Stock de peças acabadas**: limite de alerta e reposição (tarefa criada à mão ou automaticamente).

## Oficina
- **Fila de encomendas** com margem real, agenda de clientes, pagamentos, faturas de sinal e notas de crédito, e-mail SMTP, exportação CSV.
- **Página pública de acompanhamento** por encomenda, sem conta: nunca mostra preços, margem nem notas internas.
- **Distribuição inteligente**: o Stellio propõe a impressora mais adequada para cada tarefa (livre, material carregado, fila) **sem nunca iniciar uma impressão**.
- **Resumo diário ou semanal** por notificação e push (tarefas, atrasos, energia, bobinas, faturas, stock).
- **Partilha de perfis de slicer** com uma instância emparelhada.

## Relatórios
- **Fiabilidade**: taxa de sucesso e custo das falhas por perfil, material, impressora ou bobina.
- **Relatório mensal** comparado com o mês anterior, exportável em PDF.
- **Relatório de impressão** partilhável (imagem PNG) a partir do histórico.
- **Energia** real por tomada inteligente.



{{img:stats}}
@@@ Remote-Access | Acesso remoto e móvel
# Acesso remoto e móvel

## Telemóvel e tablet
- **Código QR** de acesso móvel à biblioteca (**PWA instalável**).
- **App Android complementar**: um código QR próprio (Definições → acesso móvel) transfere o APK. Gere endereços interno e externo com alternância automática, emparelhamento por QR, fotos diretamente a partir de uma impressão e leitura/escrita de etiquetas NFC OpenPrintTag.
- **Modo oficina** em ecrã inteiro para tablet/telemóvel.

## Acesso remoto
- **Cloudflare Tunnel** (gratuito, endereço aleatório ou fixo), ou um **endereço personalizado** (nome de domínio, DynDNS, VPN, Tailscale…) para evitar o Cloudflare, com regresso ao Cloudflare com um clique.
- **Ligações de partilha** temporárias (24 h, uso único).

## Contas
- **Contas locais** com código de recuperação e pergunta secreta.
- **Confirmação de sessão**: ao abrir a app com uma sessão guardada, o Stellio pede para confirmar a conta.
- **Contas de convidado só de leitura**: partilhe biblioteca, impressoras e stock sem risco.
- Num PC, o acesso por navegador à app do Windows está bloqueado (token interno): use a janela da aplicação.

## Várias instâncias do Stellio
- As outras instalações da rede local são **detetadas** e adicionam-se com um clique (introduza a sua chave local).
- **Enviar um ficheiro** para outra instância, para a pasta que escolher.
- Widget de estado das instâncias no painel.

## Notificações
- Notificações nativas do **Windows**, notificações do **navegador** (Pi, telemóvel).
- **Push**: ntfy, Telegram, Discord ou webhook, mesmo com a janela fechada (fim de impressão, falha, manutenção, stock).

## Domótica
- **MQTT / Home Assistant**: publicação do estado e descoberta automática; dispositivo MQTT «Stellio» e sensores.

@@@ Server-Edition | Edição servidor
# Edição servidor

A **edição servidor** ativa-se em Linux (Raspberry Pi, VM, LXC, Docker) ou com `STELLIO_HEADLESS=1`. O Windows e o macOS mantêm a aplicação de secretária. O Stellio funciona em segundo plano e usa-se a partir de um navegador: `http://<ip>:5000`.

## Raspberry Pi / Linux
Requisitos: recomenda-se Raspberry Pi 4 ou 5, Raspberry Pi OS de **64 bits**.

O `install-pi.sh` instala as dependências do sistema (`ffmpeg`, `unrar`, bibliotecas de renderização 3D), um ambiente Python dedicado e um **serviço systemd** `stellio` que arranca com o sistema e reinicia em caso de falha.

```bash
sudo systemctl status stellio
sudo systemctl restart stellio
sudo journalctl -u stellio -f
```
Pouca RAM? Aumente o swap se a instalação das dependências Python falhar e volte a executar o script.

## Proxmox VE (contentor LXC)
O script `stellio-lxc.sh` propõe definições **predefinidas** ou **avançadas** (CTID, núcleos, RAM, disco, bridge, VLAN, DHCP ou IP fixo, armazenamento, pasta do anfitrião a montar) e depois:
- cria um contentor **Debian 12 sem privilégios** (2 núcleos, 2 GB de RAM, 32 GB de disco, arranque automático);
- instala nele o Stellio com o `install-pi.sh`;
- mostra o endereço `http://<ip-do-contentor>:5000` e a palavra-passe de root.

```bash
pct exec <CTID> -- update-stellio              # atualizar
pct exec <CTID> -- journalctl -u stellio -f    # registos
```
- **Modo não interativo**: variáveis `var_mode=default var_cpu=4 var_ram=4096 var_disk=16 var_ip=192.168.1.50/24 var_gw=192.168.1.1` (lista no início do script).
- **Armazenamento**: `var_choose_storage=1`, `var_storage`, `var_template_storage`.
- **Idioma** do script: `var_lang=pt` (fr, en, de, es, pt, it, zh, ja).
- **Fontes**: neste contentor só são propostas as partilhas **SMB/NFS**. Com `var_mount=/host:/mnt/models`, também é permitida a «Pasta local». Definição: `/etc/systemd/system/stellio.service.d/sources.conf` (`STELLIO_ALLOWED_SOURCE_TYPES`).

## Salvaguardas (1.0.7)
O `install-pi.sh` configura:
- uma **vigilância a cada minuto** (`stellio-watchdog`): reinicia o Stellio se deixar de responder (3 verificações falhadas, 3 minutos de tolerância após um arranque), arranca-o se estiver parado, reinicia a rede se o endereço IP se perder e limpa registos e cache do apt se o disco tiver menos de 300 MB livres;
- um serviço que **nunca desiste** de reiniciar;
- limites de **CPU 75 %**, **RAM 75 % (abrandamento) / 85 % (limite rígido)**, prioridade baixa, e o Stellio é sacrificado primeiro quando falta memória;
- registos limitados a **100 MB**.

Intervenções da vigilância: `journalctl -t stellio-watchdog`. Os contentores existentes recebem tudo isto com `update-stellio`.

## Particularidades da edição servidor
- ☁️ **IA online** opcional (ver [Inteligência artificial](pt-AI)).
- 📥 **Perfis de slicer**: o Stellio não vê os slicers do seu PC e não se liga às nuvens dos slicers (Orca Cloud, Bambu Cloud…). Exporte os seus perfis (OrcaSlicer: Ficheiro → Exportar → Exportar pacote de predefinições) e importe-os em *Definições → Os meus perfis de slicer*, ou use uma **pasta de perfis vigiada** (Syncthing, partilha de rede, scp…).
- 🐯 **TigerTag**: início de sessão oficial com e-mail e palavra-passe; conta Google? Defina primeiro uma palavra-passe com «Esqueci-me da palavra-passe» na app TigerTag. Alternativa: copiar a pasta de dados do TigerTag Studio para o servidor.
- Após uma atualização, o navegador recarrega automaticamente.

## Variáveis de ambiente
| Variável | Função |
|---|---|
| `STELLIO_HEADLESS` | Força o modo servidor |
| `STELLIO_PORT` | Porta (predefinição 5000) |
| `STELLIO_SERVER_URL` | Endereço público do servidor |
| `STELLIO_DATA_DIR` | Pasta de dados |
| `STELLIO_ALLOWED_SOURCE_TYPES` | Tipos de fonte permitidos (`folder,smb,nfs`) |
| `STELLIO_START_MINIMIZED` | Arrancar minimizado |
| `STELLIO_NO_AUTO_INSTALL` | Desativa a instalação automática de módulos |

@@@ Settings-and-Data | Definições e dados
# Definições e dados

## Aparência
- **Tema**: Escuro / Claro / Sistema. Por predefinição, **claro**; escuro apenas se o sistema (ou você) o pedir.
- **Temas de marca**: Stellio, Bambu, Prusa, Voron, Creality; 33 paletas, cor de destaque personalizada, imagem de fundo ajustável.
- **Acessibilidade**: alto contraste, animações reduzidas, foco de teclado visível, tamanho do texto, modo daltónico.
- **8 idiomas**: fr, en, de, es, it, pt, ja, zh.
- Navegação reordenável arrastando e largando; **anular a última definição alterada**.

{{img:settings}}

## Atalhos de teclado
| Atalho | Ação |
|---|---|
| `Ctrl+K` | Paleta de comandos |
| `Ctrl+F` | Pesquisa |
| `Ctrl+N` | Nova transferência |
| `Ctrl+,` | Definições |
| `Ctrl+Z` | Anular a última eliminação |
| `Alt+1-8` | Navegação rápida |
| `Shift+clique` | Selecionar um intervalo |
| `↑ ↓ ← →` + `Enter` | Navegar e abrir |
| `F` | Favoritos |
| `T` | Gestor de etiquetas |
| `?` | Ajuda dos atalhos |
| `Esc` | Fechar / limpar a pesquisa |

## Onde estão os meus dados?
| Sistema | Pasta |
|---|---|
| Windows | `%APPDATA%\Stellio` |
| macOS / Linux | `~/.stellio` |
| Windows portátil | `data` junto a `Stellio.exe` |
| Personalizado | variável `STELLIO_DATA_DIR` |

Conteúdo: base de dados `stellio.db` (SQLite), definições `app_settings.json`, registo `stellio.log`, módulos transferidos `extra_libs`. O código fica separado dos dados e uma atualização nunca lhe toca.

## Cópia de segurança
- **Exportação / importação completa** (.zip) dos seus dados.
- **Cópias automáticas** programáveis.
- **Reciclagem** de 5 minutos, registo de operações com anulação.
- As atualizações nunca perdem dados.

## Registos e diagnóstico
- O nível de registo predefinido é **aviso**; o ficheiro `stellio.log` é recriado em cada arranque.
- **Modo debug**: ative-o nas Definições; aplica-se no próximo arranque.
- **Exportar o diagnóstico** (Definições → Diagnóstico): segredos ocultados, impressoras integradas listadas (tipo, modelo, estado — sem nome, endereço nem chave).
- Bloco **Saúde do Stellio**: estado geral da aplicação.

## Sugestões e erros
Na aplicação: **Sugestões e erros** na barra lateral. A mensagem torna-se uma issue do GitHub (anónima, através de uma GitHub App), com um distintivo «Nova resposta».

@@@ Troubleshooting | Resolução de problemas
# Resolução de problemas

Antes de mais: exporte o **diagnóstico** (Definições → Diagnóstico) e guarde-o para um relatório.

## O ecrã fica branco no arranque (macOS)
A porta **5000** está muitas vezes ocupada pelo *Recetor AirPlay* (um 403 no Safari). O Stellio escolhe agora **automaticamente** uma porta livre (5001–5030). Caso contrário: Definições do Sistema → Geral → AirDrop e Handoff → desative o *Recetor AirPlay*. Registo: `~/.stellio/stellio.log` (vazio no nível normal: ative o modo debug).

## O contentor LXC fica inacessível
A partir da shell do Proxmox:
1. `pct status <CTID>` e depois `pct start <CTID>` se estiver parado.
2. `pvesm status`: **armazenamento cheio**? É a causa mais frequente quando o armazenamento é partilhado.
3. `pct exec <CTID> -- free -m` e `dmesg -T | grep -i "oom\|killed process"`: falta de memória.
4. `pct exec <CTID> -- ip -4 a`: o IP de DHCP mudou? Reserve-o no router.
5. `pct exec <CTID> -- systemctl status stellio` e `journalctl -u stellio -n 100`.

Desde a 1.0.7, a vigilância automática trata os casos habituais; veja `journalctl -t stellio-watchdog`.

## As miniaturas são lentas ou não aparecem
- Escolha *Definições → Desempenho das miniaturas*: **Eco** numa máquina pequena.
- Os ficheiros muito pesados mantêm uma miniatura de substituição após um tempo limite.
- A geração faz pausa enquanto usa a aplicação: é normal.

## A minha impressora não é detetada
- Verifique se está na mesma rede (VLAN, Wi-Fi de convidados).
- Adicione-a à mão com o seu endereço IP e a sua chave.
- Bambu Lab: ative o modo LAN; Klipper: a API do Moonraker tem de estar acessível.

## Falta a foto de fim de impressão
Ative a caixa *Foto de fim de impressão* na impressora (tal como a vigilância por IA e a tomada inteligente) e verifique se a câmara responde.

## «Módulo em falta»
No primeiro arranque de cada versão, o Stellio transfere os módulos em falta. Verifique a ligação à internet; não defina `STELLIO_NO_AUTO_INSTALL` salvo necessidade.

## O Windows SmartScreen / macOS bloqueia a aplicação
Os instaladores não estão assinados. Verifique o `.sha256` e depois *Mais informações → Executar mesmo assim* (Windows) ou clique com o botão direito → *Abrir* (macOS).

## Obter ajuda
[GitHub Issues](https://github.com/stellio-app/stellio/issues), [Discord](https://discord.gg/ySxpHvS6bd) ou **Sugestões e erros** na aplicação. Indique: versão do Stellio, sistema, passos para reproduzir, registo exportado.

@@@ Contributing | Contribuir
# Contribuir

As contribuições são bem-vindas. 🎉

1. Faça um **fork** do repositório.
2. Crie o seu ramo: `git checkout -b feature/MinhaFuncao`.
3. Faça commit: `git commit -m "Adiciona MinhaFuncao"`.
4. Faça push: `git push origin feature/MinhaFuncao`.
5. Abra um **Pull Request**.

Regras: respeitar o estilo existente, comentar em francês ou inglês, testar no Windows se possível, atualizar a documentação. Qualquer nova cadeia de texto da interface deve ser adicionada nos **8 ficheiros de idioma**.

## Tecnologias
| Componente | Tecnologia |
|---|---|
| Backend | Python 3.8+, Flask, Waitress |
| Frontend | HTML5, CSS3, JavaScript puro (sem compilação) |
| Base de dados | SQLite (modo WAL) |
| Secretária | pywebview (Windows, macOS) / navegador (servidor) |
| 3D | PyRender, rasterizador CPU com numpy, Three.js |
| Malhas | trimesh, pymeshfix, shapely, rectpack |
| IA | Ollama (local) |
| Rede | paho-mqtt, smbclient, requests |
| Cifragem | cryptography (AES) |

## Estrutura do repositório
```
stellio/
├── main.py            Núcleo Flask: base de dados, auth, biblioteca, impressoras, IA, arranque
├── modules/           Funções separadas do main.py (print_session, timelapse, quote_portal…)
├── interface/         index.html, script.js, style.css, management.js (JavaScript puro)
├── packaging/         launcher.py, instalador do Windows (.iss), permissões do macOS
├── languages/         Traduções (8 idiomas) e changelog.json
├── tests/  tools/     Testes pytest, ferramentas de manutenção
├── release-notes/     notes_version_X.Y.Z.txt
├── install-pi.sh      Instalação Raspberry Pi / Linux
└── stellio-lxc.sh     Instalação Proxmox LXC
```
Um módulo declara os serviços do `main.py` que usa (`_REQUIRED`), as suas rotas (`_ROUTES`) e uma função `init`. Verificação antes de publicar: `python -m pytest tests -q`.

## Segurança e privacidade
- O Stellio é **local-first**: por predefinição, nada é recolhido nem enviado. Única exceção, se a ativar: a IA online da edição servidor.
- Os ficheiros de código e configuração não são acessíveis a partir do navegador; a API é protegida por sessão e CSRF; os convidados são só de leitura; os segredos são cifrados.
- Cada versão é publicada com uma soma `.sha256` que a atualização integrada verifica.

## Licença
**GNU AGPL v3**: pode copiar, modificar e distribuir o Stellio; se o modificar ou o oferecer como serviço de rede, tem de publicar o código-fonte sob a mesma licença.

## Parceria e agradecimentos
O Stellio é parceiro oficial de integração da **TigerTag** ([tigersystem.io](https://tigersystem.io)). Obrigado ao Ollama, Flask, Three.js, trimesh, Spoolman e à comunidade maker. ☕ Apoiar: [Ko-fi](https://ko-fi.com/E6J828RYVD).
