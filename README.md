# 🏸 Badminton Court Pro - Smart Booking System

A production-ready Django badminton court booking system with intelligent pricing, real-time availability, waitlist management, and notifications.

---

## 🎯 Overview

**Badminton Court Pro** handles concurrent bookings, dynamic pricing, equipment rental, coach scheduling, and waitlist notifications using Django and Django REST Framework.

### Key Highlights

- **Atomic Booking System**: Race condition-free booking using database-level locking
- **Dynamic Pricing Engine**: Context-aware pricing based on time, day, and court type
- **Real-time Notifications**: HTMX-powered live updates
- **Production-Ready**: Configured for Render deployment with PostgreSQL

---

## ✨ Features

- **Smart Court Booking**: Real-time availability, hourly slots (9 AM - 10 PM), concurrent booking prevention
- **Dynamic Pricing**: Peak hours (1.5x), weekends (1.3x), indoor courts (1.4x), equipment & coach fees
- **Waitlist Management**: Automatic queue, 15-minute notification window
- **Real-time Notifications**: In-app alerts using HTMX
- **Equipment & Coach Management**: Inventory tracking, atomic updates, availability scheduling
- **User Dashboard**: View bookings, spending tracker, waitlist status

---

## 🛠 Technology Stack

**Backend**: Django 5.1.2, Django REST Framework 3.14.0, PostgreSQL/SQLite  
**Frontend**: Django Templates, HTMX 1.18.0, CSS  
**Deployment**: Gunicorn, WhiteNoise, Render, dj-database-url, python-dotenv

---

## 🏗 Architecture

### Service-Oriented Architecture

```
Views Layer (HTTP Handling)
    ↓
Services Layer (Business Logic)
  - booking_service: create_booking, cancel_booking, join_waitlist
  - pricing_service: calculate_price, get_breakdown
  - availability_service: check_court, check_coach, check_equipment
  - notification_service: create_notif, mark_as_read
    ↓
Models Layer (Database Schema)
```

### Core Models

- **Court**: Indoor/Outdoor courts with active status
- **BookingSlot**: Time slots with unique constraint (court, date, start_time)
- **Booking**: Links user, court, slot, equipment, coach
- **Equipment**: Inventory with atomic quantity updates
- **Coach**: JSON availability schedule
- **WaitlistEntry**: Queue position tracking
- **WaitlistNotification**: 15-minute expiration
- **PricingRule**: Configurable multipliers

### Concurrency Control

```python
@transaction.atomic
def create_booking(...):
    court = Court.objects.select_for_update().get(id=court_id)
    slot = BookingSlot.objects.select_for_update().get(...)
    equipment_list = Equipment.objects.select_for_update().filter(...)
    eq.quantity_available = F('quantity_available') - 1
```

---

## 📁 Project Structure

```
Badminton_Court_Pro/
├── booking_app/
│   ├── models.py, views.py, urls.py, admin.py, serializers.py
│   ├── services/
│   │   ├── booking_service.py, pricing_service.py
│   │   ├── availability_service.py, notification_service.py
│   ├── templates/, static/, migrations/
├── booking_system/
│   ├── settings.py, urls.py, wsgi.py, asgi.py
├── manage.py, requirements.txt, .env
├── build.sh, start.sh, render.yaml
├── seed_data.py, debug_slot.py
```

---

## 🚀 Setup & Installation

### Prerequisites
Python 3.10+, pip, Git, PostgreSQL (production) or SQLite (development)

### Quick Start

```bash
# 1. Clone & navigate
git clone <repo-url>
cd Badminton_Court_Pro

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
SECRET_KEY=<generate-key>
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=  # Empty for SQLite

# Generate secret key:
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# 5. Setup database
python manage.py migrate
python manage.py createsuperuser
python seed_data.py  # Optional sample data

# 6. Run server
python manage.py runserver
```

Visit: `http://127.0.0.1:8000`

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SECRET_KEY` | Django secret key | Yes | - |
| `DEBUG` | Debug mode | No | False |
| `ALLOWED_HOSTS` | Comma-separated hosts | No | localhost,127.0.0.1 |
| `DATABASE_URL` | PostgreSQL connection | No | SQLite |
| `ADMIN_CREATION_SECRET` | Admin endpoint secret | Production | - |
| `DEFAULT_ADMIN_USERNAME` | Admin username | Production | admin |
| `DEFAULT_ADMIN_EMAIL` | Admin email | Production | - |
| `DEFAULT_ADMIN_PASSWORD` | Admin password | Production | - |

### Security (Production)
When `DEBUG=False`: SSL redirect, secure cookies, HSTS, XSS filter, X-Frame-Options: DENY

---

## 🔍 How It Works

### Dynamic Pricing Example

```python
Base Price: ₹500
+ Indoor Court (40%): ₹200 → ₹700
+ Peak Hour (50%): ₹350 → ₹1,050
+ Weekend (30%): ₹315 → ₹1,365
+ Equipment: ₹100
+ Coach: ₹800
= Total: ₹2,265
```

### Waitlist Flow

```python
@transaction.atomic
def cancel_booking(booking_id):
    booking.booking_status = 'CANCELLED'
    slot.is_booked = False
    # Restore equipment quantities
    equipment.quantity_available = F('quantity_available') + 1
    # Notify next in waitlist
    next_waitlist = WaitlistEntry.objects.filter(
        requested_slot=slot, notified=False
    ).order_by('created_at').first()
    if next_waitlist:
        create_slot_available_notification(next_waitlist.user, slot)
```

### HTMX Real-time Updates

```html
<select name="court" hx-get="/calculate-price/" hx-trigger="change" hx-target="#price-display">
```
No JavaScript needed - HTMX sends request, server calculates, returns HTML fragment.

---

## 📡 API Endpoints

### Get Available Slots
```http
GET /api/slots/available/?date=2024-12-15
```

### Create Booking
```http
POST /api/bookings/create/
Authorization: Token <token>
{
  "court_id": 1,
  "date": "2024-12-15",
  "start_time": "18:00",
  "equipment_ids": [1, 2],
  "coach_id": 1
}
```

### Get Notifications
```http
GET /api/notifications/
Authorization: Token <token>
```

### Notification Count
```http
GET /api/notifications/count/
```

### Mark as Read
```http
POST /api/notifications/<id>/mark-read/
```

---

## 🚢 Deployment (Render)

### Steps

1. **Create PostgreSQL Database** on Render
2. **Create Web Service**, connect GitHub repo
3. **Set Environment Variables**:
   ```
   SECRET_KEY=<new-key>
   DEBUG=False
   DATABASE_URL=<postgres-url>
   ALLOWED_HOSTS=<app>.onrender.com
   ADMIN_CREATION_SECRET=<secret>
   DEFAULT_ADMIN_USERNAME=admin
   DEFAULT_ADMIN_EMAIL=admin@domain.com
   DEFAULT_ADMIN_PASSWORD=<password>
   ```
4. **Deploy** (build.sh → migrations, static files; start.sh → Gunicorn)
5. **Create Admin**: Visit `https://<app>.onrender.com/create-admin/?secret=<ADMIN_CREATION_SECRET>`

### Build Script
```bash
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
```

### Start Script
```bash
gunicorn booking_system.wsgi:application --bind 0.0.0.0:$PORT
```

---

## 📚 Learning Resources

### Explore the Code

1. **[models.py](file:///c:/Users/modiu/OneDrive/Desktop/bcourt/Badminton_Court_Pro/booking_app/models.py)**: Database schema, unique constraints
2. **[services/](file:///c:/Users/modiu/OneDrive/Desktop/bcourt/Badminton_Court_Pro/booking_app/services)**: Business logic (booking, pricing, availability, notifications)
3. **[views.py](file:///c:/Users/modiu/OneDrive/Desktop/bcourt/Badminton_Court_Pro/booking_app/views.py)**: HTTP handling, API endpoints, HTMX views
4. **[settings.py](file:///c:/Users/modiu/OneDrive/Desktop/bcourt/Badminton_Court_Pro/booking_system/settings.py)**: Production config, security, database

### Key Concepts

- Database Transactions (`@transaction.atomic`)
- Database Locking (`select_for_update()`)
- F() Expressions (atomic updates)
- Model Relationships (ForeignKey, ManyToMany)
- Django REST Framework (Serializers, APIView)
- HTMX Integration
- Environment Variables
- WhiteNoise (static files)

### Common Tasks

```python
# Add Court
from booking_app.models import Court
Court.objects.create(name="Court 3", court_type="INDOOR", is_active=True)

# Add Equipment
from booking_app.models import Equipment
Equipment.objects.create(name="Premium Racket", equipment_type="RACKET", 
                        quantity_available=10, rent_price_per_hour=150.00)

# Add Coach
from booking_app.models import Coach
Coach.objects.create(name="John Doe", hourly_rate=1000.00,
    availability_slots={"Mon": ["09:00", "10:00"], "Wed": ["18:00", "19:00"]})

# Update Pricing
from booking_app.models import PricingRule
rule = PricingRule.objects.first()
rule.peak_multiplier = 1.8
rule.save()
```

---

## 🤝 Contributing

Areas for improvement:
- Email/SMS notifications
- Payment gateway integration
- Booking export (PDF/CSV)
- Analytics dashboard
- Automated tests
- Celery for scheduled tasks

---

## 📄 License

MIT License

---

**Happy Coding! 🚀**
