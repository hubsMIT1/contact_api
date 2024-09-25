import os
import sys
import django
from faker import Faker
import random

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contact_api.settings')

# Setup Django
django.setup()

# Now you can import your models
from users.models import User, Contact, SpamReport

fake = Faker()

def create_users(num_users):
    for _ in range(num_users):
        name = fake.name()
        phone_number = f'+91{fake.msisdn()[3:]}'
        email = fake.email()
        User.objects.create_user(name=name, phone_number=phone_number, email=email, password='password')

def create_contacts(num_contacts):
    users = User.objects.all()
    for user in users:
        for _ in range(num_contacts):
            name = fake.name()
            phone_number = f'+91{fake.msisdn()[3:]}'
            email = fake.email()
            Contact.objects.create(user=user, name=name, phone_number=phone_number, email=email)

def create_spam_reports(num_reports):
    users = User.objects.all()
    all_phone_numbers = list(Contact.objects.values_list('phone_number', flat=True)) + list(User.objects.values_list('phone_number', flat=True))
    
    for user in users:
        for _ in range(num_reports):
            phone_number = random.choice(all_phone_numbers)
            SpamReport.objects.get_or_create(reporter=user, phone_number=phone_number)

if __name__ == '__main__':
    print("Starting data population...")
    create_users(50)
    print("Users created.")
    create_contacts(20)
    print("Contacts created.")
    create_spam_reports(10)
    print("Spam reports created.")
    print("Data population completed.")