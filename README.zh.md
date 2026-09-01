<div align="center">

#  <img src="https://stellio-app.com/assets/logo-nom-stellio.png" alt="Stellio Logo" width="200"/>

### 面向创客与 3D 打印用户的终极 3D 文件管理工具

[![Version](https://img.shields.io/badge/version-0.6.2-blue.svg)](https://github.com/stellio-app/stellio-app/releases)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Raspberry%20Pi%20%2F%20Linux-lightgrey.svg)]()
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)]()

[🇬🇧 English](README.md) | [🇫🇷 Français](README.fr.md) | [🇩🇪 Deutsch](README.de.md) | [🇪🇸 Español](README.es.md) | [🇮🇹 Italiano](README.it.md) | [🇵🇹 Português](README.pt.md) | [🇯🇵 日本語](README.ja.md) | 🇨🇳 **中文**

[🚀 安装](#-安装) • [✨ 功能](#-功能) • [📖 文档](#-文档) • [🤝 贡献](#-贡献) • [📜 许可证](#-许可证)

</div>

---

## 🎯 简介

**Stellio** 是一款现代化的桌面应用程序，可集中管理您的整个 3D 文件库（STL、3MF、OBJ），自动化重复性任务,并无缝集成到您的 3D 打印工作流程中。

无论您是刚入门的创客，还是拥有多台设备的资深打印用户，Stellio 都能凭借**本地 AI**（Ollama）、**智能打印机管理**以及**专为效率设计的界面**,为您节省宝贵的时间。

> 💡 **理念**：数据留在本地，一切均在本地运行。

---

## ✨ 功能

### 📚 文件库管理
- 🗂️ **多来源支持**：本地文件夹、单个文件、SMB/NFS 共享
- 🖼️ 通过 PyRender（高质量渲染）或 Matplotlib（备用方案）实现**自动生成 3D 缩略图**
- 🏷️ 带颜色的**自定义标签** + AI 自动打标
- 🔍 AI 辅助的**语义搜索**（例如“我在找一个用于……的支撑件”）
- ⭐ **收藏夹**和高级筛选（类型、大小、重量、打印状态）
- 🧩 **项目/装配体**：将多个文件归类为同一物体
- 📊 详细的**统计信息**（格式、平台、配置文件可靠性)

### 🤖 人工智能（本地 Ollama）
- 🏷️ 智能**自动打标**文件
- 📝 模型的**自动描述生成**
- 🔎 自然语言**语义搜索**
- 🎯 基于几何形状与历史成功率的**切片配置推荐**
- 🩺 **S.O.S Print**：打印失败诊断（支持照片分析）

### 🖨️ 打印机管理
- 🔌 支持 **OctoPrint**、**Klipper/Moonraker**、**Bambu Lab**（MQTT）
- 📡 实时监控（温度、进度、摄像头）
- 🔧 按品牌提供建议的**预测性维护**（Bambu、Prusa、Creality 等）
- ⏱️ 自动统计打印小时数
- 📤 直接发送至切片软件或上传到打印机

### 🧵 耗材管理
- 🔗 **Spoolman** 集成（线材管理服务器）
- 🟠 支持 **Bambu Lab AMS**（读取料槽）
- 🟢 支持 **Creality CFS**
- ⚪ 手动线材记录
- 📉 发送至切片软件时自动统计消耗量
- ✅ 兼容性检查（余量是否充足?）

### 📥 从平台下载
- 🟠 **Printables**（GraphQL API）
- 🟢 **MakerWorld**（Bambu Lab 两步登录）
- 🔵 **Thingiverse**（通过 API 密钥）
- 📁 直接下载到已配置的文件来源

### 🧩 高级工具
- 🎨 打印板的**自动排版**（rectpack 或通过 shapely 实现的真实轮廓排版）
- 🔧 **网格修复**（trimesh + pymeshfix）
- 🔄 **格式转换器**（STL ↔ 3MF ↔ OBJ）
- 🛡️ **完整性检查**（损坏/缺失文件）
- 💰 **打印成本计算**（材料费 + 电费）
- 📸 打印**照片图库**（成功/失败）
- 🕒 带成功/失败评级的**历史记录**（用于训练 AI）
- 🔍 **重复文件检测**（完全一致及几何相似）

### 🌐 远程与移动端访问
- 📱 用于移动端访问的**二维码**（可安装为 PWA）
- 🌍 通过 Cloudflare Tunnel 实现**远程访问**（免费，支持随机或固定网址）
- 🔗 临时**分享链接**（24 小时有效，仅限一次使用）

### 🎨 个性化设置
- 🌓 主题：深色 / 浅色 / 跟随系统
- 🎨 品牌主题：Stellio、Bambu、Prusa、Voron、Creality
- 🎯 自定义强调色
- 🌍 **支持 8 种语言**：FR、EN、DE、ES、IT、PT、JA、ZH
- 🧲 拖放式导航栏排序

### 💾 备份与更新
- 📦 完整备份的导出/导入（.zip）
- 🔄 从 GitHub 自动更新（`.zip` 补丁 — Windows 与 Raspberry Pi/Linux 采用相同机制）
- 📋 导出诊断日志（隐藏敏感信息）

---

## 🖼️ 界面截图

<div align="center">
<table>
<tr></tr>
<td><img src="library.png" alt="文件库" width="400"/><br><em>带缩略图的文件库</em></td>
<td><img src="monitoring.png" alt="打印机" width="400"/><br><em>打印机监控</em></td>
</tr>
<tr>
<td><img src="slicer.png" alt="切片软件" width="400"/><br><em>AI 配置文件推荐</em></td>
<td><img src="nesting.png" alt="排版" width="400"/><br><em>自动排版</em></td>
</tr>
</table>
</div>

---

## 🚀 安装

### 🪟 Windows（推荐）

1. 从 [Releases](https://github.com/stellio-app/stellio-app/releases) 下载最新安装程序
2. 运行 `Stellio-Setup.exe`
3. 完成！🎉

### 🐧 Raspberry Pi / Linux

以**无界面服务器模式**运行（无图形界面）：Stellio 在后台运行,可通过浏览器在 Pi 本机或局域网内任意设备上使用。

**运行要求**：建议使用 Raspberry Pi 4 或 5，**64 位**版 Raspberry Pi OS。

```bash
curl -O https://raw.githubusercontent.com/stellio-app/stellio-app/main/install-pi.sh
chmod +x install-pi.sh
./install-pi.sh
```

该脚本会自动安装：
- 系统依赖项（`ffmpeg`、`unrar-free`、3D 渲染库）
- 专用的 Python 虚拟环境
- 一个 **systemd 服务**（`stellio.service`），可在开机时启动 Stellio，并在崩溃时自动重启

安装完成后，可通过 `http://<Pi的IP地址>:5000` 访问 Stellio。

```bash
sudo systemctl status stellio     # 查看服务状态
sudo systemctl restart stellio    # 重启服务
sudo journalctl -u stellio -f     # 实时查看日志
```

> 💡 **与 Windows 相同的更新方式**：每次发布随附的 `.zip` 补丁在两个平台上完全相同（纯源代码，无需编译）。Stellio 会自动检测并应用更新，然后重启服务 — 无需手动重新安装。

> 🎥 功能与 Windows 版本基本相同，区别在于原生桌面窗口被浏览器访问取代,并且本地 Ollama AI 需要一个性能较好的模型才能在 Pi 上流畅运行 — 如有需要，可在设置中将 `ollama_url` 指向远程 Ollama 服务器。

### 支持的切片软件

Stellio 可自动识别：
- ✅ OrcaSlicer
- ✅ Bambu Studio
- ✅ PrusaSlicer / SuperSlicer
- ✅ Ultimaker Cura
- ✅ Creality Print

### 支持的打印机

| 类型 | 协议 | 功能 |
|------|-----------|-----------------|
| OctoPrint | HTTP API | 监控、上传、摄像头 |
| Klipper/Moonraker | HTTP API | 监控、上传、摄像头、精确工时 |
| Bambu Lab | MQTT | 实时监控、AMS、摄像头（JPEG A1/P1，RTSPS X1/X2/H2） |

---

## 🛠️ 技术栈

| 组件 | 技术 |
|-----------|-------------|
| 后端 | Python 3.8+、Flask、Waitress |
| 前端 | HTML5、CSS3、原生 JavaScript |
| 数据库 | SQLite（WAL 模式） |
| 桌面端 | pywebview（Windows）/ 无界面浏览器模式（Raspberry Pi、Linux） |
| 3D 渲染 | PyRender、Matplotlib、Three.js |
| 网格处理 | trimesh、pymeshfix、shapely |
| AI | Ollama（本地） |
| 网络 | paho-mqtt、smbclient、requests |
| 加密 | cryptography（AES-CFB） |
| 压缩包 | zipfile、rarfile、py7zr、tarfile |

---

## 📖 文档

### 键盘快捷键

| 快捷键 | 操作 |
|-----------|--------|
| `Ctrl+F` | 搜索 |
| `Ctrl+N` | 新建下载 |
| `Ctrl+,` | 设置 |
| `Alt+1-8` | 快速导航 |
| `F` | 切换收藏 |
| `T` | 标签管理器 |
| `?` | 快捷键帮助 |
| `Esc` | 关闭弹窗 / 清空搜索 |

### 项目结构
```
stellio-app/
├── main.py                 # Flask + 桌面端 后端
├── script.js                # 前端 JavaScript
├── index.html                # 主界面
├── style.css                  # 样式表
├── assets/                     # 徽标、图标
├── languages/                   # 翻译文件（JSON）
├── requirements-pi.txt           # Python 依赖项（Raspberry Pi / Linux 安装用）
├── install-pi.sh                  # Raspberry Pi / Linux 安装脚本（systemd 服务）
```

---

有好的想法？[提交一个 issue](https://github.com/stellio-app/stellio-app/issues) 吧！

---

## 🤝 贡献

欢迎贡献代码！🎉

1. **Fork** 本项目
2. 创建您的分支（`git checkout -b feature/AmazingFeature`）
3. 提交您的更改（`git commit -m 'Add AmazingFeature'`）
4. 推送分支（`git push origin feature/AmazingFeature`）
5. 发起一个 **Pull Request**

### 贡献指南
- 请遵循现有的代码风格
- 请使用法语或英语撰写注释
- 如条件允许，请在 Windows 上测试您的更改
- 如有需要，请更新相关文档

### 报告问题
请使用 bug 报告模板，并附上以下信息：
- Stellio 版本号
- 操作系统
- 复现步骤
- 错误日志（可从“设置 → 诊断”中导出）

---

## 📜 许可证

本项目采用自由许可证 **GNU Affero General Public License v3.0** 授权 — 详情请参阅 [LICENSE](./LICENSE) 文件。

> 💡 **简而言之**：您可以自由复制、修改和分发本软件。如果您修改了 Stellio，或将其用于通过网络提供托管服务，则必须以相同的 AGPLv3 许可证公开完整源代码。

---

## 🙏 鸣谢

- [Ollama](https://ollama.com/)——本地 AI 支持
- [Flask](https://flask.palletsprojects.com/)——后端框架
- [Three.js](https://threejs.org/)——Web 端 3D 渲染
- [trimesh](https://github.com/mikedh/trimesh)——网格处理
- 感谢创客社区提供的反馈与建议
- 感谢所有贡献者 ❤️

---

## 📞 联系与支持

- 🐛 **问题反馈**：[GitHub Issues](https://github.com/stellio-app/stellio-app/issues)
- 💡 **功能建议**：[GitHub Discussions](https://github.com/stellio-app/stellio-app/discussions)
- 📧 **邮箱**：contact@stellio-app.com
- 🌐 **官网**：[stellio-app.com](https://stellio-app.com)

---

## ⭐ 支持本项目

如果 Stellio 对您有帮助，欢迎：
- 在 GitHub 上点个**星标** ⭐
- 向身边的人分享本项目
- [参与代码贡献](#-贡献)或帮助翻译
- 报告问题，帮助改进应用

---

<div align="center">

**用 ❤️ 为创客社区打造**

[⭐ Star this repo](https://github.com/stellio-app/stellio-app) • [🐛 Report a bug](https://github.com/stellio-app/stellio-app/issues) • [💡 Request a feature](https://github.com/stellio-app/stellio-app/discussions)

</div>
