

<h1 align="center">E-commerce Engine — Django & Docker</h1>

<div align='center'>
  <strong>Documentación:</strong>
  <a href="README.md">
    <img src="https://img.shields.io/badge/EN-English-0052B4?style=flat-square" alt="English">
  </a>
  <a href="README-es.md">
    <img src="https://img.shields.io/badge/ES-Español-AA151B?style=flat-square" alt="Español">
  </a>
</div>

<br>


<p>
  <strong>Un motor (engine) de e-commerce full-stack diseñado para un despliegue rápido y fácil integración.</strong>
  Construido con un enfoque en la modularidad, permitiendo a las empresas lanzar tiendas completas mediante la carga masiva de datos (XLSX/CSV) y un stack de Docker listo para producción.
</p>
<p>
  Esta plataforma integra <strong>Autenticación de Usuarios</strong> (basada en roles), un <strong>Catálogo de Productos</strong> con sistema de favoritos, un <strong>Carrito de Compras</strong> persistente, <strong>Gestión de Pedidos</strong> y <strong>Procesamiento de Pagos</strong> seguro a través de Mercado Pago — todo bajo un diseño totalmente responsive.
</p>


<div align="center">
  <a href="#features">Funcionalidades</a> • 
  <a href="#tech-stack">Tech Stack</a> • 
  <a href="#technical-overview">Arquitectura</a> • 
  <a href="#demo">Video Demo</a> • 
  <a href="#contact">Contacto</a>
</div>

<br>

<div align="center">
   <img src="https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white">
   <img src="https://img.shields.io/badge/Django-5.2.1-092E20?style=for-the-badge&logo=django&logoColor=white">
   <img src="https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white" />
   <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white">
   <img src="https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white">
</div>


<section id="features">
  <h2>Funcionalidades</h2>

  <h3>Core de E-commerce</h3>
  <ul>
    <li><strong>Catálogo de Productos:</strong> Organización dinámica con categorías, subcategorías y marcas.</li>
    <li><strong>Carrito de Compras:</strong> Gestión basada en sesiones para evitar la pérdida de datos del usuario.</li>
    <li><strong>Flujo de Pedidos:</strong> Procesamiento robusto con gestión de estados en tiempo real.</li>
    <li><strong>Autenticación de Usuarios:</strong> Sistema seguro con permisos basados en roles (Cliente/Staff).</li>
  </ul>

  <h3>Integraciones y Datos</h3>
  <ul>
    <li><strong>API de Mercado Pago:</strong> Integración de pasarela de pagos lista para producción.</li>
    <li><strong>Carga Masiva de Productos:</strong> Configuración rápida del inventario usando <strong>OpenPyXL</strong> para procesar archivos Excel/CSV.</li>
    <li><strong>Renderizado Híbrido:</strong> Optimizado para SEO mediante <strong>SSR</strong> (Server-Side Rendering) manteniendo interacciones fluidas con <strong>AJAX</strong>.</li>
  </ul>
</section>


<br>


<section id="tech-stack">
  <h2>Technology Stack</h2>
  <div>
    <table style="border-collapse: collapse; border: none;">
      <tr>
        <td align="right"><b>Backend & Core</b></td>
        <td>
          <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" />
          <img src="https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white" />
          <img src="https://img.shields.io/badge/DRF-ff1709?style=for-the-badge&logo=django&logoColor=white" />
        </td>
      </tr>
      <tr>
        <td align="right"><b>Database & Cache</b></td>
        <td>
          <img src="https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white" />
          <img src="https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white" />
        </td>
      </tr>
      <tr>
        <td align="right"><b>UI & AJAX Interactions</b></td>
        <td>
          <img src="https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black" />
          <img src="https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white" />
          <img src="https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white" />
          <img src="https://img.shields.io/badge/Django_Templates-092E20?style=for-the-badge&logo=django&logoColor=white" />
        </td>
      </tr>
      <tr>
        <td align="right"><b>Deployment & Infra</b></td>
        <td>
          <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" />
          <img src="https://img.shields.io/badge/Docker_Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white" />
          <img src="https://img.shields.io/badge/Nginx-009639?style=for-the-badge&logo=nginx&logoColor=white" />
          <img src="https://img.shields.io/badge/Gunicorn-499848?style=for-the-badge&logo=gunicorn&logoColor=white" />
        </td>
      </tr>
      <tr>
        <td align="right"><b>APIs & Integrations</b></td>
        <td>
          <img src="https://img.shields.io/badge/Mercado_Pago-00B1EA?style=for-the-badge" />
          <img src="https://img.shields.io/badge/OpenPyXL-217346?style=for-the-badge&logo=microsoftexcel&logoColor=white" />
        </td>
      </tr>
      <tr>
        <td align="right"><b>Testing & API Docs</b></td>
        <td>
          <img src="https://img.shields.io/badge/Pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white" />
          <img src="https://img.shields.io/badge/Postman-FF6C37?style=for-the-badge&logo=postman&logoColor=white" />
          <img src="https://img.shields.io/badge/Swagger-85EA2D?style=for-the-badge&logo=swagger&logoColor=black" />
        </td>
      </tr>
      <tr>
        <td align="right"><b>Version Control</b></td>
        <td>
          <img src="https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=git&logoColor=white" />
          <img src="https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white" />
          <img src="https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white" />
        </td>
      </tr>
    </table>
  </div>
</section>


<br>


<section id="technical-overview">
  <h2>Implementación Técnica y Arquitectura</h2>
  <p>
    Este proyecto es un motor de e-commerce diseñado para un <strong>despliegue sin fricciones</strong>. El concepto central es la velocidad: cualquier tienda puede configurarse por completo en segundos realizando una <strong>carga masiva</strong> de productos a través de archivos CSV o Excel.
  </p>
  <p>
    Para lograr esto, construí una arquitectura de <strong>Monolito Modular</strong> que prioriza el bajo acoplamiento y la escalabilidad a largo plazo. El sistema está organizado en una estructura limpia de capas:
  </p>
  <ul>
    <li><strong>Modelos y Repositorio (Django ORM):</strong> Definición robusta de datos y acceso optimizado a la base de datos.</li>
    <li><strong>Capa de Servicios (Service Layer):</strong> Lógica de negocio centralizada para cada módulo, manteniendo las vistas "livianas" y mantenibles al desacoplar la lógica del flujo de la petición.</li>
    <li><strong>Controladores (Views):</strong> Gestión eficiente de la interacción del usuario y renderizado de plantillas mediante un enfoque <strong>API-First</strong> usando DRF.</li>
  </ul>

  <h3>Pilares Arquitectónicos Clave</h3>
  
  <h4>DevOps y Rendimiento</h4>
  <ul>
    <li><strong>Docker Compose:</strong> Orquestación multi-contenedor (Django, Postgres, Redis, Nginx) para un stack portátil.</li>
    <li><strong>Proxy Inverso con Nginx:</strong> Configurado para servir archivos estáticos y media de forma eficiente, añadiendo una capa de seguridad y optimizando la entrega de alto rendimiento.</li>
    <li><strong>Optimización de Consultas:</strong> Resolución de problemas de consultas N+1 mediante el uso de <code>select_related</code> y <code>prefetch_related</code>.</li>
    <li><strong>Caché con Redis:</strong> Estrategia para cachear consultas costosas y fragmentos pre-renderizados para minimizar la carga de la base de datos.</li>
  </ul>

  <h4>Base de Datos, Caché y Backups</h4>
  <ul>
    <li><strong>PostgreSQL:</strong> Elegido por su cumplimiento de <strong>propiedades ACID</strong>, garantizando 100% de fiabilidad en transacciones financieras (Pedidos y Pagos) incluso ante fallos del sistema.
      <ul>
        <li><strong>Integración de JSONB:</strong> Utilizado para almacenar metadatos dinámicos y complejos de las respuestas de la <strong>API de Mercado Pago</strong>, permitiendo un seguimiento flexible de pagos sin sacrificar rendimiento.</li>
        <li><strong>Búsqueda de Texto Completo (FTS):</strong> Implementación nativa para el descubrimiento de productos de alto rendimiento y filtrado optimizado.</li>
      </ul>
    </li>
    <li><strong>Persistencia en Redis:</strong> Configurado con la estrategia <em>Append Only File (AOF)</em> para asegurar que las sesiones, diccionarios de consultas y datos del carrito sobrevivan a reinicios del contenedor.</li>
    <li><strong>Automatización con Bash:</strong> Scripts personalizados para backups rotativos diarios tanto de la base de datos como de los archivos media para prevenir la pérdida de datos.</li>
  </ul>

  <h4>Estrategia de SEO y UX</h4>
  <ul>
    <li><strong>Diseño Mobile-First:</strong> Arquitectura responsive con SSR y etiquetas Meta dinámicas para un mejor posicionamiento en buscadores.</li>
    <li><strong>Core Web Vitals:</strong> Optimizado mediante carga perezosa (lazy loading) y minificación de recursos.</li>
  </ul>
</section>


<br>


<h2 id="scope">Alcance del Proyecto y Valor Comercial</h2>
<p>
  Este repositorio representa el <strong>Core Público</strong> de una solución de comercio electrónico profesional y lista para producción. Está diseñado para demostrar un flujo de negocio completo, desde la captación del usuario hasta la concreción del pago.
</p>

### El Flujo de Trabajo Principal
La versión pública de este motor soporta totalmente el ciclo de vida principal de un e-commerce:
1. **Descubrimiento:** Registro de usuarios y filtrado avanzado de productos.
2. **Selección:** Gestión de Favoritos y un Carrito de Compras con persistencia de sesión.
3. **Checkout:** Creación de pedidos con gestión de estados (Pendiente/Confirmado).
4. **Pago:** Integración profunda con <strong>Mercado Pago</strong>, manejando promesas de pago y actualizaciones de estado en tiempo real (webhooks).

<p>
  Aunque esta versión es totalmente funcional para el recorrido del usuario final, los módulos administrativos especializados están reservados para la <strong>Edición Empresarial Privada</strong> para proteger la lógica de negocio propietaria.
</p>

<blockquote>
  <strong>Nota:</strong> El núcleo público permite realizar el flujo completo descrito anteriormente. Sin embargo, la edición privada mejora la experiencia con paneles de administración personalizados que van más allá de las capacidades estándar del Admin de Django.
</blockquote>

<div align="center">
  <table style="width: 80%; border-collapse: collapse;">
    <tr>
      <th style="padding: 10px; border-bottom: 2px solid #ddd;">Módulos Públicos (Core)</th>
      <th style="padding: 10px; border-bottom: 2px solid #ddd;">Módulos Privados (Enterprise)</th>
    </tr>
    <tr>
      <td valign="top" style="padding: 10px;">
        <ul>
          <li>Autenticación de Usuarios</li>
          <li>Catálogo de Productos y Favoritos</li>
          <li>Lógica del Carrito de Compras</li>
          <li>Procesamiento de Pedidos</li>
          <li>Integración con Mercado Pago</li>
        </ul>
      </td>
      <td valign="top" style="padding: 10px;">
        <ul>
          <li>Paneles de Ventas Avanzados</li>
          <li>Seguimiento de Auditoría Automatizado</li>
          <li>Herramientas de CRM Especializadas</li>
          <li>UX/UI de Administración Personalizada</li>
        </ul>
      </td>
    </tr>
  </table>
</div>


<br>


<h2 id="demo">E-commerce Public Project Demo</h2>
<p>
  <strong>Public demonstration version</strong> - A full-stack e-commerce platform built with Django and vanilla JavaScript.
</p>

<div align="center">
  <a href="https://youtu.be/v9cFwaaIpew" target="_blank">
    <img src="https://img.youtube.com/vi/v9cFwaaIpew/0.jpg" alt="E-commerce Demo Video" width="600" style="border-radius: 10px; border: 2px solid #333;">
  </a>
  <br><br>
  <a href="https://youtu.be/v9cFwaaIpew" target="_blank">
    <img src="https://img.shields.io/badge/Watch_on_YouTube-FF0000?style=for-the-badge&logo=youtube&logoColor=white" alt="Watch on YouTube">
  </a>
  <p><em>Click the image or button to watch the full demo (includes admin panel walkthrough)</em></p>
</div>


<h2 id="images">E-commerce Images</h2>


<br>


<h2 id="contact">💻 Contacto Back-End Developer / Full-Stack Developer: </h2>

| [![GitHub Badge](https://img.shields.io/badge/github-%23121011.svg?&style=for-the-badge&logo=github&logoColor=white)](https://github.com/LucasCallamullo) | [![LinkedIn Badge](https://img.shields.io/badge/linkedin-%230077B5.svg?&style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/lucas-callamullo/) | [![YouTube Badge](https://img.shields.io/badge/YouTube%20-%23FF0000.svg?&style=for-the-badge&logo=YouTube&logoColor=white)](https://www.youtube.com/@lucas_clases_python) | [![Gmail Badge](https://img.shields.io/badge/Gmail-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:lucas.callamullo.dev@gmail.com) | [![Wsp Badge](https://img.shields.io/badge/WhatsApp-25D366?style=for-the-badge&logo=whatsapp&logoColor=white)](https://wa.me/5493515437688) |
|:---:|:---:|:---:|:---:|:---:|
