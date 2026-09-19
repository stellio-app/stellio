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

### 📚 Gerenciamento de biblioteca
- 🗂️ **Múltiplas fontes**: pastas locais, arquivos individuais, compartilhamentos SMB/NFS
- 🖼️ **Miniaturas 3D automáticas** via PyRender (renderização de alta qualidade) ou um rasterizador de CPU numpy (alternativa)
- 🏷️ **Tags personalizadas** com cores + marcação automática por IA
- 🔍 **Busca semântica assistida por IA** ("estou procurando um suporte para...")
- ⭐ **Favoritos** e filtros avançados (tipo, tamanho, peso, status de impressão)
- 🧩 **Projetos/Montagens**: agrupe vários arquivos em um único objeto, com suporte a múltiplas bandejas 3MF (navegação entre bandejas no visualizador)
- 🔁 **Detecção de duplicatas** (exatas e semelhantes por geometria)
- 📊 **Estatísticas detalhadas** (formatos, plataformas, confiabilidade dos perfis)

### 🤖 Inteligência artificial (Ollama local)
- 🏷️ **Marcação automática** inteligente dos arquivos
- 📝 **Descrição automática** dos modelos
- 🔎 **Busca semântica** em linguagem natural
- 📐 **Análise de imprimibilidade** (detecção de balanços/overhangs)
- 🎯 **Recomendação de perfil de slicer** baseada na geometria + histórico de sucesso
- 🩺 **S.O.S Print**: diagnóstico adaptativo de falhas de impressão, passo a passo — o Stellio faz uma pergunta por vez, reduz uma lista de hipóteses conforme suas respostas (máximo 4 perguntas) e depois entrega um diagnóstico final; a análise de fotos está disponível a qualquer momento

### 🖨️ Gerenciamento de impressoras
- 🔌 Suporte a **OctoPrint**, **Klipper/Moonraker**, **Bambu Lab** (MQTT), **Creality** (WebSocket), **FlashForge**
- 📡 **Descoberta automática na rede**: o Stellio varre sua rede local (SSDP para Bambu Lab, broadcast UDP para Elegoo/Centauri/FlashForge, sondagem direcionada para Klipper/OctoPrint/PrusaLink/Creality) e permite adicionar as impressoras detectadas com um clique
- 📡 Monitoramento em tempo real (temperaturas, progresso, câmera)
- 🔧 **Manutenção preditiva** com acompanhamento de tarefas e recomendações específicas por marca (Bambu, Prusa, Creality, etc.)
- ⏱️ Contador automático de horas de impressão
- 📤 Envio direto ao slicer, com um seletor de carretel para atribuir o filamento certo diretamente na janela de envio, ou upload para a impressora

### 🧵 Gerenciamento de filamento
- 🔗 Integração com **Spoolman** (servidor de gestão de carretéis)
- 🏷️ Integração de inventário **TigerTag** (somente leitura)
- 🟠 Suporte a **AMS da Bambu Lab** (leitura dos slots)
- 🟢 Suporte a **CFS da Creality**
- ⚪ Carretéis manuais
- 📉 Acompanhamento automático do consumo ao enviar para o slicer, com verificação de compatibilidade antes de imprimir (material suficiente?)
- 🔔 **Alertas de estoque baixo** na inicialização, com um link rápido para comprar mais

### 📥 Download de plataformas
- 🟠 **Printables** (API GraphQL)
- 🟢 **MakerWorld** (login Bambu Lab em 2 etapas)
- 🔵 **Thingiverse** (via chave de API)
- 🟣 **Cults3D**
- 📁 Download direto para suas fontes configuradas

### 🧩 Ferramentas avançadas
- 🎨 **Nesting automático** na mesa (rectpack ou silhueta real via shapely)
- 🔧 **Reparo de mesh** (trimesh + pymeshfix)
- 🔄 **Conversor de formatos** (STL ↔ 3MF ↔ OBJ)
- 🛡️ **Verificação de integridade** (arquivos corrompidos/ausentes)
- 💰 **Cálculo de custo de impressão** (material + eletricidade)
- 📸 **Galeria de fotos de impressões** (bem-sucedidas/com falha)
- 🕒 **Histórico** com avaliação de sucesso/falha (alimenta a IA)

### 🌐 Acesso móvel e remoto
- 📱 **QR code** para acessar sua biblioteca pelo celular (PWA instalável)
- 📲 **App complementar Android**: um QR code dedicado permite baixar e instalar o APK do app complementar do Stellio diretamente nas configurações de acesso móvel
- 🌍 **Acesso remoto** via Cloudflare Tunnel (gratuito, URL aleatória ou fixa)
- 🔗 **Links de compartilhamento** temporários (24h, uso único)

### 🎨 Personalização
- 🌓 Temas: Escuro / Claro / Sistema
- 🎨 Temas de marca: Stellio, Bambu, Prusa, Voron, Creality
- 🎯 Cor de destaque personalizada
- 🌍 **8 idiomas**: FR, EN, DE, ES, IT, PT, JA, ZH
- 🧲 Reorganização da navegação por arrastar e soltar

### 💾 Backup e atualizações
- 📦 Exportação/importação de backup completo (.zip)
- 🔄 Atualizações automáticas a partir do GitHub (patch `.zip` — mesmo mecanismo no Windows e no Raspberry Pi/Linux)
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
| `Ctrl+F` | Busca |
| `Ctrl+N` | Novo download |
| `Ctrl+,` | Configurações |
| `Alt+1-8` | Navegação rápida |
| `F` | Alternar favoritos |
| `T` | Gerenciador de tags |
| `?` | Ajuda de atalhos |
| `Esc` | Fechar modal / limpar busca |

### Estrutura do projeto

```
stellio/
├── main.py                 # Backend Flask + Desktop
├── script.js                # JavaScript do frontend
├── index.html                # Interface principal
├── style.css                  # Estilos
├── launcher.py                  # Launcher leve / bootstrap do runtime
├── check_deps.py                 # Verificador de dependências autorreparável
├── worker.py                       # Worker em segundo plano (miniaturas, varreduras)
├── assets/                          # Logos, ícones
├── languages/                        # Arquivos de tradução (JSON)
├── apk/                                # Pacote do app complementar Android
├── docs/                                # Documentação, política de privacidade, READMEs traduzidos
├── requirements.txt                      # Dependências Python
├── install-pi.sh                          # Script de instalação para Raspberry Pi / Linux (serviço systemd)
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
