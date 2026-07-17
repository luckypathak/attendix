from django.http import HttpResponse, Http404
from django.views.decorators.clickjacking import xframe_options_exempt
from attendix.apps.attendance.models import StoredFile

@xframe_options_exempt
def serve_database_file(request, path):
    try:
        # Search by suffix/path matching
        sf = StoredFile.objects.filter(name__endswith=path).first()
        if not sf:
            sf = StoredFile.objects.get(name=path)
        content_type = 'image/jpeg'
        if path.lower().endswith('.png'):
            content_type = 'image/png'
        elif path.lower().endswith('.gif'):
            content_type = 'image/gif'
        elif path.lower().endswith('.webp'):
            content_type = 'image/webp'
        return HttpResponse(sf.content, content_type=content_type)
    except Exception:
        raise Http404("File not found")
