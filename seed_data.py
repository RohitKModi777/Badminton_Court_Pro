import os
import django
from datetime import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'booking_system.settings')
django.setup()

from django.contrib.auth.models import User
from booking_app.models import Court, Equipment, Coach, PricingRule

def seed():
    print("Seeding data...")

    # 1. Create Courts
    courts = [
        {'name': 'Court A', 'court_type': 'INDOOR', 'is_active': True},
        {'name': 'Court B', 'court_type': 'INDOOR', 'is_active': True},
        {'name': 'Court C', 'court_type': 'OUTDOOR', 'is_active': True},
        {'name': 'Court D', 'court_type': 'OUTDOOR', 'is_active': True},
    ]
    for c in courts:
        Court.objects.get_or_create(name=c['name'], defaults=c)
    print("Courts seeded.")

    # 2. Create Equipment
    equipment = [
        {'name': 'Yonex Racket', 'equipment_type': 'RACKET', 'quantity_available': 10, 'rent_price_per_hour': 50},
        {'name': 'Badminton Shoes', 'equipment_type': 'SHOES', 'quantity_available': 10, 'rent_price_per_hour': 100},
    ]
    for e in equipment:
        Equipment.objects.get_or_create(name=e['name'], defaults=e)
    print("Equipment seeded.")

    # 3. Create Coaches
    coaches = [
        {
            'name': 'Coach John', 
            'hourly_rate': 500, 
            'availability_slots': {'Mon': ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00']}
        },
        {
            'name': 'Coach Sarah', 
            'hourly_rate': 600, 
            'availability_slots': {'Tue': ['14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '21:00']}
        },
        {
            'name': 'Coach Mike', 
            'hourly_rate': 450, 
            'availability_slots': {'Mon': ['10:00', '11:00'], 'Sun': ['10:00', '11:00']} # Simplified
        },
    ]
    for coach in coaches:
        Coach.objects.get_or_create(name=coach['name'], defaults=coach)
    print("Coaches seeded.")

    # 4. Pricing Rules
    PricingRule.objects.get_or_create(
        name="Standard Rule",
        defaults={
            'peak_start_time': time(18, 0),
            'peak_end_time': time(21, 0),
            'peak_multiplier': 1.5,
            'weekend_multiplier': 1.3,
            'indoor_court_multiplier': 1.4,
            'base_price': 500.00,
            'is_active': True
        }
    )
    print("Pricing Rules seeded.")

    # 5. Admin User
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@badminton.com', 'admin123')
        print("Admin user created.")
    else:
        print("Admin user already exists.")

if __name__ == '__main__':
    seed()
