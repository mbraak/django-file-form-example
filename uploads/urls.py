from django.urls import path

from . import views

urlpatterns = [
    path("", views.DocumentListView.as_view(), name="document_list"),
    path("documents/new/", views.DocumentCreateView.as_view(), name="document_create"),
    path(
        "documents/<int:pk>/",
        views.DocumentDetailView.as_view(),
        name="document_detail",
    ),
    path("simple/", views.SimpleUploadView.as_view(), name="simple_upload"),
    # Not "s3_upload": django-file-form already uses that name for /s3upload/.
    path("s3/", views.S3UploadView.as_view(), name="s3_demo"),
    path(
        "accessibility/",
        views.AccessibilityDemoView.as_view(),
        name="accessibility",
    ),
]
