<p align="center">
  <img src="https://stellio-app.com/assets/logo-nom-stellio.png" alt="Logo Stellio" width="360">
</p>

<h3 align="center">O gerenciador de arquivos 3D definitivo para makers e donos de impressoras 3D</h3>

<p align="center">
  <a href="https://github.com/stellio-app/stellio/releases"><img src="https://img.shields.io/github/v/release/stellio-app/stellio?color=blue" alt="Versão"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python"></a>
  <a href="https://flask.palletsprojects.com/"><img src="https://img.shields.io/badge/flask-3.0+-green.svg" alt="Flask"></a>
  <a href="https://www.gnu.org/licenses/agpl-3.0"><img src="https://img.shields.io/badge/License-AGPL%20v3-blue.svg" alt="License: AGPL v3"></a>
  <a href="https://github.com/stellio-app/stellio/blob/main"><img src="https://img.shields.io/badge/platform-Windows%20%7C%20Raspberry%20Pi%20%2F%20Linux-lightgrey.svg" alt="Platform"></a>
  <a href="https://github.com/stellio-app/stellio/blob/main"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome"></a>
</p>

<p align="center">
  <a href="../../README.md">🇬🇧 English</a> |
  <a href="README.fr.md">🇫🇷 Français</a> |
  <a href="README.de.md">🇩🇪 Deutsch</a> |
  <a href="README.es.md">🇪🇸 Español</a> |
  <a href="README.it.md">🇮🇹 Italiano</a> |
  🇵🇹 <strong>Português</strong> |
  <a href="README.ja.md">🇯🇵 日本語</a> |
  <a href="README.zh.md">🇨🇳 中文</a>
</p>

<p align="center">
  <a href="#-instalação">🚀 Instalação</a> •
  <a href="#-funcionalidades">✨ Funcionalidades</a> •
  <a href="#-documentação">📖 Documentação</a> •
  <a href="#-como-contribuir">🤝 Como contribuir</a> •
  <a href="#-licença">📜 Licença</a>
</p>

---

## 🎯 Visão geral

**Stellio** é um aplicativo de desktop moderno que centraliza toda a sua biblioteca 3D (STL, 3MF, OBJ), automatiza tarefas repetitivas e se integra perfeitamente ao seu fluxo de trabalho de impressão 3D.

Seja você um maker iniciante ou um usuário experiente com várias máquinas, o Stellio economiza um tempo precioso graças à **IA local** (Ollama), a uma **gestão inteligente de impressoras** e a uma **interface pensada para produtividade**.

> 💡 **Filosofia**: Seus dados ficam com você. Tudo funciona localmente.

---

## ✨ Funcionalidades

### 🏠 Painel e produtividade
- 📊 **Painel ao iniciar**: impressões em andamento, estoque de filamento baixo, últimas impressões e arquivos recentes num relance
- 🧱 **Totalmente personalizável**: reordene e oculte widgets arrastando e soltando (12 disponíveis: impressões em andamento, estoque baixo, último S.O.S Print, sugestões, instâncias do Stellio…)
- ✅ **Checklist «Primeiros passos»** para novos usuários
- 💡 **Widget «Sugestões»**: identifica arquivos que você reimprime com frequência mas não revê há algum tempo, e perfis de slicer com alta taxa de falha
- ⌨️ **Paleta de comandos (`Ctrl+K`)**: navegue, execute uma ação ou encontre instantaneamente um arquivo, uma tag, um carretel ou um perfil de slicer
- 🔔 **Central de notificações (sino)**: fim de impressão, falhas, manutenção próxima, estoque de filamento baixo e lembretes de secagem num só lugar
- 📺 **Widget flutuante** que mostra o progresso da impressão em andamento, visível em todas as páginas
- 🧭 **Tour guiado interativo** para descobrir os principais recursos, reiniciável nas Configurações
- ♿ **Acessibilidade**: modo de alto contraste, redução de animações, indicadores de foco do teclado visíveis em todo lugar

### 📚 Gerenciamento de biblioteca
- 🗂️ **Múltiplas fontes**: pastas locais, arquivos individuais, compartilhamentos SMB/NFS — as pastas 3D detectadas no computador são sugeridas e podem ser adicionadas com um clique
- 🖼️ **Miniaturas 3D automáticas** via PyRender (renderização de alta qualidade) ou um rasterizador de CPU numpy (alternativa), com efeito de carregamento e **pré-visualização ampliada ao passar o mouse**
- 🏷️ **Tags personalizadas** com cores + marcação automática por IA, e **marcação com um clique de vários arquivos selecionados**
- 🔍 **Busca semântica assistida por IA** ("estou procurando um suporte para...") com **buscas recentes memorizadas**
- ⭐ **Favoritos** e filtros avançados (tipo, tamanho, peso, status de impressão), com um **aviso de reposição** quando o estoque de filamento não é suficiente para seus favoritos
- 🧵 **Filtro «Estoque de filamento»**: mantém apenas os arquivos imprimíveis com os carretéis que você realmente tem (Spoolman, inventário manual, TigerTag), por material
- 💾 **Filtros salvos**: salve qualquer combinação de filtros e reutilize-a com um clique
- 📋 **Fila «Imprimir em breve»**, separada dos favoritos, reordenável por arrastar e soltar e enviável diretamente ao slicer
- 🖱️ **Seleção rápida**: seleção por intervalo (`Shift+clique`) e navegação pelo teclado (setas + `Enter`)
- ✏️ **Renomeação em massa** (localizar/substituir, prefixo, sufixo, numeração) com pré-visualização antes de aplicar
- ↩️ **Desfazer exclusões** (`Ctrl+Z`) graças a uma lixeira temporária de 5 minutos — excluir uma tag, um projeto ou uma fonte também pode ser desfeito, sem confirmação bloqueante
- 🔗 **Origem do modelo**: link de origem, autor, licença e notas na ficha do arquivo, com a data de download quando aplicável
- 🧩 **Projetos/Montagens**: agrupe vários arquivos em um único objeto, com suporte a múltiplas bandejas 3MF (navegação entre bandejas no visualizador)
- 🔁 **Detecção de duplicatas** (exatas e semelhantes por geometria)
- 🗜️ **Suporte a arquivos compactados**: navegue e extraia modelos diretamente de arquivos compactados
- 🖱️ **Arrastar e soltar arquivos 3D** do explorador de arquivos — funciona no app de desktop e também por um navegador (Raspberry Pi, celular, acesso remoto)
- 📊 **Estatísticas detalhadas** (formatos, plataformas, confiabilidade dos perfis)

### 🤖 Inteligência artificial (Ollama local)
- 🏷️ **Marcação automática** inteligente dos arquivos
- 📝 **Descrição automática** dos modelos
- 🔎 **Busca semântica** em linguagem natural
- 📐 **Análise de imprimibilidade** (detecção de balanços/overhangs) e **orientações sugeridas** (menos overhang, contato com a mesa exibido)
- 🎯 **Recomendação de perfil de slicer** baseada na geometria + histórico de sucesso
- ⏱️ **Estimativa do tempo de impressão** antes do fatiamento
- 🩺 **S.O.S Print**: diagnóstico adaptativo de falhas de impressão, passo a passo — o Stellio faz uma pergunta por vez, reduz uma lista de hipóteses conforme suas respostas (máximo 4 perguntas) e depois entrega um diagnóstico final; a análise de fotos está disponível a qualquer momento e as conversas são salvas (reabrir, marcar como resolvido)

### 🖨️ Gerenciamento de impressoras
- 🔌 Suporte a **OctoPrint**, **Klipper/Moonraker**, **Bambu Lab** (MQTT), **Creality** (WebSocket), **FlashForge**, **Elegoo** (SDCP) e **PrusaLink**
- 📡 **Descoberta automática na rede**: o Stellio varre sua rede local (SSDP para Bambu Lab, broadcast UDP para Elegoo/Centauri/FlashForge, sondagem direcionada para Klipper/OctoPrint/PrusaLink/Creality) e permite adicionar as impressoras detectadas com um clique
- 📡 Monitoramento em tempo real (temperaturas, progresso, câmera)
- 🔧 **Manutenção preditiva** com acompanhamento de tarefas e recomendações específicas por marca (Bambu, Prusa, Creality, etc.)
- 🔩 **Peças de desgaste e consumíveis**: estoque de bicos, mesas, correias… com alertas, vinculado às tarefas de manutenção (cada intervenção desconta uma peça)
- ⏱️ Contador automático de horas de impressão
- 📤 Envio direto ao slicer, com um seletor de carretel para atribuir o filamento certo diretamente na janela de envio, ou upload para a impressora
- 👀 **Pré-visualização rápida** (peso, tempo de impressão estimado) diretamente na janela de envio ao slicer, antes de confirmar
- 🛡️ **Verificação pré-impressão aprimorada**: avisa se o carretel atribuído precisa ser seco, se o filamento é abrasivo (recomendado bico de aço endurecido) ou se não existe calibração para esta impressora
- 🔁 **Reimprimir como da última vez**: a partir do histórico, um clique reabre a janela de envio com a mesma impressora, perfil e carretel
- 🎛️ **Calibrações**: salve flow, pressure advance, temperaturas… por filamento e por impressora, recuperadas na janela de envio ao slicer
- 👥 **Modo colaborativo leve**: veja se outro dispositivo conectado já está consultando um arquivo, e um aviso evita enviar o mesmo arquivo duas vezes ao slicer por engano

### 🧵 Gerenciamento de filamento
- 🔗 Integração com **Spoolman** (servidor de gestão de carretéis), com detecção automática na sua rede
- 🟠 Suporte a **AMS da Bambu Lab** (leitura dos slots)
- 🟢 Suporte a **CFS da Creality**
- 🐯 Integração com **TigerTag** (identificação NFC/RFID de carretéis): entre na sua conta para ver seus carretéis TigerTag no inventário, ou deixe o Stellio recuperar automaticamente uma sessão existente do TigerTag Studio — somente leitura, nunca modifica seu inventário TigerTag
- ⚪ Carretéis manuais
- 📉 Acompanhamento automático do consumo ao enviar para o slicer, com verificação de compatibilidade antes de imprimir (material suficiente?)
- 🔔 **Alertas de estoque baixo** na inicialização, com um link rápido para comprar mais
- 💨 **Secagem de carretéis**: registro de secagem, status (seco / precisa secar) conforme o material, temperatura e duração sugeridas e lembretes nas notificações
- 📈 **Resumo por carretel**: impressões, gramas, custo e diferença não rastreada na ficha de cada carretel

### 📥 Download de plataformas
- 🟠 **Printables** (API GraphQL)
- 🟢 **MakerWorld** (login Bambu Lab em 2 etapas)
- 🔵 **Thingiverse** (via chave de API)
- 📁 Download direto para suas fontes configuradas
- 🆕 **Detecção de novas versões**: o Stellio verifica todos os dias se os modelos baixados (Printables, MakerWorld, Thingiverse) foram atualizados
- 🛒 **Links úteis**: lojas, fabricantes, sites de modelos 3D e recursos agrupados em seções recolhíveis

### 🧩 Ferramentas avançadas
- 🎨 **Nesting automático** na mesa (rectpack ou silhueta real via shapely)
- 🔧 **Reparo de mesh** (trimesh + pymeshfix) com **comparação antes/depois** (estanqueidade, triângulos, vértices, tamanho)
- 🔄 **Conversor de formatos** (STL ↔ 3MF ↔ OBJ)
- 🛡️ **Verificação de integridade** (arquivos corrompidos/ausentes)
- 💰 **Cálculo de custo de impressão**: material, eletricidade, desgaste da máquina (por hora), custos fixos, margem em % e quantidade — preço unitário e total calculados ao centavo
- 🧾 **Orçamentos em PDF**: gerados a partir do cálculo de custo, com cliente, designação e notas personalizáveis; cabeçalho do orçamento configurável (nome/empresa, logotipo, endereço, telefone, e-mail, site, CNPJ/NIF) e avisos legais no rodapé
- 🌱 **Estimativa ambiental**: pegada de CO₂ das suas impressões (material + eletricidade)
- 📸 **Galeria de fotos de impressões** (bem-sucedidas/com falha)
- 🕒 **Histórico** com avaliação de sucesso/falha (alimenta a IA), botões **«Ver arquivo»** e **«Reimprimir»** em cada linha (com detecção de arquivos movidos/excluídos) e filtros por plataforma, resultado (bem-sucedida/falha/parcial/sem avaliação) e intervalo de datas

### 📈 Relatórios e confiabilidade
- 🧮 **Confiabilidade de impressão**: taxa de sucesso e custo das falhas classificados por perfil de slicer, material, impressora ou carretel
- 🗓️ **Relatório mensal**: impressões, taxa de sucesso, filamento, custo, falhas e CO₂ do mês, comparados com o mês anterior, exportável em PDF

### 🔔 Notificações
- 🪟 **Notificações nativas do Windows**
- 🌐 **Notificações do navegador**, ativáveis para acesso via Raspberry Pi ou celular
- 📣 **Notificações push** (ntfy, Telegram, Discord ou webhook): fim e falha de impressão detectados mesmo com a janela fechada, além de alertas de manutenção e de estoque

### 🌐 Acesso móvel e remoto
- 📱 **QR code** para acessar sua biblioteca pelo celular (PWA instalável)
- 📲 **App complementar Android**: um QR code dedicado permite baixar e instalar o APK do app complementar do Stellio diretamente nas configurações de acesso móvel, com a possibilidade de tirar fotos diretamente de uma impressão
- 🌍 **Acesso remoto** via Cloudflare Tunnel (gratuito, URL aleatória ou fixa), ou **endereço personalizado** (nome de domínio, DynDNS, VPN, Tailscale…) para dispensar o Cloudflare, com retorno ao Cloudflare em um clique
- 🔗 **Links de compartilhamento** temporários (24h, uso único)

### 👥 Contas e multi-instância
- 🔐 **Contas locais** com código de recuperação e pergunta secreta: redefinição de senha 100 % local, sem e-mail nem internet
- 👤 **Contas de convidado somente leitura**: compartilhe sua biblioteca, impressoras e estoque sem nenhum risco
- 🔄 **Instâncias do Stellio**: detecção automática de outras instalações na rede local e adição com um clique (basta informar a chave local delas)
- 📨 **Envio de arquivo para outra instância**: escolha da pasta de destino na instância de destino, e o arquivo recebido aparece imediatamente na biblioteca dela
- ✅ **Widget de status das instâncias** no painel (marca verde ou cruz vermelha para cada instância salva)

### 🎨 Personalização
- 🌓 Temas: Escuro / Claro / Sistema
- 🎨 Temas de marca: Stellio, Bambu, Prusa, Voron, Creality
- 🎯 Cor de destaque personalizada
- 🌍 **8 idiomas**: FR, EN, DE, ES, IT, PT, JA, ZH
- 🧲 Reorganização da navegação por arrastar e soltar
- ↩️ **Desfazer configurações**: reverta a última alteração de configuração feita

### 💾 Backup e atualizações
- 📦 Exportação/importação de backup completo (.zip)
- 🔄 Atualizações automáticas a partir do GitHub (patch `.zip` — mesmo mecanismo no Windows e no Raspberry Pi/Linux)
- 🔁 Reinício confiável após uma atualização ou ao ativar o modo de depuração, no Windows e no Raspberry Pi/Linux
- 📋 Exportação de logs de diagnóstico (segredos ocultados)

---

## 🖼️ Capturas de tela

| | |
|---|---|
| ![Biblioteca](../../library.png) *Biblioteca com miniaturas* | ![Impressoras](../../monitoring.png) *Monitoramento de impressoras* |
| ![Slicer](../../slicer.png) *Recomendação de perfil por IA* | ![Nesting](../../nesting.png) *Nesting automático* |

---

## 🚀 Instalação

### 🪟 Windows (recomendado)

1. Baixe o instalador mais recente em [Releases](https://github.com/stellio-app/stellio/releases)
2. Execute `Stellio-Setup.exe`
3. Pronto! 🎉

### 🐧 Raspberry Pi / Linux

Funciona em **modo servidor headless** (sem interface gráfica): o Stellio roda em segundo plano e é acessado por um navegador, seja no próprio Pi ou em qualquer dispositivo da rede local.

**Requisitos**: Raspberry Pi 4 ou 5 recomendado, Raspberry Pi OS de **64 bits**.

```bash
curl -O https://raw.githubusercontent.com/stellio-app/stellio/main/install-pi.sh
chmod +x install-pi.sh
./install-pi.sh
```

O script instala automaticamente:
- as dependências do sistema (`ffmpeg`, `unrar-free`, bibliotecas de renderização 3D)
- um ambiente virtual Python dedicado
- um **serviço systemd** (`stellio.service`) que inicia o Stellio ao ligar e o reinicia automaticamente em caso de falha

Após a instalação, o Stellio fica disponível em `http://<ip-do-pi>:5000`.

```bash
sudo systemctl status stellio     # Status do serviço
sudo systemctl restart stellio    # Reiniciar
sudo journalctl -u stellio -f     # Acompanhar os logs em tempo real
```

> 💡 **Mesmas atualizações que no Windows**: o patch `.zip` publicado em cada versão é idêntico nas duas plataformas (código-fonte puro, nada compilado). O Stellio o detecta e aplica automaticamente, depois reinicia o serviço — sem necessidade de reinstalação manual.
>
> 🎥 Mesmas funcionalidades da versão Windows, exceto a janela de desktop nativa (substituída pelo acesso via navegador) e a IA Ollama local, que precisa de um modelo razoavelmente robusto para rodar bem em um Pi — aponte `ollama_url` para um servidor Ollama remoto nas Configurações, se necessário.

### Slicers compatíveis

O Stellio detecta automaticamente:
- ✅ OrcaSlicer
- ✅ Bambu Studio
- ✅ PrusaSlicer / SuperSlicer
- ✅ Ultimaker Cura
- ✅ Creality Print

### Impressoras

| Tipo | Protocolo | Funcionalidades |
|---|---|---|
| OctoPrint / PrusaLink | API HTTP | Monitoramento, upload, câmera |
| Klipper/Moonraker | API HTTP | Monitoramento, upload, câmera, horas exatas |
| Bambu Lab | MQTT (nuvem + LAN) | Monitoramento em tempo real, AMS, câmera (JPEG A1/P1, RTSPS X1/X2/H2), detecção SSDP |
| Creality | WebSocket | Monitoramento, CFS, detecção UDP |
| FlashForge | API proprietária | Monitoramento, detecção UDP |
| Elegoo | SDCP sobre WebSocket | Monitoramento, detecção UDP |

---

## 🛠️ Tecnologia

| Componente | Tecnologia |
|---|---|
| Backend | Python 3.8+, Flask, Waitress |
| Frontend | HTML5, CSS3, JavaScript puro |
| Banco de dados | SQLite (modo WAL) |
| Desktop | pywebview (Windows) / modo navegador headless (Raspberry Pi, Linux) |
| Renderização 3D | PyRender, rasterizador de CPU numpy, Three.js |
| Mesh e nesting | trimesh, pymeshfix, shapely, rectpack |
| IA | Ollama (local) |
| Rede | paho-mqtt, smbclient, requests |
| Criptografia | cryptography (AES, IV aleatório por chamada) |
| Arquivos compactados | zipfile, rarfile, py7zr, tarfile |

---

## 📖 Documentação

### Atalhos de teclado

| Atalho | Ação |
|---|---|
| `Ctrl+K` | Paleta de comandos |
| `Ctrl+F` | Busca |
| `Ctrl+N` | Novo download |
| `Ctrl+,` | Configurações |
| `Ctrl+Z` | Desfazer a última exclusão (lixeira de 5 min) |
| `Alt+1-8` | Navegação rápida |
| `Shift+Clique` | Selecionar um intervalo de arquivos |
| `↑ ↓ ← →` + `Enter` | Navegar e abrir arquivos na biblioteca |
| `F` | Alternar favoritos |
| `T` | Gerenciador de tags |
| `?` | Ajuda de atalhos |
| `Esc` | Fechar modal / limpar busca |

### Estrutura do projeto

```
stellio/
├── main.py             # Backend Flask + Desktop
├── script.js           # JavaScript do frontend
├── index.html          # Interface principal
├── style.css           # Estilos
├── launcher.py         # Launcher leve / bootstrap do runtime
├── check_deps.py       # Verificador de dependências autorreparável
├── worker.py           # Worker em segundo plano (miniaturas, varreduras)
├── assets/             # Logos, ícones
├── languages/          # Arquivos de tradução (JSON)
├── apk/                # Pacote do app complementar Android
├── docs/               # Documentação, política de privacidade, READMEs traduzidos
├── requirements.txt    # Dependências Python
└── install-pi.sh       # Script de instalação para Raspberry Pi / Linux (serviço systemd)
```

Tem uma ideia? [Abra uma issue](https://github.com/stellio-app/stellio/issues)!

---

## 🤝 Como contribuir

Contribuições são bem-vindas! 🎉

1. Faça um **fork** do projeto
2. Crie sua branch (`git checkout -b feature/MinhaFuncionalidade`)
3. Faça commit das suas alterações (`git commit -m 'Adiciona MinhaFuncionalidade'`)
4. Envie a branch (`git push origin feature/MinhaFuncionalidade`)
5. Abra um **Pull Request**

### Diretrizes
- Siga o estilo de código existente
- Adicione comentários em francês ou inglês
- Teste suas alterações no Windows, se possível
- Atualize a documentação se necessário

### Reportar um bug

Use o modelo de relatório de bug e inclua:
- Versão do Stellio
- Sistema operacional
- Passos para reproduzir
- Logs de erro (exportáveis em Configurações → Diagnóstico)

---

## 📜 Licença

Este projeto está licenciado sob a **GNU Affero General Public License v3.0** — consulte o arquivo [LICENSE](../../LICENSE) para mais detalhes.

> 💡 **Em resumo**: você é livre para copiar, modificar e distribuir este software. Se você modificar o Stellio ou usá-lo para oferecer um serviço hospedado em rede, deve publicar o código-fonte completo sob a mesma licença AGPLv3.

---

## 🔒 Privacidade

O Stellio é local-first: seus dados permanecem na sua máquina, e nada é coletado ou enviado para servidores externos por padrão. Veja nossa [Política de Privacidade](../privacy/PRIVACY.md) para todos os detalhes.

---

## 🔏 Política de assinatura de código

Os executáveis do Windows publicados nas [Releases](https://github.com/stellio-app/stellio/releases) são assinados digitalmente. Veja [CODE_SIGNING_POLICY.md](../../CODE_SIGNING_POLICY.md) para detalhes sobre nosso processo de assinatura e a proteção da chave privada.

---

## 🙏 Agradecimentos

- [Ollama](https://ollama.com/) pela IA local
- [Flask](https://flask.palletsprojects.com/) pelo backend
- [Three.js](https://threejs.org/) pela renderização 3D na web
- [trimesh](https://github.com/mikedh/trimesh) pelo processamento de mesh
- [Spoolman](https://github.com/Donkie/Spoolman) pela gestão de carretéis de filamento
- [TigerTag](https://tigersystem.io) pela identificação NFC/RFID de filamentos
- À comunidade maker pelos comentários e sugestões
- A todos os contribuidores ❤️

---

## 📞 Contato e suporte

- 🐛 **Reportar um bug**: [GitHub Issues](https://github.com/stellio-app/stellio/issues)
- 💡 **Solicitar uma funcionalidade**: [GitHub Discussions](https://github.com/stellio-app/stellio/discussions)
- 📧 **Email**: contact@stellio-app.com
- 🌐 **Site**: [stellio-app.com](https://stellio-app.com)

---

## ⭐ Apoie o projeto

Se o Stellio é útil para você, considere:
- Dar uma **estrela** ⭐ no GitHub
- Compartilhar o projeto com outras pessoas
- [Contribuir com código](#-como-contribuir) ou traduções
- Reportar bugs para ajudar a melhorar o app

---

<p align="center"><strong>Feito com ❤️ para a comunidade maker</strong></p>

<p align="center">
  <a href="https://github.com/stellio-app/stellio">⭐ Dê uma estrela a este repositório</a> •
  <a href="https://github.com/stellio-app/stellio/issues">🐛 Reportar um bug</a> •
  <a href="https://github.com/stellio-app/stellio/discussions">💡 Solicitar uma funcionalidade</a>
</p>
