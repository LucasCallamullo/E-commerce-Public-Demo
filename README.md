

<h1 align="center">E-commerce Engine — Django & Docker</h1>

<div align='center'>
  <strong>Documentation:</strong>
  <a href="README.md">
    <img src="https://img.shields.io/badge/EN-English-0052B4?style=flat-square" alt="English">
  </a>
  <a href="README-es.md">
    <img src="https://img.shields.io/badge/ES-Español-AA151B?style=flat-square" alt="Español">
  </a>
</div>

<br>

<p>
  <strong>A full-stack e-commerce engine designed for rapid deployment and easy integration.</strong>
  Built with a focus on modularity, allowing businesses to launch fully-featured stores via bulk product uploads using Excel or CSV files. and a production-ready Docker stack.
</p>
<p>
  This platform integrates <strong>User Authentication</strong> (role-based), a <strong>Product Catalog</strong> with a favorites system, a persistent <strong>Shopping Cart</strong>, <strong>Order Management</strong>, and secure <strong>Payment Processing</strong> via Mercado Pago—all wrapped in a fully responsive design.
</p>


<div align="center">
  <a href="#features">Features</a> • 
  <a href="#tech-stack">Tech Stack</a> • 
  <a href="#technical-overview">Architecture</a> • 
  <a href="#demo">Demo Video</a> • 
  <a href="#contact">Contact</a>
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
  <h2>Features</h2>
  <h3>Core E-commerce</h3>
  <ul>
    <li><strong>Product Catalog:</strong> Dynamic organization with categories, subcategories, and brands.</li>
    <li><strong>Shopping Cart:</strong> Reliable session-based management to prevent data loss.</li>
    <li><strong>Order Workflow:</strong> Robust processing with real-time state management.</li>
    <li><strong>User Authentication:</strong> Secure system with role-based permissions (Customer/Staff).</li>
  </ul>
  <h3>Integration & Data</h3>
  <ul>
    <li><strong>Mercado Pago API:</strong> Production-ready payment gateway integration.</li>
    <li><strong>Bulk Product Load:</strong> Fast inventory setup using <strong>OpenPyXL</strong> for Excel/CSV processing.</li>
    <li><strong>Hybrid Rendering:</strong> Optimized for SEO via <strong>SSR</strong> while maintaining fluid <strong>AJAX</strong> interactions.</li>
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
  <h2>Technical Implementation & Architecture</h2>
  <p>
    This project is an E-commerce engine engineered for <strong>seamless deployment</strong>. The core concept is speed: any store can be fully configured in seconds by performing a <strong>Bulk Load</strong> of products through CSV or Excel files. 
  </p>
  <p>
    To achieve this, I built a <strong>Modular Monolith</strong> architecture that prioritizes low coupling and long-term scalability. The system is organized into a clean, layered structure:
  </p>
  <ul>
    <li><strong>Models & Repository (Django ORM):</strong> Robust data definition and optimized database access.</li>
    <li><strong>Service Layer:</strong> Centralized business logic for each module, keeping views "lean" and maintainable by decoupling logic from the request/response flow.</li>
    <li><strong>Controllers (Views):</strong> Efficient handling of user interactions and template rendering via an <strong>API-First</strong> approach using DRF.</li>
  </ul>
  <h3>Key Architectural Pillars</h3>
  <h4>DevOps & Performance</h4>
  <ul>
    <li><strong>Docker Compose:</strong> Multi-container orchestration (Django, Postgres, Redis, Nginx) for a portable stack.</li>
    <li><strong>Nginx Reverse Proxy:</strong>Configured to serve static and media files efficiently, adding a security layer and optimizing high-performance delivery.</li>
    <li><strong>Query Optimization:</strong> Solved N+1 query issues via <code>select_related</code> and <code>prefetch_related</code>.</li>
    <li><strong>Redis Caching:</strong> Strategy to cache expensive queries and pre-rendered fragments to minimize database load.</li>
  </ul>
  <h4>Database, Cache, Backups</h4>
  <ul>
    <li><strong>PostgreSQL:</strong> Selected for its <strong>ACID-compliance</strong>, ensuring 100% reliability in financial transactions (Orders & Payments) even during system failures.
    <ul>
      <li><strong>JSONB Integration:</strong> Utilized for storing complex, dynamic metadata from <strong>Mercado Pago API</strong> responses, allowing for flexible payment tracking without sacrificing performance.</li>
      <li><strong>Full-Text Search (FTS):</strong> Native implementation for high-performance product discovery and optimized filtering.</li>
    </ul>
    <li><strong>Redis Persistence:</strong> Configured with <em>Append Only File (AOF)</em> strategy to ensure session, query dicts, and cart data survive container restarts.</li>
    <li><strong>Bash Automation:</strong> Daily rotating backups for both DB and Media assets to prevent data loss.</li>
  </ul>
  <h4>SEO & UX Strategy</h4>
  <ul>
    <li><strong>Mobile-First Design:</strong> Responsive architecture with SSR and dynamic Meta Tags for high search engine ranking.</li>
    <li><strong>Core Web Vitals:</strong> Optimized through lazy loading and resource minification.</li>
  </ul>
</section>


<br>


<h2 id="scope">Project Scope & Commercial Value</h2>
<p>
  This repository represents the <strong>Public Core</strong> of a professional, production-ready e-commerce solution. It is designed to demonstrate a complete business flow, from user acquisition to payment fulfillment.
</p>
### The Core Workflow
The public version of this engine fully supports the primary e-commerce lifecycle:
1. **Discovery:** User registration and advanced product filtering.
2. **Selection:** Management of Favorites and a session-persistent Shopping Cart.
3. **Checkout:** Order creation with state management (Pending/Confirmed).
4. **Payment:** Deep integration with <strong>Mercado Pago</strong>, handling payment promises and real-time status updates.
<p>
  While this version is fully functional for the end-user journey, specialized administrative modules are reserved for the <strong>Private Enterprise Edition</strong> to protect proprietary business logic.
</p>

<blockquote>
  <strong>Note:</strong> The public core allows for the complete workflow described above. However, the private edition enhances the experience with custom-built administration panels that go beyond the standard Django Admin capabilities.
</blockquote>

<div align="center">
  <table>
    <tr>
      <th>Public Modules (Core)</th>
      <th>Private Modules (Private)</th>
    </tr>
    <tr>
      <td>
        <ul>
          <li>User Authentication</li>
          <li>Product Catalog & Favorites</li>
          <li>Shopping Cart Logic</li>
          <li>Order Processing</li>
          <li>Mercado Pago Integration</li>
        </ul>
      </td>
      <td>
        <ul>
          <li>Advanced Sales Dashboards</li>
          <li>Automated Audit Tracking</li>
          <li>Specialized CRM Tools</li>
          <li>Custom Admin UX/UI</li>
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


<h2 id="contact">💻 Contact Back-End Developer / Full-Stack Developer: </h2>

| [![GitHub Badge](https://img.shields.io/badge/github-%23121011.svg?&style=for-the-badge&logo=github&logoColor=white)](https://github.com/LucasCallamullo) | [![LinkedIn Badge](https://img.shields.io/badge/linkedin-%230077B5.svg?&style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/lucas-callamullo/) | [![YouTube Badge](https://img.shields.io/badge/YouTube%20-%23FF0000.svg?&style=for-the-badge&logo=YouTube&logoColor=white)](https://www.youtube.com/@lucas_clases_python) | [![Gmail Badge](https://img.shields.io/badge/Gmail-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:lucas.callamullo.dev@gmail.com) | [![Wsp Badge](https://img.shields.io/badge/WhatsApp-25D366?style=for-the-badge&logo=whatsapp&logoColor=white)](https://wa.me/5493515437688) |
|:---:|:---:|:---:|:---:|:---:|
