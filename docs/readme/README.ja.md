<div align="center">

#  <img src="https://stellio-app.com/assets/logo-nom-stellio.png" alt="Stellio Logo" width="200"/>

### メイカーと3Dプリンターユーザーのための究極の3Dファイル管理ツール

[![Version](https://img.shields.io/github/v/release/stellio-app/stellio?color=blue)](https://github.com/stellio-app/stellio/releases)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Raspberry%20Pi%20%2F%20Linux-lightgrey.svg)]()
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)]()

[🇬🇧 English](README.md) | [🇫🇷 Français](docs/readme/README.fr.md) | [🇩🇪 Deutsch](docs/readme/README.de.md) | [🇪🇸 Español](docs/readme/README.es.md) | [🇮🇹 Italiano](docs/readme/README.it.md) | [🇵🇹 Português](docs/readme/README.pt.md) | 🇯🇵 **日本語** | [🇨🇳 中文](docs/readme/README.zh.md)

[🚀 インストール](#-インストール) • [✨ 機能](#-機能) • [📖 ドキュメント](#-ドキュメント) • [🤝 貢献](#-貢献) • [📜 ライセンス](#-ライセンス)

</div>

---

## 🎯 概要

**Stellio** は、3Dライブラリ（STL、3MF、OBJ）を一元管理し、繰り返し作業を自動化し、3Dプリントのワークフローにシームレスに統合されるモダンなデスクトップアプリケーションです。

初心者メイカーでも複数台の機器を扱う熟練プリンターオーナーでも、**ローカルAI**（Ollama）、**スマートなプリンター管理**、そして**生産性を重視したインターフェース**により、Stellioは貴重な時間を節約します。

> 💡 **理念**：あなたのデータは、あなたの手元に。すべてローカルで動作します。

---

## ✨ 機能

### 📚 ライブラリ管理
- 🗂️ **複数のソース**：ローカルフォルダー、単一ファイル、SMB/NFS共有
- 🖼️ PyRender（高品質レンダリング）またはMatplotlib（フォールバック）による**自動3Dサムネイル**
- 🏷️ 色分け可能な**カスタムタグ** + AIによる自動タグ付け
- 🔍 AI支援による**セマンティック検索**（「〜用のサポート材を探している」など）
- ⭐ **お気に入り**と高度なフィルター（種類、サイズ、重量、印刷状態）
- 🧩 **プロジェクト/アセンブリ**：同じオブジェクトの複数ファイルをグループ化
- 📊 詳細な**統計情報**（フォーマット、プラットフォーム、プロファイルの信頼性）

### 🤖 人工知能（ローカルOllama）
- 🏷️ ファイルのスマートな**自動タグ付け**
- 📝 モデルの**自動説明文生成**
- 🔎 自然言語による**セマンティック検索**
- 🎯 ジオメトリと成功履歴に基づく**スライサープロファイルの推奨**
- 🩺 **S.O.S Print**：印刷失敗の診断（写真解析付き）

### 🖨️ プリンター管理
- 🔌 **OctoPrint**、**Klipper/Moonraker**、**Bambu Lab**（MQTT）に対応
- 📡 リアルタイムモニタリング（温度、進捗、カメラ）
- 🔧 ブランド別の推奨事項による**予知保全**（Bambu、Prusa、Crealityなど）
- ⏱️ 印刷時間の自動カウント
- 📤 スライサーへの直接送信、またはプリンターへのアップロード

### 🧵 フィラメント管理
- 🔗 **Spoolman** 連携（スプール管理サーバー）
- 🟠 **Bambu Lab AMS** 対応（スロット読み取り）
- 🟢 **Creality CFS** 対応
- ⚪ 手動スプール登録
- 📉 スライサー送信時の自動消費量トラッキング
- ✅ 互換性チェック（残量は十分か？）

### 📥 プラットフォームからのダウンロード
- 🟠 **Printables**（GraphQL API）
- 🟢 **MakerWorld**（Bambu Labの2段階ログイン）
- 🔵 **Thingiverse**（APIキー経由）
- 📁 設定済みのソースへ直接ダウンロード

### 🧩 高度なツール
- 🎨 プレートの**自動ネスティング**（rectpack、またはshapelyによる実シルエット）
- 🔧 **メッシュ修復**（trimesh + pymeshfix）
- 🔄 **フォーマット変換**（STL ↔ 3MF ↔ OBJ）
- 🛡️ **整合性チェック**（破損・欠落ファイル）
- 💰 **印刷コスト計算**（材料費 + 電気代）
- 📸 印刷結果の**写真ギャラリー**（成功/失敗）
- 🕒 成功/失敗評価付きの**履歴**（AIの学習に活用）
- 🔍 **重複検出**（完全一致およびジオメトリの類似）

### 🌐 リモート・モバイルアクセス
- 📱 モバイルアクセス用の**QRコード**（インストール可能なPWA）
- 🌍 Cloudflare Tunnel経由の**リモートアクセス**（無料、ランダムまたは固定URL）
- 🔗 一時的な**共有リンク**（24時間、一度限り使用）

### 🎨 カスタマイズ
- 🌓 テーマ：ダーク／ライト／システム
- 🎨 ブランドテーマ：Stellio、Bambu、Prusa、Voron、Creality
- 🎯 カスタムアクセントカラー
- 🌍 **8言語対応**：FR、EN、DE、ES、IT、PT、JA、ZH
- 🧲 ドラッグ&ドロップによるナビゲーションの並べ替え

### 💾 バックアップとアップデート
- 📦 完全バックアップのエクスポート/インポート（.zip）
- 🔄 GitHubからの自動アップデート（`.zip`パッチ — WindowsとRaspberry Pi/Linuxで同じ仕組み）
- 📋 診断ログのエクスポート（機密情報はマスク処理）

---

## 🖼️ スクリーンショット

<div align="center">
<table>
<tr></tr>
<td><img src="library.png" alt="ライブラリ" width="400"/><br><em>サムネイル付きライブラリ</em></td>
<td><img src="monitoring.png" alt="プリンター" width="400"/><br><em>プリンターモニタリング</em></td>
</tr>
<tr>
<td><img src="slicer.png" alt="スライサー" width="400"/><br><em>AIによるプロファイル推奨</em></td>
<td><img src="nesting.png" alt="ネスティング" width="400"/><br><em>自動ネスティング</em></td>
</tr>
</table>
</div>

---

## 🚀 インストール

### 🪟 Windows（推奨）

1. [Releases](https://github.com/stellio-app/stellio-app/releases) から最新のインストーラーをダウンロード
2. `Stellio-Setup.exe` を実行
3. これで完了です！🎉

### 🐧 Raspberry Pi / Linux

**ヘッドレスサーバーモード**（GUIなし）で動作します。Stellioはバックグラウンドで動作し、Pi本体またはローカルネットワーク上の任意のデバイスのブラウザから利用します。

**推奨環境**：Raspberry Pi 4または5、**64ビット**版Raspberry Pi OS。

```bash
curl -O https://raw.githubusercontent.com/stellio-app/stellio-app/main/install-pi.sh
chmod +x install-pi.sh
./install-pi.sh
```

このスクリプトは以下を自動でインストールします：
- システム依存関係（`ffmpeg`、`unrar-free`、3Dレンダリング用ライブラリ）
- 専用のPython仮想環境
- 起動時にStellioを自動起動し、クラッシュ時に自動再起動する**systemdサービス**（`stellio.service`）

インストール後は `http://<piのIPアドレス>:5000` でStellioにアクセスできます。

```bash
sudo systemctl status stellio     # サービスの状態確認
sudo systemctl restart stellio    # 再起動
sudo journalctl -u stellio -f     # ログをリアルタイムで確認
```

> 💡 **Windowsと同じ更新方式**：各リリースで公開される`.zip`パッチは両プラットフォームで共通です（純粋なソースコードで、コンパイル済みバイナリはありません）。Stellioが自動で検出・適用し、サービスを再起動します — 手動での再インストールは不要です。

> 🎥 機能はWindows版とほぼ同じですが、ネイティブなデスクトップウィンドウの代わりにブラウザアクセスとなる点、そしてローカルOllama AIはPi上で快適に動作させるためにある程度性能のあるモデルが必要な点が異なります。必要に応じて設定画面で `ollama_url` をリモートのOllamaサーバーに向けてください。

### 対応スライサー

Stellioは以下を自動検出します：
- ✅ OrcaSlicer
- ✅ Bambu Studio
- ✅ PrusaSlicer / SuperSlicer
- ✅ Ultimaker Cura
- ✅ Creality Print

### 対応プリンター

| 種類 | プロトコル | 機能 |
|------|-----------|-----------------|
| OctoPrint | HTTP API | モニタリング、アップロード、カメラ |
| Klipper/Moonraker | HTTP API | モニタリング、アップロード、カメラ、正確な稼働時間 |
| Bambu Lab | MQTT | リアルタイムモニタリング、AMS、カメラ（JPEG A1/P1、RTSPS X1/X2/H2） |

---

## 🛠️ 使用技術

| コンポーネント | 技術 |
|-----------|-------------|
| バックエンド | Python 3.8+、Flask、Waitress |
| フロントエンド | HTML5、CSS3、Vanilla JavaScript |
| データベース | SQLite（WALモード） |
| デスクトップ | pywebview（Windows）／ヘッドレスブラウザモード（Raspberry Pi、Linux） |
| 3Dレンダリング | PyRender、Matplotlib、Three.js |
| メッシュ処理 | trimesh、pymeshfix、shapely |
| AI | Ollama（ローカル） |
| ネットワーク | paho-mqtt、smbclient、requests |
| 暗号化 | cryptography（AES-CFB） |
| アーカイブ | zipfile、rarfile、py7zr、tarfile |

---

## 📖 ドキュメント

### キーボードショートカット

| ショートカット | アクション |
|-----------|--------|
| `Ctrl+F` | 検索 |
| `Ctrl+N` | 新規ダウンロード |
| `Ctrl+,` | 設定 |
| `Alt+1-8` | クイックナビゲーション |
| `F` | お気に入りの切り替え |
| `T` | タグマネージャー |
| `?` | ショートカットヘルプ |
| `Esc` | モーダルを閉じる／検索をクリア |

### プロジェクト構成
```
stellio-app/
├── main.py                 # Flask + デスクトップ バックエンド
├── script.js                # フロントエンドJavaScript
├── index.html                # メインインターフェース
├── style.css                  # スタイル
├── assets/                     # ロゴ、アイコン
├── languages/                   # 翻訳ファイル（JSON）
├── requirements-pi.txt           # Python依存関係（Raspberry Pi / Linuxインストール用）
├── install-pi.sh                  # Raspberry Pi / Linuxインストールスクリプト（systemdサービス）
```

---

アイデアをお持ちですか？ [Issueを開いてください](https://github.com/stellio-app/stellio-app/issues)！

---

## 🤝 貢献

コントリビューションを歓迎します！🎉

1. プロジェクトを**フォーク**する
2. ブランチを作成する（`git checkout -b feature/AmazingFeature`）
3. 変更をコミットする（`git commit -m 'Add AmazingFeature'`）
4. ブランチをプッシュする（`git push origin feature/AmazingFeature`）
5. **プルリクエスト**を開く

### ガイドライン
- 既存のコードスタイルに従ってください
- コメントはフランス語または英語で記述してください
- 可能であればWindows上で変更をテストしてください
- 必要に応じてドキュメントを更新してください

### バグ報告
バグ報告テンプレートを使用し、以下を記載してください：
- Stellioのバージョン
- オペレーティングシステム
- 再現手順
- エラーログ（設定 → 診断からエクスポート可能）

---

## 📜 ライセンス

このプロジェクトはフリーライセンス **GNU Affero General Public License v3.0** の下で公開されています。詳細は [LICENSE](./LICENSE) ファイルをご覧ください。

> 💡 **要約**：本ソフトウェアは自由に複製、改変、配布できます。Stellioを改変したり、ネットワーク経由でホストするサービスとして利用したりする場合は、完全なソースコードを同じAGPLv3ライセンスの下で公開する必要があります。

---

## 🙏 謝辞

- ローカルAIを提供する [Ollama](https://ollama.com/)
- バックエンドを支える [Flask](https://flask.palletsprojects.com/)
- Web上の3Dレンダリングを実現する [Three.js](https://threejs.org/)
- メッシュ処理を担う [trimesh](https://github.com/mikedh/trimesh)
- フィードバックと提案をくださるメイカーコミュニティ
- すべてのコントリビューターの皆様 ❤️

---

## 📞 お問い合わせ・サポート

- 🐛 **バグ報告**：[GitHub Issues](https://github.com/stellio-app/stellio-app/issues)
- 💡 **機能リクエスト**：[GitHub Discussions](https://github.com/stellio-app/stellio-app/discussions)
- 📧 **メール**：contact@stellio-app.com
- 🌐 **ウェブサイト**：[stellio-app.com](https://stellio-app.com)

---

## ⭐ プロジェクトを応援する

Stellioが役立った方は、ぜひ：
- GitHubで**スター** ⭐ をつける
- 周囲にプロジェクトを共有する
- [コードで貢献する](#-貢献)、または翻訳に協力する
- バグを報告してアプリの改善に協力する

---

<div align="center">

**メイカーコミュニティのために ❤️ を込めて作られました**

[⭐ Star this repo](https://github.com/stellio-app/stellio-app) • [🐛 Report a bug](https://github.com/stellio-app/stellio-app/issues) • [💡 Request a feature](https://github.com/stellio-app/stellio-app/discussions)

</div>
