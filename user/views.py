from django.contrib.auth import get_user_model

from rest_framework.generics import CreateAPIView, RetrieveUpdateAPIView

from rest_framework.permissions import AllowAny, IsAuthenticated

from user.serializers import RegisterUserSerializer, MeSerializer


class RegisterUserAPIView(CreateAPIView):
    serializer_class = RegisterUserSerializer
    permission_classes = (AllowAny,)


class MeAPIView(RetrieveUpdateAPIView):
    serializer_class = MeSerializer
    queryset = get_user_model().objects.all()
    permission_classes = (IsAuthenticated,)

    def get_object(self, *args, **kwargs):
        return self.request.user
