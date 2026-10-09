from rest_framework.generics import GenericAPIView
from rest_framework.mixins import CreateModelMixin, UpdateModelMixin, RetrieveModelMixin

from user.serializers import *

class CreateUserAPIView(
    GenericAPIView,
    CreateModelMixin,
    UpdateModelMixin,
    RetrieveModelMixin
):
    serializer_class = ...
    queryset = ...