class MavenReadReplicaRouter:
    def db_for_read(self, model, **hints):
        return "replica" if model._meta.app_label == "maven" else None

    def db_for_write(self, model, **hints):
        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        # Reads use the standby, but all related objects are written on the
        # primary; permit Django to construct those primary-side relations.
        # Django may combine an object loaded from the replica with a new
        # primary-side object while constructing an API write relation.
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return db == "default"
