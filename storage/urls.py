
from django.urls import path, re_path
from .views import ResourceView, ResourceDownloadView, ResourceRenameMoveView, ResourceSearchView, DirectoryView

urlpatterns = [
    re_path(r"^resource/?$", ResourceView.as_view(), name = "resource"),
    re_path(r"^resource/download/?$", ResourceDownloadView.as_view(), name = "download"),
    re_path(r"^resource/move/?$", ResourceRenameMoveView.as_view(), name = "move"),
    re_path(r"^resource/search/?$", ResourceSearchView.as_view(), name = "search"),
    re_path(r"^directory/?$", DirectoryView.as_view(), name="directory"),

]

