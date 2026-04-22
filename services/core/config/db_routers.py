# Router para enrutar modelos a diferentes bases de datos


class CoreRouter:
    """
    Router que dirige modelos a bases de datos especificas:
    MongoDB: Productos (Catalogo)
    PostgreSQL: Transacciones y Pedidos
    """

    # Para lecturas de modelos, determinar la base de datos a usar
    # Database.objects.all()
    def db_for_read(self, model, **hints):
        # Productos en MongoDB
        if model._meta.app_label == "api" and model._meta.model_name == "product":
            return "mongodb"
        # Default: Postgres
        return None

    # Para escrituras de modelos, determinar la base de datos a usar
    # Database.objects.create()
    def db_for_write(self, model, **hints):
        # Escrituras de productos a MongoDB
        if model._meta.app_label == "api" and model._meta.model_name == "product":
            return "mongodb"
        # Escrituras de transacciones a PostgreSQL
        return None

    def allow_relation(self, obj1, obj2, **hints):
        # Permitir relaciones solo entre modelos de la misma BD
        return None

    # Permitir migraciones solo en la base de datos correspondiente
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Migraciones de Product en MongoDB, resto en PostgreSQL
        if app_label == "api":
            if model_name == "product":
                return db == "mongodb"
            else:
                return db == "default"
        return None
