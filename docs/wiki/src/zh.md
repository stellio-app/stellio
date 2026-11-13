@@@ Home | 首页
# Stellio 维基
{{img:dashboard}}


**Stellio** 是为创客和 3D 打印机用户打造的 3D 文件管理器。它集中管理您的资料库（STL、3MF、OBJ、STEP、PLY、AMF），自动完成重复性工作，并融入您的打印工作流程。

> 🔒 **理念**：您的数据留在您手中。一切在本地运行；默认情况下，任何内容都不会离开您的电脑。

## 从哪里开始？

| 我想… | 页面 |
|---|---|
| 安装 Stellio | [安装](zh-Installation) |
| 迈出第一步 | [快速上手](zh-Getting-Started) |
| 管理我的 3D 文件 | [资料库](zh-Library) |
| 连接我的打印机 | [打印机](zh-Printers) |
| 跟踪我的耗材盘 | [耗材](zh-Filament) |
| 下载模型 | [下载](zh-Downloads) |
| 使用 AI 和 S.O.S Print | [人工智能](zh-AI) |
| 计算成本、报价、发票 | [成本与管理](zh-Costs-and-Management) |
| 用手机访问 | [远程与移动访问](zh-Remote-Access) |
| 安装到树莓派 / Proxmox | [服务器版](zh-Server-Edition) |
| 设置、备份、了解我的数据 | [设置与数据](zh-Settings-and-Data) |
| 解决问题 | [故障排除](zh-Troubleshooting) |
| 参与项目 | [参与贡献](zh-Contributing) |

## 实用链接

- 🌐 网站：[stellio-app.com](https://stellio-app.com) — ▶ [在线演示（只读）](https://demo.stellio-app.com)
- 📦 [下载（Releases）](https://github.com/stellio-app/stellio/releases)
- 🐛 [报告错误](https://github.com/stellio-app/stellio/issues) · 💡 [提出想法](https://github.com/stellio-app/stellio/discussions) · 💬 [Discord](https://discord.gg/ySxpHvS6bd)
- 📜 许可证 **AGPL v3**

@@@ Installation | 安装
# 安装

| 平台 | 文件 / 方式 | 模式 |
|---|---|---|
| 🪟 Windows | `Stellio-Setup-<version>.exe` | 桌面应用 |
| 🪟 Windows 便携版 | `Stellio-v<version>-portable-win64.zip` | 桌面应用，免安装 |
| 🍎 macOS | `.dmg`（Apple Silicon `arm64` 或 Intel `x86_64`） | 桌面应用 |
| 🐧 Linux | `Stellio-v<version>-x86_64.AppImage` | 桌面应用 |
| 🍓 树莓派 / Linux | `install-pi.sh` | 服务器（浏览器） |
| 🖥️ Proxmox VE | `stellio-lxc.sh` | 一条命令创建 LXC 容器 |
| 📲 Android | 配套 APK | 参见 [远程与移动访问](zh-Remote-Access) |

所有文件都在 [Releases](https://github.com/stellio-app/stellio/releases) 页面，每个文件都附有 `.sha256` 校验值。

## Windows

1. 从 Releases 下载安装程序。
2. 运行 `Stellio-Setup-<version>.exe`。
3. 完成。

**便携版**：解压到任意位置（硬盘、U 盘），运行 `Stellio.exe`。您的数据保存在可执行文件旁的 `data` 文件夹中（请保留 `portable.flag` 文件）。

> ⚠️ 安装程序**未经代码签名**：Windows SmartScreen 可能会显示警告。如有需要可核对 `.sha256`；内置更新在安装前会进行校验。

## macOS

打开 `.dmg`，将 Stellio 拖入“应用程序”。请选择与您的 Mac 匹配的文件：`arm64`（M1、M2、M3……）或 `x86_64`（Intel）。构建未经公证：首次启动时，右键点击 → **打开**。

> 如果屏幕一直空白：5000 端口可能被 macOS 的“AirPlay 接收器”占用。此时 Stellio 会自动选择另一个空闲端口。参见 [故障排除](zh-Troubleshooting)。

## Linux (AppImage)

```bash
chmod +x Stellio-v*-x86_64.AppImage
./Stellio-v*-x86_64.AppImage
```
AppImage 内置更新信息（`.zsync`）。

## 树莓派 / Linux 服务器

**无界面服务器**模式：Stellio 在后台运行，通过浏览器使用。详情参见 [服务器版](zh-Server-Edition)。

```bash
curl -O https://raw.githubusercontent.com/stellio-app/stellio/main/install-pi.sh
chmod +x install-pi.sh
./install-pi.sh
```

## Proxmox VE

在 **Proxmox 主机的 Shell** 中：
```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/stellio-app/stellio/main/stellio-lxc.sh)"
```
详情参见 [服务器版](zh-Server-Edition)。

## 更新

- **桌面版**：Stellio 从 GitHub 检测新版本并应用 `.zip` 补丁（Windows、macOS 和 Linux 机制相同）。仪表盘上的“更新”小组件会打开更新窗口。
- **服务器版**：同样的自动更新，或使用 `update-stellio`（LXC 容器）/ `./install-pi.sh`（树莓派）。
- 每个版本首次启动时，缺失的模块（PDF 报价、表格导入、通知等）会自动下载。

@@@ Getting-Started | 快速上手
# 快速上手
{{img:library}}


## 1. 首次启动
Stellio 会显示**引导式导览**和“快速上手”清单。您可以随时在设置中重新开始导览。

## 2. 创建账户
账户是**本地**的：密码 + 恢复码 + 密保问题。密码重置完全在本地完成，无需邮件和网络。

## 3. 添加来源
**来源**是存放模型的文件夹或共享：
- 本地文件夹、单个文件、**SMB** 或 **NFS** 共享；
- 在您的电脑上检测到的 3D 文件夹会被**推荐**，一键即可添加；
- 对每个来源，您可以选择显示哪些文件类型。

随后 Stellio 会扫描您的文件，并在后台生成 3D 缩略图。

## 4. 添加打印机（可选）
打开**打印机**页面：网络发现会列出检测到的设备。参见 [打印机](zh-Printers)。

## 5. 选择切片软件
Stellio 会自动检测已安装的切片软件（OrcaSlicer、Bambu Studio、PrusaSlicer、Cura 等）。发送按钮会直接在切片软件中打开文件。

## 仪表盘
主页汇总了正在进行的打印、低库存、最近的打印和最近的文件。**小组件**（约二十个）可通过拖放重新排序并可隐藏：当前打印、低库存、最新 S.O.S Print、建议、Stellio 实例、已完成项目、图库、报价等。

## 日常工具
- **命令面板** `Ctrl+K`：导航、执行操作、查找文件、标签、耗材盘或配置。
- **通知中心**（铃铛）：打印完成、失败、维护、低库存、耗材烘干。
- **悬浮小组件**：显示当前打印进度，所有页面可见。
- **键盘快捷键**：参见 [设置与数据](zh-Settings-and-Data)。

@@@ Library | 资料库
# 资料库
{{img:library}}


## 来源与缩略图
- 多个来源：本地文件夹、文件、SMB/NFS 共享。
- **自动 3D 缩略图**（PyRender，或 CPU 备用渲染器），悬停时显示放大预览。
- 一旦您使用应用，生成就会**暂停**，之后再继续。
- **缩略图性能**设置：自动 / 节能 / 普通 / 快速。
- 格式：STL、3MF（含多盘和 PrusaSlicer）、OBJ、STEP/STP、PLY、AMF（对无法读取它们的切片软件会转换为 STL），以及可直接浏览的压缩包（ZIP、RAR、7z、TAR）。

## 整理
- 彩色**标签**，支持 AI 自动打标签；一键为多个文件打标签。
- **收藏**、高级筛选（类型、大小、重量、打印状态）、**已保存的筛选**。
- 状态筛选：“已发送到切片软件”、“已打印”、“已成功”、“已失败”。
- **“耗材库存”筛选**：只保留用您现有耗材盘即可打印的文件。
- 排序、搜索和筛选在重新打开应用时会被**记住**。
- **“即将打印”**队列，可重新排序，可发送到切片软件。
- **批量重命名**（查找/替换、前缀、后缀、编号），带预览。
- **撤销删除**（`Ctrl+Z`）：借助 5 分钟的临时回收站；也适用于标签、项目和来源。
- 快速选择：`Shift+点击` 选择范围，方向键 + `Enter`。
- **重复文件检测**（完全相同和几何相似）。
- **模型来源**：来源链接、作者、许可证、备注、下载日期。
- 从文件资源管理器**拖放** 3D 文件，通过浏览器也可使用。

## 搜索
- 常规搜索和 **AI 语义搜索**（“我想找一个……的支架”），并记住最近的搜索。
- **智能合集**。

## 项目 / 组装件
把多个文件归入同一个物体。
- **多盘** 3MF：添加到项目时会拆分为每个盘一个 3MF（6 个盘 = 6 个文件），存放在隐藏文件夹中。
- 文件 ⋯ 菜单中的**“拆分盘”**操作。
- 项目卡片：点击缩略图 = 3D 查看器；“全部 / 进行中 / 已完成”筛选会被记住；一键查看**项目成本**。

{{img:projects}}

## 3D 查看器与工具
- **3D 查看器**（Three.js，可离线使用），支持在各盘之间切换。
- **自动排版**（rectpack，或使用 shapely 的真实轮廓）。
- **网格修复**（trimesh + pymeshfix），带修复前后对比。
- **转换器** STL ↔ 3MF ↔ OBJ。
- **可打印性分析**（悬垂）和**推荐摆放方向**。
- **完整性检查**（损坏或缺失的文件）。
- 详细**统计**（格式、平台、配置可靠性）。

{{img:viewer}}

## 历史与照片
- 按周分页的**历史**，支持成功/失败评价（用于训练 AI）、**查看文件**和**重新打印**按钮，可按平台、结果和日期筛选。
- **打印照片图库**。打印结束照片之后可一键标记为*成功*或*失败*。
- **我的 G-code**：与文件关联的 G-code、下载，以及**在切片软件中打开**按钮。
- 资料库的**备份**：参见 [设置与数据](zh-Settings-and-Data)。

@@@ Printers | 打印机
# 打印机
{{img:printers}}


## 支持的品牌

| 品牌 | 型号 | 连接方式 |
|---|---|---|
| **Bambu Lab** | X1/X1C/X1E、X2D、P1P/P1S、P2S、A1/A1 mini、H2D/H2S/H2C | MQTT（局域网 + 云）：监控、AMS、摄像头、SSDP 发现 |
| **Prusa** | MK4、MK3.9、MK3.5、MINI+、XL、CORE One | PrusaLink（HTTP） |
| **Creality** | K1/K2 系列、Ender-3 V3、Hi | WebSocket：监控、CFS、UDP 发现 |
| **Elegoo** | Centauri Carbon 1 和 2、Saturn/Mars 光固化系列 | SDCP（WebSocket） |
| **FlashForge** | Adventurer 5M/5M Pro、AD5X | 专有 API |
| **Klipper / Moonraker** | 任何运行 Klipper 的机器（Voron 等） | HTTP：监控、上传、摄像头、精确小时数 |
| **OctoPrint** | 任何由 OctoPrint 控制的打印机 | HTTP |

使用相同协议的其他型号通常也能工作。欢迎在 GitHub 上告诉我们您的机型是否可用。

## 添加打印机
- 局域网**自动发现**（SSDP、UDP 广播、定向探测）：检测到的打印机一键添加。
- 否则手动输入（类型、型号、地址、访问密钥）。
- 设置**打印体积**（X、Y、Z）：如果零件太大，Stellio 会在发送前提醒。

## 监控
- 温度、进度、实时摄像头；卡片上显示当前文件的缩略图和名称。
- 自动打印时长计数。
- **悬浮进度小组件**；当“回到顶部”箭头出现时，它会位于箭头左侧。

## 发送到切片软件 / 打印机
- 发送窗口提供**快速预览**（重量、预计时间）、**耗材盘选择**和已记住的校准。
- **打印前检查**：耗材盘需要烘干、磨蚀性耗材（建议使用硬化钢喷嘴）、缺少校准、打印体积、材料是否足够。
- 从历史中**按上次的方式重新打印**。
- **轻量协作模式**：当另一台设备正在查看该文件，或在重复发送前给出提醒。
- 在“我的 G-code”中**在切片软件中打开**。

## 打印过程中
- **智能插座**（Shelly、Tasmota、Home Assistant）：Stellio 读取瓦数，记录实际用电量（kWh）和成本。
- **实际耗材用量**，打印后记录。
- **打印结束照片**在打印达到 **100%** 时拍摄（零件仍在热床上），仅一张，用于评定*成功/失败*。
- **AI 故障监视**（带视觉的 Ollama，100% 本地）：出现意大利面或零件脱落时提醒，**绝不自动停止**。
- 自动**延时摄影**（摄像头 → MP4 视频，需要 ffmpeg）。
- 只读的**状态分享链接**。

## 维护
- **预测性维护**，任务因品牌而异。
- **易损件**（喷嘴、平台、皮带等），带库存提醒，并与维护任务关联。
- 按耗材和打印机保存的**校准**（流量、压力提前、温度）。

@@@ Filament | 耗材
# 耗材

## 库存来源
| 来源 | 说明 |
|---|---|
| **Spoolman** | 在网络中自动检测。Stellio **不再向其写入**消耗量（避免重复扣减）。 |
| **手动** | 手动录入的耗材盘，支持 Excel/CSV 导入。 |
| **TigerTag** | NFC/RFID 识别。使用邮箱和密码登录（只保存加密令牌），或沿用 TigerTag Studio 的会话。**只读。** |
| **OpenPrintTag** | 开放的 NFC 标签标准：导入/导出 `.bin` 文件，通过 Android 应用读写，已消耗重量保持更新。 |
| **Bambu AMS / Creality CFS** | 读取各槽位。 |

**Open Filament Database**：按品牌、材料和颜色搜索耗材盘，一键创建（重量、直径和密度已预填）。

## 日常使用
- 发送到切片软件时**自动扣减用量**，并进行兼容性检查（材料够吗？）。
- 启动时的**低库存提醒**，阈值可调，“待订购”复选框和购买链接。
- **再次购买耗材盘**：优先显示制造商自己的商店（Arianeplast、Bambu Lab、Polymaker、eSUN、Sunlu 等），其次是综合商店；网站允许时会自动检查库存。
- **烘干**：记录、按材料显示状态（干燥 / 需要烘干）、建议温度和时长、提醒。
- **耗材盘详情**：打印次数、克数、成本以及未跟踪的差额。

## 称重与预测
**耗材称重与预测**模块根据每日消耗量估算每个耗材盘的**用尽日期**。
- 剩余重量来自手动称重或 TigerTag。
- TigerTag 的重量**仅用于预测**：只有**即将用完**（14 天或更短）的耗材盘才会显示在这里。其余的在库存中查看。
- 手动称重表单始终可用。

{{img:filament}}

## 消耗预测
当库存不足以打印您的收藏文件时，资料库可以显示**补货提醒**。

@@@ Downloads | 下载
# 下载

可从多个平台将模型直接下载到您的来源中：

| 平台 | 登录方式 |
|---|---|
| **Printables** | GraphQL API |
| **MakerWorld** | Bambu Lab 两步登录 |
| **Thingiverse** | API 密钥 |
| **Nexprint**（Elegoo） | 账户邮箱和密码，加密保存 |
| **Creality Cloud** | 在设置中登录（凭据加密；不支持 Google 登录） |
| **Snapmaker Space** | 同上 |

- **Ctrl+N** 打开新的下载。
- 文件会保存到您选择的来源，并记录**模型来源**（链接、作者、许可证）。
- **新版本**：Stellio 每天检查已下载的模型（Printables、MakerWorld、Thingiverse）是否有更新。
- **我的点赞 / 我的作品**：桌面版每次启动时测试已连接的账户（服务器版每 24 小时一次）。
- **实用链接**：商店、制造商、模型网站和资源，以可折叠的分区呈现。

@@@ AI | 人工智能
# 人工智能

## 本地 AI（Ollama）
默认情况下，AI **100% 在本地**通过 [Ollama](https://ollama.com/) 运行。可以关闭。

功能：
- 模型的**自动打标签**和**描述**；
- 自然语言**语义搜索**；
- **可打印性分析**和**推荐摆放方向**；
- **切片配置推荐**（几何形状 + 成功历史）；
- 切片前的**打印时间估算**；
- **故障监视**（视觉模型）。

Ollama 服务器地址在设置中配置（`ollama_url`）：您可以指向性能更强的远程机器（在树莓派上很有用）。

## 在线 AI（服务器版，可选）
可以用 **Claude**（Anthropic）、**ChatGPT**（OpenAI）或 **Gemini**（Google）代替 Ollama，使用**您自己的 API 密钥**（设置 → 人工智能）。
- 密钥在服务器上加密保存，绝不会回传给浏览器。
- 请求（文件名、标签、描述、S.O.S Print 照片）会发送到您选择的服务商，并按您的密钥计费。
- Ollama 仍是默认选项。

## S.O.S Print
对打印故障进行**自适应**诊断：
1. 您描述问题（每一步都可附照片），也可以提供所用设置（温度、速度、回抽等）。
2. Stellio **每次只问一个问题**（最多 4 个），并实时缩小假设列表。
3. 给出**最终诊断**。

对话会被保存：可重新打开，或标记为已解决。

> ℹ️ 您在历史中评定的“成功 / 失败”结果会改进推荐。

@@@ Costs-and-Management | 成本与管理
# 成本与管理
{{img:management}}


## 打印成本计算
材料、电费、机器损耗（按小时）、固定费用、利润率（%）和数量：单价和总价精确到分。
- **默认利润率**在 *设置 → 打印定价* 中设置一次；历史会在成本旁显示**售价**，而统计仍使用真实成本。
- **项目成本**：对项目内所有文件采用相同的计算。
- **智能插座**：实测功率取代电费估算。
- 您的打印的 **CO₂ 足迹**（材料 + 电力）。

## PDF 报价单
由计算器生成：客户、品名、备注；可配置的抬头（姓名/公司、徽标、地址、电话、邮箱、网站、税号）和页脚的法律声明。每份报价单都会保留（PDF 副本），可在**报价**小组件中查看。

## “管理”界面
勾选*启用成本、报价和开票功能*后可见：
- **客户报价**：**跟踪链接**让客户在线查看、接受或拒绝报价；接受后会创建打印任务并显示您的定金信息。**Stellio 不处理任何付款。**链接始终是外部链接；如果远程访问未开启，界面会提供一键开启。
- **会计**：按月导出 ZIP（单据 CSV、发票 PDF、各月合计）。
- **成品库存**：提醒阈值和补货（手动或自动创建任务）。

## 工坊
- **订单队列**：含真实利润、客户簿、付款、定金发票和贷项通知单、SMTP 邮件、CSV 导出。
- 每个订单的公开**客户跟踪页面**，无需账户：绝不显示价格、利润或内部备注。
- **智能分配**：Stellio 为每个任务推荐最合适的打印机（空闲、已装材料、队列），**绝不会自行开始打印**。
- 通过通知和推送发送的**每日或每周摘要**（任务、延迟、能耗、耗材盘、发票、库存）。
- 向已配对实例**分享切片配置**。

## 报告
- **可靠性**：按配置、材料、打印机或耗材盘统计成功率和失败成本。
- 与上月对比的**月度报告**，可导出为 PDF。
- 可从历史中分享的**打印报告**（PNG 图片）。
- 每个智能插座的实际**能耗**。



{{img:stats}}
@@@ Remote-Access | 远程与移动访问
# 远程与移动访问

## 手机和平板
- 用于手机访问资料库的**二维码**（**可安装的 PWA**）。
- **Android 配套应用**：专用二维码（设置 → 移动访问）可下载 APK。它支持内外网地址自动切换、二维码配对、直接从打印任务拍照，以及读写 OpenPrintTag NFC 标签。
- 适用于平板/手机的全屏**工坊模式**。

## 远程访问
- **Cloudflare Tunnel**（免费，随机或固定地址），或**自定义地址**（域名、DynDNS、VPN、Tailscale 等）以避开 Cloudflare，并可一键切回 Cloudflare。
- 临时**分享链接**（24 小时，一次性使用）。

## 账户
- 带恢复码和密保问题的**本地账户**。
- **会话确认**：使用已保存的会话打开应用时，Stellio 会请您确认账户。
- **只读访客账户**：放心地共享资料库、打印机和库存。
- 在电脑上，通过浏览器访问 Windows 应用被阻止（内部令牌）：请使用应用窗口。

## 多个 Stellio 实例
- 本地网络中的其他安装会被**检测到**，一键添加（输入其本地密钥）。
- 向另一个实例**发送文件**，放入您选择的文件夹。
- 仪表盘上的实例状态小组件。

## 通知
- 原生 **Windows** 通知、**浏览器**通知（树莓派、手机）。
- **推送**：ntfy、Telegram、Discord 或 webhook，即使窗口关闭也能收到（打印完成、失败、维护、库存）。

## 智能家居
- **MQTT / Home Assistant**：状态发布和自动发现；“Stellio” MQTT 设备和传感器。

@@@ Server-Edition | 服务器版
# 服务器版

**服务器版**在 Linux（树莓派、虚拟机、LXC、Docker）上，或设置 `STELLIO_HEADLESS=1` 时启用。Windows 和 macOS 保持桌面应用。Stellio 在后台运行，通过浏览器使用：`http://<ip>:5000`。

## 树莓派 / Linux
要求：推荐树莓派 4 或 5，**64 位**树莓派操作系统。

`install-pi.sh` 会安装系统依赖（`ffmpeg`、`unrar`、3D 渲染库）、专用 Python 环境，以及开机自启、崩溃后自动重启的 `stellio` **systemd 服务**。

```bash
sudo systemctl status stellio
sudo systemctl restart stellio
sudo journalctl -u stellio -f
```
内存不足？如果 Python 依赖安装失败，请增大交换空间，然后重新运行脚本。

## Proxmox VE（LXC 容器）
`stellio-lxc.sh` 脚本提供**默认**或**高级**设置（CTID、核心数、内存、磁盘、网桥、VLAN、DHCP 或静态 IP、存储、要挂载的主机文件夹），然后：
- 创建一个**非特权 Debian 12** 容器（2 核、2 GB 内存、32 GB 磁盘、开机自启）；
- 使用 `install-pi.sh` 在其中安装 Stellio；
- 显示地址 `http://<容器IP>:5000` 和 root 密码。

```bash
pct exec <CTID> -- update-stellio              # 更新
pct exec <CTID> -- journalctl -u stellio -f    # 日志
```
- **非交互模式**：变量 `var_mode=default var_cpu=4 var_ram=4096 var_disk=16 var_ip=192.168.1.50/24 var_gw=192.168.1.1`（完整列表见脚本开头）。
- **存储**：`var_choose_storage=1`、`var_storage`、`var_template_storage`。
- 脚本**语言**：`var_lang=zh`（fr、en、de、es、pt、it、zh、ja）。
- **来源**：在此容器中只提供 **SMB/NFS** 共享。使用 `var_mount=/host:/mnt/models` 时也允许“本地文件夹”。设置位于 `/etc/systemd/system/stellio.service.d/sources.conf`（`STELLIO_ALLOWED_SOURCE_TYPES`）。

## 保护机制（1.0.7）
`install-pi.sh` 会设置：
- **每分钟一次的检查**（`stellio-watchdog`）：Stellio 无响应时重启它（连续 3 次检查失败，启动后有 3 分钟宽限期），已停止时启动它，IP 地址丢失时重启网络，磁盘剩余不足 300 MB 时清理日志和 apt 缓存；
- **永不放弃**重启的服务；
- **CPU 75%**、**内存 75%（减速）/ 85%（硬上限）**的限制、低优先级，内存耗尽时优先牺牲 Stellio；
- 日志限制为 **100 MB**。

检查的干预记录：`journalctl -t stellio-watchdog`。已有容器通过 `update-stellio` 即可获得以上全部内容。

## 服务器版特性
- ☁️ 可选的**在线 AI**（参见 [人工智能](zh-AI)）。
- 📥 **切片配置**：Stellio 看不到您电脑上的切片软件，也不会连接切片软件云（Orca Cloud、Bambu Cloud 等）。请导出您的配置（OrcaSlicer：文件 → 导出 → 导出预设包），然后在 *设置 → 我的切片配置* 中导入，或使用**受监视的配置文件夹**（Syncthing、网络共享、scp 等）。
- 🐯 **TigerTag**：使用邮箱和密码官方登录；使用 Google 账户？请先在 TigerTag 应用中通过“忘记密码”设置密码。备用方案：把 TigerTag Studio 数据文件夹复制到服务器。
- 更新后，浏览器会自动刷新。

## 环境变量
| 变量 | 用途 |
|---|---|
| `STELLIO_HEADLESS` | 强制服务器模式 |
| `STELLIO_PORT` | 端口（默认 5000） |
| `STELLIO_SERVER_URL` | 服务器公开地址 |
| `STELLIO_DATA_DIR` | 数据文件夹 |
| `STELLIO_ALLOWED_SOURCE_TYPES` | 允许的来源类型（`folder,smb,nfs`） |
| `STELLIO_START_MINIMIZED` | 启动时最小化 |
| `STELLIO_NO_AUTO_INSTALL` | 禁用模块自动安装 |

@@@ Settings-and-Data | 设置与数据
# 设置与数据

## 外观
- **主题**：深色 / 浅色 / 跟随系统。默认**浅色**；仅当系统（或您）要求时才使用深色。
- **品牌主题**：Stellio、Bambu、Prusa、Voron、Creality；33 种配色、自定义强调色、可调背景图片。
- **无障碍**：高对比度、减少动画、可见的键盘焦点、文字大小、色盲模式。
- **8 种语言**：fr、en、de、es、it、pt、ja、zh。
- 导航栏可通过拖放重新排序；可**撤销最近一次修改的设置**。

{{img:settings}}

## 键盘快捷键
| 快捷键 | 操作 |
|---|---|
| `Ctrl+K` | 命令面板 |
| `Ctrl+F` | 搜索 |
| `Ctrl+N` | 新建下载 |
| `Ctrl+,` | 设置 |
| `Ctrl+Z` | 撤销上一次删除 |
| `Alt+1-8` | 快速导航 |
| `Shift+点击` | 选择范围 |
| `↑ ↓ ← →` + `Enter` | 浏览并打开 |
| `F` | 收藏 |
| `T` | 标签管理器 |
| `?` | 快捷键帮助 |
| `Esc` | 关闭 / 清除搜索 |

## 我的数据在哪里？
| 系统 | 文件夹 |
|---|---|
| Windows | `%APPDATA%\Stellio` |
| macOS / Linux | `~/.stellio` |
| Windows 便携版 | `Stellio.exe` 旁的 `data` |
| 自定义 | 变量 `STELLIO_DATA_DIR` |

内容：数据库 `stellio.db`（SQLite）、设置 `app_settings.json`、日志 `stellio.log`、已下载的模块 `extra_libs`。代码与数据分开存放，更新绝不会触碰数据。

## 备份
- 数据的**完整导出 / 导入**（.zip）。
- 可计划的**自动备份**。
- 5 分钟**回收站**，带撤销的操作日志。
- 更新绝不会丢失数据。

## 日志与诊断
- 默认日志级别为**警告**；`stellio.log` 文件在每次启动时重新创建。
- **调试模式**：在设置中开启；下次启动时生效。
- **导出诊断**（设置 → 诊断）：隐藏机密信息，列出已添加的打印机（类型、型号、状态——不含名称、地址或密钥）。
- **Stellio 健康**模块：应用的整体状态。

## 建议与错误
在应用中：侧边栏的**建议与错误**。消息会变成 GitHub issue（匿名，通过 GitHub App），并带有“新回复”徽章。

@@@ Troubleshooting | 故障排除
# 故障排除

首先：导出**诊断**（设置 → 诊断），并保留以便反馈问题。

## 启动时屏幕一直空白（macOS）
**5000** 端口常被 *AirPlay 接收器* 占用（Safari 中显示 403）。Stellio 现在会**自动**选择空闲端口（5001–5030）。否则：系统设置 → 通用 → 隔空投送与接力 → 关闭 *AirPlay 接收器*。日志：`~/.stellio/stellio.log`（普通级别下为空：请开启调试模式）。

## LXC 容器无法访问
在 Proxmox 的 shell 中：
1. `pct status <CTID>`，如果已停止则执行 `pct start <CTID>`。
2. `pvesm status`：**存储已满**？当存储为共享时，这是最常见的原因。
3. `pct exec <CTID> -- free -m` 和 `dmesg -T | grep -i "oom\|killed process"`：内存不足。
4. `pct exec <CTID> -- ip -4 a`：DHCP 分配的 IP 是否变了？请在路由器上为其预留。
5. `pct exec <CTID> -- systemctl status stellio` 和 `journalctl -u stellio -n 100`。

自 1.0.7 起，自动监控会处理常见情况；参见 `journalctl -t stellio-watchdog`。

## 缩略图很慢或不显示
- 选择 *设置 → 缩略图性能*：在小型机器上选**节能**。
- 特别大的文件在超时后会保留替代缩略图。
- 您使用应用时生成会暂停：这是正常的。

## 我的打印机未被检测到
- 检查它是否在同一网络中（VLAN、访客 Wi-Fi）。
- 使用 IP 地址和密钥手动添加。
- Bambu Lab：启用局域网模式；Klipper：Moonraker API 必须可访问。

## 缺少打印结束照片
在打印机上勾选*打印结束照片*（与 AI 监视和智能插座一样），并检查摄像头是否有响应。

## “缺少模块”
每个版本首次启动时，Stellio 会下载缺失的模块。请检查网络连接；除非必要，不要设置 `STELLIO_NO_AUTO_INSTALL`。

## Windows SmartScreen / macOS 阻止了应用
安装程序未经签名。请核对 `.sha256`，然后点击 *更多信息 → 仍要运行*（Windows），或右键点击 → *打开*（macOS）。

## 获取帮助
[GitHub Issues](https://github.com/stellio-app/stellio/issues)、[Discord](https://discord.gg/ySxpHvS6bd)，或应用内的**建议与错误**。请注明：Stellio 版本、系统、复现步骤、导出的日志。

@@@ Contributing | 参与贡献
# 参与贡献

欢迎贡献。🎉

1. **Fork** 仓库。
2. 创建分支：`git checkout -b feature/MyFeature`。
3. 提交：`git commit -m "Add MyFeature"`。
4. 推送：`git push origin feature/MyFeature`。
5. 发起 **Pull Request**。

规则：遵循现有风格，用法语或英语注释，尽可能在 Windows 上测试，同步更新文档。每个新增的界面文字都必须添加到**全部 8 个语言文件**。

## 技术栈
| 组件 | 技术 |
|---|---|
| 后端 | Python 3.8+、Flask、Waitress |
| 前端 | HTML5、CSS3、原生 JavaScript（无需构建） |
| 数据库 | SQLite（WAL 模式） |
| 桌面 | pywebview（Windows、macOS）/ 浏览器（服务器） |
| 3D | PyRender、numpy CPU 光栅化、Three.js |
| 网格 | trimesh、pymeshfix、shapely、rectpack |
| AI | Ollama（本地） |
| 网络 | paho-mqtt、smbclient、requests |
| 加密 | cryptography（AES） |

## 仓库结构
```
stellio/
├── main.py            Flask 核心：数据库、认证、资料库、打印机、AI、启动
├── modules/           从 main.py 拆分出的功能（print_session、timelapse、quote_portal 等）
├── interface/         index.html、script.js、style.css、management.js（原生 JavaScript）
├── packaging/         launcher.py、Windows 安装程序（.iss）、macOS 权限
├── languages/         翻译（8 种语言）和 changelog.json
├── tests/  tools/     pytest 测试、维护工具
├── release-notes/     notes_version_X.Y.Z.txt
├── install-pi.sh      树莓派 / Linux 安装
└── stellio-lxc.sh     Proxmox LXC 安装
```
一个模块会声明它使用的 `main.py` 服务（`_REQUIRED`）、自己的路由（`_ROUTES`）以及一个 `init` 函数。发布前检查：`python -m pytest tests -q`。

## 安全与隐私
- Stellio 是**本地优先**的：默认不收集也不发送任何内容。唯一例外（需您主动启用）：服务器版的在线 AI。
- 代码和配置文件无法通过浏览器访问；API 受会话和 CSRF 保护；访客为只读；机密信息已加密。
- 每个版本都附带 `.sha256` 校验值，由内置更新程序验证。

## 许可证
**GNU AGPL v3**：您可以复制、修改和分发 Stellio；如果您修改它或将其作为网络服务提供，必须以相同许可证公开源代码。

## 合作与致谢
Stellio 是 **TigerTag**（[tigersystem.io](https://tigersystem.io)）的官方集成合作伙伴。感谢 Ollama、Flask、Three.js、trimesh、Spoolman 以及创客社区。☕ 支持项目：[Ko-fi](https://ko-fi.com/E6J828RYVD)。
