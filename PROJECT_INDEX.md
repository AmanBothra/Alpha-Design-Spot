# Alpha Design Spot - Project Documentation Index

## Table of Contents
- [🏗️ Project Overview](#-project-overview)
- [📋 Quick Start Guide](#-quick-start-guide)
- [🔧 Architecture & Structure](#-architecture--structure)
- [📊 Database Models & Relationships](#-database-models--relationships)
- [🌐 API Endpoints Documentation](#-api-endpoints-documentation)
- [⚡ Background Processing](#-background-processing)
- [🔒 Authentication & Authorization](#-authentication--authorization)
- [📱 Frontend Integration](#-frontend-integration)
- [🛠️ Development Guidelines](#-development-guidelines)
- [📚 Resources & References](#-resources--references)

---

## 🏗️ Project Overview

**Alpha Design Spot** is a Django REST API platform for design content management and user interactions. The system provides a comprehensive solution for managing design templates, user subscriptions, and content delivery for design professionals and businesses.

### Core Features
- **User Management**: Customer registration, authentication, and profile management
- **Content Management**: Design templates, categories, events, and media files
- **Subscription System**: Plans, payments, and subscription tracking
- **Frame Management**: Customer-specific design frames with business categories
- **Background Processing**: Async task processing with Celery
- **Admin Dashboard**: Comprehensive admin interface with Jazzmin theme
- **Advanced Monitoring**: Real-time error tracking, performance monitoring, and business analytics

### Technology Stack
- **Backend**: Django 4.x, Django REST Framework
- **Database**: PostgreSQL with connection pooling
- **Caching**: Redis for sessions and caching
- **Background Tasks**: Celery with Redis broker
- **Authentication**: JWT with SimpleJWT
- **File Processing**: Auto WebP conversion
- **API Documentation**: Swagger/OpenAPI with drf-yasg
- **Error Tracking**: Sentry for advanced monitoring and performance tracking
- **Logging**: Comprehensive structured logging with real-time alerting

---

## 📋 Quick Start Guide

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- System dependencies: `memcached`, `ffmpeg`

### Setup Commands
```bash
# Install dependencies
pip install -r requirements.txt
sudo apt-get install memcached redis ffmpeg

# Environment setup
cp .env.example .env
# Configure .env variables

# Database setup
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

# Development server
python manage.py runserver

# Background services
celery -A config worker -l info
celery -A config beat -l info
celery -A config flower  # Monitoring
```

### Key URLs
- **API Documentation**: `/docs/` (Swagger UI)
- **Admin Panel**: `/admin/`
- **JWT Tokens**: `/api/token/`, `/api/token/refresh/`, `/api/token/verify/`

---

## 🔧 Architecture & Structure

### Directory Structure
```
Alpha-Design-Spot/
├── config/                    # Django configuration
│   ├── settings.py           # Main settings with optimizations
│   ├── urls.py               # Root URL configuration
│   ├── celery.py             # Celery configuration
│   ├── middleware.py         # Custom middleware
│   └── management/           # Management commands
│       └── commands/
│           ├── clear_cache.py
│           └── logout_all_users.py
├── app_modules/              # Application modules
│   ├── account/              # User management & auth
│   ├── post/                 # Content management
│   ├── master/               # Master data & references
│   └── website/              # Website functionality
├── lib/                      # Shared utilities
│   ├── models.py             # BaseModel with optimizations
│   ├── viewsets.py           # Custom DRF viewsets
│   ├── helpers.py            # File & image utilities
│   ├── constants.py          # Application constants
│   ├── renderer.py           # Custom API renderer
│   ├── paginator.py          # Custom pagination
│   └── filters.py            # Common filters
└── media/                    # User uploads
```

### Key Design Patterns
- **BaseModel**: Timestamp tracking with change detection optimization
- **Soft Delete**: User soft deletion with `is_deleted` and `deleted_at`
- **File Handling**: Auto WebP conversion for images
- **Connection Pooling**: PostgreSQL optimization for high load
- **Caching Strategy**: Redis-based caching for performance

---

## 📊 Database Models & Relationships

### Core Models Overview

#### Account Module (`app_modules/account/`)

**User Model** - Custom user with enhanced features
```python
# Key Fields: email (unique), user_type, whatsapp_number, no_of_post
# Features: Soft delete, JWT auth, custom manager
# Indexes: user_type+is_deleted, email+is_deleted, whatsapp_number
```

**CustomerFrame Model** - User design frames
```python
# Relations: User, BusinessCategory, CustomerGroup
# Features: Image conversion, group-based validation
# Indexes: customer+group, customer+profession_type
```

**Subscription Model** - Payment & plan management
```python
# Relations: User, CustomerFrame, Plan, PaymentMethod
# Features: Auto order numbering, date validation
# Indexes: user+end_date, end_date+is_active
```

#### Post Module (`app_modules/post/`)

**Category Model** - Hierarchical categories
```python
# Features: Self-referencing, banner images, featured flag
# Indexes: sub_category, is_active+is_featured
```

**Event Model** - Time-based events
```python
# Features: Date-based organization, thumbnails
# Indexes: event_date+event_type, event_date
```

**Post Model** - Main content
```python
# Relations: Event, CustomerGroup
# Features: File type handling, group association
# Indexes: event+group, file_type
```

#### Master Module (`app_modules/master/`)
- **Banner**: Homepage banners with URL links
- **BirthdayPost**: Special birthday templates
- **SplashScreen**: App startup screens
- **Tutorials**: Help content with video links

#### Website Module (`app_modules/website/`)
- **Enquiry**: Contact form submissions
- **Testimonial**: Client testimonials with images

### Database Relationships
```
User (1) ←→ (N) CustomerFrame ←→ (1) CustomerGroup
User (1) ←→ (N) Subscription ←→ (1) Plan
CustomerFrame (1) ←→ (N) Post ←→ (1) Event
Category (1) ←→ (N) OtherPost ←→ (1) CustomerGroup
```

### Performance Optimizations
- **Connection Pooling**: 20 connections, 10 overflow, 30min recycle
- **Indexes**: Strategic indexing on query patterns
- **Select Related**: Eager loading in querysets
- **Change Detection**: BaseModel saves only changed fields

---

## 🌐 API Endpoints Documentation

### Authentication Endpoints (`/api/auth/`)

**POST /api/auth/register/**
- Register new customers or admins
- Validates unique email and phone
- Auto-sets user_type based on request

**POST /api/auth/login/**
- JWT authentication with enhanced response
- Returns user profile data and profession types
- Optimized queries with caching

**POST /api/auth/logout/**
- Blacklists all user tokens
- Clears active sessions

**Password Reset Flow**
- `POST /api/auth/check-email/` - Verify email exists
- `GET /api/auth/send-otp/` - Send OTP via email
- `POST /api/auth/verify-otp/` - Verify OTP code
- `POST /api/auth/set-password/` - Update password

### User Management Endpoints

**CustomerFrame Management**
- `GET/POST/PUT/DELETE /api/auth/customer-frames/`
- Validation for post limits and display names
- Group-based post mapping updates

**Subscription Management**
- `GET/POST/PUT /api/auth/subscriptions/`
- Filters: `days_until_expiry`, `expired`, `active`
- Auto-calculates expiry status and days left

### Content Management (`/api/post/`, `/api/master/`)

**Post & Event Management**
- Category-based organization
- File type support (image/video)
- Group-based content filtering

**Master Data APIs**
- Banner management for homepage
- Tutorial content with video links
- App configuration data

### Response Format
All APIs use custom renderer with consistent structure:
```json
{
  "status": true,
  "message": "Success message",
  "data": { ... },
  "errors": null
}
```

---

## ⚡ Background Processing

### Celery Configuration
- **Broker**: Redis (`redis://localhost:6379/0`)
- **Backend**: Django database storage
- **Timezone**: Asia/Kolkata
- **Serialization**: JSON

### Task Categories
- **Email Tasks**: OTP sending, notifications
- **File Processing**: Image conversion, optimization
- **Data Sync**: Subscription updates, bulk operations

### Monitoring
- **Flower**: Web-based monitoring at default port
- **Database**: Task results stored in Django database
- **Logging**: Integrated with Django logging system

---

## 🔒 Authentication & Authorization

### JWT Configuration
- **Access Token**: 365 days lifetime
- **Refresh Token**: 365 days lifetime
- **Header**: `Authorization: Bearer <token>`
- **Blacklisting**: Manual logout support

### User Types & Permissions
- **customer**: Standard users with post limits
- **admin**: Full system access
- **is_verify**: Email verification status
- **soft_delete**: Account deactivation without data loss

### Security Features
- Password hashing with Django's built-in system
- Email-based OTP verification
- Token blacklisting on logout
- Input validation and sanitization

---

## 📱 Frontend Integration

### CORS Configuration
- **Allowed Origins**: 
  - `https://dashboard.alphawala.xyz`
  - `http://localhost:3000`
- **Custom Headers**: timezone, authorization
- **Credentials**: Supported for authenticated requests

### File Upload Handling
- **Auto WebP Conversion**: All images converted for optimization
- **Organized Storage**: Files organized by upload purpose
- **URL Generation**: Absolute URLs in API responses

### Mobile API Features
- **Dashboard API**: User-specific dashboard data
- **Profession Types**: Organized by business categories
- **Subscription Status**: Real-time expiry tracking

---

## 🛠️ Development Guidelines

### Code Standards
- **Models**: Inherit from `lib.models.BaseModel`
- **Viewsets**: Use `lib.viewsets.BaseModelViewSet`
- **Serializers**: Follow DRF conventions
- **File Handling**: Use `lib.helpers` utilities

### Database Best Practices
- **Migrations**: Always review before applying
- **Indexes**: Add indexes for frequent queries
- **Relationships**: Use select_related/prefetch_related
- **Soft Delete**: Implement for user data retention

### Testing Guidelines
- **Unit Tests**: Test model behavior and business logic
- **API Tests**: Test endpoints with various scenarios
- **Integration Tests**: Test complete workflows

### Performance Considerations
- **Query Optimization**: Use select_related, prefetch_related
- **Caching**: Implement Redis caching for frequent data
- **Connection Pooling**: Configured for high concurrency
- **File Optimization**: Auto WebP conversion for images

---

## 📚 Resources & References

### Configuration Files
- `config/settings.py` - Main Django configuration
- `CLAUDE.md` - Development environment guide
- `.env.example` - Environment variables template

### Key Libraries
- **Django REST Framework**: API development
- **SimpleJWT**: JWT authentication
- **dj-db-conn-pool**: Database connection pooling
- **django-redis**: Redis caching integration
- **drf-yasg**: API documentation
- **Jazzmin**: Enhanced admin interface

### External Services
- **Redis**: Caching and Celery broker
- **PostgreSQL**: Primary database
- **Email**: SMTP configuration for notifications

### Monitoring & Debugging
- **Django Debug Toolbar**: Development debugging
- **API Logging**: Request/response logging
- **Flower**: Celery task monitoring
- **Log Files**: `api_requests.log`, `api_errors.log`
- **Sentry**: Advanced error tracking and performance monitoring
- **Real-time Alerting**: Business intelligence and user journey tracking

---

## Development Workflow

### Local Development
1. Set up environment variables in `.env`
2. Run migrations and create superuser
3. Start development server
4. Start Celery worker and beat for background tasks
5. Use `/docs/` for API testing

### Database Management
- Use custom management commands for maintenance
- Monitor connection pool usage
- Regular backup of PostgreSQL database

### Performance Monitoring
- Monitor Redis memory usage
- Track database query performance
- Use Flower for Celery task monitoring

---

## 🔍 Advanced Monitoring & Error Tracking

### Sentry Integration
Our comprehensive Sentry implementation provides real-time monitoring and advanced error tracking:

#### Key Features
- **Real-time Error Tracking**: Immediate notification of application errors with detailed context
- **Performance Monitoring**: API response time tracking and bottleneck identification  
- **User Journey Tracking**: Multi-step process monitoring for UX optimization
- **Business Intelligence**: Conversion funnel analysis and feature usage metrics
- **Security Monitoring**: Enhanced threat detection and incident response

#### Monitoring Coverage
- Authentication flows (login, registration, logout)
- Business operations (post creation, updates, deletions)
- Background task processing (Celery jobs)
- Database operations and performance
- API endpoint response times

#### Documentation Files
- `SENTRY_MONITORING_GUIDE.md` - Comprehensive Sentry setup and usage guide
- `lib/sentry_utils.py` - Core Sentry utilities and context management
- `lib/sentry_monitoring.py` - Advanced monitoring features and business metrics
- `lib/logging_utils.py` - Enhanced logging with Sentry integration

---

*This documentation index provides a comprehensive overview of the Alpha Design Spot project with advanced Sentry monitoring integration. For detailed implementation examples and code references, see the respective module files and the SENTRY_MONITORING_GUIDE.md.*

*Last Updated: [Current Date]*  
*Project Version: 1.0*  
*Monitoring: Advanced Sentry Integration ✅*