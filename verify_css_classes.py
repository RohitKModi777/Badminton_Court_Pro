import os
import django
import requests
from bs4 import BeautifulSoup

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'booking_system.settings')
django.setup()

def verify_css():
    print("Starting CSS Verification...")
    
    session = requests.Session()
    base_url = "http://127.0.0.1:8000"
    
    # 1. Login
    print("Logging in...")
    login_url = f"{base_url}/accounts/login/"
    
    # Get CSRF token
    response = session.get(login_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']
    
    login_data = {
        'username': 'admin',
        'password': 'admin123',
        'csrfmiddlewaretoken': csrf_token
    }
    
    response = session.post(login_url, data=login_data, headers={'Referer': login_url})
    
    if response.status_code == 200 and "Dashboard" in response.text:
        print("Login successful (redirected to dashboard or similar).")
    elif response.url == f"{base_url}/dashboard/":
        print("Login successful (redirected to dashboard).")
    else:
        # It might have redirected to profile (404) but session is still valid
        print(f"Login response url: {response.url}")
        
    # 2. Fetch Booking Form
    print("\nFetching Booking Form...")
    booking_url = f"{base_url}/book/?date=2025-12-30"
    response = session.get(booking_url)
    
    if response.status_code != 200:
        print(f"Failed to fetch booking page. Status: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 3. Verify Time Slot Options
    print("\nVerifying Time Slot Dropdown...")
    time_select = soup.find('select', {'name': 'time'})
    if time_select:
        options = time_select.find_all('option')
        # Check the first few options (skipping the placeholder if it doesn't have classes)
        valid_options = [opt for opt in options if opt.get('value')]
        if valid_options:
            first_opt = valid_options[0]
            classes = first_opt.get('class', [])
            print(f"Found option: {first_opt.text.strip()}")
            print(f"Classes: {classes}")
            
            if 'bg-dark' in classes and 'text-white' in classes:
                print("SUCCESS: Time slot options have correct dark theme classes.")
            else:
                print("FAILURE: Time slot options missing dark theme classes.")
        else:
            print("No time slots found.")
    else:
        print("Time select element not found.")

    # 4. Verify Coach Dropdown
    print("\nVerifying Coach Dropdown...")
    coach_select = soup.find('select', {'name': 'coach'})
    if coach_select:
        options = coach_select.find_all('option')
        valid_options = [opt for opt in options if opt.get('value')]
        if valid_options:
            first_opt = valid_options[0]
            classes = first_opt.get('class', [])
            print(f"Found option: {first_opt.text.strip()}")
            print(f"Classes: {classes}")
            
            if 'bg-dark' in classes and 'text-white' in classes:
                print("SUCCESS: Coach options have correct dark theme classes.")
            else:
                print("FAILURE: Coach options missing dark theme classes.")
        else:
            print("No coaches found.")
    else:
        print("Coach select element not found.")

if __name__ == "__main__":
    verify_css()
