from django.http import HttpResponse
from django.views.decorators.http import require_GET


@require_GET
def robots_txt(request):
    """
    Vue pour servir robots.txt dynamiquement
    """
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /accounts/dashboard/",
        "Disallow: /vendors/dashboard/",
        "Disallow: /messages/",
        "Disallow: /projects/create/",
        "Disallow: /projects/*/edit/",
        "Disallow: /media/messages/",
        "Disallow: /static/",
        "",
        f"Sitemap: {request.scheme}://{request.get_host()}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")
