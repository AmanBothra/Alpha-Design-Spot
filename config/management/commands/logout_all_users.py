# your_app/management/commands/logout_all_users.py

from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

class Command(BaseCommand):
    help = 'Logs out all users by deleting sessions and blacklisting tokens.'

    def handle(self, *args, **options):
        # Delete all sessions
        Session.objects.all().delete()

        # Blacklist all outstanding tokens
        tokens = OutstandingToken.objects.all()
        for token in tokens:
            try:
                BlacklistedToken.objects.get(token=token)
            except BlacklistedToken.DoesNotExist:
                BlacklistedToken.objects.create(token=token)

        self.stdout.write(self.style.SUCCESS('Successfully logged out all users.'))
