class MavenReadReplicaRouter:
    def db_for_read(self, model, **hints):
        return "replica" if model._meta.app_label == "maven" else None

    def db_for_write(self, model, **hints):
        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        # Reads use the standby, but all related objects are written on the
        # primary; permit Django to construct those primary-side relations.
        if obj1._state.db == "default" or obj2._state.db == "default":
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return db == "default"
