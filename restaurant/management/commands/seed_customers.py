import json
from pathlib import Path
from django.core.management.base import BaseCommand
from restaurant.models import Customer, User
class Command(BaseCommand):
    help = 'Seed customer records from customers_corrected.json into the database.'

    def handle(self, *args, **options):
        json_path = Path(__file__).resolve().parents[3] / 'customers_corrected.json'

        if not json_path.exists():
            self.stderr.write(f'JSON file not found: {json_path}')
            return
        with json_path.open(encoding='utf-8') as file:
            customers = json.load(file)
        created = 0
        for index, item in enumerate(customers, start=1):
            username = f'customer_{index}'
            user = User.objects.filter(username=username).first()
            if user is None:
                user = User.objects.create_user(
                    username=username,
                    password='12345',
                    role='customer',
                    phone=item.get('phone', ''),
                )
            customer, customer_created = Customer.objects.get_or_create(
                user=user,
                defaults={
                    'full_name': item['full_name'],
                    'phone': item.get('phone', ''),
                    'address': item.get('address', ''),
                },
            )
            if not customer_created:
                customer.full_name = item['full_name']
                customer.phone = item.get('phone', '')
                customer.address = item.get('address', '')
                customer.save(update_fields=['full_name', 'phone', 'address'])
            if customer_created:
                created += 1
        total_customers = Customer.objects.count()
        self.stdout.write(self.style.SUCCESS(f'siderlangan klentlar qatorlar soni: {created} | umumiysi: {total_customers}') )
