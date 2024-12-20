# management/commands/clear_cache.py
from django.core.management.base import BaseCommand
from django.core.cache import cache
from django_redis import get_redis_connection

class Command(BaseCommand):
    help = 'Clears all Django caches'

    def handle(self, *args, **kwargs):
        try:
            # Clear default cache
            cache.clear()
            self.stdout.write('Cleared default cache\n')
            
            # Clear Redis cache
            get_redis_connection("default").flushall()
            self.stdout.write('Cleared Redis cache\n')
            
        except Exception as e:
            self.stderr.write(f'Error clearing cache: {str(e)}\n')