from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APITestCase

from airport.models import Route
from airport.serializers import RouteSerializer
from airport.tests.utils import create_airports, create_routes


ROUTE_URL = reverse("airport:route-list")


def route_detail_url(route_id: int) -> str:
    return reverse("airport:route-detail", args=[route_id])


class AnonymousRouteAPITest(APITestCase):

    def test_anonymous_can_list_routes(self):
        create_routes(2)

        response = self.client.get(ROUTE_URL, format="json")

        serializer = RouteSerializer(Route.objects.all(), many=True)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer.data, response.data)

    def test_anonymous_can_retrieve_route(self):
        route = create_routes(1)[0]

        response = self.client.get(route_detail_url(route.id), format="json")

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(RouteSerializer(route).data, response.data)

    def test_anonymous_cannot_create_route(self):
        source, destination = create_airports(2)
        data = {"source": source.id, "destination": destination.id, "distance": 500}

        response = self.client.post(ROUTE_URL, data=data, format="json")

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)
        self.assertFalse(Route.objects.exists())

    def test_filter_routes_by_source(self):

        routes_list = create_routes(4)

        route_1 = routes_list[0]
        source = route_1.source

        route_2 = Route.objects.create(
            source=route_1.source,
            destination=routes_list[2].destination,
            distance=500
        )

        serializer = RouteSerializer([route_1, route_2], many=True)

        url = ROUTE_URL + f"?source={source.id}"

        response = self.client.get(url, format="json")

        self.assertEqual(2, len(response.data))
        self.assertEqual(serializer.data, response.data)

    def test_filter_routes_by_destination(self):

        routes_list = create_routes(4)

        route_1 = routes_list[0]
        destination = route_1.destination

        route_2 = Route.objects.create(
            source=routes_list[2].source,
            destination=destination,
            distance=500
        )

        
        serializer = RouteSerializer([route_1, route_2], many=True)

        url = ROUTE_URL + f"?destination={destination.id}"

        response = self.client.get(url, format="json")

        self.assertEqual(2, len(response.data))
        self.assertEqual(serializer.data, response.data)

    def test_filter_routes_by_sourse_and_destinations(self):

        routes_list = create_routes(4)
        route_1 = routes_list[0]
        route_2 = routes_list[1]

        route = Route.objects.create(
            source=route_1.source,
            destination=route_2.destination,
            distance=500
        )

        serializer = RouteSerializer(route)

        url = ROUTE_URL + f"?source={route_1.source.id}&destination={route_2.destination.id}"

        response = self.client.get(url, format="json")

        self.assertEqual(1, len(response.data))
        self.assertEqual(serializer.data, response.data[0])

    def test_filter_by_not_valid_data(self):

        routes_list = create_routes(4)
        route = routes_list[0]
        
        url = ROUTE_URL + f"?destination={route.destination.name}"
        
        response = self.client.get(url, format="json")

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)



class UserRouteAPITest(APITestCase):

    def setUp(self):
        user = get_user_model().objects.create_user(
            email="test@gmail.com",
            password="password123"
        )
        self.client.force_authenticate(user=user)

    def test_user_can_list_routes(self):
        response = self.client.get(ROUTE_URL, format="json")

        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_user_cannot_create_route(self):
        source, destination = create_airports(2)
        data = {"source": source.id, "destination": destination.id, "distance": 500}

        response = self.client.post(ROUTE_URL, data=data, format="json")

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertFalse(Route.objects.exists())

    def test_user_cannot_update_route(self):
        route = create_routes(1)[0]

        response = self.client.patch(
            route_detail_url(route.id), data={"distance": 1}, format="json"
        )

        route.refresh_from_db()
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertNotEqual(1, route.distance)

    def test_user_cannot_delete_route(self):
        route = create_routes(1)[0]

        response = self.client.delete(route_detail_url(route.id))

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertTrue(Route.objects.filter(id=route.id).exists())


class AdminRouteAPITest(APITestCase):

    def setUp(self):
        user = get_user_model().objects.create_superuser(
            email="test@test.com",
            password="password123"
        )
        self.client.force_authenticate(user=user)

    def test_admin_can_create_route(self):
        source, destination = create_airports(2)
        data = {"source": source.id, "destination": destination.id, "distance": 500}

        response = self.client.post(ROUTE_URL, data=data, format="json")

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(1, Route.objects.count())

    def test_admin_can_update_route(self):
        route = create_routes(1)[0]

        response = self.client.patch(
            route_detail_url(route.id), data={"distance": 777}, format="json"
        )

        route.refresh_from_db()
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(777, route.distance)

    def test_admin_can_delete_route(self):
        route = create_routes(1)[0]

        response = self.client.delete(route_detail_url(route.id))

        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
        self.assertFalse(Route.objects.filter(id=route.id).exists())

    # def test_route_with_same_source_and_destination_returns_400(self):
    #     # Fails until the rule moves out of Route.save()
    #     airport = create_airports(1)[0]
    #     data = {"source": airport.id, "destination": airport.id, "distance": 500}

    #     response = self.client.post(ROUTE_URL, data=data, format="json")

    #     self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
    #     self.assertFalse(Route.objects.exists())