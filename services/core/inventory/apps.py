import os
from django.apps import AppConfig


class InventoryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "inventory"

    def ready(self):
        from mongoengine import connect

        connect(
            db=os.environ.get("CORE_MONGO_DB_NAME", "core_catalog"),
            host=os.environ.get("CORE_MONGO_HOST", "db-core-mongo"),
            port=int(os.environ.get("CORE_MONGO_PORT", 27017)),
            alias="default",
        )
