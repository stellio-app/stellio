@@@ Home | Inicio
# 🧊 Stellio, tu taller 3D en un solo lugar
{{img:dashboard}}

> **Biblioteca, impresoras, bobinas, costes y presupuestos: todo ordenado, a un clic y siempre en tu equipo.**

🔒 **100 % local** · 🆓 **Gratis y de código abierto** (AGPL v3) · 🌍 **8 idiomas** · 🖥️ Windows, macOS, Linux, Raspberry Pi, Proxmox · 📱 Android

**[⬇️ Descargar Stellio](https://github.com/stellio-app/stellio/releases)** · **[▶ Probar la demo en línea](https://demo.stellio-app.com)** · **[💬 Unirse al Discord](https://discord.gg/ySxpHvS6bd)**

## ✨ Por qué te va a encantar

| Para ti… | Lo que cambia Stellio |
|---|---|
| 🗂️ **Una biblioteca que se ordena sola** | Miniaturas 3D automáticas, etiquetas con IA, búsqueda en lenguaje natural, duplicados detectados. |
| 🖨️ **Todas tus impresoras en una pantalla** | Bambu Lab, Prusa, Klipper, OctoPrint, Creality… temperatura, cámara, progreso, foto final y timelapse. |
| 🚀 **De la biblioteca a la máquina en un clic** | Envío al slicer con los perfiles y la bobina correctos (un slicer por impresora), comprobaciones antes de imprimir. |
| 🧵 **Tus bobinas bajo control** | Inventario, Spoolman, TigerTag, OpenPrintTag, previsión de agotamiento, recordatorios de secado. |
| 💶 **Costes, presupuestos y pedidos** | Coste real (material, electricidad, desgaste), presupuestos en PDF, seguimiento del cliente en línea, facturas. |
| 🤖 **Una IA que se queda en casa** | Ollama local: etiquetado, búsqueda, imprimibilidad, vigilancia de fallos, S.O.S Print. |
| 🛠️ **Herramientas que salvan una pieza** | Visor 3D, reparación de malla, conversión, colocación automática, orientaciones sugeridas. |
| 📱 **Contigo en todas partes** | Móvil (PWA y app Android), acceso remoto, notificaciones push, Home Assistant. |

## 🚀 Empieza en 3 minutos

1. **Instala** Stellio: un instalador, un AppImage o un comando en Raspberry Pi y Proxmox ([Instalación](es-Installation)).
2. **Añade una carpeta** con tus modelos: Stellio los ordena y crea las miniaturas 3D por sí solo.
3. **Añade una impresora** (opcional): se detecta automáticamente en tu red.

👉 A continuación: los [Primeros pasos](es-Getting-Started) y la [Guía paso a paso](es-How-To), que explica **cada función y cómo usarla**.

## 🧭 Explorar la wiki

| Quiero… | Página |
|---|---|
| Aprender a usar cada función | [Guía paso a paso](es-How-To) |
| Instalar Stellio | [Instalación](es-Installation) |
| Dar mis primeros pasos | [Primeros pasos](es-Getting-Started) |
| Gestionar mis archivos 3D | [Biblioteca](es-Library) |
| Conectar mis impresoras | [Impresoras](es-Printers) |
| Controlar mis bobinas | [Filamento](es-Filament) |
| Descargar modelos | [Descargas](es-Downloads) |
| Usar la IA y S.O.S Print | [Inteligencia artificial](es-AI) |
| Calcular costes, presupuestos y facturas | [Costes y gestión](es-Costs-and-Management) |
| Acceder desde mi móvil | [Acceso remoto y móvil](es-Remote-Access) |
| Instalar en Raspberry Pi / Proxmox | [Edición servidor](es-Server-Edition) |
| Configurar, hacer copias, entender mis datos | [Ajustes y datos](es-Settings-and-Data) |
| Resolver un problema | [Solución de problemas](es-Troubleshooting) |
| Contribuir al proyecto | [Contribuir](es-Contributing) |
| Ver las novedades de cada versión | [Novedades](es-Changelog) |

> 🔒 **Filosofía**: tus datos se quedan contigo. Todo funciona en local; por defecto, nada sale de tu equipo.

## Enlaces útiles

- 🌐 Sitio web: [stellio-app.com](https://stellio-app.com) · ▶ [demo en línea (solo lectura)](https://demo.stellio-app.com)
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

> 💡 Si la ventana integrada no puede abrirse (WebView2 o `Python.Runtime.dll` bloqueado, a menudo tras una descarga), Stellio se abre en una ventana separada de Edge/Chrome y se detiene al cerrarla. Para recuperar la ventana integrada: clic derecho en el zip → Propiedades → **Desbloquear** y descomprime de nuevo. Los detalles están en `data\stellio.log`.

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

La barra izquierda es un **riel** de iconos; al pulsar una categoría se abre su **panel** a la derecha, que se cierra tras tu elección.

{{img:sidebar-panel}}


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

## Navegación
La barra izquierda es un **carril estrecho**: Inicio, Biblioteca, Impresión, Filamento, Herramientas y Seguimiento. Haz clic en una categoría para abrir su **panel**; se cierra tras tu elección. Las insignias de notificación de las páginas de una categoría se **suman** en su icono. Abajo: Modo taller, Ayuda, **Actualizaciones** y Ajustes. **Proyectos** y **Ya impresos** están en Impresión.

## Herramientas del día a día
- **Paleta de comandos** `Ctrl+K`: navegar, ejecutar una acción, encontrar un archivo, una etiqueta, una bobina o un perfil.
- **Centro de notificaciones** (campana): fin de impresión, fallo, mantenimiento, stock bajo, secado de bobinas.
- **Widget flotante** con el progreso de la impresión en curso, visible en todas las páginas.
- **Atajos de teclado**: ver [Ajustes y datos](es-Settings-and-Data).

@@@ How-To | Guía paso a paso
# Guía paso a paso

Cada función de Stellio: **para qué sirve y cómo usarla**. Los detalles técnicos están en las demás páginas; aquí se practica.

> 💡 En toda la aplicación: `Ctrl+K` abre la **paleta de comandos** (ir a un sitio, lanzar una acción, encontrar un archivo, una etiqueta, una bobina) y `?` muestra los atajos.

## Orientarse en Stellio

| Menú | Para qué sirve |
|---|---|
| **Panel** | Impresiones en curso, stock bajo, archivos recientes; widgets reordenables. |
| **Biblioteca** | Todos tus modelos 3D, con miniaturas, etiquetas, filtros y búsqueda. |
| **Imprimir pronto** | Tu lista de espera de impresiones, reordenable. |
| **Proyectos** | Varios archivos agrupados para un mismo objeto. |
| **Impresoras** | Seguimiento en directo, envío, mantenimiento, piezas de desgaste. |
| **Inventario de filamento** | Tus bobinas, la previsión de agotamiento, el secado. |
| **Historial** | Cada impresión enviada, valorada como éxito o fallo. |
| **Galería** | Las fotos de tus impresiones. |
| **Estadísticas** | Fiabilidad, consumo, formatos, informes. |
| **Gestión** | Costes, presupuestos de clientes, pedidos, contabilidad. |
| **Modo taller** | Pantalla completa para tableta o móvil. |
| **S.O.S Print** | Diagnóstico guiado de una impresión fallida. |
| **Descargar** | Obtener modelos de Printables, MakerWorld, Thingiverse… |
| **Reparación** | Encontrar y reparar mallas dañadas. |
| **Convertidor** | Pasar de un formato 3D a otro. |
| **Duplicados** | Detectar archivos repetidos. |
| **Papelera** | Restaurar lo que has eliminado. |
| **Ajustes** | Apariencia, slicer, IA, copias de seguridad, acceso remoto. |

## Añadir y encontrar mis archivos

1. Haz clic en **Añadir una fuente** (o `Ctrl+K` y «Añadir una fuente») y elige una **carpeta**, un archivo suelto o un recurso **SMB / NFS**. Las carpetas 3D encontradas en tu ordenador se sugieren.
2. Stellio escanea y crea las **miniaturas 3D** en segundo plano; la generación se pausa mientras usas la aplicación.
3. Para encontrar un modelo: escribe en la barra de **búsqueda** o descríbelo en lenguaje natural («un soporte para auriculares») con la búsqueda por IA.
4. Arrastra y suelta archivos 3D desde el explorador para añadirlos directamente.

💡 Los archivos comprimidos (ZIP, RAR, 7z, TAR) se exploran sin extraerlos.

## Organizar con etiquetas, favoritos y filtros

1. Abre el menú **⋯** de un archivo, o selecciona varios (`Mayús+clic` para un rango) para actuar en bloque.
2. Añade **etiquetas** de colores a mano o deja que la IA las proponga; `T` abre el gestor de etiquetas.
3. Haz clic en la estrella para marcar un modelo como **favorito** (`F` abre los favoritos).
4. Combina **filtros** (tipo, tamaño, peso, estado de impresión, «Stock de filamento») y **guarda** el filtro para reutilizarlo.
5. Para renombrar muchos archivos: **Renombrado en bloque** (buscar/reemplazar, prefijo, sufijo, numeración), con vista previa antes de confirmar.

## Ver y preparar un modelo en 3D

1. Haz clic en la miniatura de un archivo: se abre el **visor 3D** (funciona sin conexión).
2. Gira y haz zoom; en un 3MF multiplaca, cambia de una placa a otra.
3. Lanza el **análisis de imprimibilidad** (voladizos): Stellio propone **orientaciones** recomendadas.
4. Usa la **colocación automática** para disponer varias piezas en la cama de tu impresora.
5. Envía el resultado al slicer desde el visor.

## Reparar una malla dañada

1. Abre **Reparación**: Stellio lista los archivos con agujeros o aristas abiertas (el análisis también se hace en segundo plano al crear las miniaturas).
2. Elige un archivo y lanza la **reparación**; compara **antes / después**.
3. El archivo se repara en su sitio; se conserva una copia de seguridad `.bak` por si acaso.

## Convertir archivos

1. Abre **Convertidor** y elige uno o varios archivos (STL, 3MF, OBJ, PLY, AMF, STEP).
2. Selecciona el formato de salida: STL, 3MF, OBJ, PLY, OFF o GLB.
3. Si hace falta, marca **Reparar automáticamente la malla** y **Eliminar el archivo original**.
4. Inicia la conversión. Una conversión por lotes se puede cancelar en cualquier momento: los archivos ya convertidos se conservan.

## Ampliar un modelo a tamaño real (BigPrint)
BigPrint (menú **Herramientas**) amplía un modelo al tamaño que quiera — 1,8 m o más — y lo corta en piezas que caben en su cama: piezas vaciadas, pasadores de unión y un número grabado en cada pieza. El cálculo lo hace el motor de código abierto [bigprint](https://github.com/PooterTF/bigprint) (AGPL-3.0, de Michael Christopher Stone), integrado en Stellio.

{{img:bigprint}}

1. Elija el modelo: **Elegir de la biblioteca**, **Importar un archivo**, o el botón **Enviar a BigPrint** del menú **Acciones** de un archivo (STL, 3MF, OBJ, PLY).
2. Indique el **tamaño final** (altura, anchura, profundidad o factor de escala) y su **impresora** (lista de modelos o dimensiones personalizadas).
3. Ajuste la **resistencia** (uso, material, vaciado, grosor de la cáscara) y los **pasadores**; las opciones avanzadas (eje vertical, margen, suavizado…) están plegadas.
4. Pulse **Vista previa**: Stellio muestra las piezas en vista explosionada, el peso de filamento, el coste estimado y la tabla de piezas. Un cálculo se puede cancelar en cualquier momento.

{{img:bigprint-result}}

Elija dónde guardar (origen de la biblioteca, subcarpeta, creación de carpeta posible, recursos de red incluidos) y pulse **Guardar los archivos**: las piezas STL, el proyecto 3MF, los pasadores, el informe y la vista previa se copian en la carpeta `<modelo>_bigprint`.

Si cambia un ajuste después de la vista previa, vuelva a lanzarla antes de guardar.

## Poner orden: duplicados y papelera

1. Abre **Duplicados**: se agrupan los archivos idénticos y los de **geometría similar** (el mismo modelo renombrado o reexportado).
2. Conserva el que quieras y elimina los demás.
3. ¿Eliminado por error? `Ctrl+Z` lo deshace durante 5 minutos; la **Papelera** guarda los elementos más tiempo y permite restaurarlos o eliminarlos definitivamente.

## Agrupar archivos en proyectos

1. Abre **Proyectos** y crea uno; añade los archivos de un mismo objeto (cuerpo, tapa, soportes…).
2. Un 3MF **multiplaca** añadido a un proyecto se divide en un 3MF por placa (también disponible: **Dividir las placas**, en el menú ⋯).
3. Sigue el avance («En curso» / «Terminados») y haz clic en **Coste del proyecto** para valorar todo el conjunto.

## Descargar modelos

1. Abre **Descargar** (o `Ctrl+N`) y pega el enlace de un modelo (Printables, MakerWorld, Thingiverse, Nexprint, Creality Cloud, Snapmaker Space).
2. Conecta una vez la cuenta que se pida (consulta [Descargas](es-Downloads)).
3. Elige la **fuente** de destino: el archivo llega con su **origen** (enlace, autor, licencia).
4. Stellio comprueba cada día si existe una **nueva versión** del modelo; **Mis likes** y **Mis creaciones** recuperan tus modelos de las cuentas conectadas.

## Conectar una impresora

1. Abre **Impresoras → Añadir**: la **detección de red** propone las máquinas encontradas; si no, introduce tipo, dirección y clave de acceso.
2. Indica el **volumen de impresión** (X, Y, Z): Stellio te avisa antes del envío si una pieza es demasiado grande.
3. Si quieres, elige el **slicer de esta impresora** (1.0.8): será el que se abra para esta máquina.
4. Activa las opciones útiles: **timelapse**, **foto de fin de impresión**, **vigilancia por IA**, **enchufe inteligente** (consumo real).

## Enviar un archivo al slicer

1. Desde la biblioteca o el visor, haz clic en **Enviar al slicer**.
2. En la ventana: mira la **estimación** (peso, tiempo), elige la **impresora**, la **bobina** y el **perfil de ajustes**, o deja «Automático».
3. Lee las **comprobaciones antes de imprimir**: bobina por secar, filamento abrasivo, volumen superado, material insuficiente.
4. Haz clic en **Enviar**: el archivo se abre en el slicer de la impresora (o en el de Ajustes), con los perfiles vinculados a la máquina. La bobina se descuenta si lo has pedido.

💡 Para vincular perfiles a una impresora, impórtalos desde Ajustes → Slicer.

## Preparar lo siguiente: «Imprimir pronto»

1. En el menú **⋯** de un archivo, elige **Añadir a imprimir pronto**.
2. Abre **Imprimir pronto**: arrastra para **reordenar**.
3. Envía un elemento directamente al slicer o quítalo de la lista.

## Seguir una impresión

1. En la tarjeta de la impresora: temperatura, progreso, **cámara en directo** y nombre del archivo en curso.
2. Un **widget flotante** muestra el avance en todas las páginas.
3. La **campana** te avisa (fin, fallo, mantenimiento, stock bajo); activa las **notificaciones push** (ntfy, Gotify, Pushover, Telegram, Discord, Slack, webhook) para enterarte con la ventana cerrada.
4. Al 100 %, Stellio toma la **foto final**: márcala como *Éxito* o *Fallo* con un clic. El **timelapse** se monta automáticamente.

## Valorar, reimprimir, encontrar tus fotos

1. Abre **Historial**: filtra por plataforma, resultado o fechas.
2. Valora cada impresión como **éxito** o **fallo**: alimenta las recomendaciones y las estadísticas.
3. **Ver el archivo** o **Reimprimir** como la última vez (mismos ajustes).
4. Encuentra tus fotos en la **Galería**; **Mis G-codes** guarda los G-codes vinculados a un archivo con el botón **Abrir en el slicer**.

## Controlar mis bobinas

1. Abre **Inventario de filamento**: añade bobinas a mano (o importa Excel/CSV), vincula **Spoolman**, **TigerTag** u **OpenPrintTag**, o busca una bobina en la **Open Filament Database**.
2. Al enviar al slicer, elige la bobina: Stellio **descuenta** el consumo y comprueba que queda suficiente.
3. En **Pesaje y previsión**, pesa una bobina: Stellio estima su **fecha de agotamiento** y te avisa cuando se acerca.
4. Registra el **secado** de una bobina para seguir su estado; usa **Recomprar** para abrir la tienda del fabricante.

## Calcular un coste y hacer un presupuesto

1. Abre la calculadora desde un archivo (**Coste**) o un proyecto (**Coste del proyecto**).
2. Revisa material, electricidad, **desgaste de la máquina**, **gastos fijos**, **margen** y **cantidad**: se muestran el precio unitario y el total.
3. Haz clic en **Generar el presupuesto (PDF)**: indica cliente y descripción. El PDF se conserva y se encuentra en el widget **Presupuestos**.
4. Fija el margen por defecto en **Ajustes → Tarificación de impresión**.

## Gestionar pedidos, clientes y facturas

1. Activa *Activar las funciones de coste, presupuesto y facturación* en Ajustes: aparece la pantalla **Gestión**.
2. Envía un presupuesto al cliente con su **enlace de seguimiento**: puede aceptarlo o rechazarlo en línea; la aceptación crea la tarea de impresión. **Stellio no procesa ningún pago.**
3. Sigue la **cola de pedidos**, los pagos, las facturas de anticipo y los abonos; el **reparto inteligente** propone la impresora adecuada sin lanzar nunca una impresión.
4. Cada mes, exporta la **contabilidad** (ZIP con CSV y PDF).

## Planificar la producción (planificación y capacidad)
La página **Planificación** (menú **Impresión**) calcula, para cada impresora, la fecha de fin estimada de cada pedido, compara la capacidad disponible con la carga solicitada y le avisa de una sobrecarga o un retraso antes de que ocurra.

{{img:planning}}

1. En **Pedidos**, indique para cada pedido la **duración por pieza** (en horas): un pedido creado desde un presupuesto la toma del cálculo de costes. Un pedido sin duración no se planifica y queda señalado arriba en la página (puede rellenarla ahí mismo).
2. Elija la **impresora** de cada pedido (si no, Stellio lo coloca, a modo de sugerencia, en la máquina que se libera antes) y su **fecha de entrega**.
3. Abra **Planificación**: las barras muestran cómo se encadenan los pedidos en cada impresora (rojo = retraso previsto, naranja = menos de un día de margen), con la **tasa de carga** de cada máquina. La impresión en curso se tiene en cuenta mediante el tiempo restante leído en la impresora.
4. Ajuste el **horizonte** (7, 14 o 30 días). Las tarjetas superiores resumen capacidad, carga, retrasos previstos y **cumplimiento de plazos** en 90 días.

**Capacidad de las impresoras**: indique las horas de impresión posibles por día y los días laborables (por defecto 16 h, todos los días), máquina por máquina; desmarque una impresora para excluirla de la planificación.

Stellio le envía una notificación cuando un pedido va a superar su fecha de entrega o una impresora está sobrecargada (una vez por pedido y día).

El cálculo es deliberadamente sencillo: duraciones introducidas, pedidos encadenados por fecha de entrega, sin considerar cambios de material ni averías.

## Encontrar la mejor combinación (trazabilidad)
La página **Trazabilidad** (menú **Impresión**) vincula cada impresión con la **versión exacta del modelo** y el **perfil de slicer** utilizados, y muestra, para cada modelo, la combinación que mejor funciona.

{{img:trace}}

1. Imprima como siempre desde Stellio: la impresión se vincula automáticamente al modelo. Si el archivo cambió desde la última versión, Stellio guarda una versión «Antes de imprimir», así que la asociación siempre es exacta.
2. Tras imprimir, **valore el resultado** (éxito, fallo, parcial) en el historial: esas valoraciones alimentan las tasas.
3. Abra **Trazabilidad**: una fila por modelo con sus versiones y su **mejor combinación** (versión + perfil, éxitos sobre impresiones valoradas). Un clic abre **Versiones del modelo**.
4. En **Versiones del modelo**, cada versión muestra sus éxitos, fallos y tasa, y la tabla cruza **versión × perfil**.

{{img:trace_versions}}

La clasificación no se deja engañar por muestras pequeñas: 8 éxitos de 9 van por delante de 1 de 1. La mejor combinación solo se propone a partir de 2 impresiones valoradas y una versión conocida.

El seguimiento empieza con la v1.1.6: las impresiones anteriores no se reconstruyen.

## Mantener mis impresoras

1. En la tarjeta de una impresora, abre **Mantenimiento** y elige la **marca**: se ofrecen tareas recomendadas.
2. Añádelas a tu seguimiento: pasan a «pendientes» según las horas de impresión y los días transcurridos.
3. Registra tus **piezas de desgaste** (boquillas, placas, correas) con umbral de alerta y tus **calibraciones** por filamento.

## Diagnosticar un fallo: S.O.S Print e IA

1. Abre **S.O.S Print** y describe el problema (foto posible).
2. Responde a las preguntas, una a una, **sin límite**: Stellio reduce las hipótesis (y añade otras nuevas si hace falta) hasta encontrar la causa, y da un **diagnóstico final**. Si la solución no funciona, responde «sigue sin resolverse» y la investigación continúa.
3. Para la IA local, instala [Ollama](https://ollama.com/) y configúralo en **Ajustes → Inteligencia artificial**. La **vigilancia de fallos** te avisa sin detener nunca la impresión.

## Usar Stellio en el móvil y a distancia

1. En **Ajustes → Acceso móvil**, escanea el **código QR**: la biblioteca se abre en tu móvil (instalable como una aplicación).
2. Para la app **Android**, escanea el código QR específico.
3. Fuera de casa: activa el **acceso remoto** (Cloudflare Tunnel o dirección personalizada) o crea un **enlace para compartir** temporal.
4. Comparte en solo lectura con una **cuenta de invitado**.

## Copia de seguridad y restauración

1. Abre **Ajustes → Copia de seguridad y datos** y **exporta** tus datos (.zip).
2. Programa **copias de seguridad automáticas**.
3. Para restaurar, **importa** el archivo .zip. Una actualización de Stellio nunca toca tus datos.

## Atajos que conviene conocer

| Atajo | Acción |
|---|---|
| `Ctrl+K` | Paleta de comandos |
| `Ctrl+N` | Nueva descarga |
| `Ctrl+Z` | Deshacer la última eliminación |
| `F` · `T` | Favoritos · gestor de etiquetas |
| `?` | Ayuda de atajos |

Lista completa: [Ajustes y datos](es-Settings-and-Data).

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
- **Favoritos**, filtros avanzados (tipo, tamaño, peso, estado de impresión), **filtros guardados**. Acceso: tecla **F**, widget del panel o estrella de cada archivo (al quitar una estrella, el archivo desaparece al instante de la vista Favoritos).
- Filtros de estado: «Enviado al slicer», «Ya impreso», «Ya conseguido», «Ya fallido».
- **Filtro «Stock de filamento»**: conserva solo los archivos imprimibles con las bobinas que tiene.
- El orden, la búsqueda y los filtros se **recuerdan** al reabrir la aplicación.
- Cola **«Imprimir pronto»**, reordenable y enviable al slicer.
- **Renombrado masivo** (buscar/reemplazar, prefijo, sufijo, numeración) con vista previa.
- **Deshacer eliminaciones** (`Ctrl+Z`) gracias a una papelera temporal de 5 minutos; vale también para etiquetas, proyectos y fuentes.
- **Halo verde / rojo** alrededor de la miniatura: verde para un archivo ya impreso con éxito, rojo para una impresión fallida (vistas galería y detalles).
- **Ya impreso** (menú ⋯ de un archivo): anote a mano una impresión hecha en otro sitio — elija la impresora, los ajustes (perfil del slicer) y la bobina, luego **Logrado** o **Fallido**. El archivo entra en los filtros «Ya logrado» / «Ya fallido» y su ficha (clic derecho) muestra impresora, ajustes y bobina. Con **Fallido**, se guarda con la impresión un campo opcional **Motivo del fallo** (1.1.9).
- **Página «Ya impresos»** (panel Impresión): todos los archivos impresos o marcados como «ya impreso», con las mismas miniaturas y halos que la biblioteca, una búsqueda y un filtro Correctos / Fallidos. Al pasar el ratón sobre una miniatura aparece una **cruz roja** (en el móvil: un toque la muestra y un segundo toque abre el archivo); tras una confirmación, retira el archivo de la lista y vuelve a ser «nunca impreso». El botón **Quitar** de la ficha del archivo hace lo mismo. Hay un widget del mismo nombre en el inicio.
- Selección rápida: `Mayús+clic` para un rango, flechas + `Intro`.
- **Detección de duplicados** (exactos y de geometría similar).
- **Origen del modelo**: enlace de origen, autor, licencia, notas, fecha de descarga.
- **Arrastrar y soltar** archivos 3D desde el explorador, también a través del navegador.

{{img:library-halo}}

{{img:already-printed}}

En un 3MF de **varias bandejas**, la ventana «Ya impreso» ofrece una zona por bandeja, cada una con su bobina; un archivo **multicolor** admite varios colores por bandeja (**Añadir un color**). Los puntos de color reproducen los de tus bobinas y la ficha del archivo muestra el detalle.

{{img:already-printed-plates}}

Los archivos **enviados al slicer** llevan un **halo ámbar** (verde si la impresión salió bien, rojo si falló) desde el envío, y la etiqueta **Enviados al slicer** de la biblioteca los encuentra con un clic.

- **Colecciones**: agrupa modelos por tema (menú del archivo → *Añadir a una colección*). Cada colección se convierte en un chip de filtro en la biblioteca; define una **cantidad** por archivo y **añade toda la colección a la cola de impresión** con un clic.
- **Versiones de modelos**: menú del archivo → *Versiones*. Guarda una copia antes de modificar un modelo, **compárala** con el archivo actual (tamaño, triángulos, dimensiones, volumen), descárgala o **restáurala** (el estado actual se guarda antes).

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
- **BigPrint** (menú **Herramientas**): amplía un modelo al tamaño que quiera y lo corta en piezas numeradas con pasadores, vista previa 3D explosionada y estimación de filamento y coste (motor de código abierto bigprint).
- **Fusionar en 3MF**: selecciona varios modelos (STL, 3MF, OBJ…) y Stellio crea un único archivo 3MF — una placa si todo cabe, si no un archivo con varias placas (estructura compatible con Bambu Studio / OrcaSlicer; PrusaSlicer muestra todas las piezas juntas). Eliges el nombre y la carpeta (incluidos recursos de red, con creación de carpetas) y Stellio pregunta si eliminar o conservar los archivos originales.
- **Color de la bobina al slicer**: al enviar, el color y el material de la bobina elegida se aplican al perfil de filamento cargado en OrcaSlicer, Bambu Studio o PrusaSlicer (hace falta un perfil de filamento importado y vinculado a la impresora; en envío en lote, solo si todas las bobinas son iguales).
- **Barra de selección**: todos los botones tienen el mismo tamaño y caben en una sola línea (solo iconos en pantallas pequeñas, nombre en la información emergente).
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

## Modelos voluminosos
Un STL ocupa en memoria unas 12 veces su tamaño al cargarse. Por encima de un umbral (256 MB, hasta 1 GB si el ordenador tiene mucha memoria libre), Stellio ya no lo carga entero: análisis en flujo (STL binario y de texto), miniatura y visor sobre una **versión simplificada** (unos 300 000 triángulos), y las operaciones de escritura (reparación, conversión…) se rechazan con un mensaje claro.
Para trabajar igualmente con él: clic derecho › **Crear una versión ligera**. Stellio escribe una copia simplificada junto al original (`nombre (ligero).stl`), que nunca se modifica. La copia sirve para ver, medir, reparar o indexar, no para imprimir a plena resolución. La acción también se propone cuando se rechaza una reparación por tamaño; solo se aplica a archivos STL locales. Una exportación del slicer (OrcaSlicer…) en STL o 3MF suele pesar mucho menos.
En el Taller avanzado, cada campo «Ruta del modelo» ofrece **Elegir de la biblioteca**: origen, búsqueda, filtro por formato (STL, 3MF…), miniaturas y paginación.

@@@ Printers | Impresoras
# Impresoras
{{img:printers}}

En el inicio, el widget **Cámaras** muestra hasta **4 cámaras** (una por impresora en curso): al pulsar una miniatura se abre una ventana con **solo la cámara** (el widget «Impresiones en curso» conserva el seguimiento completo). El botón **Ver todo** abre la lista de todas las cámaras para elegir la que se muestra.


## Marcas compatibles

| Marca | Modelos | Conexión |
|---|---|---|
| **Bambu Lab** | X1/X1C/X1E, X2D, P1P/P1S, P2S, A1/A1 mini, H2D/H2S/H2C | MQTT (LAN + nube): seguimiento, AMS, cámara, descubrimiento SSDP |
| **Prusa** | MK4, MK3.9, MK3.5, MINI+, XL, CORE One | PrusaLink (HTTP) |
| **Creality** | Series K1/K2, Ender-3 V3, Hi | WebSocket: seguimiento, CFS, descubrimiento UDP |
| **Elegoo** | Centauri Carbon 1 y 2, series de resina Saturn/Mars | SDCP (WebSocket) |
| **Resina Chitubox** | Phrozen, Uniformation GKtwo y otras placas Chitubox | SDCP v3: seguimiento (mismo protocolo que Elegoo) |
| **Impresora USB** | Marlin, Prusa, Creality, placas Klipper… conectadas al PC de Stellio | Detección de puertos serie (el puerto nunca se abre): conectada / ausente, sin estado ni temperaturas |
| **Anycubic Photon** | Modelos Wi-Fi antiguos: Mono X, Mono X 6K, Mono SQ (no las M5s / M7) | Comandos de texto TCP 6000: solo estado y archivo actual |
| **Formlabs** | Form 3 / 3L / 4 | API web oficial (client_id:client_secret): estado, progreso, capas; el envío se hace con PreForm |
| **FlashForge** | Adventurer 5M/5M Pro, AD5X | API propietaria |
| **Klipper / Moonraker** | Cualquier máquina Klipper (Voron…) | HTTP: seguimiento, envío, cámara, horas exactas |
| **OctoPrint** | Cualquier impresora controlada por OctoPrint | HTTP |
| **Duet / RepRapFirmware** | Duet 2/3, standalone o con SBC (DSF) | HTTP: seguimiento, envío de archivos, temperaturas |
| **Repetier-Server** | Cualquier impresora gestionada por Repetier-Server | HTTP: seguimiento, envío de archivos, temperaturas (Marlin por USB serie no está admitido) |

> **Impresoras de resina: solo seguimiento.** Stellio nunca inicia ni detiene una impresión de resina. Cuéntanos en GitHub lo que no funcione (Creality Halot: aún no admitida).

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
- **Slicer por impresora**: cada impresora puede tener su propio slicer por defecto (OrcaSlicer, QIDIStudio, Bambu Studio…). El envío lo usa con los perfiles (ajustes, filamento) asociados a esa impresora y la lista de perfiles se adapta.
- **Software de resina**: Stellio detecta CHITUBOX, CHITUBOX Pro, Anycubic Photon Workshop, PreForm (Formlabs), Voxeldance Tango y Lychee Slicer. Una impresora de resina sin slicer elegido abre automáticamente el primer software de resina detectado; también puedes elegir uno a mano (Ajustes → Slicer o la ficha de la impresora). Se comprueban las rutas de instalación habituales: si tu software no se reconoce, selecciónalo a mano.

{{img:printer-slicer}}

**Producir con asistencia (1.1.8).** En el menú de un archivo, **Producir con asistencia** propone la impresora más adecuada (libre, material correcto, cola corta) y el perfil de slicer recomendado por Intelligence, y luego comprueba el archivo (modelo en bruto que hay que laminar, formato incompatible con la impresora), la impresora (sin conexión, ocupada) y los consumibles (bobina o resina suficiente). **No se envía nada sin tu validación**: el servidor rechaza el envío hasta que pulses *Validar esta elección*. Después Stellio envía el archivo a la impresora **sin iniciar la impresión a distancia** (la inicias en la máquina). Detecta el final de la impresión y lo anota en el historial; si la máquina no lo indica, introduce tú el resultado. Las recomendaciones **seguidas** y su resultado corrigen la clasificación de Intelligence: un perfil seguido al menos 3 veces que acierta menos del 40 % se rebaja, desde el 80 % se favorece (tarjeta *Producción asistida* de la página Estadísticas).

## Durante la impresión
- **Enchufe inteligente** (Shelly, Tasmota, Home Assistant): Stellio lee los vatios y registra el consumo real (kWh) y el coste.
- **Consumo real de filamento**, registrado tras la impresión.
- **Foto de fin de impresión** tomada al llegar al **100 %** (la pieza sigue en la cama), una sola foto para valorar *Conseguido/Fallido*.
- **Vigilancia de fallos por IA** (Ollama con visión, 100 % local): alerta ante espagueti o pieza despegada, **nunca una parada automática**.
- **Timelapse** automático (cámara → vídeo MP4, requiere ffmpeg).
- **Enlaces para compartir el estado**, de solo lectura.

## Detección de fallos por cámara (Obico)
En *Ajustes → Obico*, indica la dirección de tu servidor Obico (autoalojado u obico.io) y un token de API. Stellio comprueba las alertas con regularidad y te envía una **notificación push** en cuanto Obico detecta un fallo. La acción (pausa, cancelar) sigue siendo la de Obico: Stellio nunca detiene una impresión por sí solo. Un botón *Probar la conexión* verifica la dirección y el token.

## Mantenimiento
- **Mantenimiento de resina**: el botón **Mantenimiento** de las tarjetas de impresoras de resina propone tareas adecuadas (lámina FEP/nFEP, filtrado de resina, plataforma, pantalla LCD, filtro de carbón, eje Z, IPA de lavado, desgaste UV/LCD).
- **Mantenimiento predictivo** con tareas propias de cada marca.
- **Piezas de desgaste** (boquillas, placas, correas…) con alertas de stock, vinculadas a las tareas de mantenimiento.
- **Calibraciones** (flujo, pressure advance, temperaturas) por filamento e impresora.

@@@ Filament | Filamento
# Filamento

## Resina
La categoría de la barra lateral ahora se llama **Materiales** y agrupa dos páginas: **Filamento** (inventario de bobinas) y **Resina**. El inventario de resina es **manual**: añade tus botes (nombre, marca, tipo, color, volumen, restante, precio, ubicación, notas) y usa el botón «Usar» para restar un volumen en ml. Desde la 1.1.8 existe **Consumo automático** (al final de la página Resina): elige el **bote activo** de cada impresora de resina; al terminar una impresión, Stellio descuenta la resina usada de ese bote. El volumen se lee del archivo `.sl1` (campo `usedMaterial`); si no, se **estima** a partir del modelo del mismo nombre en tu biblioteca (volumen de la malla cerrada + 15 % de margen para soportes y pérdidas) y se señala como estimación; si no hay nada fiable, **no se descuenta nada** y una notificación te lo dice. Una impresión fallida solo descuenta la parte ya impresa (si se conoce el progreso). Cada descuento aparece en el historial y se puede **deshacer**; el resto nunca baja de cero.

Como con el filamento, el recordatorio **«A pedir»** también funciona con la resina: una resina (marca + nombre + color, todos los botes juntos) entra en la lista cuando su total restante baja del umbral fijado en la página (200 ml por defecto, 0 = desactivado) o cuando marcas «A pedir» en un bote. También aparece en el widget «A pedir» del panel; **Pedir** abre enlaces de búsqueda a tus tiendas (el stock de resina no se comprueba automáticamente) y **Ya pedido** aplaza el recordatorio 14 días.

## Fuentes de inventario
| Fuente | Detalles |
|---|---|
| **Spoolman** | Detección automática en la red. Stellio **ya no le escribe** el consumo (evita el doble recuento). |
| **Manual** | Bobinas introducidas a mano, importación Excel/CSV. |
| **TigerTag** | Identificación NFC/RFID. Inicio de sesión con correo y contraseña (solo se guarda un token cifrado) o reutilización de una sesión de TigerTag Studio. **Solo lectura.** |
| **OpenPrintTag** | Estándar abierto de etiquetas NFC: importación/exportación de archivos `.bin`, lectura/escritura desde la app Android, peso consumido siempre actualizado. |
| **Bambu AMS / Creality CFS** | Lectura de los slots. |

**Open Filament Database**: busque una bobina por marca, material y color y créela con un clic (peso, diámetro y densidad rellenados).

En la ventana de envío al slicer, la lista de bobinas está ordenada y tiene un **campo de búsqueda**.

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

Las **tiendas de Open Filament Database** (86) se añaden a **Enlaces útiles**, filtradas según tu país, y también las usa la búsqueda **Volver a comprar una bobina**: Stellio propone las tiendas que envían a tu zona.

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

> ⚠️ La IA no es 100 % fiable: puede equivocarse (etiquetas, descripciones, diagnósticos de S.O.S Print…). Considera sus respuestas como pistas que hay que comprobar, no como certezas.

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
1. Usted describe el problema (foto posible en cada paso) y, si quiere, los ajustes usados (temperaturas, velocidades, retracción…). Las **velocidades** se leen del perfil de slicer elegido (o las escribes tú); si faltan, la IA las pide. En impresiones **multicolor** la IA revisa la **torre de purga** (se despega, se derrumba, cae sobre la pieza, colores mezclados) y hace las preguntas útiles; el ancho de la torre se lee del perfil. Desde el primer paso y tras cada respuesta, la IA muestra sus **hipótesis ordenadas por probabilidad** (%), cada una con su motivo o una comprobación rápida.
2. Stellio hace **una pregunta cada vez**, sin límite, y reduce en directo una lista de hipótesis (añade nuevas si las primeras se descartan).
3. Entrega un **diagnóstico final**.

Desde la **pregunta 3**, el botón **Concluir y proponer una solución** da las causas más probables y pregunta «¿Este diagnóstico resolvió el problema?» (**Sí, resuelto** / **No, continuar la investigación**). El botón **Detener la investigación** permite abandonar en cualquier momento.

Las conversaciones se guardan: vuelva a abrirlas o márquelas como resueltas.

> ℹ️ Los resultados «Conseguido / Fallido» que valora en el historial mejoran las recomendaciones.

@@@ Costs-and-Management | Costes y gestión

> ⚠️ La IA no es 100 % fiable: puede equivocarse. Sus hipótesis son pistas que hay que comprobar, no certezas; verifica antes de cambiar tus ajustes o tu máquina.

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
- **Horas valle / punta**: en *Ajustes → Electricidad*, introduce dos precios por kWh y tus franjas valle (p. ej. `22:00-06:00`, fin de semana opcional). El **coste real** de las impresiones medidas los tiene en cuenta, un balance de 30 días muestra el **ahorro posible**, un simulador compara «ahora» con «próxima franja valle», y un aviso te dice cuándo empiezan las horas valle con tareas en espera. Stellio nunca inicia una impresión por sí solo.
- **Por qué fallan mis impresiones**: en *Estadísticas*, tasa de fallos por motivo, material, impresora, perfil de slicer, día de la semana y momento del día, archivos que más fallan y pistas con cifras (p. ej. «PETG: 45 % de fallos frente a 12 % de media»). Valora tus impresiones en el historial para alimentarla.



{{img:stats}}
@@@ Remote-Access | Acceso remoto y móvil
# Acceso remoto y móvil

## Móvil y tableta
- **Código QR** de acceso móvil a la biblioteca (**PWA instalable**).
- **App Android complementaria**: un código QR específico (Ajustes → acceso móvil) descarga el APK. Gestiona direcciones interna y externa con cambio automático, vinculación por QR, fotos directamente desde una impresión y lectura/escritura de etiquetas NFC OpenPrintTag.
- **Actualización de la app Android**: al abrirla, una ventana avisa de la nueva versión publicada en GitHub y ofrece descargarla e instalarla con un toque (suma de comprobación verificada).
- **Actualizaciones sobre la app existente**: desde la 1.1.0 el APK está firmado con una clave permanente. Si Android muestra «el paquete entra en conflicto con un paquete existente», desinstala la versión anterior una vez e instala la nueva; las siguientes actualizaciones se instalan con normalidad.
- **Modo taller** a pantalla completa para tableta/móvil. La tarjeta de impresora (1.1.9) muestra la cámara a la izquierda y los datos a la derecha en PC / servidor, sin desplazarse; en el teléfono, el progreso va antes que las temperaturas. En el modo taller, al tocar una impresora que imprime se abre su tarjeta.

{{img:android-update}}

**Menú en pantallas pequeñas**: desaparece la barra inferior; un botón arriba a la izquierda abre la misma barra lateral que en el ordenador (categorías + panel a la derecha). Las insignias (impresión en curso, notificaciones, avisos) se reducen para no estorbar. El logo de Stellio aparece en las páginas de configuración y «Servidor inaccesible».

{{img:mobile-drawer}}

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
- **Push**: ntfy, Gotify, Pushover, Telegram, Discord, Slack o webhook, incluso con la ventana cerrada (fin de impresión con nombre de archivo y duración, fallo, mantenimiento, stock, impresora sin conexión).

## Domótica
- **MQTT / Home Assistant**: publicación del estado y descubrimiento automático; dispositivo MQTT «Stellio» y sensores.

@@@ Desktop-Edition | Edición de escritorio
# Edición de escritorio

La **edición de escritorio** es la aplicación de escritorio: una ventana de Stellio en su PC (Windows, macOS). Conserva su comportamiento original; solo faltan algunas funciones pensadas para un servidor siempre encendido.

## ¿Qué edición tengo?
| Sistema | Edición por defecto |
|---|---|
| Windows, macOS | Escritorio |
| Linux, Raspberry Pi, VM, LXC, Docker | Servidor |

Para forzar la elección (pruebas, un PC Linux usado como escritorio):
```bash
STELLIO_SERVER_EDITION=0   # escritorio
STELLIO_SERVER_EDITION=1   # servidor (STELLIO_HEADLESS=1 también lleva ahí)
```

## Lo propio del escritorio
- **Ventana integrada** (pywebview). En Windows, abrir Stellio en un navegador del mismo PC está bloqueado (token interno): use la ventana. El teléfono, el APK y el túnel siguen permitidos.
- **Notificaciones de Windows** nativas.
- **Slicers del PC** detectados automáticamente (OrcaSlicer, Bambu Studio, PrusaSlicer, Cura…).
- **Fuentes**: carpeta local, archivo, SMB y NFS.
- **Datos** en `%APPDATA%\Stellio` en Windows; en la versión portátil, en la carpeta `data` junto a `Stellio.exe`.
- **Actualizaciones** desde GitHub mediante parche `.zip`, verificado antes de instalar.

## Funciones reservadas a la edición servidor
Estas funciones responden «reservado a la edición servidor» en la aplicación de escritorio:

| Función | Utilidad |
|---|---|
| IA en línea | Claude, ChatGPT o Gemini con su clave |
| Perfiles de slicer importados | Importación de perfiles exportados desde sus slicers |
| Notificaciones push | ntfy, Telegram, Discord, webhook… |
| MQTT / Home Assistant | Publicación de estado y descubrimiento automático |
| Resumen periódico | Diario o semanal |
| Sincronización entre dos instancias | Herramientas › Sincronización |
| Webhooks salientes | Mensajes firmados (HMAC-SHA256) a tus servicios |
| API pública y acceso móvil | Tokens de alcance limitado, rutas /api/v1 |

La entrada **Sincronización** del menú Herramientas se oculta en escritorio porque solo mostraría este mensaje.

## Taller avanzado en escritorio
Todo lo demás funciona como en un servidor. Las herramientas del Taller avanzado están en la barra lateral, cada una en su categoría: **Biblioteca** (Organización, Diff 3D, Similares, Licencias, Ficha de pieza), **Impresión** (Compatibilidad, Verificación de impresión, Archivos G-code), **Materiales** (Necesidades de material), **Herramientas** (Bandeja, Asistente de fabricación) y **Administración** (Tareas, Base de datos, Registro de auditoría, Equipos, Sesiones). Están reservadas a la cuenta propietaria; cada entrada tiene su interruptor en *Ajustes › Elementos de navegación*. En **Similares**, el botón **Archivos omitidos** (1.1.9) muestra los archivos que el índice no pudo procesar, con miniaturas, causa (demasiado grande por encima de 60 MB, malla vacía, ilegible, no encontrado) y una solución para cada uno (reexportar o simplificar el modelo, revisar la fuente); **Reintentar** los indexa de nuevo.

## Pasar a la edición servidor
Para un Stellio siempre encendido y accesible desde un navegador, vea [Edición servidor](es-Server-Edition) e [Instalación](es-Installation).

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

## Funciones reservadas al servidor (1.1.7)
Estas funciones no existen en la aplicación de escritorio, donde sus rutas responden «reservado a la edición servidor»:

| Función | Utilidad |
|---|---|
| IA en línea | Claude, ChatGPT o Gemini con su clave, en lugar de Ollama (véase [Inteligencia artificial](es-AI)) |
| Perfiles de slicer | Importación de perfiles exportados desde sus slicers |
| Notificaciones push | ntfy, Gotify, Pushover, Telegram, Discord, Slack o webhook, incluso con la ventana cerrada |
| MQTT / Home Assistant | Publicación de estado y descubrimiento automático |
| Resumen periódico | Diario o semanal, como notificación y push |
| Sincronización (Taller avanzado) | Sincroniza una carpeta con la de una instancia emparejada: primero el plan, después la aplicación confirmada, ninguna eliminación se propaga, se conservan ambas versiones en caso de conflicto. Las dos instancias deben estar en edición servidor |

El resto de las herramientas (bandeja, verificación de impresión, archivos G-code…) funciona igual en ambas ediciones.

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
- **Temas de marca**: Stellio, Bambu, Prusa, Voron, Creality; 33 paletas, color de acento personalizado, imagen de fondo ajustable. Se ofrece una imagen de Stellio por defecto (botón **Imagen por defecto**).
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

@@@ Plugins | Plugins
# Plugins

Un plugin es un pequeño programa Python que reacciona a un evento de Stellio (impresión terminada, impresión fallida, pedido atrasado, impresora sobrecargada): enviar una notificación, escribir en una hoja de cálculo, encender una luz… Los autores publican los plugins en **GitHub**; Stellio muestra un **catálogo público** (logotipo + descripción) en el menú **Plugins › Catálogo**, donde se instalan con un clic.

Cada plugin lleva una insignia: **Oficial** si está alojado en el repositorio `stellio-app/stellio-plugins`, **Comunitario** si está alojado en otro lugar (o instalado desde un .zip). Stellio decide la insignia según la dirección real del archivo: lea siempre los permisos y el código de un plugin comunitario.

**Seguridad de los plugins (1.1.8).** Antes de instalar, Stellio **audita el código** (análisis estático: red no declarada, lanzamiento de procesos, código dinámico, binarios…); un hallazgo bloqueante rechaza la instalación salvo que aceptes el riesgo de forma explícita. El catálogo y los plugins pueden estar **firmados (Ed25519)**: en cuanto hay una clave de confianza configurada, se rechaza una firma no válida, un plugin oficial sin firma y una actualización sin firma de un plugin firmado (sin clave configurada solo protege la suma SHA-256, y la página Plugins lo indica). En **Linux**, el núcleo restringe además cada plugin: archivos de solo lectura (escritura solo en su carpeta `data/`) y sin red sin el permiso `network`; **en Windows y macOS estas restricciones no se aplican**: los permisos siguen siendo declarativos. Una firma prueba el origen, no la inocuidad, y una auditoría puede pasar por alto código oculto: lee siempre el código.

**Plugins integrados.** Algunas funciones de Stellio se entregan como plugins integrados (BigPrint, resina, impresoras USB, timelapse, herramientas de archivos, estudio de placa, notificaciones push, webhooks, resumen periódico, MQTT / Home Assistant, Obico, compartir y sincronizar, Spoolman, proveedores de IA y asistente de IA, Stellio Pro). Forman parte de la aplicación, pero solo se cargan cuando están activados (sección «Plugins integrados» de la página Plugins; el cambio se aplica al reiniciar). **Actualización desde una versión anterior: no hay que hacer nada.** En el primer arranque de la 1.1.7, los plugins que usabas (por ejemplo MQTT activado, una impresora USB, webhooks, un timelapse) se activan automáticamente y conservan exactamente sus ajustes; las herramientas sin ajustes (BigPrint, herramientas de archivos, estudio de placa) se mantienen como estaban. Una instalación nueva no activa ninguno. Desactivar un plugin nunca borra sus ajustes. Otros plugins integrados: Compartir y sincronizar, Spoolman, un plugin por proveedor de IA + el asistente de IA (activa todas las funciones de IA) y **Stellio Pro** (clientes, presupuestos, facturas, pedidos, contabilidad, tarifa eléctrica, planificación, necesidades de material, stock de piezas): añaden sus páginas y botones solo si están activados.

## Usar un plugin
1. Abra **Plugins › Catálogo** (solo la cuenta propietaria).
2. Explore el catálogo y haga clic en **Instalar**: Stellio descarga el archivo y comprueba su suma SHA-256.
3. Lea los **permisos** solicitados y acéptelos. El plugin se instala **desactivado**.
4. Rellene su configuración si hace falta, actívelo y pulse **Prueba** para lanzarlo con un evento de prueba. El registro de ejecuciones muestra la salida y los errores.

También puede instalar un archivo `.zip` local (plugin en desarrollo) o cambiar la fuente del catálogo por la URL de otro catálogo.

## Crear un plugin
### 1. Estructura
Un plugin es una carpeta plana con un archivo `plugin.json` y un script Python:
```
mon-plugin/
├── plugin.json     Manifiesto (obligatorio)
├── main.py         Punto de entrada (nombre libre, indicado en "entry")
└── ...             Otros archivos: 100 como máximo, 8 MB descomprimido
```

### 2. El manifiesto plugin.json
```json
{
  "id": "mon-plugin",
  "name": "Mon plugin",
  "version": "1.0.0",
  "api": 1,
  "description": "Écrit une ligne à chaque impression terminée.",
  "author": "Votre nom",
  "entry": "main.py",
  "events": ["print.finished", "print.failed"],
  "permissions": ["events"]
}
```
| Campo | Función |
|---|---|
| `id` | Identificador único: minúsculas, dígitos, `-` o `_`, de 2 a 40 caracteres |
| `name`, `description`, `author` | Texto mostrado en Stellio |
| `version` | Numérica, por ejemplo `1.2.0`; sirve para detectar actualizaciones |
| `api` | Versión de la API de plugins: `1` |
| `entry` | Script Python en la raíz (por defecto `main.py`) |
| `events` | Eventos escuchados |
| `permissions` | Permisos solicitados |
| `ui` | Página mostrada en Stellio: `title`, `icon` (Font Awesome) y `entry` (un archivo `.html`) |

### 3. Eventos y permisos
| Evento | Se dispara cuando |
|---|---|
| `print.finished` | Termina una impresión |
| `print.failed` | Falla una impresión |
| `order.late` | Un pedido supera su plazo |
| `printer.overload` | Una impresora está sobrecargada |

| Permiso | Efecto |
|---|---|
| `events` | Recibir eventos (obligatorio si se declara `events`) |
| `api:read` | Leer datos mediante la API pública de Stellio |
| `api:write` | Modificar datos mediante la API pública |
| `network` | Información: el plugin accede a Internet |
| `ui` | Mostrar una página del plugin en el menú Plugins |

### 4. El script
Stellio ejecuta `python -I main.py <evento>` en un proceso aparte y envía por la entrada estándar un JSON `{"event": "...", "data": {...}}`. El modo `-I` (aislado) no añade la carpeta del plugin a la ruta de Python: para importar un archivo de su plugin, añada esa ruta usted mismo. La salida estándar se guarda en el registro.
```python
import json, os, sys

payload = json.loads(sys.stdin.read() or "{}")
event, data = payload.get("event", ""), payload.get("data", {})
config = json.loads(os.environ.get("STELLIO_PLUGIN_CONFIG") or "{}")

print(f"{event}: {data.get('file_name') or data.get('printer') or '-'}")
```
Para actuar sobre Stellio (permisos `api:*`), el script recibe `STELLIO_API_URL` y `STELLIO_API_TOKEN` (las claves `api_url` y `token` de la configuración del plugin). El SDK de Python `stellio_sdk.py` (carpeta `sdk/python` del repositorio) ofrece `plugin_event()`, `plugin_config()` y un cliente listo para usar: cópielo en su plugin y añada `sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))` antes de importarlo. Hay un ejemplo completo en `sdk/examples/hello-plugin`.

Límites: 10 segundos por ejecución, 512 MB de memoria, entorno mínimo (solo variables `STELLIO_*` y `PATH`). Python 3 debe estar instalado en el equipo que ejecuta Stellio. La configuración es una lista de pares clave/valor (texto, número, booleano) de 4.000 caracteres como máximo.

### 5. Probar
Comprima el **contenido** de la carpeta como `mon-plugin.zip` (2 MB máximo), instálelo desde **Plugins › Catálogo** (archivo local), acepte los permisos, actívelo y use **Prueba**. Corrija los problemas leyendo el registro.

## Plugin con una página

Un plugin también puede mostrar **su propia página** en Stellio. Aparece entonces en el menú **Plugins** de la barra lateral, bajo «Catálogo», en la lista «Instalados»: un clic abre su página. El manifiesto siguiente es un ejemplo mínimo.

```json
{
  "id": "mon-plugin",
  "name": "Mon plugin",
  "version": "1.0.0",
  "api": 1,
  "description": "Shows your archived G-code files layer by layer.",
  "author": "Stellio",
  "permissions": ["ui", "api:read"],
  "ui": {
    "title": "Mon plugin",
    "icon": "fa-layer-group",
    "entry": "viewer.html"
  }
}
```

- La página es **un único archivo HTML autónomo** (CSS y JavaScript dentro, imágenes en `data:`), 1 MB como máximo. Sin eventos, el plugin no necesita script Python.
- Se muestra en un marco **aislado**: sin acceso a la red, a las cookies ni al resto de Stellio.
- Lee los datos de Stellio con `window.stellio.api(ruta)`: solo lectura (GET), el permiso `api:read` es obligatorio, el resultado es JSON, o texto con `'text'` como segundo argumento. Los ajustes, las cuentas, la seguridad y los plugins no son accesibles.
- El tema lo proporcionan las variables CSS `--st-bg`, `--st-panel`, `--st-card`, `--st-text`, `--st-muted`, `--st-border`, `--st-accent`, `--st-success`, `--st-warning` y `--st-danger`, y el idioma `window.stellio.lang`.

```js
document.addEventListener('stellio-ready', async () => {
  const list = await window.stellio.api('/api/gcodes?limit=50');
  const id = list.gcodes[0].id;
  const text = await window.stellio.api('/api/projects/gcodes/' + id + '/download', 'text');
});
```

Para probarlo: comprima el contenido de la carpeta `mon-plugin`, instale el archivo desde **Plugins › Catálogo**, acepte los permisos, actívelo y ábralo desde el menú **Plugins**. Hace falta al menos un G-code archivado (ficha de archivo o proyecto). Un plugin desactivado aparece atenuado en la lista.

## Publicar en GitHub
1. Cree un repositorio público para su plugin con el código, un `README` y una licencia.
2. Para cada versión, cree una **release** de GitHub y adjunte el archivo `mon-plugin-1.0.0.zip`.
3. Calcule la suma SHA-256 del archivo, necesaria para el catálogo:
```bash
sha256sum mon-plugin-1.0.0.zip
```
4. Aumente siempre `version` en `plugin.json` antes de una nueva release.

## Aparecer en el catálogo de Stellio
El catálogo oficial es un archivo `catalog.json` del repositorio `stellio-app/stellio-plugins`. Su plugin se añade mediante una **Pull Request**.

1. Haga un fork del repositorio `stellio-app/stellio-plugins`.
2. Añada la entrada de su plugin en `catalog.json`:
```json
{
  "id": "mon-plugin",
  "name": "Mon plugin",
  "version": "1.0.0",
  "description": {"fr": "Écrit une ligne à chaque impression terminée.", "en": "Writes a line when a print finishes."},
  "author": "Votre nom",
  "url": "https://github.com/vous/mon-plugin/releases/download/v1.0.0/mon-plugin-1.0.0.zip",
  "sha256": "64 caractères hexadécimaux",
  "permissions": ["events"],
  "logo": "https://raw.githubusercontent.com/vous/mon-plugin/main/logo.png",
  "homepage": "https://github.com/vous/mon-plugin"
}
```
3. Abra la Pull Request: una comprobación automática verifica los enlaces, la suma SHA-256 y el logotipo, y después el equipo de Stellio revisa el plugin.

| Campo | Regla |
|---|---|
| `description` | Corta (unos 140 caracteres); texto simple o un texto por idioma (`fr`, `en`, `de`, `es`, `pt`, `it`, `zh`, `ja`) |
| `url` | Enlace `https` directo al archivo; el `sha256` debe coincidir exactamente |
| `logo` | `https`, PNG, JPEG o WebP, 200 KB como máximo, idealmente 128 × 128 (se rechaza el SVG) |
| `homepage` | Enlace `https` a la página del plugin (opcional) |
| `permissions` | Deben coincidir con las del manifiesto |

**Actualizar**: publique una nueva release y abra una Pull Request que cambie `version`, `url` y `sha256`. Si la nueva versión pide permisos adicionales, el plugin queda desactivado para el usuario hasta que los acepte; su configuración se conserva.

## Seguridad
- Un plugin **no está aislado** en un entorno protegido: se ejecuta con los derechos de Stellio en el equipo. Instale solo plugins cuyo autor le inspire confianza.
- Los plugins se instalan desactivados y sus permisos deben aceptarse.
- Las descargas solo se hacen por `https` desde direcciones públicas, con verificación SHA-256.
- El catálogo se revisa antes de publicarse, pero eso no sustituye su propia cautela: lea el código y los permisos.

Para saber más: [Contribuir](es-Contributing), el archivo `docs/plugins.md` del repositorio y el ejemplo `sdk/examples/hello-plugin`.

## Administración e instancias supervisadas
El plugin **Administración** (activo por defecto) reúne en una página (Administración › Administración) las **cuentas de invitado y sus roles**, los equipos, las sesiones, el registro de auditoría y las **instancias**.
- **Instancia autónoma** (por defecto): control total, nada cambia.
- **Instancia principal**: la subpestaña Instancias lista las instancias Stellio emparejadas y permite supervisarlas.
- **Instancia supervisada**: tras la **aceptación** de su propietario, sus cuentas, roles y permisos solo se gestionan desde la principal; el contenido local (biblioteca, impresoras) sigue siendo privado salvo que el propietario elija otra cosa al aceptar; el propietario puede **salir de la supervisión** en cualquier momento.
Una instancia supervisada no puede supervisar otras, y una instancia principal no puede ser supervisada. El resto de ajustes sigue siendo editable localmente.

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
├── release-notes/     notes.txt
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
