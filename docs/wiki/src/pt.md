@@@ Home | Início
# 🧊 Stellio, a sua oficina 3D num só lugar
{{img:dashboard}}

> **Biblioteca, impressoras, bobines, custos e orçamentos: tudo organizado, a um clique e sempre no seu computador.**

🔒 **100 % local** · 🆓 **Gratuito e de código aberto** (AGPL v3) · 🌍 **8 idiomas** · 🖥️ Windows, macOS, Linux, Raspberry Pi, Proxmox · 📱 Android

**[⬇️ Descarregar o Stellio](https://github.com/stellio-app/stellio/releases)** · **[▶ Experimentar a demonstração online](https://demo.stellio-app.com)** · **[💬 Entrar no Discord](https://discord.gg/ySxpHvS6bd)**

## ✨ Porque vai adorar

| Para si… | O que o Stellio muda |
|---|---|
| 🗂️ **Uma biblioteca que se organiza sozinha** | Miniaturas 3D automáticas, etiquetas por IA, pesquisa em linguagem natural, duplicados detetados. |
| 🖨️ **Todas as impressoras num só ecrã** | Bambu Lab, Prusa, Klipper, OctoPrint, Creality… temperatura, câmara, progresso, foto final e timelapse. |
| 🚀 **Da biblioteca à máquina com um clique** | Envio para o slicer com os perfis e a bobine certos (um slicer por impressora), verificações antes de imprimir. |
| 🧵 **As suas bobines sob controlo** | Inventário, Spoolman, TigerTag, OpenPrintTag, previsão de esgotamento, lembretes de secagem. |
| 💶 **Custos, orçamentos e encomendas** | Custo real (material, eletricidade, desgaste), orçamentos em PDF, acompanhamento do cliente online, faturas. |
| 🤖 **Uma IA que fica em casa** | Ollama local: etiquetagem, pesquisa, imprimibilidade, vigilância de falhas, S.O.S Print. |
| 🛠️ **Ferramentas que salvam uma peça** | Visualizador 3D, reparação de malha, conversão, colocação automática, orientações sugeridas. |
| 📱 **Consigo em todo o lado** | Telemóvel (PWA e app Android), acesso remoto, notificações push, Home Assistant. |

## 🚀 Comece em 3 minutos

1. **Instale** o Stellio: um instalador, um AppImage ou um comando no Raspberry Pi e no Proxmox ([Instalação](pt-Installation)).
2. **Adicione uma pasta** com os seus modelos: o Stellio organiza-os e cria as miniaturas 3D sozinho.
3. **Adicione uma impressora** (opcional): é detetada automaticamente na sua rede.

👉 A seguir: os [Primeiros passos](pt-Getting-Started) e o [Guia passo a passo](pt-How-To), que explica **cada funcionalidade e como a usar**.

## 🧭 Explorar a wiki

| Quero… | Página |
|---|---|
| Aprender a usar cada funcionalidade | [Guia passo a passo](pt-How-To) |
| Instalar o Stellio | [Instalação](pt-Installation) |
| Dar os primeiros passos | [Primeiros passos](pt-Getting-Started) |
| Gerir os meus ficheiros 3D | [Biblioteca](pt-Library) |
| Ligar as minhas impressoras | [Impressoras](pt-Printers) |
| Acompanhar as minhas bobines | [Filamento](pt-Filament) |
| Descarregar modelos | [Transferências](pt-Downloads) |
| Usar a IA e o S.O.S Print | [Inteligência artificial](pt-AI) |
| Calcular custos, orçamentos e faturas | [Custos e gestão](pt-Costs-and-Management) |
| Aceder a partir do telemóvel | [Acesso remoto e móvel](pt-Remote-Access) |
| Instalar no Raspberry Pi / Proxmox | [Edição servidor](pt-Server-Edition) |
| Configurar, fazer cópias, entender os meus dados | [Definições e dados](pt-Settings-and-Data) |
| Resolver um problema | [Resolução de problemas](pt-Troubleshooting) |
| Contribuir para o projeto | [Contribuir](pt-Contributing) |
| Ver as novidades de cada versão | [Novidades](pt-Changelog) |

> 🔒 **Filosofia**: os seus dados ficam consigo. Tudo funciona localmente; por defeito, nada sai do seu computador.

## Ligações úteis

- 🌐 Site: [stellio-app.com](https://stellio-app.com) · ▶ [demonstração online (só leitura)](https://demo.stellio-app.com)
- 📦 [Transferências (Releases)](https://github.com/stellio-app/stellio/releases)
- 🐛 [Comunicar um erro](https://github.com/stellio-app/stellio/issues) · 💡 [Propor uma ideia](https://github.com/stellio-app/stellio/discussions) · 💬 [Discord](https://discord.gg/ySxpHvS6bd)
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

> 💡 Se a janela integrada não conseguir abrir (WebView2 ou `Python.Runtime.dll` bloqueado, frequente após um download), o Stellio abre numa janela separada do Edge/Chrome e para quando a fecha. Para recuperar a janela integrada: botão direito no zip → Propriedades → **Desbloquear** e extraia de novo. Os detalhes estão em `data\stellio.log`.

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

A barra da esquerda é uma **régua** de ícones; um clique numa categoria abre o seu **painel** à direita, que se fecha após a escolha.

{{img:sidebar-panel}}


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

## Navegação
A barra da esquerda é um **trilho estreito**: Início, Biblioteca, Impressão, Filamento, Ferramentas e Acompanhamento. Clique numa categoria para abrir o seu **painel**; fecha-se depois da sua escolha. Os distintivos de notificação das páginas de uma categoria são **somados** no seu ícone. Em baixo: Modo oficina, Ajuda, **Atualizações** e Definições. **Projetos** e **Já impressos** estão em Impressão.

## Ferramentas do dia a dia
- **Paleta de comandos** `Ctrl+K`: navegar, executar uma ação, encontrar um ficheiro, uma etiqueta, uma bobina ou um perfil.
- **Centro de notificações** (sino): fim de impressão, falha, manutenção, stock baixo, secagem de bobinas.
- **Widget flutuante** com o progresso da impressão em curso, visível em todas as páginas.
- **Atalhos de teclado**: ver [Definições e dados](pt-Settings-and-Data).

@@@ How-To | Guia passo a passo
# Guia passo a passo

Cada funcionalidade do Stellio: **para que serve e como a usar**. Os detalhes técnicos estão nas outras páginas; aqui, pratica-se.

> 💡 Em toda a aplicação: `Ctrl+K` abre a **paleta de comandos** (ir a um sítio, lançar uma ação, encontrar um ficheiro, uma etiqueta, uma bobine) e `?` mostra os atalhos.

## Orientar-se no Stellio

| Menu | Para que serve |
|---|---|
| **Painel** | Impressões em curso, stock baixo, ficheiros recentes; widgets reordenáveis. |
| **Biblioteca** | Todos os seus modelos 3D, com miniaturas, etiquetas, filtros e pesquisa. |
| **Imprimir em breve** | A sua lista de espera de impressões, reordenável. |
| **Projetos** | Vários ficheiros agrupados para o mesmo objeto. |
| **Impressoras** | Acompanhamento em direto, envio, manutenção, peças de desgaste. |
| **Inventário de filamento** | As suas bobines, a previsão de esgotamento, a secagem. |
| **Histórico** | Cada impressão enviada, avaliada como sucesso ou falha. |
| **Galeria** | As fotos das suas impressões. |
| **Estatísticas** | Fiabilidade, consumo, formatos, relatórios. |
| **Gestão** | Custos, orçamentos de clientes, encomendas, contabilidade. |
| **Modo oficina** | Ecrã inteiro para tablet ou telemóvel. |
| **S.O.S Print** | Diagnóstico guiado de uma impressão falhada. |
| **Descarregar** | Obter modelos do Printables, MakerWorld, Thingiverse… |
| **Reparação** | Encontrar e reparar malhas danificadas. |
| **Conversor** | Passar de um formato 3D para outro. |
| **Duplicados** | Detetar ficheiros repetidos. |
| **Reciclagem** | Restaurar o que eliminou. |
| **Definições** | Aparência, slicer, IA, cópias de segurança, acesso remoto. |

## Adicionar e encontrar os meus ficheiros

1. Clique em **Adicionar uma fonte** (ou `Ctrl+K` e «Adicionar uma fonte») e escolha uma **pasta**, um ficheiro isolado ou uma partilha **SMB / NFS**. As pastas 3D encontradas no seu computador são sugeridas.
2. O Stellio analisa e cria as **miniaturas 3D** em segundo plano; a geração fica em pausa enquanto usa a aplicação.
3. Para encontrar um modelo: escreva na barra de **pesquisa** ou descreva-o em linguagem natural («um suporte para auscultadores») com a pesquisa por IA.
4. Arraste e largue ficheiros 3D do explorador para os adicionar diretamente.

💡 Os arquivos (ZIP, RAR, 7z, TAR) exploram-se sem os extrair.

## Organizar com etiquetas, favoritos e filtros

1. Abra o menu **⋯** de um ficheiro, ou selecione vários (`Shift+clique` para um intervalo) para agir em bloco.
2. Adicione **etiquetas** coloridas à mão ou deixe a IA propô-las; `T` abre o gestor de etiquetas.
3. Clique na estrela para tornar um modelo **favorito** (`F` abre os favoritos).
4. Combine **filtros** (tipo, tamanho, peso, estado de impressão, «Stock de filamento») e **guarde** o filtro para o reutilizar.
5. Para renomear muitos ficheiros: **Renomeação em massa** (procurar/substituir, prefixo, sufixo, numeração), com pré-visualização antes de confirmar.

## Ver e preparar um modelo em 3D

1. Clique na miniatura de um ficheiro: abre o **visualizador 3D** (funciona offline).
2. Rode e faça zoom; num 3MF multiplaca, passe de uma placa para outra.
3. Lance a **análise de imprimibilidade** (saliências): o Stellio sugere **orientações** recomendadas.
4. Use a **colocação automática** para dispor várias peças na mesa da impressora.
5. Envie o resultado para o slicer a partir do visualizador.

## Reparar uma malha danificada

1. Abra **Reparação**: o Stellio lista os ficheiros com buracos ou arestas abertas (a análise também é feita em segundo plano ao criar as miniaturas).
2. Escolha um ficheiro e lance a **reparação**; compare **antes / depois**.
3. O ficheiro é reparado no próprio local; fica uma cópia de segurança `.bak`, por precaução.

## Converter ficheiros

1. Abra o **Conversor** e escolha um ou vários ficheiros (STL, 3MF, OBJ, PLY, AMF, STEP).
2. Selecione o formato de saída: STL, 3MF, OBJ, PLY, OFF ou GLB.
3. Se necessário, assinale **Reparar automaticamente a malha** e **Eliminar o ficheiro original**.
4. Inicie. Uma conversão em lote pode ser cancelada a qualquer momento: os ficheiros já convertidos são mantidos.

## Ampliar um modelo para o tamanho real (BigPrint)
O BigPrint (menu **Ferramentas**) amplia um modelo para o tamanho desejado — 1,8 m ou mais — e corta-o em peças que cabem na sua mesa: peças esvaziadas, pinos de união e um número gravado em cada peça. O cálculo é feito pelo motor de código aberto [bigprint](https://github.com/PooterTF/bigprint) (AGPL-3.0, de Michael Christopher Stone), integrado no Stellio.

{{img:bigprint}}

1. Escolha o modelo: **Escolher da biblioteca**, **Importar um ficheiro**, ou o botão **Enviar para o BigPrint** do menu **Ações** de um ficheiro (STL, 3MF, OBJ, PLY).
2. Indique o **tamanho final** (altura, largura, profundidade ou fator de escala) e a sua **impressora** (lista de modelos ou dimensões personalizadas).
3. Ajuste a **resistência** (uso, material, esvaziamento, espessura da casca) e os **pinos**; as opções avançadas (eixo vertical, margem, suavização…) estão recolhidas.
4. Clique em **Pré-visualização**: o Stellio mostra as peças em vista explodida, o peso de filamento, o custo estimado e a tabela de peças. Um cálculo pode ser cancelado a qualquer momento.

{{img:bigprint-result}}

Escolha onde guardar (origem da biblioteca, subpasta, criação de pasta possível, partilhas de rede incluídas) e clique em **Guardar os ficheiros**: as peças STL, o projeto 3MF, os pinos, o relatório e a pré-visualização são copiados para a pasta `<modelo>_bigprint`.

Se alterar uma definição depois da pré-visualização, execute-a novamente antes de guardar.

## Arrumar: duplicados e reciclagem

1. Abra **Duplicados**: os ficheiros idênticos e os de **geometria semelhante** (o mesmo modelo renomeado ou reexportado) ficam agrupados.
2. Fique com o que quiser e elimine os outros.
3. Eliminou por engano? `Ctrl+Z` desfaz durante 5 minutos; a **Reciclagem** guarda os itens por mais tempo e permite restaurá-los ou eliminá-los definitivamente.

## Agrupar ficheiros em projetos

1. Abra **Projetos** e crie um projeto; adicione os ficheiros de um mesmo objeto (corpo, tampa, suportes…).
2. Um 3MF **multiplaca** adicionado a um projeto é dividido num 3MF por placa (também disponível: **Dividir as placas**, no menu ⋯).
3. Acompanhe o progresso («Em curso» / «Concluídos») e clique em **Custo do projeto** para orçamentar todo o conjunto.

## Descarregar modelos

1. Abra **Descarregar** (ou `Ctrl+N`) e cole a ligação de um modelo (Printables, MakerWorld, Thingiverse, Nexprint, Creality Cloud, Snapmaker Space).
2. Ligue uma vez a conta pedida (veja [Transferências](pt-Downloads)).
3. Escolha a **fonte** de destino: o ficheiro chega com a sua **origem** (ligação, autor, licença).
4. O Stellio verifica todos os dias se existe uma **nova versão** do modelo; **Os meus likes** e **As minhas criações** encontram os seus modelos nas contas ligadas.

## Ligar uma impressora

1. Abra **Impressoras → Adicionar**: a **deteção na rede** propõe as máquinas encontradas; caso contrário, introduza tipo, endereço e chave de acesso.
2. Indique o **volume de impressão** (X, Y, Z): o Stellio avisa antes do envio se uma peça for demasiado grande.
3. Se quiser, escolha o **slicer desta impressora** (1.0.8): é esse que abre para esta máquina.
4. Ative as opções úteis: **timelapse**, **foto de fim de impressão**, **vigilância por IA**, **tomada inteligente** (consumo real).

## Enviar um ficheiro para o slicer

1. A partir da biblioteca ou do visualizador, clique em **Enviar para o slicer**.
2. Na janela: veja a **estimativa** (peso, tempo), escolha a **impressora**, a **bobine** e o **perfil de definições**, ou deixe «Automático».
3. Leia as **verificações antes de imprimir**: bobine a secar, filamento abrasivo, volume excedido, material insuficiente.
4. Clique em **Enviar**: o ficheiro abre no slicer da impressora (ou no das Definições), com os perfis associados à máquina. A bobine é descontada se o tiver pedido.

💡 Para associar perfis a uma impressora, importe-os em Definições → Slicer.

## Preparar o que se segue: «Imprimir em breve»

1. No menu **⋯** de um ficheiro, escolha **Adicionar a imprimir em breve**.
2. Abra **Imprimir em breve**: arraste para **reordenar**.
3. Envie um item diretamente para o slicer ou retire-o da lista.

## Acompanhar uma impressão

1. No cartão da impressora: temperatura, progresso, **câmara em direto** e nome do ficheiro em curso.
2. Um **widget flutuante** mostra o progresso em todas as páginas.
3. O **sino** avisa-o (fim, falha, manutenção, stock baixo); ative as **notificações push** (ntfy, Gotify, Pushover, Telegram, Discord, Slack, webhook) para ser avisado com a janela fechada.
4. A 100 %, o Stellio tira a **foto final**: classifique-a como *Sucesso* ou *Falha* com um clique. O **timelapse** é montado automaticamente.

## Avaliar, reimprimir, encontrar as fotos

1. Abra o **Histórico**: filtre por plataforma, resultado ou datas.
2. Avalie cada impressão como **sucesso** ou **falha**: isso alimenta as recomendações e as estatísticas.
3. **Ver o ficheiro** ou **Reimprimir** como da última vez (mesmas definições).
4. Encontre as suas fotos na **Galeria**; **Os meus G-codes** guarda os G-codes associados a um ficheiro, com o botão **Abrir no slicer**.

## Acompanhar as minhas bobines

1. Abra o **Inventário de filamento**: adicione bobines à mão (ou importe Excel/CSV), ligue o **Spoolman**, o **TigerTag** ou o **OpenPrintTag**, ou procure uma bobine na **Open Filament Database**.
2. Ao enviar para o slicer, escolha a bobine: o Stellio **desconta** o consumo e verifica se sobra o suficiente.
3. Em **Pesagem e previsão**, pese uma bobine: o Stellio estima a sua **data de esgotamento** e avisa quando se aproxima.
4. Registe a **secagem** de uma bobine para acompanhar o seu estado; use **Comprar de novo** para abrir a loja do fabricante.

## Calcular um custo e fazer um orçamento

1. Abra a calculadora a partir de um ficheiro (**Custo**) ou de um projeto (**Custo do projeto**).
2. Verifique material, eletricidade, **desgaste da máquina**, **custos fixos**, **margem** e **quantidade**: o preço unitário e o total são mostrados.
3. Clique em **Gerar o orçamento (PDF)**: indique cliente e descrição. O PDF é guardado e encontra-se no widget **Orçamentos**.
4. Defina a margem predefinida em **Definições → Preços de impressão**.

## Gerir encomendas, clientes e faturas

1. Ative *Ativar as funções de custo, orçamento e faturação* nas Definições: o ecrã **Gestão** aparece.
2. Envie um orçamento ao cliente com a sua **ligação de acompanhamento**: pode aceitá-lo ou recusá-lo online; a aceitação cria a tarefa de impressão. **O Stellio não processa nenhum pagamento.**
3. Acompanhe a **fila de encomendas**, os pagamentos, as faturas de adiantamento e as notas de crédito; a **distribuição inteligente** propõe a impressora adequada sem nunca iniciar uma impressão.
4. Todos os meses, exporte a **contabilidade** (ZIP com CSV e PDF).

## Planear a produção (planeamento e capacidade)
A página **Planeamento** (menu **Impressão**) calcula, para cada impressora, a data de fim estimada de cada encomenda, compara a capacidade disponível com a carga pedida e avisa-o de uma sobrecarga ou de um atraso antes de acontecer.

{{img:planning}}

1. Em **Encomendas**, indique para cada encomenda a **duração por peça** (em horas): uma encomenda criada a partir de um orçamento herda-a do cálculo de custos. Uma encomenda sem duração não é planeada e fica assinalada no topo da página (pode preenchê-la ali mesmo).
2. Escolha a **impressora** de cada encomenda (caso contrário, o Stellio coloca-a, como sugestão, na máquina que fica livre primeiro) e a **data de entrega**.
3. Abra **Planeamento**: as barras mostram o encadeamento das encomendas em cada impressora (vermelho = atraso previsto, laranja = menos de um dia de margem), com a **taxa de carga** de cada máquina. A impressão em curso é tida em conta através do tempo restante lido na impressora.
4. Defina o **horizonte** (7, 14 ou 30 dias). Os cartões do topo resumem capacidade, carga, atrasos previstos e **cumprimento de prazos** em 90 dias.

**Capacidade das impressoras**: indique as horas de impressão possíveis por dia e os dias de trabalho (por predefinição 16 h, todos os dias), máquina a máquina; desmarque uma impressora para a excluir do planeamento.

O Stellio envia uma notificação quando uma encomenda vai falhar a data de entrega ou uma impressora está sobrecarregada (uma vez por encomenda e por dia).

O cálculo é propositadamente simples: durações introduzidas, encomendas encadeadas por data de entrega, sem considerar trocas de material nem avarias.

## Encontrar a melhor combinação (rastreabilidade)
A página **Rastreabilidade** (menu **Impressão**) liga cada impressão à **versão exata do modelo** e ao **perfil de slicer** usados e mostra, para cada modelo, a combinação que funciona melhor.

{{img:trace}}

1. Imprima como habitualmente no Stellio: a impressão fica ligada ao modelo automaticamente. Se o ficheiro mudou desde a última versão, o Stellio guarda uma versão «Antes de imprimir», por isso a associação é sempre exata.
2. Depois de imprimir, **avalie o resultado** (sucesso, falha, parcial) no histórico: são estas avaliações que alimentam as taxas.
3. Abra **Rastreabilidade**: uma linha por modelo com as suas versões e a **melhor combinação** (versão + perfil, sucessos em impressões avaliadas). Um clique abre **Versões do modelo**.
4. Em **Versões do modelo**, cada versão mostra os seus sucessos, falhas e taxa, e a tabela cruza **versão × perfil**.

{{img:trace_versions}}

A classificação não se deixa enganar por amostras pequenas: 8 sucessos em 9 passam à frente de 1 em 1. A melhor combinação só é sugerida a partir de 2 impressões avaliadas e de uma versão conhecida.

O acompanhamento começa com a v1.1.6: as impressões anteriores não são reconstruídas.

## Manter as minhas impressoras

1. No cartão de uma impressora, abra **Manutenção** e escolha a **marca**: são propostas tarefas recomendadas.
2. Adicione-as ao seu acompanhamento: passam a «por fazer» consoante as horas de impressão e os dias decorridos.
3. Registe as suas **peças de desgaste** (bicos, placas, correias) com limiar de alerta e as suas **calibrações** por filamento.

## Diagnosticar uma falha: S.O.S Print e IA

1. Abra o **S.O.S Print** e descreva o problema (foto possível).
2. Responda às perguntas, uma de cada vez, **sem limite**: o Stellio reduz as hipóteses (e acrescenta novas se preciso) até encontrar a causa, e dá um **diagnóstico final**. Se a solução não funcionar, responda «ainda não resolvido» e a investigação continua.
3. Para a IA local, instale o [Ollama](https://ollama.com/) e configure-o em **Definições → Inteligência artificial**. A **vigilância de falhas** avisa-o sem nunca parar a impressão.

## Usar o Stellio no telemóvel e à distância

1. Em **Definições → Acesso móvel**, leia o **código QR**: a biblioteca abre no seu telemóvel (instalável como uma aplicação).
2. Para a app **Android**, leia o código QR específico.
3. Fora de casa: ative o **acesso remoto** (Cloudflare Tunnel ou endereço personalizado) ou crie uma **ligação de partilha** temporária.
4. Partilhe só para leitura com uma **conta de convidado**.

## Cópia de segurança e restauro

1. Abra **Definições → Cópia de segurança e dados** e **exporte** os seus dados (.zip).
2. Programe **cópias de segurança automáticas**.
3. Para restaurar, **importe** o ficheiro .zip. Uma atualização do Stellio nunca toca nos seus dados.

## Atalhos que vale a pena conhecer

| Atalho | Ação |
|---|---|
| `Ctrl+K` | Paleta de comandos |
| `Ctrl+N` | Nova transferência |
| `Ctrl+Z` | Anular a última eliminação |
| `F` · `T` | Favoritos · gestor de etiquetas |
| `?` | Ajuda dos atalhos |

Lista completa: [Definições e dados](pt-Settings-and-Data).

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
- **Favoritos**, filtros avançados (tipo, tamanho, peso, estado de impressão), **filtros guardados**. Acesso: tecla **F**, widget do painel ou estrela de cada ficheiro (ao retirar uma estrela, o ficheiro desaparece de imediato da vista Favoritos).
- Filtros de estado: «Enviado ao slicer», «Já impresso», «Já bem-sucedido», «Já falhado».
- **Filtro «Stock de filamento»**: mantém apenas os ficheiros imprimíveis com as bobinas que possui.
- A ordenação, a pesquisa e os filtros são **memorizados** ao reabrir a aplicação.
- Fila **«Imprimir em breve»**, reordenável e enviável ao slicer.
- **Renomeação em massa** (procurar/substituir, prefixo, sufixo, numeração) com pré-visualização.
- **Anular eliminações** (`Ctrl+Z`) graças a uma reciclagem temporária de 5 minutos; vale também para etiquetas, projetos e fontes.
- **Halo verde / vermelho** à volta da miniatura: verde para um ficheiro já impresso com sucesso, vermelho para uma impressão falhada (vistas galeria e detalhes).
- **Já impresso** (menu ⋯ de um ficheiro): registe à mão uma impressão feita noutro sítio — escolha a impressora, as definições (perfil do slicer) e a bobina, depois **Sucesso** ou **Falhou**. O ficheiro entra nos filtros «Já com sucesso» / «Já falhado» e a sua ficha (clique direito) mostra impressora, definições e bobina. Com **Falhou**, um campo opcional **Motivo da falha** é guardado com a impressão (1.1.9).
- **Página «Já impressos»** (painel Impressão): todos os ficheiros impressos ou marcados como «já impresso», com as mesmas miniaturas e halos da biblioteca, uma pesquisa e um filtro Com sucesso / Falhados. Ao passar o rato sobre uma miniatura aparece uma **cruz vermelha** (no telemóvel: um toque mostra-a e um segundo toque abre o ficheiro); após confirmação, retira o ficheiro da lista e volta a ser «nunca impresso». O botão **Remover** da ficha do ficheiro faz o mesmo. Existe um widget com o mesmo nome no início.
- Seleção rápida: `Shift+clique` para um intervalo, setas + `Enter`.
- **Deteção de duplicados** (exatos e de geometria semelhante).
- **Origem do modelo**: ligação de origem, autor, licença, notas, data de transferência.
- **Arrastar e largar** ficheiros 3D a partir do explorador, também através do navegador.

{{img:library-halo}}

{{img:already-printed}}

Num 3MF de **várias placas**, a janela «Já impresso» oferece uma zona por placa, cada uma com a sua bobina; um ficheiro **multicor** aceita várias cores por placa (**Adicionar uma cor**). Os pontos de cor reproduzem os das suas bobinas e a ficha do ficheiro mostra o detalhe.

{{img:already-printed-plates}}

Os ficheiros **enviados para o slicer** ganham um **halo âmbar** (verde se a impressão correu bem, vermelho se falhou) logo após o envio, e a etiqueta **Enviados para o slicer** da biblioteca encontra-os com um clique.

- **Coleções**: agrupe modelos por tema (menu do ficheiro → *Adicionar a uma coleção*). Cada coleção torna-se um chip de filtro na biblioteca; defina uma **quantidade** por ficheiro e **adicione toda a coleção à fila de impressão** com um clique.
- **Versões de modelos**: menu do ficheiro → *Versões*. Guarde uma cópia antes de alterar um modelo, **compare-a** com o ficheiro atual (tamanho, triângulos, dimensões, volume), transfira-a ou **restaure-a** (o estado atual é guardado primeiro).

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
- **BigPrint** (menu **Ferramentas**): amplia um modelo para o tamanho desejado e corta-o em peças numeradas com pinos, pré-visualização 3D explodida e estimativa de filamento e custo (motor de código aberto bigprint).
- **Unir em 3MF**: selecione vários modelos (STL, 3MF, OBJ…) e o Stellio cria um único ficheiro 3MF — uma placa se tudo couber, caso contrário um ficheiro com várias placas (estrutura compatível com Bambu Studio / OrcaSlicer; o PrusaSlicer mostra todas as peças juntas). Escolhe o nome e a pasta (incluindo partilhas de rede, com criação de pasta) e o Stellio pergunta se quer eliminar ou manter os ficheiros originais.
- **Cor da bobina para o slicer**: ao enviar, a cor e o material da bobina escolhida são aplicados ao perfil de filamento carregado no OrcaSlicer, Bambu Studio ou PrusaSlicer (é preciso um perfil de filamento importado e associado à impressora; no envio em lote, só se todas as bobinas forem iguais).
- **Barra de seleção**: todos os botões têm o mesmo tamanho e cabem numa única linha (só ícones em ecrãs pequenos, nome na dica).
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

## Modelos volumosos
Um STL ocupa na memória cerca de 12 vezes o seu tamanho ao ser carregado. Acima de um limiar (256 MB, até 1 GB se o computador tiver muita memória livre), o Stellio já não o carrega por inteiro: análise em fluxo (STL binário e de texto), miniatura e visualizador numa **versão simplificada** (cerca de 300 000 triângulos), e as operações de escrita (reparação, conversão…) são recusadas com uma mensagem clara.
Para trabalhar mesmo assim: clique direito › **Criar uma versão leve**. O Stellio escreve uma cópia simplificada junto ao original (`nome (leve).stl`), que nunca é alterado. A cópia serve para ver, medir, reparar ou indexar, não para imprimir em resolução total. A ação também é proposta quando uma reparação é recusada por tamanho; aplica-se apenas a ficheiros STL locais. Uma exportação do slicer (OrcaSlicer…) em STL ou 3MF costuma ser muito mais leve.
Na Oficina avançada, cada campo «Caminho do modelo» oferece **Escolher na biblioteca**: origem, pesquisa, filtro por formato (STL, 3MF…), miniaturas e paginação.

@@@ Printers | Impressoras
# Impressoras
{{img:printers}}

No início, o widget **Câmaras** mostra até **4 câmaras** (uma por impressora em curso): um clique numa miniatura abre uma janela com **só a câmara** (o widget «Impressões em curso» mantém o acompanhamento completo). O botão **Ver tudo** abre a lista de todas as câmaras para escolher a que é apresentada.


## Marcas suportadas

| Marca | Modelos | Ligação |
|---|---|---|
| **Bambu Lab** | X1/X1C/X1E, X2D, P1P/P1S, P2S, A1/A1 mini, H2D/H2S/H2C | MQTT (LAN + nuvem): acompanhamento, AMS, câmara, descoberta SSDP |
| **Prusa** | MK4, MK3.9, MK3.5, MINI+, XL, CORE One | PrusaLink (HTTP) |
| **Creality** | Séries K1/K2, Ender-3 V3, Hi | WebSocket: acompanhamento, CFS, descoberta UDP |
| **Elegoo** | Centauri Carbon 1 e 2, séries de resina Saturn/Mars | SDCP (WebSocket) |
| **Resina Chitubox** | Phrozen, Uniformation GKtwo e outras placas Chitubox | SDCP v3: acompanhamento (mesmo protocolo da Elegoo) |
| **Impressora USB** | Marlin, Prusa, Creality, placas Klipper… ligadas ao PC do Stellio | Deteção de portas série (a porta nunca é aberta): ligada / ausente, sem estado nem temperaturas |
| **Anycubic Photon** | Modelos Wi-Fi antigos: Mono X, Mono X 6K, Mono SQ (não as M5s / M7) | Comandos de texto TCP 6000: só estado e ficheiro atual |
| **Formlabs** | Form 3 / 3L / 4 | API web oficial (client_id:client_secret): estado, progresso, camadas; o envio faz-se com o PreForm |
| **FlashForge** | Adventurer 5M/5M Pro, AD5X | API proprietária |
| **Klipper / Moonraker** | Qualquer máquina Klipper (Voron…) | HTTP: acompanhamento, envio, câmara, horas exatas |
| **OctoPrint** | Qualquer impressora controlada pelo OctoPrint | HTTP |
| **Duet / RepRapFirmware** | Duet 2/3, standalone ou com SBC (DSF) | HTTP: acompanhamento, envio de ficheiros, temperaturas |
| **Repetier-Server** | Qualquer impressora gerida pelo Repetier-Server | HTTP: acompanhamento, envio de ficheiros, temperaturas (Marlin por USB série não é suportado) |

> **Impressoras de resina: apenas acompanhamento.** O Stellio nunca inicia nem para uma impressão de resina. Comunique no GitHub o que não funcionar (Creality Halot: ainda não suportada).

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
- **Slicer por impressora**: cada impressora pode ter o seu próprio slicer por defeito (OrcaSlicer, QIDIStudio, Bambu Studio…). O envio usa-o com os perfis (definições, filamento) associados a essa impressora e a lista de perfis adapta-se.
- **Software de resina**: o Stellio deteta CHITUBOX, CHITUBOX Pro, Anycubic Photon Workshop, PreForm (Formlabs), Voxeldance Tango e Lychee Slicer. Uma impressora de resina sem slicer escolhido abre automaticamente o primeiro software de resina detetado; também pode escolher um à mão (Definições → Slicer ou ficha da impressora). Os caminhos de instalação habituais são verificados: se o seu software não for reconhecido, selecione-o à mão.

{{img:printer-slicer}}

**Produzir com assistência (1.1.8).** No menu de um ficheiro, **Produzir com assistência** propõe a impressora mais adequada (livre, material certo, fila curta) e o perfil de slicer recomendado pelo Intelligence, e depois verifica o ficheiro (modelo em bruto a fatiar, formato incompatível com a impressora), a impressora (offline, ocupada) e os consumíveis (bobina ou resina suficiente). **Nada é enviado sem a sua validação**: o servidor recusa o envio enquanto não clicar em *Validar esta escolha*. O Stellio envia então o ficheiro para a impressora **sem iniciar a impressão à distância** (inicia-a na máquina). Deteta o fim da impressão e regista-o no histórico; se a máquina não o indicar, introduza você o resultado. As recomendações **seguidas** e o seu resultado corrigem a classificação do Intelligence: um perfil seguido pelo menos 3 vezes que acerta menos de 40 % é despromovido, a partir de 80 % é favorecido (cartão *Produção assistida* da página Estatísticas).

## Durante a impressão
- **Tomada inteligente** (Shelly, Tasmota, Home Assistant): o Stellio lê os watts e regista o consumo real (kWh) e o custo.
- **Consumo real de filamento**, registado após a impressão.
- **Foto de fim de impressão** tirada quando a impressão chega aos **100 %** (a peça ainda está na mesa), uma única foto para avaliar *Sucesso/Falha*.
- **Vigilância de falhas por IA** (Ollama com visão, 100 % local): alerta perante esparguete ou peça descolada, **nunca uma paragem automática**.
- **Timelapse** automático (câmara → vídeo MP4, requer ffmpeg).
- **Ligações de partilha do estado**, só de leitura.

## Deteção de falhas por câmara (Obico)
Em *Definições → Obico*, indique o endereço do seu servidor Obico (auto-alojado ou obico.io) e um token de API. O Stellio verifica regularmente os alertas e envia uma **notificação push** assim que o Obico deteta uma falha. A ação (pausa, cancelar) continua a ser a do Obico: o Stellio nunca para uma impressão sozinho. Um botão *Testar a ligação* verifica o endereço e o token.

## Manutenção
- **Manutenção de resina**: o botão **Manutenção** nos cartões de impressoras de resina propõe tarefas adequadas (película FEP/nFEP, filtragem da resina, plataforma, ecrã LCD, filtro de carvão, eixo Z, IPA de lavagem, desgaste UV/LCD).
- **Manutenção preditiva** com tarefas próprias de cada marca.
- **Peças de desgaste** (bicos, placas, correias…) com alertas de stock, ligadas às tarefas de manutenção.
- **Calibrações** (fluxo, pressure advance, temperaturas) por filamento e impressora.

@@@ Filament | Filamento
# Filamento

## Resina
A categoria da barra lateral chama-se agora **Materiais** e reúne duas páginas: **Filamento** (inventário de bobinas) e **Resina**. O inventário de resina é **manual**: adicione os seus frascos (nome, marca, tipo, cor, volume, restante, preço, local, notas) e use o botão «Usar» para retirar um volume em ml. Desde a 1.1.8 existe **Consumo automático** (no fim da página Resina): escolha o **frasco ativo** de cada impressora de resina; no fim de uma impressão, o Stellio retira a resina usada desse frasco. O volume é lido do ficheiro `.sl1` (campo `usedMaterial`); senão é **estimado** a partir do modelo com o mesmo nome na sua biblioteca (volume da malha fechada + 15 % de margem para suportes e perdas) e assinalado como estimativa; se não houver nada fiável, **nada é descontado** e uma notificação di-lo. Uma impressão falhada só desconta a parte já impressa (se o progresso for conhecido). Cada desconto aparece no histórico e pode ser **anulado**; o restante nunca desce abaixo de zero.

Tal como no filamento, o lembrete **«A encomendar»** também funciona com a resina: uma resina (marca + nome + cor, todos os frascos juntos) entra na lista quando o total restante desce abaixo do limite definido na página (200 ml por defeito, 0 = desativado) ou quando marca «A encomendar» num frasco. Também aparece no widget «A encomendar» do painel; **Encomendar** abre ligações de pesquisa para as suas lojas (o stock de resina não é verificado automaticamente) e **Já encomendado** adia o lembrete 14 dias.

## Fontes de inventário
| Fonte | Detalhes |
|---|---|
| **Spoolman** | Deteção automática na rede. O Stellio **já não lhe escreve** o consumo (evita a contagem a dobrar). |
| **Manual** | Bobinas introduzidas à mão, importação Excel/CSV. |
| **TigerTag** | Identificação NFC/RFID. Início de sessão com e-mail e palavra-passe (só se guarda um token cifrado) ou reutilização de uma sessão do TigerTag Studio. **Só leitura.** |
| **OpenPrintTag** | Norma aberta de etiquetas NFC: importação/exportação de ficheiros `.bin`, leitura/escrita a partir da app Android, peso consumido sempre atualizado. |
| **Bambu AMS / Creality CFS** | Leitura dos slots. |

**Open Filament Database**: procure uma bobina por marca, material e cor e crie-a com um clique (peso, diâmetro e densidade preenchidos).

Na janela de envio para o slicer, a lista de bobines está ordenada e tem um **campo de pesquisa**.

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

As **lojas da Open Filament Database** (86) são adicionadas aos **Links úteis**, filtradas segundo o seu país, e também são usadas pela pesquisa **Comprar de novo uma bobina**: o Stellio propõe as lojas que enviam para a sua zona.

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

> ⚠️ A IA não é 100 % fiável: pode cometer erros (etiquetas, descrições, diagnósticos do S.O.S Print…). Encare as suas respostas como pistas a verificar, não como certezas.

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
1. Descreve o problema (foto possível em cada passo) e, se quiser, as definições usadas (temperaturas, velocidades, retração…). As **velocidades** são lidas do perfil de slicer escolhido (ou escritas por si); se faltarem, a IA pede-as. Em impressões **multicor** a IA analisa a **torre de purga** (solta-se, desmorona, cai sobre a peça, cores misturadas) e faz as perguntas úteis; a largura da torre é lida do perfil. Desde o primeiro passo e após cada resposta, a IA mostra as suas **hipóteses ordenadas por probabilidade** (%), cada uma com o motivo ou um teste rápido.
2. O Stellio faz **uma pergunta de cada vez**, sem limite, e reduz em direto uma lista de hipóteses (novas são acrescentadas se as primeiras forem descartadas).
3. Apresenta um **diagnóstico final**.

A partir da **pergunta 3**, o botão **Concluir e propor uma solução** dá as causas mais prováveis e pergunta «Este diagnóstico resolveu o problema?» (**Sim, resolvido** / **Não, continuar a investigação**). O botão **Parar a investigação** permite abandonar a qualquer momento.

As conversas são guardadas: reabra-as ou marque-as como resolvidas.

> ℹ️ Os resultados «Sucesso / Falha» que avalia no histórico melhoram as recomendações.

@@@ Costs-and-Management | Custos e gestão

> ⚠️ A IA não é 100 % fiável: pode cometer erros. As suas hipóteses são pistas a verificar, não certezas; confirme antes de alterar as definições ou a máquina.

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
- **Horas de vazio / cheias**: em *Definições → Eletricidade*, introduza dois preços por kWh e as suas faixas de vazio (ex. `22:00-06:00`, fim de semana opcional). O **custo real** das impressões medidas tem-nos em conta, um balanço de 30 dias mostra a **poupança possível**, um simulador compara «agora» com «próxima faixa de vazio», e um lembrete avisa quando as horas de vazio começam com tarefas em espera. O Stellio nunca inicia uma impressão sozinho.
- **Porque falham as minhas impressões**: em *Estatísticas*, taxa de falhas por motivo, material, impressora, perfil de slicer, dia da semana e altura do dia, ficheiros que mais falham e pistas com números (ex. «PETG: 45 % de falhas contra 12 % em média»). Avalie as suas impressões no histórico para a alimentar.



{{img:stats}}
@@@ Remote-Access | Acesso remoto e móvel
# Acesso remoto e móvel

## Telemóvel e tablet
- **Código QR** de acesso móvel à biblioteca (**PWA instalável**).
- **App Android complementar**: um código QR próprio (Definições → acesso móvel) transfere o APK. Gere endereços interno e externo com alternância automática, emparelhamento por QR, fotos diretamente a partir de uma impressão e leitura/escrita de etiquetas NFC OpenPrintTag.
- **Atualização da app Android**: ao abrir, uma janela avisa da nova versão publicada no GitHub e propõe descarregá-la e instalá-la com um toque (soma de verificação validada).
- **Atualizações sobre a app existente**: desde a 1.1.0 o APK é assinado com uma chave permanente. Se o Android mostrar «o pacote está em conflito com um pacote existente», desinstale a versão antiga uma vez e instale a nova; as atualizações seguintes instalam-se normalmente.
- **Modo oficina** em ecrã inteiro para tablet/telemóvel. O cartão da impressora (1.1.9) mostra a câmara à esquerda e os dados à direita no PC / servidor, sem deslocar; no telemóvel, o progresso vem antes das temperaturas. No modo oficina, tocar numa impressora a imprimir abre o seu cartão.

{{img:android-update}}

**Menu em ecrãs pequenos**: a barra inferior desaparece; um botão no canto superior esquerdo abre a mesma barra lateral que no computador (categorias + painel à direita). Os emblemas (impressão em curso, notificações, avisos) reduzem-se para não incomodar. O logótipo do Stellio aparece nas páginas de configuração e «Servidor inacessível».

{{img:mobile-drawer}}

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
- **Push**: ntfy, Gotify, Pushover, Telegram, Discord, Slack ou webhook, mesmo com a janela fechada (fim de impressão com nome do ficheiro e duração, falha, manutenção, stock, impressora offline).

## Domótica
- **MQTT / Home Assistant**: publicação do estado e descoberta automática; dispositivo MQTT «Stellio» e sensores.

@@@ Desktop-Edition | Edição desktop
# Edição desktop

A **edição desktop** é a aplicação de ambiente de trabalho: uma janela do Stellio no seu PC (Windows, macOS). Mantém o comportamento original; apenas faltam algumas funções pensadas para um servidor sempre ligado.

## Que edição tenho?
| Sistema | Edição por defeito |
|---|---|
| Windows, macOS | Desktop |
| Linux, Raspberry Pi, VM, LXC, Docker | Servidor |

Para forçar a escolha (testes, um PC Linux usado como desktop):
```bash
STELLIO_SERVER_EDITION=0   # desktop
STELLIO_SERVER_EDITION=1   # servidor (STELLIO_HEADLESS=1 também leva aí)
```

## O que é próprio do desktop
- **Janela integrada** (pywebview). No Windows, abrir o Stellio num navegador do mesmo PC está bloqueado (token interno): use a janela. O telemóvel, o APK e o túnel continuam permitidos.
- **Notificações do Windows** nativas.
- **Slicers do PC** detetados automaticamente (OrcaSlicer, Bambu Studio, PrusaSlicer, Cura…).
- **Fontes**: pasta local, ficheiro, SMB e NFS.
- **Dados** em `%APPDATA%\Stellio` no Windows; na versão portátil, na pasta `data` junto a `Stellio.exe`.
- **Atualizações** a partir do GitHub por patch `.zip`, verificado antes da instalação.

## Funções reservadas à edição servidor
Estas funções respondem «reservado à edição servidor» na aplicação desktop:

| Função | Utilidade |
|---|---|
| IA online | Claude, ChatGPT ou Gemini com a sua chave |
| Perfis de slicer importados | Importação de perfis exportados dos seus slicers |
| Notificações push | ntfy, Telegram, Discord, webhook… |
| MQTT / Home Assistant | Publicação de estado e descoberta automática |
| Resumo periódico | Diário ou semanal |
| Sincronização entre duas instâncias | Ferramentas › Sincronização |
| Webhooks de saída | Mensagens assinadas (HMAC-SHA256) para os seus serviços |
| API pública e acesso móvel | Tokens de âmbito limitado, rotas /api/v1 |

A entrada **Sincronização** do menu Ferramentas fica oculta no desktop, pois só mostraria esta mensagem.

## Oficina avançada no desktop
Tudo o resto funciona como num servidor. As ferramentas da Oficina avançada estão na barra lateral, cada uma na sua categoria: **Biblioteca** (Organização, Diff 3D, Semelhantes, Licenças, Ficha da peça), **Impressão** (Compatibilidade, Verificação de impressão, Arquivos G-code), **Materiais** (Necessidades de material), **Ferramentas** (Mesa, Assistente de fabrico) e **Administração** (Tarefas, Base de dados, Registo de auditoria, Equipas, Sessões). Estão reservadas à conta proprietária; cada entrada tem o seu interruptor em *Definições › Elementos de navegação*. Em **Semelhantes**, o botão **Ficheiros ignorados** (1.1.9) mostra os ficheiros que o índice não conseguiu tratar, com miniaturas, causa (demasiado grande acima de 60 MB, malha vazia, ilegível, em falta) e solução para cada um (reexportar ou simplificar o modelo, verificar a fonte); **Tentar de novo** indexa-os outra vez.

## Passar à edição servidor
Para um Stellio sempre ligado e acessível a partir de um navegador, veja [Edição servidor](pt-Server-Edition) e [Instalação](pt-Installation).

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

## Funções reservadas ao servidor (1.1.7)
Estas funções não existem na aplicação desktop, onde as suas rotas respondem «reservado à edição servidor»:

| Função | Utilidade |
|---|---|
| IA online | Claude, ChatGPT ou Gemini com a sua chave, em vez do Ollama (ver [Inteligência artificial](pt-AI)) |
| Perfis de slicer | Importação de perfis exportados dos seus slicers |
| Notificações push | ntfy, Gotify, Pushover, Telegram, Discord, Slack ou webhook, mesmo com a janela fechada |
| MQTT / Home Assistant | Publicação de estado e descoberta automática |
| Resumo periódico | Diário ou semanal, como notificação e push |
| Sincronização (Oficina avançada) | Sincroniza uma pasta com a de uma instância emparelhada: primeiro o plano, depois a aplicação confirmada, nenhuma eliminação é propagada, ambas as versões são mantidas em caso de conflito. As duas instâncias têm de estar em edição servidor |

O resto das ferramentas (mesa, verificação de impressão, arquivos G-code…) funciona de forma idêntica nas duas edições.

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
- **Temas de marca**: Stellio, Bambu, Prusa, Voron, Creality; 33 paletas, cor de destaque personalizada, imagem de fundo ajustável. É proposta uma imagem Stellio por predefinição (botão **Imagem predefinida**).
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

@@@ Plugins | Plugins
# Plugins

Um plugin é um pequeno programa Python que reage a um evento do Stellio (impressão concluída, impressão falhada, encomenda atrasada, impressora sobrecarregada): enviar uma notificação, escrever numa folha de cálculo, acender uma luz… Os autores publicam os plugins no **GitHub**; o Stellio mostra um **catálogo público** (logótipo + descrição) no menu **Plugins › Catálogo**, onde se instalam com um clique.

Cada plugin tem um distintivo: **Oficial** se estiver alojado no repositório `stellio-app/stellio-plugins`, **Comunitário** se estiver alojado noutro lugar (ou instalado a partir de um .zip). O Stellio decide o distintivo pelo endereço real do arquivo: leia sempre as permissões e o código de um plugin comunitário.

**Segurança dos plugins (1.1.8).** Antes de instalar, o Stellio **audita o código** (análise estática: rede não declarada, lançamento de processos, código dinâmico, binários…); um achado bloqueante recusa a instalação, a menos que aceite o risco explicitamente. O catálogo e os plugins podem ser **assinados (Ed25519)**: assim que há uma chave de confiança configurada, é recusada uma assinatura inválida, um plugin oficial sem assinatura e uma atualização sem assinatura de um plugin assinado (sem chave configurada só a soma SHA-256 protege, e a página Plugins di-lo). No **Linux**, o núcleo restringe ainda cada plugin: ficheiros só de leitura (escrita apenas na sua pasta `data/`) e sem rede sem a permissão `network`; **no Windows e no macOS estas restrições não são aplicadas**: as permissões continuam declarativas. Uma assinatura prova a origem, não a inocuidade, e uma auditoria pode falhar código escondido: leia sempre o código.

**Plugins integrados.** Algumas funções do Stellio são entregues como plugins integrados (BigPrint, resina, impressoras USB, timelapse, ferramentas de ficheiros, estúdio de mesa, notificações push, webhooks, resumo periódico, MQTT / Home Assistant, Obico, partilha e sincronização, Spoolman, fornecedores de IA e assistente de IA, Stellio Pro). Fazem parte da aplicação, mas só são carregados quando ativados (secção «Plugins integrados» da página Plugins; a alteração aplica-se ao reiniciar). **Atualização a partir de uma versão anterior: não há nada a fazer.** No primeiro arranque da 1.1.7, os plugins que utilizava (por exemplo MQTT ativado, uma impressora USB, webhooks, um timelapse) são ativados automaticamente e mantêm exatamente as suas definições; as ferramentas sem definições (BigPrint, ferramentas de ficheiros, estúdio de mesa) ficam como estavam. Uma instalação nova não ativa nenhum. Desativar um plugin nunca apaga as suas definições. Outros plugins integrados: Partilha e sincronização, Spoolman, um plugin por fornecedor de IA + o assistente de IA (ativa todas as funções de IA) e **Stellio Pro** (clientes, orçamentos, faturas, encomendas, contabilidade, tarifa de energia, planeamento, necessidades de material, stock de peças): só adicionam as suas páginas e botões quando ativados.

## Utilizar um plugin
1. Abra **Plugins › Catálogo** (apenas a conta proprietária).
2. Explore o catálogo e clique em **Instalar**: o Stellio descarrega o arquivo e verifica a sua soma SHA-256.
3. Leia as **permissões** pedidas e aceite-as. O plugin é instalado **desativado**.
4. Preencha a configuração, se necessário, ative-o e clique em **Teste** para o acionar com um evento de teste. O registo de execuções mostra a saída e os erros.

Também pode instalar um arquivo `.zip` local (plugin em desenvolvimento) ou mudar a fonte do catálogo para o URL de outro catálogo.

## Criar um plugin
### 1. Estrutura
Um plugin é uma pasta plana com um ficheiro `plugin.json` e um script Python:
```
mon-plugin/
├── plugin.json     Manifesto (obrigatório)
├── main.py         Ponto de entrada (nome livre, indicado em "entry")
└── ...             Outros ficheiros: 100 no máximo, 8 MB descomprimido
```

### 2. O manifesto plugin.json
```json
{
  "id": "mon-plugin",
  "name": "Mon plugin",
  "version": "1.0.0",
  "api": 1,
  "description": "Écrit une ligne à chaque impression terminée.",
  "author": "Votre nom",
  "entry": "main.py",
  "events": ["print.finished", "print.failed"],
  "permissions": ["events"]
}
```
| Campo | Função |
|---|---|
| `id` | Identificador único: minúsculas, dígitos, `-` ou `_`, 2 a 40 caracteres |
| `name`, `description`, `author` | Texto apresentado no Stellio |
| `version` | Numérica, por exemplo `1.2.0`; serve para detetar atualizações |
| `api` | Versão da API de plugins: `1` |
| `entry` | Script Python na raiz (por omissão `main.py`) |
| `events` | Eventos escutados |
| `permissions` | Permissões pedidas |
| `ui` | Página apresentada no Stellio: `title`, `icon` (Font Awesome) e `entry` (um ficheiro `.html`) |

### 3. Eventos e permissões
| Evento | Disparado quando |
|---|---|
| `print.finished` | Uma impressão termina |
| `print.failed` | Uma impressão falha |
| `order.late` | Uma encomenda ultrapassa o prazo |
| `printer.overload` | Uma impressora está sobrecarregada |

| Permissão | Efeito |
|---|---|
| `events` | Receber eventos (obrigatória se `events` for declarado) |
| `api:read` | Ler dados através da API pública do Stellio |
| `api:write` | Modificar dados através da API pública |
| `network` | Informação: o plugin acede à Internet |
| `ui` | Mostrar uma página do plugin no menu Plugins |

### 4. O script
O Stellio executa `python -I main.py <evento>` num processo separado e envia pela entrada padrão um JSON `{"event": "...", "data": {...}}`. O modo `-I` (isolado) não adiciona a pasta do plugin ao caminho do Python: para importar um ficheiro do seu plugin, adicione esse caminho você mesmo. A saída padrão é guardada no registo.
```python
import json, os, sys

payload = json.loads(sys.stdin.read() or "{}")
event, data = payload.get("event", ""), payload.get("data", {})
config = json.loads(os.environ.get("STELLIO_PLUGIN_CONFIG") or "{}")

print(f"{event}: {data.get('file_name') or data.get('printer') or '-'}")
```
Para atuar sobre o Stellio (permissões `api:*`), o script recebe `STELLIO_API_URL` e `STELLIO_API_TOKEN` (as chaves `api_url` e `token` da configuração do plugin). O SDK Python `stellio_sdk.py` (pasta `sdk/python` do repositório) oferece `plugin_event()`, `plugin_config()` e um cliente pronto a usar: copie-o para o seu plugin e adicione `sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))` antes da importação. Há um exemplo completo em `sdk/examples/hello-plugin`.

Limites: 10 segundos por execução, 512 MB de memória, ambiente mínimo (apenas variáveis `STELLIO_*` e `PATH`). O Python 3 tem de estar instalado na máquina que executa o Stellio. A configuração é uma lista de pares chave/valor (texto, número, booleano) com 4000 caracteres no máximo.

### 5. Testar
Comprima o **conteúdo** da pasta como `mon-plugin.zip` (2 MB no máximo), instale-o a partir de **Plugins › Catálogo** (arquivo local), aceite as permissões, ative-o e use **Teste**. Corrija os problemas lendo o registo.

## Plugin com uma página

Um plugin também pode mostrar **a sua própria página** no Stellio. Aparece então no menu **Plugins** da barra lateral, em «Catálogo», na lista «Instalados»: um clique abre a página. O manifesto abaixo é um exemplo mínimo.

```json
{
  "id": "mon-plugin",
  "name": "Mon plugin",
  "version": "1.0.0",
  "api": 1,
  "description": "Shows your archived G-code files layer by layer.",
  "author": "Stellio",
  "permissions": ["ui", "api:read"],
  "ui": {
    "title": "Mon plugin",
    "icon": "fa-layer-group",
    "entry": "viewer.html"
  }
}
```

- A página é **um único ficheiro HTML autónomo** (CSS e JavaScript lá dentro, imagens em `data:`), 1 MB no máximo. Sem eventos, o plugin não precisa de script Python.
- É apresentada numa moldura **isolada**: sem acesso à rede, aos cookies nem ao resto do Stellio.
- Lê os dados do Stellio com `window.stellio.api(caminho)`: só leitura (GET), a permissão `api:read` é obrigatória, o resultado é JSON, ou texto com `'text'` como segundo argumento. As definições, as contas, a segurança e os plugins são inacessíveis.
- O tema é fornecido pelas variáveis CSS `--st-bg`, `--st-panel`, `--st-card`, `--st-text`, `--st-muted`, `--st-border`, `--st-accent`, `--st-success`, `--st-warning` e `--st-danger`, e o idioma por `window.stellio.lang`.

```js
document.addEventListener('stellio-ready', async () => {
  const list = await window.stellio.api('/api/gcodes?limit=50');
  const id = list.gcodes[0].id;
  const text = await window.stellio.api('/api/projects/gcodes/' + id + '/download', 'text');
});
```

Para experimentar: comprima o conteúdo da pasta `mon-plugin`, instale o arquivo em **Plugins › Catálogo**, aceite as permissões, ative-o e abra-o no menu **Plugins**. É preciso pelo menos um G-code arquivado (ficha de ficheiro ou projeto). Um plugin desativado fica acinzentado na lista.

## Publicar no GitHub
1. Crie um repositório público para o seu plugin com o código, um `README` e uma licença.
2. Para cada versão, crie uma **release** do GitHub e anexe o arquivo `mon-plugin-1.0.0.zip`.
3. Calcule a soma SHA-256 do arquivo, necessária ao catálogo:
```bash
sha256sum mon-plugin-1.0.0.zip
```
4. Aumente sempre `version` em `plugin.json` antes de uma nova release.

## Estar presente no catálogo do Stellio
O catálogo oficial é um ficheiro `catalog.json` do repositório `stellio-app/stellio-plugins`. O seu plugin é adicionado através de uma **Pull Request**.

1. Faça um fork do repositório `stellio-app/stellio-plugins`.
2. Adicione a entrada do seu plugin em `catalog.json`:
```json
{
  "id": "mon-plugin",
  "name": "Mon plugin",
  "version": "1.0.0",
  "description": {"fr": "Écrit une ligne à chaque impression terminée.", "en": "Writes a line when a print finishes."},
  "author": "Votre nom",
  "url": "https://github.com/vous/mon-plugin/releases/download/v1.0.0/mon-plugin-1.0.0.zip",
  "sha256": "64 caractères hexadécimaux",
  "permissions": ["events"],
  "logo": "https://raw.githubusercontent.com/vous/mon-plugin/main/logo.png",
  "homepage": "https://github.com/vous/mon-plugin"
}
```
3. Abra a Pull Request: uma verificação automática controla as ligações, a soma SHA-256 e o logótipo, e depois a equipa do Stellio revê o plugin.

| Campo | Regra |
|---|---|
| `description` | Curta (cerca de 140 caracteres); texto simples ou um texto por idioma (`fr`, `en`, `de`, `es`, `pt`, `it`, `zh`, `ja`) |
| `url` | Ligação `https` direta ao arquivo; o `sha256` tem de coincidir exatamente |
| `logo` | `https`, PNG, JPEG ou WebP, 200 KB no máximo, idealmente 128 × 128 (o SVG é recusado) |
| `homepage` | Ligação `https` para a página do plugin (opcional) |
| `permissions` | Têm de corresponder às do manifesto |

**Atualizar**: publique uma nova release e abra uma Pull Request que altere `version`, `url` e `sha256`. Se a nova versão pedir permissões adicionais, o plugin fica desativado no utilizador até as aceitar; a sua configuração é mantida.

## Segurança
- Um plugin **não corre isolado** numa área protegida: é executado com os direitos do Stellio na máquina. Instale apenas plugins cujo autor lhe mereça confiança.
- Os plugins são instalados desativados e as suas permissões têm de ser aceites.
- As transferências só são feitas por `https` a partir de endereços públicos, com verificação SHA-256.
- O catálogo é revisto antes da publicação, mas isso não substitui a sua própria vigilância: leia o código e as permissões.

Para ir mais longe: [Contribuir](pt-Contributing), o ficheiro `docs/plugins.md` do repositório e o exemplo `sdk/examples/hello-plugin`.

## Administração e instâncias supervisionadas
O plugin **Administração** (ativo por predefinição) reúne numa página (Administração › Administração) as **contas de convidado e as suas funções**, as equipas, as sessões, o registo de auditoria e as **instâncias**.
- **Instância autónoma** (predefinição): controlo total, nada muda.
- **Instância principal**: o separador Instâncias lista as instâncias Stellio emparelhadas e permite supervisioná-las.
- **Instância supervisionada**: após a **aceitação** do seu proprietário, as contas, funções e permissões só se gerem a partir da principal; o conteúdo local (biblioteca, impressoras) permanece privado, salvo escolha em contrário na aceitação; o proprietário pode **sair da supervisão** a qualquer momento.
Uma instância supervisionada não pode supervisionar outras e uma instância principal não pode ser supervisionada. As restantes definições continuam editáveis localmente.

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
├── release-notes/     notes.txt
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
