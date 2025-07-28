# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Environment Setup

**Dependencies Installation:**
```bash
pip install -r requirements.txt
```

**Environment Configuration:**
- Copy `.env.example` to `.env` and configure environment variables
- Required services: PostgreSQL, Redis, Celery
- Install system dependencies: `sudo apt-get install memcached redis ffmpeg`

**Database Setup:**
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

**Development Server:**
```bash
python manage.py runserver
```

**Celery Worker (for background tasks):**
```bash
celery -A config worker -l info
```

**Celery Beat (for scheduled tasks):**
```bash
celery -A config beat -l info
```

**Flower (Celery monitoring):**
```bash
celery -A config flower
```

## Project Architecture

This is a Django REST API project for Alpha Design Spot, a platform for design content management and user interactions.

### Core Structure

**Configuration Layer (`config/`):**
- `settings.py`: Main Django settings with database connection pooling, JWT authentication, Celery, and Redis caching
- `urls.py`: Root URL configuration with API versioning and Swagger documentation
- `celery.py`: Celery configuration for background task processing
- `middleware.py`: Custom middleware including API logging

**Application Modules (`app_modules/`):**
- `account/`: User management, authentication, and user profiles
- `post/`: Content management including categories, events, and posts
- `master/`: Master data and reference tables
- `website/`: Website-specific functionality and content

**Shared Library (`lib/`):**
- `models.py`: BaseModel with timestamp tracking and change detection
- `helpers.py`: Utility functions for file handling and image processing
- `constants.py`: Application constants and choices
- `viewsets.py`: Custom DRF viewsets with enhanced functionality
- `renderer.py`: Custom API response renderer
- `paginator.py`: Custom pagination classes
- `filters.py`: Common filtering utilities

### Key Features

**Authentication & Authorization:**
- JWT-based authentication using SimpleJWT
- Custom User model extending AbstractUser with email as username
- User types and verification system
- Soft delete functionality for users

**Database Configuration:**
- PostgreSQL with connection pooling (dj-db-conn-pool)
- Redis for caching and session storage
- Database retry mechanism with configurable attempts and delays

**Background Processing:**
- Celery integration for async task processing
- Celery Beat for scheduled tasks
- Database-backed result storage

**API Features:**
- Django REST Framework with custom renderers
- Swagger/OpenAPI documentation via drf-yasg
- CORS configuration for frontend integration
- Custom pagination and filtering
- API request logging middleware

**Admin Interface:**
- Jazzmin-themed admin interface
- Custom branding and configuration
- Enhanced admin functionality

## Development Guidelines

**Database Models:**
- All models should inherit from `lib.models.BaseModel` for timestamp tracking
- Use soft delete pattern where applicable via `is_deleted` and `deleted_at` fields
- Follow Django naming conventions for model fields and methods

**API Development:**
- Use custom viewsets from `lib.viewsets` for consistent behavior
- Implement proper serializers in each app's `serializers.py`
- Use Django Filter backend for querystring filtering
- Follow RESTful naming conventions for endpoints

**File Handling:**
- Use helper functions from `lib.helpers` for file operations
- Image files are automatically converted to WebP format
- Use proper upload paths with the `rename_file_name` utility

**Background Tasks:**
- Define Celery tasks in each app's `tasks.py` file
- Use appropriate task decorators and error handling
- Consider task retry logic for external service calls

**Testing:**
- Test files are located in each app's `tests.py`
- Use Django's built-in testing framework
- Test both API endpoints and model behavior

## Environment Variables

Required environment variables (see `.env.example`):
- `DEBUG`: Development mode flag
- `DOMAIN` / `DOMAIN_IP`: Domain configuration
- `POSTGRES_*`: Database credentials and connection details
- `REDIS_HOST_URL`: Redis connection string
- `EMAIL_HOST_*`: SMTP email configuration
- `TIME_ZONE`: Application timezone (default: Asia/Kolkata)

## Management Commands

**Custom Django Commands (`config/management/commands/`):**
- `clear_cache`: Clear Redis cache
- `logout_all_users`: Force logout all authenticated users

**Usage:**
```bash
python manage.py clear_cache
python manage.py logout_all_users
```

## API Documentation

- Swagger UI: `/docs/`
- Admin Interface: `/admin/`
- JWT Token endpoints: `/api/token/`, `/api/token/refresh/`, `/api/token/verify/`

## Application URLs Structure

- `/api/auth/`: User authentication and account management
- `/api/master/`: Master data and reference information
- `/api/post/`: Content management and post operations
- `/api/website/`: Website-specific endpoints

## Debugging and Monitoring

- Django Debug Toolbar enabled in development
- API request/error logging configured
- Log files: `api_requests.log`, `api_errors.log`
- Flower available for Celery task monitoring

## Database Connection Pooling

The project uses connection pooling with the following configuration:
- Pool size: 10 persistent connections
- Max overflow: 5 additional connections
- Connection recycling: 3600 seconds (1 hour)
- Pool timeout: 30 seconds
- Statement timeout: 30 seconds