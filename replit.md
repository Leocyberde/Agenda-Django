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

## Fresh GitHub Import Setup (October 04, 2025)
This project was freshly imported from GitHub and successfully configured for Replit:

**Setup Completed:**
- Python 3.12 module installed and verified
- All dependencies from requirements.txt installed successfully
- Database migrations applied successfully (56 migrations across all apps)
- Static files collected (127 static files + 12 unmodified)
- .gitignore configured with comprehensive Python patterns

**Workflow Configuration:**
- Name: "Django Server"
- Command: `python manage.py runserver 0.0.0.0:5000`
- Environment variables: Configured via Replit Secrets (secure)
- Server status: Running and operational ✅

**Environment Variables (via Replit Secrets):**
All sensitive credentials are now securely stored in Replit Secrets:
- SECRET_KEY: Django secret key
- MAIL_USERNAME: havyhost05@gmail.com
- MAIL_PASSWORD: Gmail app password for SMTP
- MERCADOPAGO_ACCESS_TOKEN: Mercado Pago API token
- MP_PUBLIC_KEY: Mercado Pago public key
- DJANGO_SUPERUSER_EMAIL: leolulu842@gmail.com
- DJANGO_SUPERUSER_PASSWORD: Admin password
- WEBHOOK_BASE_URL: https://e783855c-7522-4644-a9e3-de318795d823-00-b8fe9g56mi7n.worf.replit.dev

**Replit Domain:**
`e783855c-7522-4644-a9e3-de318795d823-00-b8fe9g56mi7n.worf.replit.dev`

**Webhook URL for Mercado Pago:**
`https://e783855c-7522-4644-a9e3-de318795d823-00-b8fe9g56mi7n.worf.replit.dev/payments/webhook/`

**Production Deployment Configured:**
- Deployment type: autoscale (for stateless Django web app)
- Build command: pip install + collectstatic + migrate
- Run command: gunicorn --bind=0.0.0.0:5000 --reuse-port salon_booking.wsgi:application
- Port: 5000 (only exposed port, not firewalled)

**Status:**
🟢 Development server operational
🟢 All dependencies installed
🟢 Database migrations applied
🟢 Static files served
🟢 Environment variables configured securely via Replit Secrets
🟢 Production deployment ready
🟢 Import setup completed successfully
