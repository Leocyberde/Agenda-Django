# Salon Booking System

## Overview
This Django-based salon booking system provides comprehensive functionality for salon management, appointment scheduling, user accounts, and subscriptions. It supports Portuguese localization and features a modern, responsive frontend with PWA capabilities. The system aims to streamline salon operations, enhance customer experience, and provide robust management tools, including a cancellation policy system with configurable fees and a product store.

## User Preferences
I prefer a clear and concise explanation style. When making changes, prioritize core functionality and maintain the existing architectural patterns. Please ask for confirmation before implementing significant structural changes or introducing new third-party libraries. Focus on delivering production-ready code with good performance and security.

## System Architecture
The project is built on Django and uses a modular application structure with dedicated apps for `accounts`, `appointments`, `core`, `salons`, and `subscriptions`.

**UI/UX Decisions:**
- **Frontend Frameworks:** Bootstrap 5.3.8, HTMX 2.0.7, and Chart.js 4.4.0 for an interactive user experience.
- **Design System:** Modern CSS design tokens, comprehensive dark/light mode support, and smooth transitions.
- **PWA Features:** Full Progressive Web App functionality including service worker, offline pages, app installation, and optimized icons.
- **Responsiveness:** Fully responsive design optimized for all device sizes.
- **Accessibility:** Full ARIA compliance, screen reader support, and keyboard navigation.

**Technical Implementations & Feature Specifications:**
- **Appointment Scheduling:** Robust system with conflict prevention, timezone awareness, and protections against race conditions using atomic transactions. Includes salon status controls.
- **Cancellation Policy:** Salons can configure cancellation policies with optional enablement, customizable penalty percentages (0-100%), and a configurable time limit before the appointment for penalty application. Tracks `CancellationFee` with payment status.
- **Product Store:** Comprehensive `Product` model with categories, prices, affiliate links, and images. Features an administrative panel for product management and a merchant dashboard section for product suggestions.
- **User Authentication:** Email and password-based login for salon owners. Registration process automatically creates a salon and assigns a trial subscription.
- **Localization:** System is localized for Portuguese (pt-br) and uses the America/Sao_Paulo timezone.
- **Deployment:** Configured for autoscale production deployment using Gunicorn.
- **Payment Integration:** Mercado Pago integration for processing payments, including webhooks for subscription activation and renewal.

**System Design Choices:**
- **Database:** SQLite for development. PostgreSQL with exclusion constraints is recommended for production.
- **Media Files:** Configured for file uploads with Pillow support. Salon and user profile photos are stored as URLFields.
- **Security:** All views are protected by authentication and access control. Service worker configured with secure caching strategies.
- **Performance:** Optimized with preconnect, lazy loading, and Core Web Vitals monitoring.

## External Dependencies
- **Django**: 5.2.6 (Web framework)
- **Pillow**: 11.3.0 (Image processing for file uploads)
- **asgiref**: 3.9.1 (ASGI support for Django)
- **sqlparse**: 0.5.3 (SQL parsing)
- **mercadopago**: 2.3.0 (Payment integration - PIX payments)
- **qrcode**: 8.2 (QR code generation)
- **gunicorn**: 23.0.0 (Production WSGI server)
- **psycopg2-binary**: PostgreSQL adapter
- **dj-database-url**: Database URL parser
- **whitenoise**: Static file serving

## Fresh GitHub Import Setup (October 05, 2025)
This project was freshly imported from GitHub and successfully configured for Replit:

**Setup Completed:**
- Python 3.12.11 installed and verified
- All dependencies from requirements.txt installed successfully
- Missing migration directories created (admin_panel, appointments, core, salons, subscriptions)
- Database migrations created and applied successfully (20+ migrations across all apps)
- Static files collected (127 static files + 12 unmodified)
- SQLite database initialized with all tables

**Workflow Configuration:**
- Name: "Django Server"
- Command: `python manage.py runserver 0.0.0.0:5000`
- Port: 5000 (webview mode)
- Server status: Running and operational ✅

**Render.yaml Fixed for Production Deployment:**
The render.yaml file was corrected to properly handle migrations during deployment:
- **buildCommand**: Now creates migrations, applies them, collects static files, and initializes admin
- **startCommand**: Only runs Gunicorn with 4 workers and 120s timeout
- **Environment Variables**: Added MERCADOPAGO_ACCESS_TOKEN, MP_PUBLIC_KEY, MAIL_USERNAME, MAIL_PASSWORD
- This fixes the migration errors that were occurring during Render deployment

**Replit Deployment Configuration:**
- Deployment type: autoscale (for stateless Django web app)
- Build command: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
- Run command: `gunicorn --bind=0.0.0.0:5000 --reuse-port --workers=4 --timeout=120 salon_booking.wsgi:application`
- Port: 5000 (only exposed port, not firewalled)

**Migration Issues Resolved:**
The project was missing migration directories for custom apps. This has been fixed:
1. Created migration directories with __init__.py files
2. Generated initial migrations for all apps (admin_panel, appointments, core, salons, subscriptions)
3. Applied all migrations successfully to SQLite database
4. Updated render.yaml to run makemigrations during build phase

**Status:**
🟢 Development server operational
🟢 All dependencies installed
🟢 Database migrations created and applied
🟢 Static files served
🟢 Render.yaml corrected for production deployment
🟢 Replit deployment configured
🟢 Import setup completed successfully
