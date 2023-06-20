from django.apps import AppConfig


class PostConfig(AppConfig):
    name = 'app_modules.post'
    
    def ready(self):
        import app_modules.post.singal
