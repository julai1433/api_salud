class DatabaseRouter:
    """
    Router para manejar los modelos compartidos entre servicios
    """
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'pacientes':
            return 'pacientes_db'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'pacientes':
            return 'pacientes_db'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return True


class ExpedientesRouter:
    """
    Router para manejar los modelos compartidos entre servicios
    """
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'pacientes':
            return 'pacientes_db'
        return 'default'

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'pacientes':
            return 'pacientes_db'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'pacientes':
            return db == 'pacientes_db'
        return db == 'default'