import json
from django.core.management.base import BaseCommand
from faker import Faker
from django.utils import timezone
from django.contrib.auth.hashers import make_password

class Command(BaseCommand):
    help = 'Generates a fixture with fake data using Faker'

    def handle(self, *args, **kwargs):
        fake = Faker()
        data = []

        for _ in range(50):  # Number of fake entries to create
            profile_data = {
                "model": "myapp.userprofile",  # Replace with your app and model name
                "pk": _ + 1,
                "fields": {
                    "name": fake.name(),
                    "email": fake.email(),
                    "address": fake.address(),
                    "phone": fake.phone_number(),
                    "password": make_password(fake.password()),
                    "created_at": timezone.now().isoformat(),  # Add created_at field
                    "updated_at": timezone.now().isoformat(),  # Add updated_at field if needed
                }
            }
            data.append(profile_data)

        with open('myapp/fixtures/fake_userprofiles.json', 'w') as f:  # Specify the fixture file path
            json.dump(data, f, indent=4)

        self.stdout.write(self.style.SUCCESS('Fixture with fake data generated successfully'))
