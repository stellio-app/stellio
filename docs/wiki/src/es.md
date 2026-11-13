@@@ Home | Inicio
# Wiki de Stellio
{{img:dashboard}}


**Stellio** es el gestor de archivos 3D para makers y propietarios de impresoras 3D. Centraliza su biblioteca (STL, 3MF, OBJ, STEP, PLY, AMF), automatiza las tareas repetitivas y se integra en su flujo de impresión.

> 🔒 **Filosofía**: sus datos se quedan con usted. Todo funciona en local; por defecto, nada sale de su equipo.

## ¿Por dónde empezar?

| Quiero… | Página |
|---|---|
| Instalar Stellio | [Instalación](es-Installation) |
| Dar mis primeros pasos | [Primeros pasos](es-Getting-Started) |
| Gestionar mis archivos 3D | [Biblioteca](es-Library) |
| Conectar mis impresoras | [Impresoras](es-Printers) |
| Seguir mis bobinas | [Filamento](es-Filament) |
| Descargar modelos | [Descargas](es-Downloads) |
| Usar la IA y S.O.S Print | [Inteligencia artificial](es-AI) |
| Calcular costes, presupuestos, facturas | [Costes y gestión](es-Costs-and-Management) |
| Acceder desde el móvil | [Acceso remoto y móvil](es-Remote-Access) |
| Instalar en Raspberry Pi / Proxmox | [Edición servidor](es-Server-Edition) |
| Configurar, respaldar, entender mis datos | [Ajustes y datos](es-Settings-and-Data) |
| Resolver un problema | [Solución de problemas](es-Troubleshooting) |
| Contribuir al proyecto | [Contribuir](es-Contributing) |

## Enlaces útiles

- 🌐 Sitio: [stellio-app.com](https://stellio-app.com) — ▶ [demo en línea (solo lectura)](https://demo.stellio-app.com)
- 📦 [Descargas (Releases)](https://github.com/stellio-app/stellio/releases)
- 🐛 [Informar de un error](https://github.com/stellio-app/stellio/issues) · 💡 [Proponer una idea](https://github.com/stellio-app/stellio/discussions) · 💬 [Discord](https://discord.gg/ySxpHvS6bd)
- 📜 Licencia **AGPL v3**

@@@ Installation | Instalación
# Instalación

| Plataforma | Archivo / método | Modo |
|---|---|---|
| 🪟 Windows | `Stellio-Setup-<version>.exe` | Aplicación de escritorio |
| 🪟 Windows portátil | `Stellio-v<version>-portable-win64.zip` | Aplicación de escritorio, sin instalación |
| 🍎 macOS | `.dmg` (Apple Silicon `arm64` o Intel `x86_64`) | Aplicación de escritorio |
| 🐧 Linux | `Stellio-v<version>-x86_64.AppImage` | Aplicación de escritorio |
| 🍓 Raspberry Pi / Linux | `install-pi.sh` | Servidor (navegador) |
| 🖥️ Proxmox VE | `stellio-lxc.sh` | Contenedor LXC con un solo comando |
| 📲 Android | APK complementario | Ver [Acceso remoto y móvil](es-Remote-Access) |

Todos los archivos están en la página [Releases](https://github.com/stellio-app/stellio/releases), cada uno con una suma de verificación `.sha256`.

## Windows

1. Descargue el instalador desde las Releases.
2. Ejecute `Stellio-Setup-<version>.exe`.
3. Listo.

**Versión portátil**: descomprima en cualquier lugar (disco, memoria USB) y ejecute `Stellio.exe`. Sus datos permanecen en la carpeta `data` junto al ejecutable (conserve el archivo `portable.flag`).

> ⚠️ El instalador **no está firmado**: Windows SmartScreen puede mostrar una advertencia. Compruebe el `.sha256` si lo desea; la actualización integrada lo verifica antes de instalar.

## macOS

Abra el `.dmg` y arrastre Stellio a Aplicaciones. Elija el archivo adecuado para su Mac: `arm64` (M1, M2, M3…) o `x86_64` (Intel). Las compilaciones no están notarizadas: en el primer inicio, clic derecho → **Abrir**.

> Si la pantalla queda en blanco: el puerto 5000 puede estar ocupado por el «Receptor AirPlay» de macOS. Stellio elige entonces automáticamente otro puerto libre. Ver [Solución de problemas](es-Troubleshooting).

## Linux (AppImage)

```bash
chmod +x Stellio-v*-x86_64.AppImage
./Stellio-v*-x86_64.AppImage
```
El AppImage incluye su información de actualización (`.zsync`).

## Raspberry Pi / servidor Linux

Modo **servidor sin interfaz**: Stellio funciona en segundo plano y se usa desde un navegador. Más detalles en [Edición servidor](es-Server-Edition).

```bash
curl -O https://raw.githubusercontent.com/stellio-app/stellio/main/install-pi.sh
chmod +x install-pi.sh
./install-pi.sh
```

## Proxmox VE

En el **Shell del host Proxmox**:
```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/stellio-app/stellio/main/stellio-lxc.sh)"
```
Detalles en [Edición servidor](es-Server-Edition).

## Actualizaciones

- **Escritorio**: Stellio detecta las nuevas versiones en GitHub y aplica un parche `.zip` (mismo mecanismo en Windows, macOS y Linux). El widget «Actualización» del panel abre la ventana de actualización.
- **Servidor**: la misma actualización automática, o `update-stellio` (contenedor LXC) / `./install-pi.sh` (Raspberry Pi).
- En el primer inicio de cada versión, los módulos que falten (presupuestos PDF, importación de hojas de cálculo, notificaciones…) se descargan automáticamente.

@@@ Getting-Started | Primeros pasos
# Primeros pasos
{{img:library}}


## 1. Primer inicio
Stellio muestra un **recorrido guiado** y una lista «Primeros pasos». Puede reiniciar el recorrido en cualquier momento desde los Ajustes.

## 2. Crear su cuenta
Las cuentas son **locales**: contraseña + código de recuperación + pregunta secreta. El restablecimiento de la contraseña es 100 % local, sin correo ni internet.

## 3. Añadir sus fuentes
Una **fuente** es una carpeta o un recurso compartido que contiene sus modelos:
- carpeta local, archivo suelto, recurso **SMB** o **NFS**;
- las carpetas 3D detectadas en su equipo se le **sugieren** y se añaden con un clic;
- para cada fuente, usted elige los tipos de archivo que se muestran.

Stellio analiza entonces sus archivos y genera las miniaturas 3D en segundo plano.

## 4. Añadir una impresora (opcional)
Abra la página **Impresoras**: el descubrimiento de red propone las máquinas detectadas. Ver [Impresoras](es-Printers).

## 5. Elegir su slicer
Stellio detecta automáticamente los slicers instalados (OrcaSlicer, Bambu Studio, PrusaSlicer, Cura…). El botón de envío abre el archivo directamente en el slicer.

## Panel de control
La página de inicio reúne impresiones en curso, stock bajo, impresiones recientes y archivos recientes. Los **widgets** (una veintena) se reordenan arrastrando y soltando y pueden ocultarse: impresiones en curso, stock bajo, últimos S.O.S Print, sugerencias, instancias de Stellio, proyectos terminados, galería, presupuestos…

## Herramientas del día a día
- **Paleta de comandos** `Ctrl+K`: navegar, ejecutar una acción, encontrar un archivo, una etiqueta, una bobina o un perfil.
- **Centro de notificaciones** (campana): fin de impresión, fallo, mantenimiento, stock bajo, secado de bobinas.
- **Widget flotante** con el progreso de la impresión en curso, visible en todas las páginas.
- **Atajos de teclado**: ver [Ajustes y datos](es-Settings-and-Data).

@@@ Library | Biblioteca
# Biblioteca
{{img:library}}


## Fuentes y miniaturas
- Varias fuentes: carpetas locales, archivos, recursos SMB/NFS.
- **Miniaturas 3D automáticas** (PyRender, o un renderizador por CPU de respaldo) con vista ampliada al pasar el ratón.
- La generación **se pausa en cuanto usa la aplicación** y se reanuda después.
- Ajuste **Rendimiento de las miniaturas**: Automático / Eco / Normal / Rápido.
- Formatos: STL, 3MF (incluidos multiplaca y PrusaSlicer), OBJ, STEP/STP, PLY, AMF (convertidos a STL para los slicers que no los leen) y archivos comprimidos (ZIP, RAR, 7z, TAR) que se pueden explorar directamente.

## Organizar
- **Etiquetas** de colores, con etiquetado automático por IA; etiquetar varios archivos con un clic.
- **Favoritos**, filtros avanzados (tipo, tamaño, peso, estado de impresión), **filtros guardados**.
- Filtros de estado: «Enviado al slicer», «Ya impreso», «Ya conseguido», «Ya fallido».
- **Filtro «Stock de filamento»**: conserva solo los archivos imprimibles con las bobinas que tiene.
- El orden, la búsqueda y los filtros se **recuerdan** al reabrir la aplicación.
- Cola **«Imprimir pronto»**, reordenable y enviable al slicer.
- **Renombrado masivo** (buscar/reemplazar, prefijo, sufijo, numeración) con vista previa.
- **Deshacer eliminaciones** (`Ctrl+Z`) gracias a una papelera temporal de 5 minutos; vale también para etiquetas, proyectos y fuentes.
- Selección rápida: `Mayús+clic` para un rango, flechas + `Intro`.
- **Detección de duplicados** (exactos y de geometría similar).
- **Origen del modelo**: enlace de origen, autor, licencia, notas, fecha de descarga.
- **Arrastrar y soltar** archivos 3D desde el explorador, también a través del navegador.

## Búsqueda
- Búsqueda clásica y **búsqueda semántica por IA** («busco un soporte para…»), con las búsquedas recientes recordadas.
- **Colecciones inteligentes**.

## Proyectos / ensamblajes
Agrupe varios archivos para un mismo objeto.
- 3MF **multiplaca**: al añadirlo a un proyecto se divide en un 3MF por placa (6 placas = 6 archivos), guardados en una carpeta oculta.
- Acción **«Dividir placas»** en el menú ⋯ de un archivo.
- Tarjeta de proyecto: clic en la miniatura = visor 3D; el filtro «Todos / En curso / Terminados» se recuerda; **Coste del proyecto** con un botón.

{{img:projects}}

## Visor 3D y herramientas
- **Visor 3D** (Three.js, funciona sin conexión), navegación entre placas.
- **Colocación automática** en la cama (rectpack, o silueta real con shapely).
- **Reparación de malla** (trimesh + pymeshfix) con comparación antes/después.
- **Conversor** STL ↔ 3MF ↔ OBJ.
- **Análisis de imprimibilidad** (voladizos) y **orientaciones sugeridas**.
- **Comprobación de integridad** (archivos dañados o ausentes).
- **Estadísticas** detalladas (formatos, plataformas, fiabilidad de los perfiles).

{{img:viewer}}

## Historial y fotos
- **Historial** paginado por semanas, con valoración conseguido/fallido (que alimenta la IA), botones **Ver archivo** y **Reimprimir**, filtros por plataforma, resultado y fechas.
- **Galería de fotos** de impresión. La foto de fin de impresión se marca después como *Conseguido* o *Fallido* con un clic.
- **Mis G-codes**: G-codes vinculados a un archivo, descarga y botón **Abrir en el slicer**.
- **Copia de seguridad** de la biblioteca: ver [Ajustes y datos](es-Settings-and-Data).

@@@ Printers | Impresoras
# Impresoras
{{img:printers}}


## Marcas compatibles

| Marca | Modelos | Conexión |
|---|---|---|
| **Bambu Lab** | X1/X1C/X1E, X2D, P1P/P1S, P2S, A1/A1 mini, H2D/H2S/H2C | MQTT (LAN + nube): seguimiento, AMS, cámara, descubrimiento SSDP |
| **Prusa** | MK4, MK3.9, MK3.5, MINI+, XL, CORE One | PrusaLink (HTTP) |
| **Creality** | Series K1/K2, Ender-3 V3, Hi | WebSocket: seguimiento, CFS, descubrimiento UDP |
| **Elegoo** | Centauri Carbon 1 y 2, series de resina Saturn/Mars | SDCP (WebSocket) |
| **FlashForge** | Adventurer 5M/5M Pro, AD5X | API propietaria |
| **Klipper / Moonraker** | Cualquier máquina Klipper (Voron…) | HTTP: seguimiento, envío, cámara, horas exactas |
| **OctoPrint** | Cualquier impresora controlada por OctoPrint | HTTP |

Los demás modelos que hablan el mismo protocolo suelen funcionar. Cuéntenos en GitHub si el suyo funciona.

## Añadir una impresora
- **Descubrimiento automático** de la red local (SSDP, difusión UDP, sondeos dirigidos): las impresoras detectadas se añaden con un clic.
- Si no, entrada manual (tipo, modelo, dirección, clave de acceso).
- Indique el **volumen de impresión** (X, Y, Z): Stellio avisa antes del envío si la pieza es demasiado grande.

## Seguimiento
- Temperatura, progreso, cámara en directo; miniatura y nombre del archivo en curso en la tarjeta.
- Contador automático de horas de impresión.
- **Widget flotante** de progreso; se coloca a la izquierda de la flecha «subir» cuando esta aparece.

## Enviar al slicer / a la impresora
- Ventana de envío con **vista rápida** (peso, tiempo estimado), **selección de bobina** y calibraciones recordadas.
- **Comprobación previa a la impresión**: bobina que necesita secado, filamento abrasivo (se aconseja boquilla de acero endurecido), falta de calibración, volumen de impresión, material suficiente.
- **Reimprimir como la última vez** desde el historial.
- **Modo colaborativo ligero**: avisa si otro dispositivo está viendo el archivo o antes de un doble envío.
- **Abrir en el slicer** desde «Mis G-codes».

## Durante la impresión
- **Enchufe inteligente** (Shelly, Tasmota, Home Assistant): Stellio lee los vatios y registra el consumo real (kWh) y el coste.
- **Consumo real de filamento**, registrado tras la impresión.
- **Foto de fin de impresión** tomada al llegar al **100 %** (la pieza sigue en la cama), una sola foto para valorar *Conseguido/Fallido*.
- **Vigilancia de fallos por IA** (Ollama con visión, 100 % local): alerta ante espagueti o pieza despegada, **nunca una parada automática**.
- **Timelapse** automático (cámara → vídeo MP4, requiere ffmpeg).
- **Enlaces para compartir el estado**, de solo lectura.

## Mantenimiento
- **Mantenimiento predictivo** con tareas propias de cada marca.
- **Piezas de desgaste** (boquillas, placas, correas…) con alertas de stock, vinculadas a las tareas de mantenimiento.
- **Calibraciones** (flujo, pressure advance, temperaturas) por filamento e impresora.

@@@ Filament | Filamento
# Filamento

## Fuentes de inventario
| Fuente | Detalles |
|---|---|
| **Spoolman** | Detección automática en la red. Stellio **ya no le escribe** el consumo (evita el doble recuento). |
| **Manual** | Bobinas introducidas a mano, importación Excel/CSV. |
| **TigerTag** | Identificación NFC/RFID. Inicio de sesión con correo y contraseña (solo se guarda un token cifrado) o reutilización de una sesión de TigerTag Studio. **Solo lectura.** |
| **OpenPrintTag** | Estándar abierto de etiquetas NFC: importación/exportación de archivos `.bin`, lectura/escritura desde la app Android, peso consumido siempre actualizado. |
| **Bambu AMS / Creality CFS** | Lectura de los slots. |

**Open Filament Database**: busque una bobina por marca, material y color y créela con un clic (peso, diámetro y densidad rellenados).

## Día a día
- **Consumo automático** al enviar al slicer, con comprobación de compatibilidad (¿queda material suficiente?).
- **Alertas de stock bajo** al iniciar, umbral ajustable, casilla «Por pedir» y enlace de compra.
- **Volver a comprar una bobina**: primero la tienda del fabricante (Arianeplast, Bambu Lab, Polymaker, eSUN, Sunlu…), luego tiendas generales; el stock se comprueba automáticamente cuando el sitio lo permite.
- **Secado**: registro, estado (seca / necesita secado) según el material, temperatura y duración sugeridas, recordatorios.
- **Ficha de bobina**: impresiones, gramos, coste y diferencia sin seguimiento.

## Pesaje y previsión
El bloque **Pesaje y previsión de filamento** estima la **fecha de agotamiento** de cada bobina según su consumo diario.
- El peso restante procede de un pesaje manual o de TigerTag.
- Los pesos de TigerTag alimentan **solo la previsión**: aquí solo aparecen para una bobina **a punto de agotarse** (14 días o menos). El resto está en el inventario.
- Un formulario de pesaje manual siempre está disponible.

{{img:filament}}

## Previsión de consumo
La biblioteca puede mostrar un **aviso de reposición** cuando el stock no basta para sus favoritos.

@@@ Downloads | Descargas
# Descargas

Descargue modelos directamente en sus fuentes desde varias plataformas:

| Plataforma | Inicio de sesión |
|---|---|
| **Printables** | API GraphQL |
| **MakerWorld** | Inicio de sesión Bambu Lab en 2 pasos |
| **Thingiverse** | Clave de API |
| **Nexprint** (Elegoo) | Correo y contraseña de la cuenta, guardados cifrados |
| **Creality Cloud** | Desde los Ajustes (credenciales cifradas; no se admite el inicio de sesión con Google) |
| **Snapmaker Space** | Igual |

- **Ctrl+N** abre una nueva descarga.
- El archivo llega a la fuente que elija y se guarda el **origen del modelo** (enlace, autor, licencia).
- **Nueva versión**: cada día, Stellio comprueba si los modelos descargados (Printables, MakerWorld, Thingiverse) se han actualizado.
- **Mis likes / Mis creaciones**: las cuentas conectadas se prueban en cada inicio del escritorio (cada 24 h en servidor).
- **Enlaces útiles**: tiendas, fabricantes, sitios de modelos y recursos, en secciones plegables.

@@@ AI | Inteligencia artificial
# Inteligencia artificial

## IA local (Ollama)
Por defecto, la IA funciona **100 % en local** con [Ollama](https://ollama.com/). Se puede desactivar.

Funciones:
- **Etiquetado automático** y **descripción** de los modelos;
- **Búsqueda semántica** en lenguaje natural;
- **Análisis de imprimibilidad** y **orientaciones sugeridas**;
- **Recomendación de perfil de slicer** (geometría + historial de éxitos);
- **Estimación del tiempo de impresión** antes de laminar;
- **Vigilancia de fallos** (modelo de visión).

La dirección del servidor Ollama se define en los Ajustes (`ollama_url`): puede apuntar a una máquina remota más potente (útil en una Raspberry Pi).

## IA en línea (edición servidor, opcional)
En lugar de Ollama, use **Claude** (Anthropic), **ChatGPT** (OpenAI) o **Gemini** (Google) con **su propia clave de API** (Ajustes → Inteligencia artificial).
- La clave se cifra en el servidor y nunca se devuelve al navegador.
- Las peticiones (nombres de archivo, etiquetas, descripciones, fotos de S.O.S Print) van al proveedor elegido y se facturan con su clave.
- Ollama sigue siendo la opción por defecto.

## S.O.S Print
Diagnóstico **adaptativo** de un fallo de impresión:
1. Usted describe el problema (foto posible en cada paso) y, si quiere, los ajustes usados (temperaturas, velocidades, retracción…).
2. Stellio hace **una pregunta cada vez** (4 como máximo) y reduce en directo una lista de hipótesis.
3. Entrega un **diagnóstico final**.

Las conversaciones se guardan: vuelva a abrirlas o márquelas como resueltas.

> ℹ️ Los resultados «Conseguido / Fallido» que valora en el historial mejoran las recomendaciones.

@@@ Costs-and-Management | Costes y gestión
# Costes y gestión
{{img:management}}


## Cálculo del coste de impresión
Material, electricidad, desgaste de la máquina (por hora), gastos fijos, margen en % y cantidad: precio unitario y total al céntimo.
- El **margen por defecto** se fija una vez en *Ajustes → Tarifas de impresión*; el historial muestra el **precio de venta** junto al coste, mientras que las estadísticas conservan el coste real.
- **Coste del proyecto**: el mismo cálculo para todos los archivos de un proyecto.
- **Enchufe inteligente**: la potencia medida sustituye la estimación de electricidad.
- **Huella de CO₂** de sus impresiones (material + electricidad).

## Presupuestos PDF
Generados desde la calculadora: cliente, designación, notas; cabecera configurable (nombre/empresa, logotipo, dirección, teléfono, correo, web, NIF) y avisos legales al pie. Cada presupuesto se conserva (copia PDF) y se puede consultar en el widget **Presupuestos**.

## Pantalla «Gestión»
Visible cuando está marcada la opción *Activar las funciones de costes, presupuestos y facturación*:
- **Presupuestos de clientes**: un **enlace de seguimiento** permite al cliente ver, aceptar o rechazar el presupuesto en línea; la aceptación crea la tarea de impresión y muestra sus datos de anticipo. **Stellio no procesa ningún pago.** Los enlaces son siempre externos; si el acceso remoto está desactivado, la pantalla propone activarlo con un clic.
- **Contabilidad**: exportación mensual ZIP (CSV de documentos, PDF de facturas, totales por mes).
- **Stock de piezas terminadas**: umbral de alerta y reposición (tarea creada a mano o automáticamente).

## Taller
- **Cola de pedidos** con margen real, agenda de clientes, pagos, facturas de anticipo y abonos, correo SMTP, exportación CSV.
- **Página pública de seguimiento** por pedido, sin cuenta: nunca muestra precios, margen ni notas internas.
- **Reparto inteligente**: Stellio propone la impresora más adecuada para cada tarea (libre, material cargado, cola) **sin lanzar nunca una impresión**.
- **Resumen diario o semanal** por notificación y push (tareas, retrasos, energía, bobinas, facturas, stock).
- **Compartir perfiles de slicer** con una instancia emparejada.

## Informes
- **Fiabilidad**: tasa de éxito y coste de los fallos por perfil, material, impresora o bobina.
- **Informe mensual** comparado con el mes anterior, exportable en PDF.
- **Informe de impresión** compartible (imagen PNG) desde el historial.
- **Energía** real por enchufe inteligente.



{{img:stats}}
@@@ Remote-Access | Acceso remoto y móvil
# Acceso remoto y móvil

## Móvil y tableta
- **Código QR** de acceso móvil a la biblioteca (**PWA instalable**).
- **App Android complementaria**: un código QR específico (Ajustes → acceso móvil) descarga el APK. Gestiona direcciones interna y externa con cambio automático, vinculación por QR, fotos directamente desde una impresión y lectura/escritura de etiquetas NFC OpenPrintTag.
- **Modo taller** a pantalla completa para tableta/móvil.

## Acceso remoto
- **Cloudflare Tunnel** (gratuito, dirección aleatoria o fija), o una **dirección personalizada** (nombre de dominio, DynDNS, VPN, Tailscale…) para evitar Cloudflare, con regreso a Cloudflare con un clic.
- **Enlaces para compartir** temporales (24 h, un solo uso).

## Cuentas
- **Cuentas locales** con código de recuperación y pregunta secreta.
- **Confirmación de sesión**: al abrir la app con una sesión guardada, Stellio le pide confirmar la cuenta.
- **Cuentas de invitado de solo lectura**: comparta biblioteca, impresoras y stock sin riesgo.
- En un PC, el acceso por navegador a la app de Windows está bloqueado (token interno): use la ventana de la aplicación.

## Varias instancias de Stellio
- Las demás instalaciones de la red local se **detectan** y se añaden con un clic (introduzca su clave local).
- **Enviar un archivo** a otra instancia, a la carpeta que elija.
- Widget de estado de las instancias en el panel.

## Notificaciones
- Notificaciones nativas de **Windows**, notificaciones del **navegador** (Pi, móvil).
- **Push**: ntfy, Telegram, Discord o webhook, incluso con la ventana cerrada (fin de impresión, fallo, mantenimiento, stock).

## Domótica
- **MQTT / Home Assistant**: publicación del estado y descubrimiento automático; dispositivo MQTT «Stellio» y sensores.

@@@ Server-Edition | Edición servidor
# Edición servidor

La **edición servidor** se activa en Linux (Raspberry Pi, VM, LXC, Docker) o con `STELLIO_HEADLESS=1`. Windows y macOS conservan la aplicación de escritorio. Stellio funciona en segundo plano y se usa desde un navegador: `http://<ip>:5000`.

## Raspberry Pi / Linux
Requisitos: se recomienda Raspberry Pi 4 o 5, Raspberry Pi OS de **64 bits**.

`install-pi.sh` instala las dependencias del sistema (`ffmpeg`, `unrar`, bibliotecas de renderizado 3D), un entorno Python dedicado y un **servicio systemd** `stellio` que arranca con el sistema y se reinicia si falla.

```bash
sudo systemctl status stellio
sudo systemctl restart stellio
sudo journalctl -u stellio -f
```
¿Poca RAM? Aumente el swap si falla la instalación de las dependencias de Python y vuelva a lanzar el script.

## Proxmox VE (contenedor LXC)
El script `stellio-lxc.sh` ofrece ajustes **por defecto** o **avanzados** (CTID, núcleos, RAM, disco, puente, VLAN, DHCP o IP fija, almacenamiento, carpeta del host a montar) y después:
- crea un contenedor **Debian 12 sin privilegios** (2 núcleos, 2 GB de RAM, 32 GB de disco, arranque automático);
- instala en él Stellio con `install-pi.sh`;
- muestra la dirección `http://<ip-del-contenedor>:5000` y la contraseña de root.

```bash
pct exec <CTID> -- update-stellio              # actualizar
pct exec <CTID> -- journalctl -u stellio -f    # registros
```
- **Modo no interactivo**: variables `var_mode=default var_cpu=4 var_ram=4096 var_disk=16 var_ip=192.168.1.50/24 var_gw=192.168.1.1` (lista al principio del script).
- **Almacenamiento**: `var_choose_storage=1`, `var_storage`, `var_template_storage`.
- **Idioma** del script: `var_lang=es` (fr, en, de, es, pt, it, zh, ja).
- **Fuentes**: en este contenedor solo se ofrecen los recursos **SMB/NFS**. Con `var_mount=/host:/mnt/models` también se permite «Carpeta local». Ajuste: `/etc/systemd/system/stellio.service.d/sources.conf` (`STELLIO_ALLOWED_SOURCE_TYPES`).

## Salvaguardas (1.0.7)
`install-pi.sh` configura:
- una **vigilancia cada minuto** (`stellio-watchdog`): reinicia Stellio si deja de responder (3 comprobaciones fallidas, 3 minutos de gracia tras un arranque), lo arranca si está detenido, reinicia la red si se pierde la dirección IP y limpia registros y caché de apt si quedan menos de 300 MB libres en el disco;
- un servicio que **nunca renuncia** a reiniciarse;
- límites de **CPU 75 %**, **RAM 75 % (ralentización) / 85 % (límite duro)**, prioridad baja, y Stellio se sacrifica primero si falta memoria;
- registros limitados a **100 MB**.

Intervenciones de la vigilancia: `journalctl -t stellio-watchdog`. Los contenedores existentes reciben todo esto con `update-stellio`.

## Particularidades de la edición servidor
- ☁️ **IA en línea** opcional (ver [Inteligencia artificial](es-AI)).
- 📥 **Perfiles de slicer**: Stellio no ve los slicers de su PC y no se conecta a las nubes de los slicers (Orca Cloud, Bambu Cloud…). Exporte sus perfiles (OrcaSlicer: Archivo → Exportar → Exportar paquete de preajustes) e impórtelos en *Ajustes → Mis perfiles de slicer*, o use una **carpeta de perfiles vigilada** (Syncthing, recurso de red, scp…).
- 🐯 **TigerTag**: inicio de sesión oficial con correo y contraseña; ¿cuenta de Google? Primero defina una contraseña con «Olvidé mi contraseña» en la app TigerTag. Alternativa: copiar la carpeta de datos de TigerTag Studio al servidor.
- Tras una actualización, el navegador se recarga automáticamente.

## Variables de entorno
| Variable | Función |
|---|---|
| `STELLIO_HEADLESS` | Fuerza el modo servidor |
| `STELLIO_PORT` | Puerto (por defecto 5000) |
| `STELLIO_SERVER_URL` | Dirección pública del servidor |
| `STELLIO_DATA_DIR` | Carpeta de datos |
| `STELLIO_ALLOWED_SOURCE_TYPES` | Tipos de fuente permitidos (`folder,smb,nfs`) |
| `STELLIO_START_MINIMIZED` | Iniciar minimizado |
| `STELLIO_NO_AUTO_INSTALL` | Desactiva la instalación automática de módulos |

@@@ Settings-and-Data | Ajustes y datos
# Ajustes y datos

## Apariencia
- **Tema**: Oscuro / Claro / Sistema. Por defecto, **claro**; oscuro solo si el sistema (o usted) lo pide.
- **Temas de marca**: Stellio, Bambu, Prusa, Voron, Creality; 33 paletas, color de acento personalizado, imagen de fondo ajustable.
- **Accesibilidad**: alto contraste, animaciones reducidas, foco de teclado visible, tamaño del texto, modo daltónico.
- **8 idiomas**: fr, en, de, es, it, pt, ja, zh.
- Navegación reordenable arrastrando y soltando; **deshacer el último ajuste modificado**.

{{img:settings}}

## Atajos de teclado
| Atajo | Acción |
|---|---|
| `Ctrl+K` | Paleta de comandos |
| `Ctrl+F` | Búsqueda |
| `Ctrl+N` | Nueva descarga |
| `Ctrl+,` | Ajustes |
| `Ctrl+Z` | Deshacer la última eliminación |
| `Alt+1-8` | Navegación rápida |
| `Mayús+clic` | Seleccionar un rango |
| `↑ ↓ ← →` + `Intro` | Navegar y abrir |
| `F` | Favoritos |
| `T` | Gestor de etiquetas |
| `?` | Ayuda de atajos |
| `Esc` | Cerrar / borrar la búsqueda |

## ¿Dónde están mis datos?
| Sistema | Carpeta |
|---|---|
| Windows | `%APPDATA%\Stellio` |
| macOS / Linux | `~/.stellio` |
| Windows portátil | `data` junto a `Stellio.exe` |
| Personalizado | variable `STELLIO_DATA_DIR` |

Contenido: base de datos `stellio.db` (SQLite), ajustes `app_settings.json`, registro `stellio.log`, módulos descargados `extra_libs`. El código está separado de los datos y una actualización nunca lo toca.

## Copia de seguridad
- **Exportación / importación completa** (.zip) de sus datos.
- **Copias automáticas** programables.
- **Papelera** de 5 minutos, registro de operaciones con deshacer.
- Las actualizaciones nunca pierden datos.

## Registros y diagnóstico
- El nivel de registro por defecto es **advertencia**; el archivo `stellio.log` se recrea en cada inicio.
- **Modo debug**: actívelo en los Ajustes; se aplica al próximo inicio.
- **Exportar el diagnóstico** (Ajustes → Diagnóstico): secretos ocultos, impresoras integradas listadas (tipo, modelo, estado — sin nombre, dirección ni clave).
- Bloque **Salud de Stellio**: estado general de la aplicación.

## Sugerencias y errores
Desde la aplicación: **Sugerencias y errores** en la barra lateral. El mensaje se convierte en una incidencia de GitHub (anónima, mediante una GitHub App), con una insignia «Nueva respuesta».

@@@ Troubleshooting | Solución de problemas
# Solución de problemas

Antes de nada: exporte el **diagnóstico** (Ajustes → Diagnóstico) y consérvelo para un informe.

## La pantalla se queda en blanco al iniciar (macOS)
El puerto **5000** suele estar ocupado por el *Receptor AirPlay* (un 403 en Safari). Stellio elige ahora **automáticamente** un puerto libre (5001–5030). Si no: Ajustes del Sistema → General → AirDrop y Handoff → desactive *Receptor AirPlay*. Registro: `~/.stellio/stellio.log` (vacío en el nivel normal: active el modo debug).

## El contenedor LXC deja de ser accesible
Desde el shell de Proxmox:
1. `pct status <CTID>` y luego `pct start <CTID>` si está detenido.
2. `pvesm status`: ¿**almacenamiento lleno**? Es la causa más frecuente cuando el almacenamiento se comparte.
3. `pct exec <CTID> -- free -m` y `dmesg -T | grep -i "oom\|killed process"`: falta de memoria.
4. `pct exec <CTID> -- ip -4 a`: ¿ha cambiado la IP de DHCP? Resérvela en el router.
5. `pct exec <CTID> -- systemctl status stellio` y `journalctl -u stellio -n 100`.

Desde la 1.0.7, la vigilancia automática trata los casos habituales; vea `journalctl -t stellio-watchdog`.

## Las miniaturas son lentas o no aparecen
- Elija *Ajustes → Rendimiento de las miniaturas*: **Eco** en una máquina pequeña.
- Los archivos muy pesados conservan una miniatura de sustitución tras agotar el tiempo.
- La generación se pausa mientras usa la aplicación: es normal.

## Mi impresora no se detecta
- Compruebe que está en la misma red (VLAN, Wi-Fi de invitados).
- Añádala a mano con su dirección IP y su clave.
- Bambu Lab: active el modo LAN; Klipper: la API de Moonraker debe ser accesible.

## Falta la foto de fin de impresión
Active la casilla *Foto de fin de impresión* en la impresora (igual que la vigilancia por IA y el enchufe inteligente) y compruebe que la cámara responde.

## «Módulo ausente»
En el primer inicio de cada versión, Stellio descarga los módulos que faltan. Compruebe su conexión a internet; no defina `STELLIO_NO_AUTO_INSTALL` salvo necesidad.

## Windows SmartScreen / macOS bloquea la aplicación
Los instaladores no están firmados. Compruebe el `.sha256` y luego *Más información → Ejecutar de todas formas* (Windows) o clic derecho → *Abrir* (macOS).

## Obtener ayuda
[GitHub Issues](https://github.com/stellio-app/stellio/issues), [Discord](https://discord.gg/ySxpHvS6bd) o **Sugerencias y errores** en la aplicación. Indique: versión de Stellio, sistema, pasos para reproducir, registro exportado.

@@@ Contributing | Contribuir
# Contribuir

Las contribuciones son bienvenidas. 🎉

1. Haga un **fork** del repositorio.
2. Cree su rama: `git checkout -b feature/MiFuncion`.
3. Haga commit: `git commit -m "Añade MiFuncion"`.
4. Haga push: `git push origin feature/MiFuncion`.
5. Abra una **Pull Request**.

Reglas: respetar el estilo existente, comentar en francés o inglés, probar en Windows si es posible, actualizar la documentación. Toda cadena nueva de la interfaz debe añadirse en los **8 archivos de idioma**.

## Tecnologías
| Componente | Tecnología |
|---|---|
| Backend | Python 3.8+, Flask, Waitress |
| Frontend | HTML5, CSS3, JavaScript puro (sin compilación) |
| Base de datos | SQLite (modo WAL) |
| Escritorio | pywebview (Windows, macOS) / navegador (servidor) |
| 3D | PyRender, rasterizador CPU con numpy, Three.js |
| Mallas | trimesh, pymeshfix, shapely, rectpack |
| IA | Ollama (local) |
| Red | paho-mqtt, smbclient, requests |
| Cifrado | cryptography (AES) |

## Estructura del repositorio
```
stellio/
├── main.py            Núcleo Flask: base de datos, auth, biblioteca, impresoras, IA, arranque
├── modules/           Funciones separadas de main.py (print_session, timelapse, quote_portal…)
├── interface/         index.html, script.js, style.css, management.js (JavaScript puro)
├── packaging/         launcher.py, instalador de Windows (.iss), permisos de macOS
├── languages/         Traducciones (8 idiomas) y changelog.json
├── tests/  tools/     Pruebas pytest, herramientas de mantenimiento
├── release-notes/     notes_version_X.Y.Z.txt
├── install-pi.sh      Instalación Raspberry Pi / Linux
└── stellio-lxc.sh     Instalación Proxmox LXC
```
Un módulo declara los servicios de `main.py` que usa (`_REQUIRED`), sus rutas (`_ROUTES`) y una función `init`. Comprobación antes de publicar: `python -m pytest tests -q`.

## Seguridad y privacidad
- Stellio es **local-first**: por defecto no se recopila ni se envía nada. Única excepción, si usted la activa: la IA en línea de la edición servidor.
- Los archivos de código y configuración no son accesibles desde el navegador; la API está protegida por sesión y CSRF; los invitados son de solo lectura; los secretos están cifrados.
- Cada versión se publica con una suma `.sha256` que verifica la actualización integrada.

## Licencia
**GNU AGPL v3**: puede copiar, modificar y distribuir Stellio; si lo modifica o lo ofrece como servicio de red, debe publicar el código fuente bajo la misma licencia.

## Colaboración y agradecimientos
Stellio es socio oficial de integración de **TigerTag** ([tigersystem.io](https://tigersystem.io)). Gracias a Ollama, Flask, Three.js, trimesh, Spoolman y a la comunidad maker. ☕ Apoyar: [Ko-fi](https://ko-fi.com/E6J828RYVD).
