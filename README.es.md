<div align="center">

#  <img src="https://stellio-app.com/assets/logo-nom-stellio.png" alt="Stellio Logo" width="200"/>

### El gestor de archivos 3D definitivo para makers e impresores 3D

[![Version](https://img.shields.io/badge/version-0.5.9-blue.svg)](https://github.com/stellio-app/stellio-app/releases)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Raspberry%20Pi%20%2F%20Linux-lightgrey.svg)]()
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)]()

[🇬🇧 English](README.md) | [🇫🇷 Français](README.fr.md) | [🇩🇪 Deutsch](README.de.md) | 🇪🇸 **Español** | [🇮🇹 Italiano](README.it.md) | [🇵🇹 Português](README.pt.md) | [🇯🇵 日本語](README.ja.md) | [🇨🇳 中文](README.zh.md)

[🚀 Instalación](#-instalación) • [✨ Funcionalidades](#-funcionalidades) • [📖 Documentación](#-documentación) • [🤝 Contribuir](#-contribuir) • [📜 Licencia](#-licencia)

</div>

---

## 🎯 Presentación

**Stellio** es una aplicación de escritorio moderna que centraliza toda tu biblioteca 3D (STL, 3MF, OBJ), automatiza tareas repetitivas y se integra perfectamente en tu flujo de trabajo de impresión 3D.

Ya seas un maker principiante o un impresor experimentado con varias máquinas, Stellio te ahorra un tiempo valioso gracias a la **IA local** (Ollama), la **gestión inteligente de impresoras** y una **interfaz pensada para la productividad**.

> 💡 **Filosofía**: Tus datos se quedan contigo. Todo funciona en local.

---

## ✨ Funcionalidades

### 📚 Gestión de biblioteca
- 🗂️ **Múltiples fuentes**: carpetas locales, archivos individuales, recursos compartidos SMB/NFS
- 🖼️ **Miniaturas 3D automáticas** vía PyRender (renderizado de alta calidad) o Matplotlib (respaldo)
- 🏷️ **Etiquetas personalizadas** con colores + auto-etiquetado por IA
- 🔍 **Búsqueda semántica** asistida por IA ("busco un soporte para...")
- ⭐ **Favoritos** y filtros avanzados (tipo, tamaño, peso, estado de impresión)
- 🧩 **Proyectos/Ensamblajes**: agrupa varios archivos para un mismo objeto
- 📊 **Estadísticas** detalladas (formatos, plataformas, fiabilidad de perfiles)

### 🤖 Inteligencia Artificial (Ollama local)
- 🏷️ **Auto-etiquetado** inteligente de archivos
- 📝 **Descripción automática** de modelos
- 🔎 **Búsqueda semántica** en lenguaje natural
- 🎯 **Recomendación de perfil de slicer** basada en la geometría + historial de éxito
- 🩺 **S.O.S Print**: diagnóstico de fallos de impresión (con análisis de fotos)

### 🖨️ Gestión de impresoras
- 🔌 Soporte para **OctoPrint**, **Klipper/Moonraker**, **Bambu Lab** (MQTT)
- 📡 Monitorización en tiempo real (temperaturas, progreso, cámara)
- 🔧 **Mantenimiento predictivo** con recomendaciones por marca (Bambu, Prusa, Creality, etc.)
- ⏱️ Contador automático de horas de impresión
- 📤 Envío directo al slicer o subida a la impresora

### 🧵 Gestión de filamento
- 🔗 Integración con **Spoolman** (servidor de gestión de bobinas)
- 🟠 Soporte para **AMS Bambu Lab** (lectura de slots)
- 🟢 Soporte para **CFS Creality**
- ⚪ Bobinas manuales
- 📉 Descuento automático al enviar al slicer
- ✅ Verificación de compatibilidad (¿cantidad suficiente?)

### 📥 Descarga desde plataformas
- 🟠 **Printables** (API GraphQL)
- 🟢 **MakerWorld** (login en 2 pasos de Bambu Lab)
- 🔵 **Thingiverse** (mediante clave API)
- 📁 Descarga directa a tus fuentes configuradas

### 🧩 Herramientas avanzadas
- 🎨 **Nesting automático** de la plataforma (rectpack o silueta real vía shapely)
- 🔧 **Reparación de malla** (trimesh + pymeshfix)
- 🔄 **Convertidor de formatos** (STL ↔ 3MF ↔ OBJ)
- 🛡️ **Verificación de integridad** (archivos corruptos/faltantes)
- 💰 **Cálculo del coste de impresión** (material + electricidad)
- 📸 **Galería de fotos** de impresión (exitosas/fallidas)
- 🕒 **Historial** con calificación de éxito/fallo (alimenta la IA)
- 🔍 **Detección de duplicados** (exactos y similares por geometría)

### 🌐 Acceso remoto y móvil
- 📱 **Código QR** para acceso móvil (PWA instalable)
- 🌍 **Acceso remoto** vía Cloudflare Tunnel (gratis, URL aleatoria o fija)
- 🔗 **Enlaces para compartir** temporales (24 h, uso único)

### 🎨 Personalización
- 🌓 Temas: Oscuro / Claro / Sistema
- 🎨 Temas de marca: Stellio, Bambu, Prusa, Voron, Creality
- 🎯 Color de acento personalizado
- 🌍 **8 idiomas**: FR, EN, DE, ES, IT, PT, JA, ZH
- 🧲 Reordenación de la navegación mediante arrastrar y soltar

### 💾 Copias de seguridad y actualizaciones
- 📦 Exportación/Importación de copia de seguridad completa (.zip)
- 🔄 Actualizaciones automáticas desde GitHub (parche `.zip` — mismo mecanismo en Windows y Raspberry Pi/Linux)
- 📋 Exportación de registros de diagnóstico (secretos ocultos)

---

## 🖼️ Capturas de pantalla

<div align="center">
<table>
<tr></tr>
<td><img src="library.png" alt="Biblioteca" width="400"/><br><em>Biblioteca con miniaturas</em></td>
<td><img src="monitoring.png" alt="Impresoras" width="400"/><br><em>Monitorización de impresoras</em></td>
</tr>
<tr>
<td><img src="slicer.png" alt="Slicer" width="400"/><br><em>Recomendación de perfil por IA</em></td>
<td><img src="nesting.png" alt="Nesting" width="400"/><br><em>Nesting automático</em></td>
</tr>
</table>
</div>

---

## 🚀 Instalación

### 🪟 Windows (recomendado)

1. Descarga el último instalador desde [Releases](https://github.com/stellio-app/stellio-app/releases)
2. Ejecuta `Stellio-Setup.exe`
3. ¡Eso es todo! 🎉

### 🐧 Raspberry Pi / Linux

Funciona en **modo servidor headless** (sin interfaz gráfica): Stellio se ejecuta en segundo plano y se usa desde un navegador, ya sea en la propia Pi o desde cualquier dispositivo de la red local.

**Requisitos**: se recomienda Raspberry Pi 4 o 5, Raspberry Pi OS de **64 bits**.

```bash
curl -O https://raw.githubusercontent.com/stellio-app/stellio-app/main/install-pi.sh
chmod +x install-pi.sh
./install-pi.sh
```

El script instala automáticamente:
- las dependencias del sistema (`ffmpeg`, `unrar-free`, librerías de renderizado 3D)
- un entorno virtual de Python dedicado
- un **servicio systemd** (`stellio.service`) que inicia Stellio al arrancar y lo reinicia automáticamente en caso de fallo

Una vez instalado, Stellio es accesible en `http://<ip-de-la-pi>:5000`.

```bash
sudo systemctl status stellio     # Estado del servicio
sudo systemctl restart stellio    # Reiniciar
sudo journalctl -u stellio -f     # Ver los logs en directo
```

> 💡 **Mismas actualizaciones que en Windows**: el parche `.zip` publicado en cada versión es idéntico en ambas plataformas (código fuente puro, nada compilado). Stellio lo detecta y lo aplica automáticamente, y luego reinicia el servicio — no hace falta reinstalar manualmente.

> 🎥 Funcionalidades idénticas a la versión de Windows, salvo la ventana de escritorio nativa (sustituida por el acceso vía navegador) y la IA local Ollama, que necesita un modelo razonablemente capaz para funcionar bien en una Pi — apunta `ollama_url` a un servidor Ollama remoto en los Ajustes si es necesario.

### Slicers compatibles

Stellio detecta automáticamente:
- ✅ OrcaSlicer
- ✅ Bambu Studio
- ✅ PrusaSlicer / SuperSlicer
- ✅ Ultimaker Cura
- ✅ Creality Print

### Impresoras

| Tipo | Protocolo | Funcionalidades |
|------|-----------|-----------------|
| OctoPrint | API HTTP | Monitorización, subida, cámara |
| Klipper/Moonraker | API HTTP | Monitorización, subida, cámara, horas exactas |
| Bambu Lab | MQTT | Monitorización en tiempo real, AMS, cámara (JPEG A1/P1, RTSPS X1/X2/H2) |

---

## 🛠️ Tecnologías

| Componente | Tecnología |
|-----------|-------------|
| Backend | Python 3.8+, Flask, Waitress |
| Frontend | HTML5, CSS3, JavaScript vanilla |
| Base de datos | SQLite (modo WAL) |
| Escritorio | pywebview (Windows) / modo headless por navegador (Raspberry Pi, Linux) |
| Renderizado 3D | PyRender, Matplotlib, Three.js |
| Malla | trimesh, pymeshfix, shapely |
| IA | Ollama (local) |
| Red | paho-mqtt, smbclient, requests |
| Cifrado | cryptography (AES-CFB) |
| Archivos comprimidos | zipfile, rarfile, py7zr, tarfile |

---

## 📖 Documentación

### Atajos de teclado

| Atajo | Acción |
|-----------|--------|
| `Ctrl+F` | Buscar |
| `Ctrl+N` | Nueva descarga |
| `Ctrl+,` | Ajustes |
| `Alt+1-8` | Navegación rápida |
| `F` | Alternar favoritos |
| `T` | Gestor de etiquetas |
| `?` | Ayuda de atajos |
| `Esc` | Cerrar modal / vaciar búsqueda |

### Estructura del proyecto
```
stellio-app/
├── main.py                 # Backend Flask + Escritorio
├── script.js                # JavaScript del frontend
├── index.html                # Interfaz principal
├── style.css                  # Estilos
├── assets/                     # Logos, iconos
├── languages/                   # Archivos de traducción (JSON)
├── requirements-pi.txt           # Dependencias de Python (instalación en Raspberry Pi / Linux)
├── install-pi.sh                  # Script de instalación para Raspberry Pi / Linux (servicio systemd)
```

---

¿Tienes una idea? [Abre un issue](https://github.com/stellio-app/stellio-app/issues)!

---

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! 🎉

1. Haz un **fork** del proyecto
2. Crea tu rama (`git checkout -b feature/AmazingFeature`)
3. Confirma tus cambios (`git commit -m 'Add AmazingFeature'`)
4. Sube la rama (`git push origin feature/AmazingFeature`)
5. Abre un **Pull Request**

### Directrices
- Respeta el estilo de código existente
- Añade comentarios en francés o inglés
- Prueba tus cambios en Windows si es posible
- Actualiza la documentación si es necesario

### Reportar un error
Usa la plantilla de reporte de errores e incluye:
- Versión de Stellio
- Sistema operativo
- Pasos para reproducirlo
- Registros de error (exportables desde Ajustes → Diagnóstico)

---

## 📜 Licencia

Este proyecto está bajo la licencia libre **GNU Affero General Public License v3.0**; consulta el archivo [LICENSE](./LICENSE) para más detalles.

> 💡 **En resumen**: Eres libre de copiar, modificar y distribuir este software. Si modificas Stellio o lo usas para ofrecer un servicio alojado en red, debes publicar el código fuente completo bajo la misma licencia AGPLv3.

---

## 🙏 Agradecimientos

- [Ollama](https://ollama.com/) por la IA local
- [Flask](https://flask.palletsprojects.com/) por el backend
- [Three.js](https://threejs.org/) por el renderizado 3D web
- [trimesh](https://github.com/mikedh/trimesh) por el procesamiento de mallas
- La comunidad maker por sus comentarios y sugerencias
- Todos los contribuidores ❤️

---

## 📞 Contacto y soporte

- 🐛 **Reporte de errores**: [GitHub Issues](https://github.com/stellio-app/stellio-app/issues)
- 💡 **Solicitud de funcionalidad**: [GitHub Discussions](https://github.com/stellio-app/stellio-app/discussions)
- 📧 **Email**: contact@stellio-app.com
- 🌐 **Sitio web**: [stellio-app.com](https://stellio-app.com)

---

## ⭐ Apoya el proyecto

Si Stellio te resulta útil, considera:
- Darle una **estrella** ⭐ en GitHub
- Compartir el proyecto con otros
- [Contribuir con código](#-contribuir) o traducciones
- Reportar errores para mejorar la aplicación

---

<div align="center">

**Hecho con ❤️ para la comunidad maker**

[⭐ Star this repo](https://github.com/stellio-app/stellio-app) • [🐛 Report a bug](https://github.com/stellio-app/stellio-app/issues) • [💡 Request a feature](https://github.com/stellio-app/stellio-app/discussions)

</div>
