from django.urls import path

from rest_framework_simplejwt.views import token_refresh, token_obtain_pair

from user.views import RegisterUserAPIView, MeAPIView

urlpatterns = [
    path("register/", RegisterUserAPIView.as_view(), name="user_register"),
    path("token/", token_obtain_pair, name="get_toket"),
    path("refresh-token/", token_refresh, name="refresh_token"),
    path("me/", MeAPIView.as_view(), name="me"),
]

app_name = "user"
