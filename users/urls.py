from django.urls import path, re_path
from .views import LoginAPIView, UserAPIView, SignOutView, RegisterAPIView

urlpatterns = [
    re_path(r"^auth/sign-in/?$", LoginAPIView.as_view(), name="sign-in"),
    re_path(r"^auth/sign-out/?$", SignOutView.as_view(), name="logout"),
    re_path(r"^auth/sign-up/?$", RegisterAPIView.as_view(), name="sign-up"),
    re_path(r"^user/me/?$", UserAPIView.as_view(), name="api-me"),
]
