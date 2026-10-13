import time
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db.utils import OperationalError


class Command(BaseCommand):

    requires_system_checks = []

    def handle(self, *args, **options):

        n = 5
        seconds_wait = 5

        for _ in range(n):

            try:
                with connection.cursor():
                    print("DB is available!")
                    return
            except OperationalError as e:

                print("DB is unavailable, waiting 5 second...")
                time.sleep(5)
                print("Error: ", e)

        raise CommandError(f"DB is unavailable after {n} attempts.")
