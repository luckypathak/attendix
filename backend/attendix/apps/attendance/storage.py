from django.core.files.storage import Storage
from django.core.files.base import ContentFile
from django.utils.deconstruct import deconstructible
from django.apps import apps

@deconstructible
class DatabaseStorage(Storage):
    def _get_model(self):
        return apps.get_model('attendance', 'StoredFile')

    def _open(self, name, mode='rb'):
        StoredFile = self._get_model()
        try:
            sf = StoredFile.objects.get(name=name)
            return ContentFile(sf.content, name=name)
        except StoredFile.DoesNotExist:
            raise FileNotFoundError(f"File {name} not found.")

    def _save(self, name, content):
        StoredFile = self._get_model()
        content_bytes = content.read()
        StoredFile.objects.update_or_create(
            name=name,
            defaults={'content': content_bytes}
        )
        return name

    def exists(self, name):
        StoredFile = self._get_model()
        return StoredFile.objects.filter(name=name).exists()

    def url(self, name):
        from django.conf import settings
        if name.startswith('http://') or name.startswith('https://'):
            return name
        clean_name = name
        media_prefix = settings.MEDIA_URL.lstrip('/')
        if clean_name.startswith(media_prefix):
            clean_name = clean_name[len(media_prefix):].lstrip('/')
        return f"{settings.MEDIA_URL}{clean_name}"

    def delete(self, name):
        StoredFile = self._get_model()
        StoredFile.objects.filter(name=name).delete()
