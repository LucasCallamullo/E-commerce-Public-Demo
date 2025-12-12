

<h1 align="center">E-commerce Full Stack - Django + DRF</h1>

<p>
  <strong>Plataforma de e-commerce completa desarrollada con Django y JavaScript vanilla.</strong> 
  Incluye: autenticación de usuarios con permisos por roles, catálogo de productos con favoritos, carrito de compras, gestión de pedidos, procesamiento de pagos (Mercado Pago), panel de administración avanzado y diseño responsive.
</p>

<br>

<!-- Navegación Rápida -->
<p>
  <strong>Navegación rápida:</strong>
   <a href="#features">Características</a> • 
   <a href="#tech-stack">Tecnologías</a> • 
   <a href="#demo">Demo Video</a> • 
   <a href="#images">Imágenes</a> • 
   <a href="#contact">Contacto</a>
</p>



<div>
  <!-- Primera fila de badges con estilo for-the-badge -->
  <a href="#tech-stack">
    <img src="https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.13">
  </a>
  <a href="#tech-stack">
    <img src="https://img.shields.io/badge/Django-5.2.1-092E20?style=for-the-badge&logo=django&logoColor=white" alt="Django 5.2.1">
  </a>
  <a href="#tech-stack">
    <img src="https://img.shields.io/badge/DRF-3.16-red?style=for-the-badge" alt="DRF 3.16">
  </a>
  <a href="#tech-stack">
    <img src="https://img.shields.io/badge/JavaScript-Vanilla-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black" alt="Vanilla JavaScript">
  </a>
</div>

<br>

<strong>Documentación:</strong>

<div>
  <a href="README.md">
    <img src="https://img.shields.io/badge/EN-English-0052B4?style=flat-square" alt="English">
  </a>
  <a href="README-es.md">
    <img src="https://img.shields.io/badge/ES-Español-AA151B?style=flat-square" alt="Español">
  </a>
</div>

<hr>


<h2 id="features">Funcionalidades Principales</h2>

<h3>Funcionalidades del E-commerce</h3>
<ul>
  <li><strong>Catálogo de Productos</strong> organizado por categorías, subcategorías y marcas</li>
  <li><strong>Carrito de Compras</strong> gestionado por sesiones de usuario</li>
  <li><strong>Sistema de Pedidos</strong> con seguimiento de estados</li>
  <li><strong>Autenticación</strong> con sistema de roles (admin/usuario)</li>
  <li><strong>Panel de Administración</strong> completo con CRUD y métricas</li>
</ul>

<h3>Sistema de Pagos</h3>
<ul>
  <li><strong>Integración con Mercado Pago</strong> para procesamiento seguro de pagos</li>
  <li><strong>Importación Masiva</strong> desde archivos Excel usando OpenPyXL</li>
  <li><strong>Gestión de Imágenes</strong> mediante API externa (ImgBB) para almacenamiento</li>
</ul>

<h3>Arquitectura Hibrida</h3>
<ul>
  <li><strong>Renderizado en Servidor (SSR)</strong> para mejor SEO y carga inicial rápida</li>
  <li><strong>Actualizaciones en Tiempo Real del lado del cliente (CSR)</strong> mediante AJAX sin recargar la página</li>
  <li><strong>Diseño Responsive</strong> que se adapta a todos los dispositivos</li>
</ul>

<h3>Optimizaciones Implementadas</h3>
<ul>
  <li><strong>Consultas Optimizadas</strong> a la base de datos con joins inteligentes, selected_related y prefetch_related (ORM Django para Joins)</li>
  <li><strong>Sistema de Caché</strong> para mejorar tiempos de respuesta</li>
  <li><strong>Carga Diferida (Lazy)</strong> de imágenes para mejor performance</li>
</ul>

<!-- Stack -->
<h2 id="tech-stack">Stack Tecnológico</h2>


### Back-End
| [![Python Badge](https://img.shields.io/badge/python-%2314354C.svg?style=for-the-badge&logo=python&logoColor=white)](#features) | [![Django Badge](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=green)](#features) | [![DRF Badge](https://img.shields.io/badge/django%20rest-ff1709?style=for-the-badge&logo=django&logoColor=white)](#features) | [![PostgreSQL Badge](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](#features) |
|:-:|:-:|:-:|:-:|


###  Fornt-End
| [![HTML Badge](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)](#features) | [![JavaScript Badge](https://img.shields.io/badge/JavaScript-323330?style=for-the-badge&logo=javascript&logoColor=F7DF1E)](#features) | [![CSS Badge](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)](#features) | 
|:-:|:-:|:-:|


### Herramientas 
| [![Git Badge](https://img.shields.io/badge/git%20-%23F05033.svg?&style=for-the-badge&logo=git&logoColor=white)](#features) | [![GitHub Badge](https://img.shields.io/badge/github%20-%23121011.svg?&style=for-the-badge&logo=github&logoColor=white)](https://github.com/LucasCallamullo) |  [![Postman Badge](https://img.shields.io/badge/Postman-FF6C37?style=for-the-badge&logo=Postman&logoColor=white)](#features) |
|:-:|:-:|:-:|


### APIs e Integraciones
| [![MercadoPago](https://img.shields.io/badge/MercadoPago-00B1EA?style=for-the-badge&logo=mercadopago&logoColor=white)](#features) | [![ImgBB](https://img.shields.io/badge/ImgBB-Image%20Storage-00A3E0?style=for-the-badge&logo=imgbb&logoColor=white)](#features) | [![OpenPyXL](https://img.shields.io/badge/OpenPyXL-Excel%20Import-217346?style=for-the-badge&logo=microsoftexcel&logoColor=white)](#features) | [![REST API](https://img.shields.io/badge/REST%20API-Design-FF6B35?style=for-the-badge&logo=rest&logoColor=white)](#features) |
|:---:|:---:|:---:|:---:|


### Deploy
| [![Railway](https://img.shields.io/badge/Railway-131415?style=for-the-badge&logo=railway&logoColor=white)](#deployment) | [![Gunicorn](https://img.shields.io/badge/gunicorn-%298729.svg?style=for-the-badge&logo=gunicorn&logoColor=white)](#deployment) | [![Environment Variables](https://img.shields.io/badge/Environment%20Variables-Config-4A90E2?style=for-the-badge&logo=dotenv&logoColor=white)](#deployment) |
|:---:|:---:|:---:|

<p align="center"><em>Desplegado en <a href="#">Railway</a> con configuración lista para producción, actualmente fuera de servicio</em></p>


<hr>
<br>


<h2 id="demo">Demostración del Proyecto E-commerce</h2>

<p>
  <strong>Versión de demostración pública de la App</strong> - Plataforma de e-commerce full-stack desarrollada con Django y JavaScript vanilla.
</p>

<div align="center">
  <a href="https://youtu.be/v9cFwaaIpew" target="_blank">
    <img src="https://img.youtube.com/vi/v9cFwaaIpew/0.jpg" alt="E-commerce Demo Video" width="600" style="border-radius: 10px; border: 2px solid #333;">
  </a>
  <br><br>
  <a href="https://youtu.be/v9cFwaaIpew" target="_blank">
    <img src="https://img.shields.io/badge/Watch_on_YouTube-FF0000?style=for-the-badge&logo=youtube&logoColor=white" alt="Watch on YouTube">
  </a>
  <p><em>Haz clic en la imagen o botón para ver la demostración completa (incluye recorrido del panel de administración)</em></p>
</div>

<h3>Nota</h3>
<p>
  Este repositorio contiene los módulos públicos de una solución de e-commerce más amplia y privada. Algunas funcionalidades empresariales se mantienen en el código privado.
</p>



<h2 id="imagenes">Imágenes del E-commerce</h2>
<br>






<h2 id="contact">💻 Contacto Back-End Developer / Full-Stack Developer: </h2>

| [![GitHub Badge](https://img.shields.io/badge/github-%23121011.svg?&style=for-the-badge&logo=github&logoColor=white)](https://github.com/LucasCallamullo) | [![LinkedIn Badge](https://img.shields.io/badge/linkedin-%230077B5.svg?&style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/lucas-callamullo/) | [![YouTube Badge](https://img.shields.io/badge/YouTube%20-%23FF0000.svg?&style=for-the-badge&logo=YouTube&logoColor=white)](https://www.youtube.com/@lucas_clases_python) | [![Gmail Badge](https://img.shields.io/badge/Gmail-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:lucas.callamullo.dev@gmail.com) | [![Wsp Badge](https://img.shields.io/badge/WhatsApp-25D366?style=for-the-badge&logo=whatsapp&logoColor=white)](https://wa.me/5493515437688) |
|:---:|:---:|:---:|:---:|:---:|


