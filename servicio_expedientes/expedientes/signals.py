from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import PacienteIndex
from django.conf import settings

@receiver(post_save)
def sync_paciente_index(sender, instance, created, **kwargs):
    """
    Sincroniza la creación de pacientes con el índice local
    """
    if created and sender._meta.model_name == 'paciente':
        try:
            PacienteIndex.objects.get_or_create(
                nss=instance.nss,
                defaults={'id_paciente': instance.id}
            )
        except Exception as e:
            print(f"Error al sincronizar paciente: {e}")