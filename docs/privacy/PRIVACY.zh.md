# 隐私政策

**最后更新：** 2026年10月20日  
**应用程序：** Stellio  
**网站：** [stellio-app.com](https://stellio-app.com)  
**仓库：** [github.com/stellio-app/stellio](https://github.com/stellio-app/stellio)

## 1. 引言
欢迎使用Stellio的隐私政策。Stellio是一款3D文件管理和3D打印应用程序。本政策描述了我们如何处理数据。

我们的基本理念很简单：**您的数据留在您身边。所有操作均在本地运行。**

## 2. 核心原则："Local-First（本地优先）"
默认情况下，Stellio**不**在外部服务器上收集、传输或存储**任何数据**。您所有的3D文件（STL、3MF、OBJ）、打印机型号、打印历史、标签和设置都仅存储在您自己的机器（Windows、Raspberry Pi或Linux）上的本地SQLite数据库中。

## 3. 本地存储的数据
以下项目仅保存在您的设备上：
- 您的3D文件库及其元数据（标签、描述、统计数据）。
- 本地生成的3D缩略图（通过PyRender或Matplotlib）。
- 您的打印机和切片软件配置。
- 您的API密钥和凭证（本地存储并通过AES-CFB加密）。
- 打印历史和相关照片。
- 用于诊断的活动日志。

## 4. 与第三方服务的交互（可选）
为了正常运行，Stellio的某些*可选*功能可能会与外部服务通信。您对这些功能的启用保留完全控制权：

- **自动更新**：Stellio可能会查询GitHub仓库（`github.com/stellio-app/stellio`）以检查新版本的可用性。在此检查期间不会传输任何个人标识符。
- **3D模型平台**：如果您使用下载功能，Stellio将使用**您自己的凭证或API密钥**直接连接到Printables、MakerWorld、Thingiverse或Nexprint（Elegoo的模型库）的API。这些信息永远不会发送到Stellio服务器。
- **打印机管理**：Stellio直接与您的本地/网络打印机或打印服务器（OctoPrint、Klipper/Moonraker、通过MQTT的Bambu Lab）通信。除非您明确配置远程访问，否则这些通信将限制在您的本地网络内。
- **远程访问（Cloudflare隧道）**：如果您启用远程访问，您的流量将通过Cloudflare服务器安全路由。请参阅[Cloudflare隐私政策](https://www.cloudflare.com/privacypolicy/)了解详情。
- **人工智能（Ollama）**：默认情况下，AI（Ollama）在您的机器上本地运行。如果您选择在设置中配置远程Ollama URL，您的请求（模型描述、语义搜索）将发送到您自己选择的该第三方服务器。
- **Spoolman**：如果您将Stellio连接到外部Spoolman服务器，耗材消耗数据将发送到您控制或选择的该服务器。
- **推送通知（可选，默认关闭）**：如果您在设置中启用，Stellio会将您所选通知的标题和文本（例如打印结束或失败，可能包含文件名或打印机名称）发送到您选择的服务：ntfy（公共服务器`ntfy.sh`或您自己的服务器）、Telegram（使用您提供的机器人令牌和聊天ID）、Discord Webhook，或您自己的Webhook URL。此后该服务的隐私政策适用。在公共ntfy服务器上，任何知道您主题名称的人都可以读取消息：请选择难以猜测的主题名称，或自行托管服务器。
- **TigerTag（可选）**：如果您使用TigerTag集成，Stellio会通过Google的身份验证和数据库服务（Firebase：`securetoken.googleapis.com`、`identitytoolkit.googleapis.com`、`firestore.googleapis.com`，以及`tigertag-cdn.web.app`）连接到您的TigerTag账户以读取您的耗材盘库存，并连接到`api.tigertag.io`下载公开的参考表。会话令牌加密存储在您的机器上。
- **错误报告和建议（可选）**：除非您提交表单并明确表示同意，否则不会发送任何内容。您填写的类型、标题和描述将发送到托管在Cloudflare Workers上的中继，由其在项目的GitHub仓库中创建一个**公开**的issue：请勿包含个人信息或机密。如果您勾选技术信息选项，将附加Stellio版本、操作系统和界面语言。之后Stellio会查询GitHub公共API以显示您请求的状态和评论，并在本地保留一个管理令牌。
- **模型更新跟踪（默认启用，可在设置中关闭）**：Stellio会自动向Printables、MakerWorld或Thingiverse（如果您已配置，则使用您的Thingiverse令牌）查询您已下载的模型是否有新版本。仅发送每个模型的标识符。
- **耗材商店搜索（仅在您使用时）**：当您在商店中查询某盘耗材的库存时，Stellio会将您的搜索词（品牌、材料、颜色）发送到商店网站（例如Atome3D、Rainbow3D、Amazon、Bambu Lab商店，以及您的实用链接列表中的商店）。
- **其他Stellio实例（可选）**：如果您添加远程Stellio实例或使用发现功能（会扫描您的本地网络），Stellio会联系相关地址。您选择发送的文件或文件夹会直接传送到您选定的实例，并通过其访问密钥进行身份验证，绝不经过我们的服务器。

## 5. 数据安全
- **加密**：敏感数据（如API密钥或打印机密码）使用AES-CFB算法在本地加密。
- **诊断**：如果您遇到错误，可以从设置中导出诊断日志。Stellio在导出前会自动屏蔽机密和敏感信息。我们不会自动收集这些日志。

## 6. 您的权利
由于您的所有数据都存储在本地，您对其拥有绝对控制权：
- 您可以通过备份功能（`.zip`）随时导出您的所有数据。
- 您可以直接从界面删除任何文件、历史记录条目或设置。
- 卸载应用程序会删除程序文件，但如果您希望永久删除您的历史和数据库，则需要手动删除本地数据文件夹。

## 7. 本政策的变更
我们可能会更新本隐私政策，以反映Stellio功能或法律义务的变化。本文档顶部的"最后更新"日期将相应修订。我们鼓励您定期查看此页面。

## 8. 联系方式
如果您对本隐私政策或数据管理有任何疑问或顾虑，可以联系我们：
- 📧 邮箱：[contact@stellio-app.com](mailto:contact@stellio-app.com)
- 🐛 错误报告：[GitHub Issues](https://github.com/stellio-app/stellio/issues)
- 💬 讨论：[GitHub Discussions](https://github.com/stellio-app/stellio/discussions)

---
*本项目是开源的。欢迎您在我们GitHub仓库审计源代码，以自行验证对本政策的遵守情况。*