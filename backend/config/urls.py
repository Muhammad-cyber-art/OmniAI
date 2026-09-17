"""OmniLab AI - Root URL Configuration"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework_simplejwt.views import TokenVerifyView

# Admin site branding
admin.site.site_header = "OmniLab AI Administration"
admin.site.site_title = "OmniLab AI Admin"
admin.site.index_title = "Welcome to OmniLab AI Control Panel"


@api_view(["GET"])
@permission_classes([AllowAny])
def api_root(request, format=None):
    """
    OmniLab AI - Root API Directory
    Interactive Browsable API navigation hub.
    """
    return Response(
        {
            "service": "OmniLab AI API v1",
            "documentation": "Explore platform domains, curriculum courses, virtual simulations, and billing.",
            "endpoints": {
                "auth": reverse("users:index", request=request, format=format),
                "domains": reverse("curriculum:domain_list", request=request, format=format),
                "courses": reverse("curriculum:course_list", request=request, format=format),
                "simulation_cases": reverse("simulation:case_list", request=request, format=format),
                "my_sessions": reverse("simulation:my_sessions", request=request, format=format),
                "billing_plans": reverse("billing:plan_list", request=request, format=format),
                "wallet": reverse("billing:wallet", request=request, format=format),
                "quota": reverse("billing:quota_status", request=request, format=format),
            },
        }
    )


api_v1_patterns = [
    # ── API Root ─────────────────────────────────────────────────────────────
    path("", api_root, name="api_root"),

    # ── Auth ─────────────────────────────────────────────────────────────────
    path("auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("auth/", include("apps.users.urls")),

    # ── Billing ───────────────────────────────────────────────────────────────
    path("billing/", include("apps.billing.urls")),

    # ── Curriculum ────────────────────────────────────────────────────────────
    path("curriculum/", include("apps.curriculum.urls")),

    # ── Simulation ────────────────────────────────────────────────────────────
    path("simulations/", include("apps.simulation.urls")),
]

urlpatterns = [
    path("", RedirectView.as_view(url="/api/v1/", permanent=False)),
    path("admin/", admin.site.urls),
    path("api-auth/", include("rest_framework.urls")),
    path("api/v1/", include(api_v1_patterns)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
