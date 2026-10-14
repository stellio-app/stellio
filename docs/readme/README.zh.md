<p align="center">
  <img src="https://stellio-app.com/assets/logo-nom-stellio.png" alt="Stellio 标志" width="360">
</p>

<h3 align="center">面向创客与3D打印机用户的终极3D文件管理工具</h3>

<p align="center">
  <a href="https://github.com/stellio-app/stellio/releases"><img src="https://img.shields.io/github/v/release/stellio-app/stellio?color=blue" alt="版本"></a>
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
  <a href="README.pt.md">🇵🇹 Português</a> |
  <a href="README.ja.md">🇯🇵 日本語</a> |
  🇨🇳 <strong>中文</strong>
</p>

<p align="center">
  <a href="#-安装">🚀 安装</a> •
  <a href="#-功能">✨ 功能</a> •
  <a href="#-文档">📖 文档</a> •
  <a href="#-贡献">🤝 贡献</a> •
  <a href="#-许可证">📜 许可证</a>
</p>

---

## 🎯 概述

**Stellio** 是一款现代化的桌面应用程序，可集中管理您的整个3D文件库（STL、3MF、OBJ），自动化重复性任务，并与您的3D打印工作流程无缝集成。

无论您是新手创客还是管理多台打印机的资深用户，Stellio 都能借助**本地AI**（Ollama）、**智能打印机管理**以及**专为效率而设计的界面**，为您节省宝贵的时间。

> 💡 **理念**：您的数据始终掌握在您手中。一切均在本地运行。

---

## ✨ 功能

### 🏠 仪表盘与效率
- 📊 **启动仪表盘**：进行中的打印、耗材低库存、最近的打印和最近的文件一目了然
- 🧱 **完全可自定义**：通过拖放重新排列和隐藏小组件（共12个：进行中的打印、低库存、最新 S.O.S Print、建议、Stellio 实例等）
- ✅ 面向新用户的**“新手入门”清单**
- 💡 **“建议”小组件**：发现经常重印但已有一段时间没查看的文件，以及失败率较高的切片配置
- ⌨️ **命令面板（`Ctrl+K`）**：快速导航、执行操作，或即时查找文件、标签、卷轴和切片配置
- 🔔 **通知中心（铃铛）**：打印完成、失败、即将到期的维护、耗材低库存和烘干提醒集中在一处
- 📺 **悬浮小组件**：在所有页面显示当前打印进度
- 🧭 **交互式引导教程**：带您了解主要功能，可在设置中重新开始
- ♿ **无障碍**：高对比度模式、减少动画、处处可见的键盘焦点指示

### 📚 文件库管理
- 🗂️ **多种来源**：本地文件夹、单个文件、SMB/NFS 共享 — 电脑上检测到的3D文件夹会被推荐，并可一键添加
- 🖼️ **自动生成3D缩略图**：通过 PyRender（高质量渲染）或 numpy CPU 光栅化器（回退方案），带加载效果和**悬停放大预览**
- 🏷️ **自定义标签**（带颜色）+ AI自动打标，并支持**一键为多个选中文件打标**
- 🔍 **AI辅助的语义搜索**（例如"我在找一个用于……的支撑件"），并**记住最近的搜索**
- ⭐ **收藏**与高级筛选（类型、大小、重量、打印状态），当耗材库存不足以打印您的收藏时会显示**补货提醒**
- 🧵 **“耗材库存”筛选**：只保留用您实际拥有的卷轴（Spoolman、手动库存、TigerTag）即可打印的文件，按材料区分
- 💾 **已保存的筛选**：保存任意筛选组合，一键重复使用
- 📋 **“稍后打印”队列**：独立于收藏，可拖放排序，并可直接发送到切片软件
- 🖱️ **快速选择**：范围选择（`Shift+点击`）与键盘导航（方向键 + `Enter`）
- ✏️ **批量重命名**（查找/替换、前缀、后缀、编号），应用前可预览
- ↩️ **撤销删除**（`Ctrl+Z`）：借助5分钟的临时回收站实现 — 删除标签、项目或来源同样可以撤销，无需阻塞式确认
- 🔗 **模型来源**：文件详情中显示来源链接、作者、许可证和备注，已下载的文件还会记录下载日期
- 🧩 **项目/组装件**：将多个文件归为同一个对象，支持多板 3MF（在预览器中切换打印板）
- 🔁 **重复文件检测**（完全相同及几何相似）
- 🗜️ **压缩包支持**：直接浏览并提取压缩包中的模型
- 🖱️ 从文件资源管理器**拖放3D文件** — 桌面应用中可用，通过浏览器（Raspberry Pi、手机、远程访问）也同样可用
- 📊 **详细统计**（格式、平台、配置文件可靠性）

### 🤖 人工智能（本地 Ollama）
- 🏷️ 智能**自动打标**文件
- 📝 模型的**自动描述**
- 🔎 自然语言**语义搜索**
- 📐 **可打印性分析**（悬垂检测）与**推荐摆放方向**（悬垂更少，并显示与热床的接触率）
- 🎯 基于几何形状与打印成功历史的**切片配置推荐**
- ⏱️ 切片前的**打印时间预估**
- 🩺 **S.O.S Print**：自适应、逐步进行的打印失败诊断——Stellio 每次只问一个问题，根据您的回答逐步缩小假设列表（最多4个问题），最终给出诊断结果；随时支持照片分析，对话会被保存（可重新打开、标记为已解决）

### 🖨️ 打印机管理
- 🔌 支持 **OctoPrint**、**Klipper/Moonraker**、**Bambu Lab**（MQTT）、**Creality**（WebSocket）、**FlashForge**、**Elegoo**（SDCP）和 **PrusaLink**
- 📡 **自动网络发现**：Stellio 会扫描您的局域网（Bambu Lab 使用 SSDP，Elegoo/Centauri/FlashForge 使用 UDP 广播，Klipper/OctoPrint/PrusaLink/Creality 使用定向探测），并让您一键添加检测到的打印机
- 📡 实时监控（温度、进度、摄像头）
- 🔧 **预测性维护**，按品牌提供任务跟踪和建议（Bambu、Prusa、Creality 等）
- 🔩 **易损件与耗材**：喷嘴、打印板、皮带等的库存及预警，并与维护任务关联（每次保养自动扣减一个部件）
- ⏱️ 自动打印时长计数器
- 📤 直接发送到切片软件，可在发送对话框中直接通过卷轴选择器分配正确的耗材，或上传至打印机
- 👀 在发送到切片软件的窗口中，确认前即可**快速预览**（重量、预估打印时间）
- 🛡️ **增强的打印前检查**：如果分配的卷轴需要烘干、耗材具有磨蚀性（建议使用硬化钢喷嘴），或该打印机尚无校准数据，都会发出警告
- 🔁 **按上次设置重新打印**：在历史记录中一键重新打开发送窗口，沿用相同的打印机、配置和卷轴
- 🎛️ **校准数据**：按耗材和打印机保存 flow、pressure advance、温度等，并在发送到切片软件的窗口中调用
- 👥 **轻量协作模式**：可看到其他已连接设备是否正在查看某个文件，并通过提醒避免误将同一文件两次发送到切片软件

### 🧵 耗材管理
- 🔗 **Spoolman** 集成（卷轴管理服务器），支持在局域网中自动发现
- 🟠 支持 **Bambu Lab AMS**（插槽读取）
- 🟢 支持 **Creality CFS**
- 🐯 **TigerTag** 集成（NFC/RFID 卷轴识别）：登录后可在库存中查看您的 TigerTag 卷轴，或让 Stellio 自动获取已有的 TigerTag Studio 会话 — 只读，绝不会修改您的 TigerTag 库存
- ⚪ 手动卷轴
- 📉 发送到切片软件时自动跟踪耗材消耗，打印前进行兼容性检查（剩余材料是否足够？）
- 🔔 启动时的**低库存提醒**，并提供快速购买链接
- 💨 **卷轴烘干**：烘干记录、按材料判断的状态（干燥／需烘干）、建议的温度与时长，以及通知中的提醒
- 📈 **卷轴汇总**：在每个卷轴的详情页中显示打印次数、克数、成本以及未追踪的差额

### 📥 从平台下载
- 🟠 **Printables**（GraphQL API）
- 🟢 **MakerWorld**（Bambu Lab 两步登录）
- 🔵 **Thingiverse**（通过 API 密钥）
- 📁 直接下载到您配置的来源
- 🆕 **新版本检测**：Stellio 每天检查已下载的模型（Printables、MakerWorld、Thingiverse）是否有更新
- 🛒 **实用链接**：商店、厂商、3D模型网站和资源，按可折叠分组展示

### 🧩 高级工具
- 🎨 **自动排版嵌套**（rectpack 或通过 shapely 计算真实轮廓）
- 🔧 **网格修复**（trimesh + pymeshfix），提供**修复前后对比**（水密性、三角面数、顶点数、大小）
- 🔄 **格式转换器**（STL ↔ 3MF ↔ OBJ）
- 🛡️ **完整性检查**（损坏/缺失文件）
- 💰 **打印成本计算**：材料、电费、机器损耗（按小时）、固定费用、利润率（%）和数量 — 单价与总价精确到分
- 🧾 **PDF 报价单**：由成本计算生成，可自定义客户、品名和备注；可配置报价单抬头（姓名/公司、标志、地址、电话、邮箱、网站、税号）以及页脚的法律声明
- 🌱 **环境影响估算**：您打印作业的 CO₂ 足迹（材料 + 电力）
- 📸 **打印照片库**（成功/失败）
- 🕒 带成功/失败评分的**历史记录**（用于训练AI），每行都有**“查看文件”**和**“重新打印”**按钮（可检测已移动/已删除的文件），并支持按平台、结果（成功/失败/部分/未评分）和日期范围筛选

### 📈 报告与可靠性
- 🧮 **打印可靠性**：按切片配置、材料、打印机或卷轴排名的成功率和失败成本
- 🗓️ **月度报告**：当月的打印数、成功率、耗材、成本、失败次数和 CO₂，并与上月对比，可导出为 PDF

### 🔔 通知
- 🪟 **Windows 原生通知**
- 🌐 可为 Raspberry Pi 或移动端访问启用的**浏览器通知**
- 📣 **推送通知**（ntfy、Telegram、Discord 或 Webhook）：即使窗口已关闭也能检测到打印完成和失败，并推送维护与库存提醒

### 🌐 移动与远程访问
- 📱 **二维码**，方便从移动设备访问您的文件库（可安装的 PWA）
- 📲 **Android 配套应用**：在移动访问设置中提供专属二维码，可直接下载并安装 Stellio 配套 APK，并支持直接从某次打印中拍照
- 🌍 通过 Cloudflare Tunnel 实现**远程访问**（免费，随机或固定网址），或使用**自定义地址**（域名、DynDNS、VPN、Tailscale 等）以摆脱 Cloudflare，并可一键切换回 Cloudflare
- 🔗 临时**分享链接**（24小时有效，仅限使用一次）

### 👥 账户与多实例
- 🔐 带恢复码和密保问题的**本地账户**：100% 本地重置密码，无需邮箱或网络
- 👤 **只读访客账户**：放心地与他人共享您的文件库、打印机和库存
- 🔄 **Stellio 实例**：自动发现局域网内的其他安装并一键添加（只需输入对方的本地密钥）
- 📨 **向另一个实例发送文件**：可选择目标实例上的目标文件夹，接收到的文件会立即出现在其文件库中
- ✅ 仪表盘上的**实例状态小组件**（每个已保存的实例以绿色对勾或红色叉号显示是否可用）

### 🎨 个性化设置
- 🌓 主题：深色 / 浅色 / 跟随系统
- 🎨 品牌主题：Stellio、Bambu、Prusa、Voron、Creality
- 🎯 自定义强调色
- 🌍 **支持8种语言**：法语、英语、德语、西班牙语、意大利语、葡萄牙语、日语、中文
- 🧲 拖放方式重新排列导航
- ↩️ **撤销设置**：还原您最近一次的配置更改

### 💾 备份与更新
- 📦 完整备份的导出/导入（.zip）
- 🔄 从 GitHub 自动更新（`.zip` 补丁 — Windows 与 Raspberry Pi/Linux 使用相同机制）
- 🔁 更新后或启用调试模式后，在 Windows 和 Raspberry Pi/Linux 上都能可靠重启
- 📋 导出诊断日志（隐藏敏感信息）

---

## 🖼️ 截图

| | |
|---|---|
| ![文件库](../../library.png) *带缩略图的文件库* | ![打印机](../../monitoring.png) *打印机监控* |
| ![切片软件](../../slicer.png) *AI配置推荐* | ![嵌套排版](../../nesting.png) *自动嵌套排版* |

---

## 🚀 安装

### 🪟 Windows（推荐）

1. 从 [Releases](https://github.com/stellio-app/stellio/releases) 下载最新安装程序
2. 运行 `Stellio-Setup.exe`
3. 大功告成！🎉

### 🐧 Raspberry Pi / Linux

以**无图形界面的服务器模式**运行：Stellio 在后台运行，可通过浏览器访问，既可以在 Pi 本机访问，也可以在局域网内的任何设备上访问。

**系统要求**：推荐使用 Raspberry Pi 4 或 5，**64位** Raspberry Pi OS。

```bash
curl -O https://raw.githubusercontent.com/stellio-app/stellio/main/install-pi.sh
chmod +x install-pi.sh
./install-pi.sh
```

该脚本会自动安装：
- 系统依赖项（`ffmpeg`、`unrar-free`、3D渲染库）
- 专用的 Python 虚拟环境
- 一个 **systemd 服务**（`stellio.service`），会在开机时启动 Stellio，并在崩溃时自动重启

安装完成后，可通过 `http://<pi的IP>:5000` 访问 Stellio。

```bash
sudo systemctl status stellio     # 查看服务状态
sudo systemctl restart stellio    # 重启服务
sudo journalctl -u stellio -f     # 实时查看日志
```

> 💡 **与 Windows 相同的更新方式**：每个版本发布的 `.zip` 补丁在两个平台上是完全相同的（纯源代码，无需编译）。Stellio 会自动检测并应用补丁，然后重启服务 — 无需手动重新安装。
>
> 🎥 除原生桌面窗口（替换为浏览器访问）以及本地 Ollama AI（需要性能较好的模型才能在 Pi 上顺畅运行，如有需要可在设置中将 `ollama_url` 指向远程 Ollama 服务器）外，其余功能与 Windows 版本相同。

### 支持的切片软件

Stellio 可自动检测：
- ✅ OrcaSlicer
- ✅ Bambu Studio
- ✅ PrusaSlicer / SuperSlicer
- ✅ Ultimaker Cura
- ✅ Creality Print

### 打印机

| 类型 | 协议 | 功能 |
|---|---|---|
| OctoPrint / PrusaLink | HTTP API | 监控、上传、摄像头 |
| Klipper/Moonraker | HTTP API | 监控、上传、摄像头、精确打印时长 |
| Bambu Lab | MQTT（云端 + 局域网） | 实时监控、AMS、摄像头（JPEG A1/P1，RTSPS X1/X2/H2）、SSDP自动发现 |
| Creality | WebSocket | 监控、CFS、UDP自动发现 |
| FlashForge | 私有协议 API | 监控、UDP自动发现 |
| Elegoo | 基于 WebSocket 的 SDCP | 监控、UDP自动发现 |

---

## 🛠️ 技术栈

| 组件 | 技术 |
|---|---|
| 后端 | Python 3.8+、Flask、Waitress |
| 前端 | HTML5、CSS3、原生 JavaScript |
| 数据库 | SQLite（WAL 模式） |
| 桌面端 | pywebview（Windows）／无图形界面浏览器模式（Raspberry Pi、Linux） |
| 3D渲染 | PyRender、numpy CPU 光栅化器、Three.js |
| 网格与嵌套排版 | trimesh、pymeshfix、shapely、rectpack |
| AI | Ollama（本地） |
| 网络 | paho-mqtt、smbclient、requests |
| 加密 | cryptography（AES，每次调用随机生成IV） |
| 压缩包 | zipfile、rarfile、py7zr、tarfile |

---

## 📖 文档

### 键盘快捷键

| 快捷键 | 操作 |
|---|---|
| `Ctrl+K` | 命令面板 |
| `Ctrl+F` | 搜索 |
| `Ctrl+N` | 新建下载 |
| `Ctrl+,` | 设置 |
| `Ctrl+Z` | 撤销上一次删除（5分钟回收站） |
| `Alt+1-8` | 快速导航 |
| `Shift+点击` | 选择文件范围 |
| `↑ ↓ ← →` + `Enter` | 在文件库中导航并打开文件 |
| `F` | 切换收藏 |
| `T` | 标签管理器 |
| `?` | 快捷键帮助 |
| `Esc` | 关闭弹窗／清空搜索 |

### 项目结构

```
stellio/
├── main.py             # Flask + 桌面端后端
├── script.js           # 前端 JavaScript
├── index.html          # 主界面
├── style.css           # 样式
├── launcher.py         # 轻量启动器／运行时引导程序
├── check_deps.py       # 自我修复式依赖检查工具
├── worker.py           # 后台工作进程（缩略图、扫描）
├── assets/             # 标志、图标
├── languages/          # 翻译文件（JSON）
├── apk/                # Android 配套应用安装包
├── docs/               # 文档、隐私政策、多语言 README
├── requirements.txt    # Python 依赖项
└── install-pi.sh       # Raspberry Pi / Linux 安装脚本（systemd 服务）
```

有想法？[提交一个 issue](https://github.com/stellio-app/stellio/issues)！

---

## 🤝 贡献

欢迎贡献代码！🎉

1. **Fork** 本项目
2. 创建您的分支（`git checkout -b feature/AmazingFeature`）
3. 提交您的更改（`git commit -m 'Add AmazingFeature'`）
4. 推送分支（`git push origin feature/AmazingFeature`）
5. 提交一个 **Pull Request**

### 贡献指南
- 遵循现有的代码风格
- 使用法语或英语添加注释
- 尽可能在 Windows 上测试您的更改
- 如有需要，请更新相关文档

### 报告问题

请使用错误报告模板，并包含以下信息：
- Stellio 版本
- 操作系统
- 复现步骤
- 错误日志（可在 设置 → 诊断 中导出）

---

## 📜 许可证

本项目采用 **GNU Affero 通用公共许可证 v3.0** — 详情请参阅 [LICENSE](../../LICENSE) 文件。

> 💡 **简而言之**：您可以自由复制、修改和分发本软件。如果您修改了 Stellio，或将其用于提供网络托管服务，则必须以相同的 AGPLv3 许可证发布完整源代码。

---

## 🔒 隐私

Stellio 采用本地优先架构：您的数据保留在您的设备上，默认情况下不会向外部服务器收集或发送任何数据。完整详情请参阅我们的[隐私政策](../privacy/PRIVACY.md)。

---

## 🔏 代码签名政策

发布在 [Releases](https://github.com/stellio-app/stellio/releases) 中的 Windows 可执行文件均经过数字签名。有关签名流程及私钥保护措施的详情，请参阅 [CODE_SIGNING_POLICY.md](../../CODE_SIGNING_POLICY.md)。

---

## 🙏 致谢

- [Ollama](https://ollama.com/) 提供本地AI支持
- [Flask](https://flask.palletsprojects.com/) 提供后端支持
- [Three.js](https://threejs.org/) 提供网页端3D渲染
- [trimesh](https://github.com/mikedh/trimesh) 提供网格处理支持
- [Spoolman](https://github.com/Donkie/Spoolman) 提供耗材卷轴管理
- [TigerTag](https://tigersystem.io) 提供 NFC/RFID 耗材识别
- 感谢创客社区的反馈与建议
- 感谢所有贡献者 ❤️

---

## 📞 联系与支持

- 🐛 **报告问题**：[GitHub Issues](https://github.com/stellio-app/stellio/issues)
- 💡 **功能建议**：[GitHub Discussions](https://github.com/stellio-app/stellio/discussions)
- 📧 **邮箱**：contact@stellio-app.com
- 🌐 **官网**：[stellio-app.com](https://stellio-app.com)

---

## ⭐ 支持本项目

如果 Stellio 对您有帮助，欢迎：
- 在 GitHub 上点亮一颗**星标** ⭐
- 与身边的人分享这个项目
- [贡献代码](#-贡献) 或参与翻译
- 报告问题以帮助改进应用
- 在 Ko-fi 上小额打赏，支持开发 ☕

<p align="center">
  <a href="https://ko-fi.com/E6J828RYVD">
    <img src="https://ko-fi.com/img/githubbutton_sm.svg" alt="在 Ko-fi 上支持 Stellio">
  </a>
</p>

---

<p align="center"><strong>用 ❤️ 为创客社区打造</strong></p>

<p align="center">
  <a href="https://github.com/stellio-app/stellio">⭐ 为本仓库点星</a> •
  <a href="https://github.com/stellio-app/stellio/issues">🐛 报告问题</a> •
  <a href="https://github.com/stellio-app/stellio/discussions">💡 建议新功能</a>
</p>
