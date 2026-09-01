<div align="center">

#  <img src="https://stellio-app.com/assets/logo-nom-stellio.png" alt="Stellio Logo" width="200"/>

### O gestor de ficheiros 3D definitivo para makers e donos de impressoras 3D

[![Version](https://img.shields.io/github/v/release/stellio-app/stellio?color=blue)](https://github.com/stellio-app/stellio/releases)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Raspberry%20Pi%20%2F%20Linux-lightgrey.svg)]()
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)]()

[🇬🇧 English](../README.md) | [🇫🇷 Français](docs/readme/README.fr.md) | [🇩🇪 Deutsch](docs/readme/README.de.md) | [🇪🇸 Español](docs/readme/README.es.md) | [🇮🇹 Italiano](docs/readme/README.it.md) | 🇵🇹 **Português** | [🇯🇵 日本語](docs/readme/README.ja.md) | [🇨🇳 中文](docs/readme/README.zh.md)

[🚀 Instalação](#-instalação) • [✨ Funcionalidades](#-funcionalidades) • [📖 Documentação](#-documentação) • [🤝 Contribuir](#-contribuir) • [📜 Licença](#-licença)

</div>

---

## 🎯 Apresentação

**Stellio** é uma aplicação desktop moderna que centraliza toda a sua biblioteca 3D (STL, 3MF, OBJ), automatiza tarefas repetitivas e integra-se perfeitamente no seu fluxo de trabalho de impressão 3D.

Quer seja um maker iniciante ou um utilizador experiente com várias máquinas, o Stellio poupa-lhe tempo precioso graças à **IA local** (Ollama), à **gestão inteligente de impressoras** e a uma **interface pensada para a produtividade**.

> 💡 **Filosofia**: Os seus dados ficam consigo. Tudo funciona localmente.

---

## ✨ Funcionalidades

### 📚 Gestão de biblioteca
- 🗂️ **Múltiplas fontes**: pastas locais, ficheiros individuais, partilhas SMB/NFS
- 🖼️ **Miniaturas 3D automáticas** via PyRender (renderização de alta qualidade) ou Matplotlib (alternativa)
- 🏷️ **Etiquetas personalizadas** com cores + etiquetagem automática por IA
- 🔍 **Pesquisa semântica** assistida por IA ("procuro um suporte para...")
- ⭐ **Favoritos** e filtros avançados (tipo, tamanho, peso, estado de impressão)
- 🧩 **Projetos/Conjuntos**: agrupe vários ficheiros para o mesmo objeto
- 📊 **Estatísticas** detalhadas (formatos, plataformas, fiabilidade dos perfis)

### 🤖 Inteligência Artificial (Ollama local)
- 🏷️ **Etiquetagem automática** inteligente de ficheiros
- 📝 **Descrição automática** dos modelos
- 🔎 **Pesquisa semântica** em linguagem natural
- 🎯 **Recomendação de perfil de slicer** com base na geometria + histórico de sucesso
- 🩺 **S.O.S Print**: diagnóstico de falhas de impressão (com análise de fotos)

### 🖨️ Gestão de impressoras
- 🔌 Suporte para **OctoPrint**, **Klipper/Moonraker**, **Bambu Lab** (MQTT)
- 📡 Monitorização em tempo real (temperaturas, progresso, câmara)
- 🔧 **Manutenção preditiva** com recomendações por marca (Bambu, Prusa, Creality, etc.)
- ⏱️ Contador automático de horas de impressão
- 📤 Envio direto para o slicer ou upload para a impressora

### 🧵 Gestão de filamento
- 🔗 Integração com **Spoolman** (servidor de gestão de bobinas)
- 🟠 Suporte para **AMS Bambu Lab** (leitura dos slots)
- 🟢 Suporte para **CFS Creality**
- ⚪ Bobinas manuais
- 📉 Contagem automática de consumo ao enviar para o slicer
- ✅ Verificação de compatibilidade (quantidade suficiente?)

### 📥 Download a partir de plataformas
- 🟠 **Printables** (API GraphQL)
- 🟢 **MakerWorld** (login Bambu Lab em 2 passos)
- 🔵 **Thingiverse** (via chave API)
- 📁 Download direto para as suas fontes configuradas

### 🧩 Ferramentas avançadas
- 🎨 **Nesting automático** da mesa (rectpack ou silhueta real via shapely)
- 🔧 **Reparação de malha** (trimesh + pymeshfix)
- 🔄 **Conversor de formatos** (STL ↔ 3MF ↔ OBJ)
- 🛡️ **Verificação de integridade** (ficheiros corrompidos/em falta)
- 💰 **Cálculo do custo de impressão** (material + eletricidade)
- 📸 **Galeria de fotos** de impressão (bem-sucedidas/falhadas)
- 🕒 **Histórico** com classificação de sucesso/falha (alimenta a IA)
- 🔍 **Deteção de duplicados** (exatos e semelhantes por geometria)

### 🌐 Acesso remoto e móvel
- 📱 **Código QR** para acesso móvel (PWA instalável)
- 🌍 **Acesso remoto** via Cloudflare Tunnel (gratuito, URL aleatório ou fixo)
- 🔗 **Links de partilha** temporários (24h, utilização única)

### 🎨 Personalização
- 🌓 Temas: Escuro / Claro / Sistema
- 🎨 Temas de marca: Stellio, Bambu, Prusa, Voron, Creality
- 🎯 Cor de destaque personalizada
- 🌍 **8 idiomas**: FR, EN, DE, ES, IT, PT, JA, ZH
- 🧲 Reorganização da navegação por arrastar e largar

### 💾 Cópias de segurança e atualizações
- 📦 Exportação/Importação de cópia de segurança completa (.zip)
- 🔄 Atualizações automáticas a partir do GitHub (patch `.zip` — mesmo mecanismo no Windows e no Raspberry Pi/Linux)
- 📋 Exportação de registos de diagnóstico (segredos ocultados)

---

## 🖼️ Capturas de ecrã

<div align="center">
<table>
<tr></tr>
<td><img src="library.png" alt="Biblioteca" width="400"/><br><em>Biblioteca com miniaturas</em></td>
<td><img src="monitoring.png" alt="Impressoras" width="400"/><br><em>Monitorização de impressoras</em></td>
</tr>
<tr>
<td><img src="slicer.png" alt="Slicer" width="400"/><br><em>Recomendação de perfil por IA</em></td>
<td><img src="nesting.png" alt="Nesting" width="400"/><br><em>Nesting automático</em></td>
</tr>
</table>
</div>

---

## 🚀 Instalação

### 🪟 Windows (recomendado)

1. Descarregue o instalador mais recente a partir das [Releases](https://github.com/stellio-app/stellio-app/releases)
2. Execute `Stellio-Setup.exe`
3. Pronto! 🎉

### 🐧 Raspberry Pi / Linux

Funciona em **modo servidor headless** (sem interface gráfica): o Stellio corre em segundo plano e é utilizado a partir de um navegador, quer no próprio Pi quer em qualquer dispositivo da rede local.

**Requisitos**: recomenda-se Raspberry Pi 4 ou 5, Raspberry Pi OS de **64 bits**.

```bash
curl -O https://raw.githubusercontent.com/stellio-app/stellio-app/main/install-pi.sh
chmod +x install-pi.sh
./install-pi.sh
```

O script instala automaticamente:
- as dependências de sistema (`ffmpeg`, `unrar-free`, bibliotecas de renderização 3D)
- um ambiente virtual Python dedicado
- um **serviço systemd** (`stellio.service`) que inicia o Stellio no arranque e o reinicia automaticamente em caso de falha

Depois de instalado, o Stellio fica acessível em `http://<ip-do-pi>:5000`.

```bash
sudo systemctl status stellio     # Estado do serviço
sudo systemctl restart stellio    # Reiniciar
sudo journalctl -u stellio -f     # Seguir os logs em direto
```

> 💡 **Mesmas atualizações que no Windows**: o patch `.zip` publicado em cada release é idêntico em ambas as plataformas (código-fonte puro, nada compilado). O Stellio deteta-o e aplica-o automaticamente, depois reinicia o serviço — sem necessidade de reinstalação manual.

> 🎥 Funcionalidades idênticas à versão Windows, exceto a janela desktop nativa (substituída pelo acesso via navegador) e a IA local Ollama, que precisa de um modelo razoavelmente capaz para funcionar bem num Pi — aponte `ollama_url` para um servidor Ollama remoto nas Definições, se necessário.

### Slicers suportados

O Stellio deteta automaticamente:
- ✅ OrcaSlicer
- ✅ Bambu Studio
- ✅ PrusaSlicer / SuperSlicer
- ✅ Ultimaker Cura
- ✅ Creality Print

### Impressoras

| Tipo | Protocolo | Funcionalidades |
|------|-----------|-----------------|
| OctoPrint | API HTTP | Monitorização, upload, câmara |
| Klipper/Moonraker | API HTTP | Monitorização, upload, câmara, horas exatas |
| Bambu Lab | MQTT | Monitorização em tempo real, AMS, câmara (JPEG A1/P1, RTSPS X1/X2/H2) |

---

## 🛠️ Tecnologias

| Componente | Tecnologia |
|-----------|-------------|
| Backend | Python 3.8+, Flask, Waitress |
| Frontend | HTML5, CSS3, JavaScript vanilla |
| Base de dados | SQLite (modo WAL) |
| Desktop | pywebview (Windows) / modo headless via navegador (Raspberry Pi, Linux) |
| Renderização 3D | PyRender, Matplotlib, Three.js |
| Malha | trimesh, pymeshfix, shapely |
| IA | Ollama (local) |
| Rede | paho-mqtt, smbclient, requests |
| Encriptação | cryptography (AES-CFB) |
| Arquivos | zipfile, rarfile, py7zr, tarfile |

---

## 📖 Documentação

### Atalhos de teclado

| Atalho | Ação |
|-----------|--------|
| `Ctrl+F` | Pesquisar |
| `Ctrl+N` | Novo download |
| `Ctrl+,` | Definições |
| `Alt+1-8` | Navegação rápida |
| `F` | Alternar favoritos |
| `T` | Gestor de etiquetas |
| `?` | Ajuda de atalhos |
| `Esc` | Fechar modal / limpar pesquisa |

### Estrutura do projeto
```
stellio-app/
├── main.py                 # Backend Flask + Desktop
├── script.js                # JavaScript do frontend
├── index.html                # Interface principal
├── style.css                  # Estilos
├── assets/                     # Logótipos, ícones
├── languages/                   # Ficheiros de tradução (JSON)
├── requirements-pi.txt           # Dependências Python (instalação Raspberry Pi / Linux)
├── install-pi.sh                  # Script de instalação Raspberry Pi / Linux (serviço systemd)
```

---

Tem uma ideia? [Abra uma issue](https://github.com/stellio-app/stellio-app/issues)!

---

## 🤝 Contribuir

As contribuições são bem-vindas! 🎉

1. Faça um **fork** do projeto
2. Crie a sua branch (`git checkout -b feature/AmazingFeature`)
3. Faça commit das suas alterações (`git commit -m 'Add AmazingFeature'`)
4. Faça push da branch (`git push origin feature/AmazingFeature`)
5. Abra um **Pull Request**

### Diretrizes
- Respeite o estilo de código existente
- Adicione comentários em francês ou inglês
- Teste as suas alterações no Windows, se possível
- Atualize a documentação se necessário

### Reportar um erro
Utilize o modelo de relatório de bug e inclua:
- Versão do Stellio
- Sistema operativo
- Passos para reproduzir
- Logs de erro (exportáveis a partir de Definições → Diagnóstico)

---

## 📜 Licença

Este projeto está sob a licença livre **GNU Affero General Public License v3.0** — consulte o ficheiro [LICENSE](./LICENSE) para mais detalhes.

> 💡 **Em resumo**: é livre para copiar, modificar e distribuir este software. Se modificar o Stellio ou o utilizar para fornecer um serviço alojado em rede, deve publicar o código-fonte completo sob a mesma licença AGPLv3.

---

## 🔒 Privacidade

O Stellio é "local-first": os seus dados ficam na sua máquina, por padrão nada é recolhido nem enviado para servidores externos. Consulte a nossa [Política de Privacidade](./docs/privacy/PRIVACY.pt.md) para mais detalhes.

---

## 🔏 Política de assinatura de código

Os executáveis do Windows publicados nas [Releases](https://github.com/stellio-app/stellio-app/releases) são assinados digitalmente. Consulte [CODE_SIGNING_POLICY.md](./CODE_SIGNING_POLICY.md) para mais detalhes sobre o nosso processo de assinatura e a proteção da chave privada.

---

## 🙏 Agradecimentos

- [Ollama](https://ollama.com/) pela IA local
- [Flask](https://flask.palletsprojects.com/) pelo backend
- [Three.js](https://threejs.org/) pela renderização 3D web
- [trimesh](https://github.com/mikedh/trimesh) pelo processamento de malhas
- À comunidade maker pelos comentários e sugestões
- A todos os contribuidores ❤️

---

## 📞 Contacto e suporte

- 🐛 **Relatório de bug**: [GitHub Issues](https://github.com/stellio-app/stellio-app/issues)
- 💡 **Pedido de funcionalidade**: [GitHub Discussions](https://github.com/stellio-app/stellio-app/discussions)
- 📧 **Email**: contact@stellio-app.com
- 🌐 **Website**: [stellio-app.com](https://stellio-app.com)

---

## ⭐ Apoiar o projeto

Se o Stellio lhe for útil, considere:
- Dar uma **estrela** ⭐ no GitHub
- Partilhar o projeto com outros
- [Contribuir com código](#-contribuir) ou traduções
- Reportar bugs para ajudar a melhorar a aplicação

---

<div align="center">

**Feito com ❤️ para a comunidade maker**

[⭐ Star this repo](https://github.com/stellio-app/stellio-app) • [🐛 Report a bug](https://github.com/stellio-app/stellio-app/issues) • [💡 Request a feature](https://github.com/stellio-app/stellio-app/discussions)

</div>
