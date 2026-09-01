# Política de Privacidad

**Última actualización:** 1 de septiembre de 2026  
**Aplicación:** Stellio  
**Sitio web:** [stellio-app.com](https://stellio-app.com)  
**Repositorio:** [github.com/stellio-app/stellio](https://github.com/stellio-app/stellio)

## 1. Introducción
Bienvenido a la Política de Privacidad de Stellio. Stellio es una aplicación de gestión de archivos 3D e impresión 3D. Esta política describe cómo procesamos los datos.

Nuestra filosofía fundamental es simple: **Tus datos se quedan contigo. Todo se ejecuta localmente.**

## 2. Principio Fundamental: "Local-First"
De forma predeterminada, Stellio **no** recopila, transmite ni almacena **ningún dato** en servidores externos. Todos tus archivos 3D (STL, 3MF, OBJ), tus modelos de impresora, historial de impresiones, etiquetas y configuraciones se almacenan exclusivamente en tu propia máquina (Windows, Raspberry Pi o Linux) en una base de datos SQLite local.

## 3. Datos Almacenados Localmente
Los siguientes elementos se guardan solo en tu dispositivo:
- Tu biblioteca de archivos 3D y sus metadatos (etiquetas, descripciones, estadísticas).
- Miniaturas 3D generadas localmente (vía PyRender o Matplotlib).
- Tus configuraciones de impresoras y slicers.
- Tus claves API y credenciales (almacenadas localmente y cifradas vía AES-CFB).
- Historial de impresiones y fotos asociadas.
- Registros de actividad para diagnóstico.

## 4. Interacciones con Servicios de Terceros (Opcional)
Para funcionar, ciertas características *opcionales* de Stellio pueden comunicarse con servicios externos. Tú mantienes el control total sobre la activación de estas características:

- **Actualizaciones automáticas**: Stellio puede consultar repositorios de GitHub (`github.com/stellio-app/stellio`) para verificar la disponibilidad de nuevas versiones. No se transmite ningún identificador personal durante esta verificación.
- **Plataformas de Modelos 3D**: Si usas la función de descarga, Stellio se conecta directamente a las APIs de Printables, MakerWorld o Thingiverse usando **tus propias credenciales o claves API**. Esta información nunca se envía a los servidores de Stellio.
- **Gestión de Impresoras**: Stellio se comunica directamente con tus impresoras locales/de red o servidores de impresión (OctoPrint, Klipper/Moonraker, Bambu Lab vía MQTT). Estas comunicaciones permanecen confinadas a tu red local, a menos que configures explícitamente el acceso remoto.
- **Acceso Remoto (Túnel Cloudflare)**: Si habilitas el acceso remoto, tu tráfico se enruta de forma segura a través de los servidores de Cloudflare. Por favor, consulta la [política de privacidad de Cloudflare](https://www.cloudflare.com/privacypolicy/) para más detalles.
- **Inteligencia Artificial (Ollama)**: De forma predeterminada, la IA (Ollama) se ejecuta localmente en tu máquina. Si eliges configurar una URL de Ollama remota en la configuración, tus solicitudes (descripciones de modelos, búsqueda semántica) se enviarán a ese servidor de terceros que hayas elegido tú mismo.
- **Spoolman**: Si conectas Stellio a un servidor Spoolman externo, los datos de consumo de filamento se envían a ese servidor que controlas o has elegido.

## 5. Seguridad de los Datos
- **Cifrado**: Los datos sensibles (como claves API o contraseñas de impresoras) se cifran localmente usando el algoritmo AES-CFB.
- **Diagnóstico**: Si encuentras un error, puedes exportar un registro de diagnóstico desde la configuración. Stellio enmascara automáticamente los secretos y la información sensible antes de la exportación. No recopilamos estos registros automáticamente.

## 6. Tus Derechos
Dado que todos tus datos se almacenan localmente, tienes control absoluto sobre ellos:
- Puedes exportar todos tus datos en cualquier momento a través de la función de copia de seguridad (`.zip`).
- Puedes eliminar cualquier archivo, entrada del historial o configuración directamente desde la interfaz.
- Desinstalar la aplicación elimina los archivos del programa, pero necesitarás eliminar manualmente la carpeta de datos locales si deseas borrar permanentemente tu historial y base de datos.

## 7. Cambios en Esta Política
Podemos actualizar esta política de privacidad para reflejar cambios en las características de Stellio u obligaciones legales. La fecha de "Última actualización" en la parte superior de este documento se revisará en consecuencia. Te animamos a consultar esta página periódicamente.

## 8. Contacto
Si tienes preguntas o preocupaciones sobre esta política de privacidad o la gestión de tus datos, puedes contactarnos:
- 📧 Email: [contact@stellio-app.com](mailto:contact@stellio-app.com)
- 🐛 Informe de error: [GitHub Issues](https://github.com/stellio-app/stellio/issues)
- 💬 Discusiones: [GitHub Discussions](https://github.com/stellio-app/stellio/discussions)

---
*Este proyecto es de código abierto. Estás invitado a auditar el código fuente en nuestro repositorio de GitHub para verificar por ti mismo el cumplimiento de esta política.*