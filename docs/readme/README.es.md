<p align="center">
  <img src="https://stellio-app.com/assets/logo-nom-stellio.png" alt="Logo de Stellio" width="360">
</p>

<h3 align="center">El gestor de archivos 3D definitivo para makers y propietarios de impresoras 3D</h3>

<p align="center">
  <a href="https://github.com/stellio-app/stellio/releases"><img src="https://img.shields.io/github/v/release/stellio-app/stellio?color=blue" alt="Versión"></a>
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
  🇪🇸 <strong>Español</strong> |
  <a href="README.it.md">🇮🇹 Italiano</a> |
  <a href="README.pt.md">🇵🇹 Português</a> |
  <a href="README.ja.md">🇯🇵 日本語</a> |
  <a href="README.zh.md">🇨🇳 中文</a>
</p>

<p align="center">
  <a href="#-descripción-general">🚀 Instalación</a> •
  <a href="#-funcionalidades">✨ Funcionalidades</a> •
  <a href="#-documentación">📖 Documentación</a> •
  <a href="#-contribuir">🤝 Contribuir</a> •
  <a href="#-licencia">📜 Licencia</a>
</p>

---

## 🎯 Descripción general

**Stellio** es una aplicación de escritorio moderna que centraliza toda tu biblioteca 3D (STL, 3MF, OBJ), automatiza tareas repetitivas y se integra perfectamente con tu flujo de trabajo de impresión 3D.

Ya seas un maker principiante o un usuario experimentado con varias máquinas, Stellio te ahorra tiempo valioso gracias a la **IA local** (Ollama), una **gestión inteligente de impresoras** y una **interfaz pensada para la productividad**.

> 💡 **Filosofía**: Tus datos se quedan contigo. Todo funciona en local.

---

## ✨ Funcionalidades

### 📚 Gestión de biblioteca
- 🗂️ **Múltiples fuentes**: carpetas locales, archivos individuales, recursos compartidos SMB/NFS
- 🖼️ **Miniaturas 3D automáticas** vía PyRender (renderizado de alta calidad) o un rasterizador CPU con numpy (alternativa)
- 🏷️ **Etiquetas personalizadas** con colores + etiquetado automático por IA
- 🔍 **Búsqueda semántica asistida por IA** ("busco un soporte para...")
- ⭐ **Favoritos** y filtros avanzados (tipo, tamaño, peso, estado de impresión)
- 🧩 **Proyectos/Ensamblajes**: agrupa varios archivos en un solo objeto, con soporte multi-bandeja 3MF (navegación entre bandejas en el visor)
- 🔁 **Detección de duplicados** (exactos y similares por geometría)
- 📊 **Estadísticas detalladas** (formatos, plataformas, fiabilidad de perfiles)

### 🤖 Inteligencia artificial (Ollama local)
- 🏷️ **Etiquetado automático** inteligente de archivos
- 📝 **Descripción automática** de modelos
- 🔎 **Búsqueda semántica** en lenguaje natural
- 📐 **Análisis de imprimibilidad** (detección de voladizos)
- 🎯 **Recomendación de perfil de slicer** basada en la geometría + historial de éxito
- 🩺 **S.O.S Print**: diagnóstico adaptativo de fallos de impresión, paso a paso — Stellio hace una pregunta a la vez, reduce una lista de hipótesis según tus respuestas (máximo 4 preguntas) y luego ofrece un diagnóstico final; el análisis de fotos está disponible en cualquier momento

### 🖨️ Gestión de impresoras
- 🔌 Compatible con **OctoPrint**, **Klipper/Moonraker**, **Bambu Lab** (MQTT), **Creality** (WebSocket), **FlashForge**
- 📡 **Detección automática en red**: Stellio escanea tu red local (SSDP para Bambu Lab, broadcast UDP para Elegoo/Centauri/FlashForge, sondeo dirigido para Klipper/OctoPrint/PrusaLink/Creality) y te permite añadir las impresoras detectadas con un clic
- 📡 Monitorización en tiempo real (temperaturas, progreso, cámara)
- 🔧 **Mantenimiento predictivo** con seguimiento de tareas y recomendaciones específicas por marca (Bambu, Prusa, Creality, etc.)
- ⏱️ Contador automático de horas de impresión
- 📤 Envío directo al slicer, con un selector de bobina para asignar el filamento correcto desde el propio diálogo de envío, o subida a la impresora

### 🧵 Gestión de filamento
- 🔗 Integración con **Spoolman** (servidor de gestión de bobinas)
- 🏷️ Integración de inventario **TigerTag** (solo lectura)
- 🟠 Compatible con **AMS de Bambu Lab** (lectura de ranuras)
- 🟢 Compatible con **CFS de Creality**
- ⚪ Bobinas manuales
- 📉 Seguimiento automático del consumo al enviar al slicer, con verificación de compatibilidad antes de imprimir (¿queda suficiente material?)
- 🔔 **Alertas de stock bajo** al iniciar, con un enlace rápido para comprar más

### 📥 Descarga desde plataformas
- 🟠 **Printables** (API GraphQL)
- 🟢 **MakerWorld** (inicio de sesión Bambu Lab en 2 pasos)
- 🔵 **Thingiverse** (mediante clave de API)
- 🟣 **Cults3D**
- 📁 Descarga directa a tus fuentes configuradas

### 🧩 Herramientas avanzadas
- 🎨 **Nesting automático** en la bandeja (rectpack o silueta real mediante shapely)
- 🔧 **Reparación de mesh** (trimesh + pymeshfix)
- 🔄 **Conversor de formatos** (STL ↔ 3MF ↔ OBJ)
- 🛡️ **Verificación de integridad** (archivos dañados/faltantes)
- 💰 **Cálculo del coste de impresión** (material + electricidad)
- 📸 **Galería de fotos de impresiones** (exitosas/fallidas)
- 🕒 **Historial** con valoración de éxito/fallo (alimenta la IA)

### 🌐 Acceso móvil y remoto
- 📱 **Código QR** para acceder a tu biblioteca desde el móvil (PWA instalable)
- 📲 **App complementaria Android**: un código QR dedicado permite descargar e instalar el APK de la app complementaria de Stellio directamente desde los ajustes de acceso móvil
- 🌍 **Acceso remoto** mediante Cloudflare Tunnel (gratuito, URL aleatoria o fija)
- 🔗 **Enlaces de compartición** temporales (24 h, un solo uso)

### 🎨 Personalización
- 🌓 Temas: Oscuro / Claro / Sistema
- 🎨 Temas de marca: Stellio, Bambu, Prusa, Voron, Creality
- 🎯 Color de acento personalizado
- 🌍 **8 idiomas**: FR, EN, DE, ES, IT, PT, JA, ZH
- 🧲 Reordenar la navegación arrastrando y soltando

### 💾 Copia de seguridad y actualizaciones
- 📦 Exportación/importación de copia de seguridad completa (.zip)
- 🔄 Actualizaciones automáticas desde GitHub (parche `.zip` — mismo mecanismo en Windows y Raspberry Pi/Linux)
- 📋 Exportación de registros de diagnóstico (secretos ocultos)

---

## 🖼️ Capturas de pantalla

| | |
|---|---|
| ![Biblioteca](../../library.png) *Biblioteca con miniaturas* | ![Impresoras](../../monitoring.png) *Monitorización de impresoras* |
| ![Slicer](../../slicer.png) *Recomendación de perfil por IA* | ![Nesting](../../nesting.png) *Nesting automático* |

---

## 🚀 Instalación

### 🪟 Windows (recomendado)

1. Descarga el último instalador desde [Releases](https://github.com/stellio-app/stellio/releases)
2. Ejecuta `Stellio-Setup.exe`
3. ¡Listo! 🎉

### 🐧 Raspberry Pi / Linux

Funciona en **modo servidor headless** (sin interfaz gráfica): Stellio se ejecuta en segundo plano y se controla desde un navegador, ya sea en la propia Pi o desde cualquier dispositivo de la red local.

**Requisitos**: se recomienda Raspberry Pi 4 o 5, Raspberry Pi OS de **64 bits**.

```bash
curl -O https://raw.githubusercontent.com/stellio-app/stellio/main/install-pi.sh
chmod +x install-pi.sh
./install-pi.sh
```

El script instala automáticamente:
- las dependencias del sistema (`ffmpeg`, `unrar-free`, bibliotecas de renderizado 3D)
- un entorno virtual de Python dedicado
- un **servicio systemd** (`stellio.service`) que inicia Stellio al arrancar y lo reinicia automáticamente si falla

Una vez instalado, Stellio está disponible en `http://<ip-de-la-pi>:5000`.

```bash
sudo systemctl status stellio     # Estado del servicio
sudo systemctl restart stellio    # Reiniciar
sudo journalctl -u stellio -f     # Ver los registros en directo
```

> 💡 **Mismas actualizaciones que en Windows**: el parche `.zip` publicado con cada versión es idéntico en ambas plataformas (código fuente puro, nada compilado). Stellio lo detecta y lo aplica automáticamente, y luego reinicia el servicio — sin necesidad de reinstalación manual.
>
> 🎥 Mismas funcionalidades que la versión de Windows, salvo la ventana de escritorio nativa (sustituida por acceso desde el navegador) y la IA local de Ollama, que necesita un modelo razonablemente potente para funcionar bien en una Pi — apunta `ollama_url` a un servidor Ollama remoto en Ajustes si lo necesitas.

### Slicers compatibles

Stellio detecta automáticamente:
- ✅ OrcaSlicer
- ✅ Bambu Studio
- ✅ PrusaSlicer / SuperSlicer
- ✅ Ultimaker Cura
- ✅ Creality Print

### Impresoras

| Tipo | Protocolo | Funcionalidades |
|---|---|---|
| OctoPrint / PrusaLink | API HTTP | Monitorización, subida, cámara |
| Klipper/Moonraker | API HTTP | Monitorización, subida, cámara, horas exactas |
| Bambu Lab | MQTT (nube + LAN) | Monitorización en tiempo real, AMS, cámara (JPEG A1/P1, RTSPS X1/X2/H2), detección SSDP |
| Creality | WebSocket | Monitorización, CFS, detección UDP |
| FlashForge | API propietaria | Monitorización, detección UDP |
| Elegoo | SDCP sobre WebSocket | Monitorización, detección UDP |

---

## 🛠️ Tecnología

| Componente | Tecnología |
|---|---|
| Backend | Python 3.8+, Flask, Waitress |
| Frontend | HTML5, CSS3, JavaScript nativo |
| Base de datos | SQLite (modo WAL) |
| Escritorio | pywebview (Windows) / modo navegador headless (Raspberry Pi, Linux) |
| Renderizado 3D | PyRender, rasterizador CPU con numpy, Three.js |
| Mesh y nesting | trimesh, pymeshfix, shapely, rectpack |
| IA | Ollama (local) |
| Red | paho-mqtt, smbclient, requests |
| Cifrado | cryptography (AES, IV aleatorio por llamada) |
| Archivos comprimidos | zipfile, rarfile, py7zr, tarfile |

---

## 📖 Documentación

### Atajos de teclado

| Atajo | Acción |
|---|---|
| `Ctrl+F` | Buscar |
| `Ctrl+N` | Nueva descarga |
| `Ctrl+,` | Ajustes |
| `Alt+1-8` | Navegación rápida |
| `F` | Alternar favoritos |
| `T` | Gestor de etiquetas |
| `?` | Ayuda de atajos |
| `Esc` | Cerrar modal / limpiar búsqueda |

### Estructura del proyecto

```
stellio/
├── main.py                 # Backend Flask + Desktop
├── script.js                # JavaScript del frontend
├── index.html                # Interfaz principal
├── style.css                  # Estilos
├── launcher.py                  # Lanzador ligero / arranque del runtime
├── check_deps.py                 # Verificador de dependencias autorreparable
├── worker.py                       # Worker en segundo plano (miniaturas, escaneos)
├── assets/                          # Logos, iconos
├── languages/                        # Archivos de traducción (JSON)
├── apk/                                # Paquete de la app complementaria Android
├── docs/                                # Documentación, política de privacidad, READMEs traducidos
├── requirements.txt                      # Dependencias de Python
├── install-pi.sh                          # Script de instalación para Raspberry Pi / Linux (servicio systemd)
```

¿Tienes una idea? ¡[Abre un issue](https://github.com/stellio-app/stellio/issues)!

---

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! 🎉

1. **Haz un fork** del proyecto
2. Crea tu rama (`git checkout -b feature/MiFuncionalidad`)
3. Confirma tus cambios (`git commit -m 'Añade MiFuncionalidad'`)
4. Sube la rama (`git push origin feature/MiFuncionalidad`)
5. Abre un **Pull Request**

### Recomendaciones
- Sigue el estilo de código existente
- Añade comentarios en francés o inglés
- Prueba tus cambios en Windows si es posible
- Actualiza la documentación si es necesario

### Informar de un error

Usa la plantilla de informe de errores e incluye:
- Versión de Stellio
- Sistema operativo
- Pasos para reproducirlo
- Registros de error (exportables desde Ajustes → Diagnóstico)

---

## 📜 Licencia

Este proyecto está licenciado bajo la **GNU Affero General Public License v3.0** — consulta el archivo [LICENSE](../../LICENSE) para más detalles.

> 💡 **En resumen**: eres libre de copiar, modificar y distribuir este software. Si modificas Stellio o lo usas para ofrecer un servicio en red, debes publicar el código fuente completo bajo la misma licencia AGPLv3.

---

## 🔒 Privacidad

Stellio es local-first: tus datos permanecen en tu equipo, por defecto no se recopila ni se envía nada a servidores externos. Consulta nuestra [Política de privacidad](../privacy/PRIVACY.md) para más detalles.

---

## 🔏 Política de firma de código

Los ejecutables de Windows publicados en [Releases](https://github.com/stellio-app/stellio/releases) están firmados digitalmente. Consulta [CODE_SIGNING_POLICY.md](../../CODE_SIGNING_POLICY.md) para conocer nuestro proceso de firma y las prácticas de protección de la clave privada.

---

## 🙏 Agradecimientos

- [Ollama](https://ollama.com/) por la IA local
- [Flask](https://flask.palletsprojects.com/) por el backend
- [Three.js](https://threejs.org/) por el renderizado 3D web
- [trimesh](https://github.com/mikedh/trimesh) por el procesamiento de mesh
- A la comunidad maker por sus comentarios y sugerencias
- A todos los contribuidores ❤️

---

## 📞 Contacto y soporte

- 🐛 **Informar de un error**: [GitHub Issues](https://github.com/stellio-app/stellio/issues)
- 💡 **Solicitar una funcionalidad**: [GitHub Discussions](https://github.com/stellio-app/stellio/discussions)
- 📧 **Email**: contact@stellio-app.com
- 🌐 **Sitio web**: [stellio-app.com](https://stellio-app.com)

---

## ⭐ Apoya el proyecto

Si Stellio te resulta útil, puedes:
- Darle una **estrella** ⭐ en GitHub
- Compartir el proyecto con tu comunidad
- [Contribuir con código](#-contribuir) o traducciones
- Informar de errores para ayudar a mejorar la app

---

<p align="center"><strong>Hecho con ❤️ para la comunidad maker</strong></p>

<p align="center">
  <a href="https://github.com/stellio-app/stellio">⭐ Da una estrella a este repo</a> •
  <a href="https://github.com/stellio-app/stellio/issues">🐛 Informar de un error</a> •
  <a href="https://github.com/stellio-app/stellio/discussions">💡 Solicitar una funcionalidad</a>
</p>
