from django.urls import path

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from user.views import RegisterUserAPIView, MeAPIView

urlpatterns = [
    path("register/", RegisterUserAPIView.as_view(), name="user_register"),
    path("token/", TokenObtainPairView.as_view(), name="get_toket"),
    path("refresh-token/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", MeAPIView.as_view(), name="me"),
]

app_namy = "user"
