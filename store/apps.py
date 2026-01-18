# store/apps.py
from django.apps import AppConfig
from django.db.models.signals import post_migrate

def create_default_category(sender, **kwargs):
    from .models import Category
    Category.objects.get_or_create(id=1, defaults={'name': '默认分类'})

class StoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'store'

    def ready(self):
        post_migrate.connect(create_default_category, sender=self)