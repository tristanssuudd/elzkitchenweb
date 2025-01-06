from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class ProductCategory(models.Model):
    category = models.CharField(max_length=20)

class Product(models.Model):
    name = models.CharField(max_length=64)
    preptime_days = models.IntegerField(default=0) # Shopping cart delivery date must be more than amount of days preptime
    preptime_hours = models.IntegerField(default=0)
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE)
    isAvailable = models.BooleanField(default=False)
    NAmessage = models.CharField(max_length=100, null=True, blank=True, default="Produk baru!")
    price = models.IntegerField(default=1000)
    product_image = models.ImageField(upload_to='products/', blank=True, default='placeholders/noImage.png')
    def __str__(self):
        return f'Product :{self.name}: with preptime (days) {self.preptime_days} and/or preptime (hours) {self.preptime_hours} of category {self.category} isAvailable?:{self.isAvailable}: Reason: {self.NAmessage}'


class Orders(models.Model):

    NOT_ORDERED = 'NORD'
    ORDERED = 'ORD'
    APPROVED = 'APR'
    REJECTED = 'REJ'
    PAID = 'PAID'
    FINISHED = 'FIN'
    CANCELLED = 'CANC'

    STATUS_CHOICES = [
        (NOT_ORDERED, 'NOT_ORDERED'),
        (ORDERED, 'ORDERED'),
        (APPROVED, 'APPROVED'),
        (REJECTED, 'REJECTED'),
        (CANCELLED, 'CANCELLED'),
        (PAID, 'PAID'),
        (FINISHED, 'FINISHED'),
    ]
    customer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    date_ordered = models.DateTimeField()
    date_delivery = models.DateTimeField()
    status = models.CharField(
        max_length=4,
        choices=STATUS_CHOICES,
        default=NOT_ORDERED,
    )
    receipt_image = models.ImageField(upload_to='receipts/', null=True, blank=True)
    status_msg = models.CharField(max_length=150, null=True, blank=True)
    def __str__(self):
        return f'Order ID:{self.id}: date ordered:{self.date_ordered}: requested delivery date:{self.date_delivery}: status: {self.status}'

class OrderHistory(models.Model):
    order_id = models.IntegerField()
    total_price = models.FloatField()
    items = models.TextField()
    customer = models.CharField(max_length=255, blank=True, null=True)
    date_completed = models.DateTimeField(auto_now_add=True)  # Salt: Record when the order was added to the history
    status = models.CharField(
        max_length=20,
        choices=[
            ('FINISHED', 'Finished'),
            ('REJECTED', 'Rejected'),
            ('CANCELLED', 'Cancelled')
        ],
        default='FINISHED'
    )
    class Meta:
        verbose_name = "Order History"
        verbose_name_plural = "Order Histories"

    def __str__(self):
        return f"Order History for Order ID: {self.order_id}"

class OrderItem(models.Model):
    order = models.ForeignKey(Orders, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    orderItemMessage = models.CharField(max_length=100)

class OrderMessage(models.Model):
    order = models.ForeignKey(Orders, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    # Add any additional fields you need

    def __str__(self):
        return f'{self.user.username} Profile'
class kitchenInfo(models.Model):
    kitchenContact = models.CharField(max_length=15, blank=True, null=True)
    kitchenOpen = models.BooleanField()

