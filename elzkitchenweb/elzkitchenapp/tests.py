from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from .models import Product, Orders, OrderItem
import json
import os

class TestUploadReceipt(TestCase):

    def setUp(self):
        # Create a test user and log them in
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.login(username='testuser', password='password')

        # Create a product and order for the user
        self.product = Product.objects.create(
            name='Test Product',
            preptime_days=2,
            preptime_hours=4,
            category='TestCategory',
            isAvailable=True,
            price=1000
        )
        self.order = Orders.objects.create(
            customer=self.user,
            date_ordered=timezone.now(),
            date_delivery=timezone.now() + timezone.timedelta(days=3),
            status=Orders.ORDERED
        )
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            orderItemMessage='Please deliver fast!'
        )

    def test_upload_receipt_image(self):
        # Specify the path to a dummy image (this needs to exist in your test environment)
        image_path = os.path.join(os.path.dirname(__file__), 'test_image.jpg')

        # Create a SimpleUploadedFile for simulating the upload
        with open(image_path, 'rb') as img:
            uploaded_file = SimpleUploadedFile(name='receipt.jpg', content=img.read(), content_type='image/jpeg')

        # Send a POST request to upload the image
        response = self.client.post(reverse('upload_receipt', args=[self.order.id]), {
            'receipt_image': uploaded_file
        })

        # Refresh the order to check if the image was added
        self.order.refresh_from_db()

        # Assertions to ensure the image was uploaded successfully
        self.assertEqual(response.status_code, 302)  # Assuming a redirect on success
        self.assertIsNotNone(self.order.receipt_image)  # Ensure the image was saved
        self.assertTrue(self.order.receipt_image.url.endswith('receipt.jpg'))  # Check that the correct file was uploaded


class AcceptOrderViewTest(TestCase):
    def setUp(self):
        # Set up test client and create a manager user
        self.client = Client()
        self.manager_user = User.objects.create_user(username='testmanager', password='password', )
        manager_group, created = Group.objects.get_or_create(name='manager')
        self.manager_user.groups.add(manager_group)
        # Assume is_manager checks for a staff status
        self.manager_user.is_staff = True
        self.manager_user.save()

        # Log in as the manager user
        self.client.login(username='testmanager', password='password')

        # Create a sample order
        self.product = Product.objects.create(
            name='Test Product',
            preptime_days=2,
            preptime_hours=4,
            category='TestCategory',
            isAvailable=True,
            price=1000
        )
        self.order = Orders.objects.create(
            customer=self.manager_user,
            date_ordered=timezone.now(),
            date_delivery=timezone.now() + timezone.timedelta(days=3),
            status=Orders.ORDERED
        )
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            orderItemMessage='Please deliver fast!'
        )

    def test_accept_order_success(self):
        response = self.client.post(reverse('accept_order', args=[self.order.id]))

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'success': True})

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Orders.ORDERED)

    def test_accept_order_invalid_request_method(self):
        response = self.client.get(reverse('accept_order', args=[self.order.id]))

        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'success': False})

    def test_accept_order_unauthorized_user(self):
        self.client.logout()
        regular_user = User.objects.create_user(username='regular_user', password='password')
        self.client.login(username='regular_user', password='password')

        response = self.client.post(reverse('accept_order', args=[self.order.id]))

        self.assertEqual(response.status_code, 302)  # User not authorizeds
class UpdateOrderViewTests(TestCase):

    def setUp(self):
        # Create customer and manager groups
        self.customer_group, _ = Group.objects.get_or_create(name='customer')
        self.manager_group, _ = Group.objects.get_or_create(name='manager')

        # Create a customer user and add to customer group
        self.customer_user = User.objects.create_user(username='customer', password='password')
        self.customer_user.groups.add(self.customer_group)

        # Create a manager user and add to manager group
        self.manager_user = User.objects.create_user(username='manager', password='password')
        self.manager_user.groups.add(self.manager_group)

        # Create a test order belonging to the customer user
        self.order = Orders.objects.create(
            customer=self.customer_user,
            date_ordered=timezone.now(),
            date_delivery=timezone.now() + timezone.timedelta(days=5),
            status=Orders.NOT_ORDERED
        )

        # Set up Django test client
        self.client = Client()

    def test_customer_can_update_delivery_date(self):
        # Authenticate as customer user
        self.client.login(username='customer', password='password')

        # Define payload to update the delivery date
        new_delivery_date = (timezone.now() + timezone.timedelta(days=10)).isoformat()
        response = self.client.put(
            reverse('update_order', args=[self.order.id]),
            data=json.dumps({'date_delivery': new_delivery_date}),
            content_type='application/json'
        )

        # Fetch updated order
        self.order.refresh_from_db()

        # Check response and updated field
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.order.date_delivery.isoformat(), new_delivery_date)
        self.assertEqual(response.json()['success'], True)

    def test_manager_can_reject_order_with_status_msg(self):
        # Authenticate as manager user
        self.client.login(username='manager', password='password')

        # Define payload to set status to REJECTED with a status_msg
        reject_reason = 'Order does not meet quality standards'
        response = self.client.put(
            reverse('update_order', args=[self.order.id]),
            data=json.dumps({'status': Orders.REJECTED, 'status_msg': reject_reason}),
            content_type='application/json'
        )

        # Fetch updated order
        self.order.refresh_from_db()

        # Check response and updated fields
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.order.status, Orders.REJECTED)
        self.assertEqual(self.order.status_msg, reject_reason)
        self.assertEqual(response.json()['success'], True)

    def test_customer_cannot_set_restricted_status(self):
        # Authenticate as customer user
        self.client.login(username='customer', password='password')

        # Attempt to set status to a restricted status (REJECTED)
        response = self.client.put(
            reverse('update_order', args=[self.order.id]),
            data=json.dumps({'status': Orders.REJECTED}),
            content_type='application/json'
        )

        # Check response and unchanged status
        self.order.refresh_from_db()
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.order.status, Orders.NOT_ORDERED)  # Original status remains unchanged
        self.assertEqual(response.json()['success'], False)
        self.assertIn('not allowed for your group', response.json()['error'])

    def test_invalid_json_request(self):
        # Authenticate as manager user
        self.client.login(username='manager', password='password')

        # Send an invalid JSON payload
        response = self.client.put(
            reverse('update_order', args=[self.order.id]),
            data='Invalid JSON',
            content_type='application/json'
        )

        # Check response for JSON decode error
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['success'], False)
        self.assertEqual(response.json()['error'], 'Invalid JSON')
