from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from app_modules.account.models import User


class Command(BaseCommand):
    help = "Create test users for load testing"

    def handle(self, *args, **options):
        """Create test users for load testing"""
        test_users_data = [
            {
                "email": "test1@example.com",
                "name": "Test User 1",
                "whatsapp_number": "1234567890",
            },
            {
                "email": "test2@example.com",
                "name": "Test User 2",
                "whatsapp_number": "1234567891",
            },
            {
                "email": "test3@example.com",
                "name": "Test User 3",
                "whatsapp_number": "1234567892",
            },
            {
                "email": "test4@example.com",
                "name": "Test User 4",
                "whatsapp_number": "1234567893",
            },
            {
                "email": "test5@example.com",
                "name": "Test User 5",
                "whatsapp_number": "1234567894",
            },
        ]

        password = "testpass123"
        created_users = []

        for user_data in test_users_data:
            try:
                # Check if user already exists
                if User.objects.filter(email=user_data["email"]).exists():
                    self.stdout.write(f"✅ User {user_data['email']} already exists")
                    continue

                # Create user
                user = User.objects.create_user(
                    email=user_data["email"],
                    username=user_data["email"],
                    name=user_data["name"],
                    whatsapp_number=user_data["whatsapp_number"],
                    password=password,
                    user_type="customer",
                    is_verify=True,
                )

                created_users.append(user)
                self.stdout.write(self.style.SUCCESS(f"✅ Created user: {user.email}"))

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"❌ Error creating user {user_data['email']}: {e}"
                    )
                )

        self.stdout.write(f"\n🎉 Created {len(created_users)} new test users")
        self.stdout.write(f"Password for all test users: {password}")
        self.stdout.write("Test users ready for load testing!")
