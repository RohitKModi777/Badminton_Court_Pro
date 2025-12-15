# Badminton Court Booking System

A robust booking system built with Django, DRF, and Bootstrap 5.

## Features
- **Atomic Booking**: Ensures no double bookings using database locks.
- **Dynamic Pricing**: Calculates price based on court type, time, and day.
- **Equipment & Coach**: Add-ons for bookings.
- **Admin Panel**: Full management of courts, inventory, and rules.
- **API**: REST API for all booking operations.

## Setup Instructions

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Initialize Database**:
   ```bash
   python manage.py migrate
   python seed_data.py
   ```

3. **Run Server**:
   ```bash
   python manage.py runserver
   ```

4. **Access Application**:
   - Frontend: http://127.0.0.1:8000/
   - Admin: http://127.0.0.1:8000/admin/ (User: `admin`, Pass: `admin123`)
   - API: http://127.0.0.1:8000/api/available-slots/?date=2025-12-15

## Architecture
- **Services**: Business logic in `booking_app/services/`.
- **Atomic Transactions**: Used in `booking_service.py` with `select_for_update`.
- **HTMX**: Used for dynamic price calculation on the frontend.

## API Documentation
- `GET /api/available-slots/?date=YYYY-MM-DD`: Get available slots.
- `POST /api/create-booking/`: Create a new booking.
