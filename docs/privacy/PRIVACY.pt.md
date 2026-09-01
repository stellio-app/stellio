# Política de Privacidade

**Última atualização:** 1 de setembro de 2026  
**Aplicação:** Stellio  
**Site:** [stellio-app.com](https://stellio-app.com)  
**Repositório:** [github.com/stellio-app/stellio](https://github.com/stellio-app/stellio)

## 1. Introdução
Bem-vindo à Política de Privacidade do Stellio. Stellio é um aplicativo de gerenciamento de arquivos 3D e impressão 3D. Esta política descreve como processamos os dados.

Nossa filosofia fundamental é simples: **Seus dados ficam com você. Tudo é executado localmente.**

## 2. Princípio Fundamental: "Local-First"
Por padrão, o Stellio **não** coleta, transmite nem armazena **nenhum dado** em servidores externos. Todos os seus arquivos 3D (STL, 3MF, OBJ), seus modelos de impressora, histórico de impressões, tags e configurações são armazenados exclusivamente em sua própria máquina (Windows, Raspberry Pi ou Linux) em um banco de dados SQLite local.

## 3. Dados Armazenados Localmente
Os seguintes itens são salvos apenas em seu dispositivo:
- Sua biblioteca de arquivos 3D e seus metadados (tags, descrições, estatísticas).
- Miniaturas 3D geradas localmente (via PyRender ou Matplotlib).
- Suas configurações de impressoras e slicers.
- Suas chaves de API e credenciais (armazenadas localmente e criptografadas via AES-CFB).
- Histórico de impressões e fotos associadas.
- Logs de atividade para diagnóstico.

## 4. Interações com Serviços de Terceiros (Opcional)
Para funcionar, certos recursos *opcionais* do Stellio podem se comunicar com serviços externos. Você mantém total controle sobre a ativação desses recursos:

- **Atualizações automáticas**: O Stellio pode consultar repositórios do GitHub (`github.com/stellio-app/stellio`) para verificar a disponibilidade de novas versões. Nenhum identificador pessoal é transmitido durante essa verificação.
- **Plataformas de Modelos 3D**: Se você usar o recurso de download, o Stellio se conecta diretamente às APIs do Printables, MakerWorld ou Thingiverse usando **suas próprias credenciais ou chaves de API**. Essas informações nunca são enviadas aos servidores do Stellio.
- **Gerenciamento de Impressoras**: O Stellio se comunica diretamente com suas impressoras locais/de rede ou servidores de impressão (OctoPrint, Klipper/Moonraker, Bambu Lab via MQTT). Essas comunicações permanecem confinadas à sua rede local, a menos que você configure explicitamente o acesso remoto.
- **Acesso Remoto (Túnel Cloudflare)**: Se você habilitar o acesso remoto, seu tráfego é roteado com segurança através dos servidores da Cloudflare. Por favor, consulte a [política de privacidade da Cloudflare](https://www.cloudflare.com/privacypolicy/) para detalhes.
- **Inteligência Artificial (Ollama)**: Por padrão, a IA (Ollama) é executada localmente em sua máquina. Se você escolher configurar um URL Ollama remoto nas configurações, suas solicitações (descrições de modelos, busca semântica) serão enviadas para esse servidor de terceiros que você mesmo escolheu.
- **Spoolman**: Se você conectar o Stellio a um servidor Spoolman externo, os dados de consumo de filamento são enviados para esse servidor que você controla ou escolheu.

## 5. Segurança dos Dados
- **Criptografia**: Dados sensíveis (como chaves de API ou senhas de impressoras) são criptografados localmente usando o algoritmo AES-CFB.
- **Diagnóstico**: Se você encontrar um bug, pode exportar um log de diagnóstico nas configurações. O Stellio mascara automaticamente segredos e informações sensíveis antes da exportação. Não coletamos esses logs automaticamente.

## 6. Seus Direitos
Como todos os seus dados são armazenados localmente, você tem controle absoluto sobre eles:
- Você pode exportar todos os seus dados a qualquer momento através da função de backup (`.zip`).
- Você pode excluir qualquer arquivo, entrada de histórico ou configuração diretamente da interface.
- Desinstalar o aplicativo remove os arquivos do programa, mas você precisará excluir manualmente a pasta de dados locais se desejar apagar permanentemente seu histórico e banco de dados.

## 7. Alterações Nesta Política
Podemos atualizar esta política de privacidade para refletir mudanças nos recursos do Stellio ou obrigações legais. A data de "Última atualização" no topo deste documento será revisada de acordo. Encorajamos você a consultar esta página periodicamente.

## 8. Contato
Se você tiver dúvidas ou preocupações sobre esta política de privacidade ou o gerenciamento de seus dados, pode entrar em contato conosco:
- 📧 Email: [contact@stellio-app.com](mailto:contact@stellio-app.com)
- 🐛 Relatório de bug: [GitHub Issues](https://github.com/stellio-app/stellio/issues)
- 💬 Discussões: [GitHub Discussions](https://github.com/stellio-app/stellio/discussions)

---
*Este projeto é de código aberto. Você está convidado a auditar o código-fonte em nosso repositório GitHub para verificar por si mesmo o cumprimento desta política.*