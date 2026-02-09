from django.shortcuts import render
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden, HttpResponseRedirect #for returning httpresponses duh
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.utils.decorators import method_decorator
from django.utils.dateparse import parse_datetime
from django.conf import settings
from django.db.models import Case, When, IntegerField, Q
from django.db import transaction
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from django.contrib.auth import views as auth_views
from django.contrib import messages
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.serializers import serialize
from .models import Product,ProductCategory, Orders, OrderItem, OrderMessage, UserProfile, OrderHistory, kitchenInfo
from .forms import UserRegistrationForm, ReceiptUploadForm, UserProfileForm
import json

## Globals

GLOBAL_SHOP_OPEN = None


### UTIL FUNCTIONS
def initialize_kitchen_status():
    global GLOBAL_SHOP_OPEN
    refresh_kitchen_status()

def refresh_kitchen_status():
    global GLOBAL_SHOP_OPEN
    print('kitchen status obtained in session')
    kitchen_status = kitchenInfo.objects.first()
    GLOBAL_SHOP_OPEN = kitchen_status.kitchenOpen if kitchen_status else False

def isKitchenOpen():
    global GLOBAL_SHOP_OPEN
    return GLOBAL_SHOP_OPEN
def get_standard_context(request):
    context = {
        'MEDIA_URL' : settings.MEDIA_URL,
        'user_authenticated': request.user.is_authenticated,
        'is_manager': is_manager(request.user)
    }
    return context
def get_user_cart_order(user):
    order = Orders.objects.filter(customer=user, status=Orders.NOT_ORDERED).first()
    return order
def build_cart_dict(user):
    cart = get_object_or_404(Orders, customer=user, status=Orders.NOT_ORDERED)
    order_items = cart.orderitem_set.all()

    order_data = []
    items_data = []
    for item in order_items:
        items_data.append({
            'product_id': item.product.id,
            'product_name': item.product.name,  # Assuming you want to include product name
            'quantity': item.quantity,
            'price' : item.product.price,
            'orderItemMessage': item.orderItemMessage,
        })
    order_data.append({
                'id': cart.id,
                'customer': cart.customer.username if cart.customer else None,
                'date_ordered': cart.date_ordered.isoformat(),
                'date_delivery': cart.date_delivery.isoformat(),
                'status': cart.status,
                'order_items': items_data,
            })
    return order_data
def is_manager(user):

    return user.groups.filter(name='manager').exists()

### SITES
def index(request):
    products = Product.objects.all()
    context = {'products': products,
               'user': request.user,
               }
    context.update(get_standard_context(request))
    return render(request, 'index.html', context)

def about(request):
    context = {}
    context.update(get_standard_context(request))
    return render(request, 'tentang.html', context)
@login_required
def checkout(request):
    if not isKitchenOpen():

        return JsonResponse({"error": "Toko sedang tutup"}, status=403)
    if not request.user.is_authenticated:
         redirect('login')
    else:

        order_data = build_cart_dict(request.user)[0]
        cart = order_data['order_items']
        context = {'cart':cart,
                   'order_id': order_data['id']}
        context.update(get_standard_context(request))
        return  render(request, 'checkout.html', context)
@login_required
def user_profile(request):
    if not request.user.is_authenticated :
        redirect('login')
    else:
        context = {}
        context.update(get_standard_context(request))
        return render(request, 'user_profile.html', context)

@login_required
def manager(request):
    if not is_manager(request.user):
        return redirect('index')
    context = {}
    context.update(get_standard_context(request))
    return render(request, 'admin_dashboard.html', context)

@login_required
@user_passes_test(is_manager)
def product_manager(request):
    context = {}
    context.update(get_standard_context(request))
    return render(request, 'product_manager.html', context)

@login_required
def history_viewer(request):
    context = {}
    context.update(get_standard_context(request))
    return render(request, 'history.html', context)
def whiteboard(request):
    context = {}
    context.update(get_standard_context(request))
    return render(request, 'whiteboard.html', context)
@login_required
@user_passes_test(is_manager)
def kitchen_settings(request):
    context = {}
    context.update(get_standard_context(request))
    return render(request, 'settings.html', context)
### Endpoints

def get_kitchen_status(request):
    try:
        global GLOBAL_SHOP_OPEN
        if GLOBAL_SHOP_OPEN:
            print(GLOBAL_SHOP_OPEN)
            return JsonResponse({'kitchen_status' : GLOBAL_SHOP_OPEN}, status=200)
        else:
            refresh_kitchen_status()
            return JsonResponse({'kitchen_status' : GLOBAL_SHOP_OPEN}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
@login_required
@user_passes_test(is_manager)
def toggle_kitchen_status(request):
    if request.method == "POST":
        kitchen_info, created = kitchenInfo.objects.get_or_create(id=1)  # Adjust if ID is not guaranteed
        kitchen_info.kitchenOpen = not kitchen_info.kitchenOpen

        toRead = kitchen_info.kitchenOpen
        kitchen_info.save()


        refresh_kitchen_status()
        #debug<
        print("Kitchen status updated. Status: ")
        print(toRead)
        #debug>

        return JsonResponse({
            "success": True,
            "kitchen_status": kitchen_info.kitchenOpen
        })

    # If not POST, return error
    return JsonResponse({"error": "Invalid request method"}, status=405)



@login_required
def get_kitchen_contact(request):
    try:
        kitchen_info = kitchenInfo.objects.first()
        if kitchen_info and kitchen_info.kitchenContact:
            return JsonResponse({'kitchenContact': kitchen_info.kitchenContact}, status=200)
        else:
            return JsonResponse({'error': 'Kitchen contact not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def get_history(request):
    if request.method == 'GET':
        try:
            # Determine if the user is a manager
            is_user_manager = is_manager(request.user)

            # Fetch all order history entries (managers get all, others filtered by user)
            order_history = OrderHistory.objects.all() if is_user_manager else OrderHistory.objects.filter(customer=request.user)

            # Apply filters
            status = request.GET.get('status')
            customer = request.GET.get('customer')
            print(status)

            if status:
                order_history = order_history.filter(status=status)
            if customer:
                order_history = order_history.filter(customer__username__icontains=customer)

            # Apply sorting
            sort_by = request.GET.get('sort_by', '-date_completed')  # Default sorting by most recent

            order_history = order_history.order_by(sort_by)

            # Pagination
            page = int(request.GET.get('page', 1))

            items_per_page = int(request.GET.get('items_per_page', 10))
            paginator = Paginator(order_history, items_per_page)
            paginated_order_history = paginator.get_page(page)

            # Serialize data
            data = [
                {
                    "order_id": entry.order_id,
                    "total_price": entry.total_price,
                    "items": entry.items,
                    "customer": entry.customer if entry.customer else "Unknown",
                    "date_completed": entry.date_completed.strftime('%Y-%m-%d %H:%M:%S') if entry.date_completed else None,
                    "status": entry.status,
                }
                for entry in paginated_order_history
            ]

            # Return response with pagination metadata
            response = {
                "page": page,
                "items_per_page": items_per_page,
                "total_pages": paginator.num_pages,
                "total_items": paginator.count,
                "results": data,
            }

            return JsonResponse(response, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)



@login_required
def get_cart(request):
    order_data = build_cart_dict(request.user)
    return JsonResponse(order_data, safe=False)

def custom_login_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            print("Hello")
            return HttpResponseRedirect('/login/')
        return view_func(request, *args, **kwargs)
    return wrapper



def add_to_cart(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'User not authenticated', 'redirect_url': '/login/'}, status=401)

    if request.method == "POST":


        data = json.loads(request.body)
        product_id = data.get('product_id')
        amount = int(data.get('amount', 1))
        msg = data.get('msg')

        shopping_cart, created = Orders.objects.get_or_create(
        customer=request.user,
        status=Orders.NOT_ORDERED,
        defaults={'date_ordered': timezone.now(), 'date_delivery': timezone.now() + timezone.timedelta(days=3), 'status_msg': ''}
        )
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return JsonResponse({'error': 'Product does not exist'}, status=404)

        existingOrderItem = OrderItem.objects.filter(order=shopping_cart, product=product).first()
        if existingOrderItem:
            existingOrderItem.quantity = amount
            existingOrderItem.save()
        else:
            OrderItem.objects.create(
                order=shopping_cart,
                product=product,
                quantity=amount,
                product_name = product.name,
                product_price = product.price,
                orderItemMessage=msg
            )
        return JsonResponse({'success': True}, status=200)
    else:
        JsonResponse({'success': False}, status=400)
@login_required
def delete_from_cart(request):
    if request.method == "POST":
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'User not authenticated'}, status=401)
        data = json.loads(request.body)
        product_id = data.get('product_id')

        product = get_object_or_404(Product, id=product_id )

        order = Orders.objects.filter(customer=request.user, status=Orders.NOT_ORDERED).first()
        if order:
            order_item = OrderItem.objects.filter(order = order, product = product).first()
            if order_item:
                order_item.delete()  # Delete the item from the cart
                return JsonResponse({'success': True, 'message': 'Item deleted from cart'}, status=200)
            else:
                return JsonResponse({'error': 'Product is not in the order'}, status=404)
        else:
            return JsonResponse({'error': 'Product is not in order or order does not exist.'}, status=404)


'''
JSON REQUEST FORMAT add_to_cart

    const requestData = {
        product_id: productId,
        amount: amount,
        msg: message
    };
    const response = await fetch('/your-add-to-cart-url/', { // Replace with the correct URL for your view
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken() // Include CSRF token if necessary
            },
            body: JSON.stringify(requestData)
        });
'''
def generate_order_items_summary(order_id):
    """
    Generate a human-readable summary of the order's items.
    """
    try:
        # Fetch order items for the given order_id
        order_items = OrderItem.objects.filter(order_id=order_id)
    except Exception:
        return "No items available"

    # Generate the summary string
    if not order_items.exists():
        return "No items available"

    item_descriptions = []
    for item in order_items:
        product_name = item.product_name
        quantity = item.quantity
        price = item.product_price
        item_descriptions.append(f"{quantity} x {product_name} at price of {price} each")

    return ", ".join(item_descriptions)

@login_required
def update_order(request, order_id):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            order = get_object_or_404(Orders, id=order_id)
            if 'date_delivery' in data:
                date_delivery = datetime.fromisoformat(data['date_delivery'])
                order.date_delivery = date_delivery
            if 'status_msg' in data:
                if is_manager(request.user):
                    order.status_msg = data['status_msg']
                else:
                    return JsonResponse({'success': False, 'error': f'Your group cannot edit this value.'}, status=403)
            if 'status' in data:

                allowed_status_by_group = {
                'customer': [Orders.CANCELLED, Orders.ORDERED],
                'manager': [Orders.APPROVED, Orders.REJECTED, Orders.PAID, Orders.FINISHED]
                }
                user_groups = request.user.groups.values_list('name', flat=True)
                for group, allowed_statuses in allowed_status_by_group.items():
                    if group in user_groups:
                        if data['status'] not in allowed_statuses:
                            return JsonResponse({'success': False, 'error': f'Status "{data["status"]}" not allowed for your group'}, status=403)
                        break
                else:
                    return JsonResponse({'success': False, 'error': 'You do not have permission to update this status'}, status=403)

                order.status = data['status']
                if data['status'] in [Orders.REJECTED, Orders.FINISHED, Orders.CANCELLED]:
                                    #write to order history
                    status_mapping = {
                        Orders.REJECTED: "REJECTED",
                        Orders.FINISHED: "FINISHED",
                        Orders.CANCELLED: "CANCELLED"
                    }

                    # Get the FinalStatus
                    FinalStatus = status_mapping.get(data['status'])  # Default to "Unknown" if no match is found

                    checkAndDeleteProducts(order)

                    OrderHistory.objects.create(
                        order_id=order.id,
                        total_price=get_order_total(order),
                        items=generate_order_items_summary(order.id),
                        customer=order.customer.username,
                        status=FinalStatus
                        )
                    order.delete()
                    return JsonResponse({'success': True, 'message': 'Order completed.'}, status=200)
            order.save()
            return JsonResponse({'success': True, 'message': 'Order updated successfully'}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

def checkAndDeleteProducts(order):
    order_items = order.orderitem_set.all()
    for order_item in order_items:
        product = order_item.product
        if not product:
            print("Product to delete not found.")
            return
        if product.isDeleted:
            other_order_items = OrderItem.objects.filter(
                product=product
            ).exclude(order=order)
            if not other_order_items.exists():
                product.delete()
                print(f"Product {product.name} (ID: {product.id}) has been fully deleted from the system.")
@login_required
def upload_receipt(request, order_id):
    order = Orders.objects.get(id=order_id, customer=request.user)  # Ensure user owns the order
    if request.method == 'POST':
        form = ReceiptUploadForm(request.POST, request.FILES, instance=order)
        if form.is_valid():
            form.save()  # Save the receipt image
            return redirect('index')  # Redirect to an order detail page or success page
    else:
        form = ReceiptUploadForm(instance=order)

    return render(request, 'upload_receipt.html', {'form': form, 'order': order})
'''
formData.append('receipt_image', file); // 'receipt_image' should match the field name expected in your form

// Additional fields, if needed
// formData.append('other_field_name', 'value'); // Add any extra fields as necessary

// Make an AJAX POST request to the upload_receipt view
fetch(`/your-upload-receipt-url/${orderId}/`, { // Replace with the correct URL and orderId
  method: 'POST',
  body: formData,
  headers: {
    'X-CSRFToken': getCSRFToken() // Include the CSRF token if your app uses CSRF protection
  }
})
.then(response => {
  if (!response.ok) {
    throw new Error('Network response was not ok');
  }
  return response.json();
})
.then(data => {
  console.log('Success:', data);
  // Handle success - you can redirect or update the UI as needed
})
.catch(error => {
  console.error('Error:', error);
  // Handle error - show an error message or take appropriate action
});

'''

@login_required
def get_receipt_image(request, order_id):
    # Check if the user is a manager
    if is_manager(request.user):
        # Managers can access any order by order_id
        order = get_object_or_404(Orders, id=order_id)
    else:
        # Non-managers can only access their own orders
        order = get_object_or_404(Orders, id=order_id, customer=request.user)

    # Check if the receipt image exists
    if order.receipt_image:
        # Return the receipt image URL
        return JsonResponse({'success': True, 'receipt_image_url': order.receipt_image.url})
    else:
        # If no receipt image exists, return an error message
        return JsonResponse({'success': False, 'error': 'Receipt image not found.'}, status=404)

def fetch_categories(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    categories = ProductCategory.objects.all()
    categories_data = []
    for category in categories:
        categories_data.append({
            'id': category.id,
            'category': category.category
        })

    return JsonResponse(categories_data, safe=False, status=200)

def get_products(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        # Parse the JSON body
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    category = body.get('category')  # Optional filter

    try:
        if category == '':
            category = None
        else:
            print("CATEGORY:" + category)
            category = ProductCategory.objects.get(id=category).category  # Adjust based on your model
            print(category)
    except ProductCategory.DoesNotExist:
        return JsonResponse({'error': 'Invalid category'}, status=400)
    sort_by = body.get('sort_by', 'price')  # Default sort by price
    ascending = body.get('ascending', 'true').lower() == 'true'  # Default ascending

    # Filter products by category if provided
    products = Product.objects.all()
    products = products.filter(isDeleted=False)
    if not is_manager(request.user):
        products = products.filter(isAvailable=True)
    if category:
        products = products.filter(category__category=category)

    # Sort products
    sort_order = '' if ascending else '-'
    if sort_by == 'price':
        products = products.order_by(f'{sort_order}price')


    # Manually serialize products
    product_data = []
    for product in products:
        product_data.append({
            'id': product.id,
            'name': product.name,
            'prep_time_days':product.preptime_days,
            'prep_time_hours': product.preptime_hours,
            'price': product.price,
            'is_Available' : product.isAvailable,
            'NAMessage' : product.NAmessage,
            'category': product.category.category,
            'category_id':product.category.id,
            'image_url': product.product_image.url if product.product_image else None,
        })

    return JsonResponse(product_data, safe=False, status=200)

@login_required
@user_passes_test(is_manager)
def create_product(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        category = request.POST.get('category') #id form
        isAvailable = request.POST.get('isAvailable') #boolean
        price = request.POST.get('price')
        productImage = request.FILES.get('image')
        if not name or not price:
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        if not category:
            category = 0
        if not isAvailable:
            isAvailable = False

        try:
            price = float(price)  # Convert price to float
        except ValueError:
            return JsonResponse({'error': 'Invalid price value'}, status=400)

        try:
            # Get the category object
            category = ProductCategory.objects.get(id=category)  # Adjust based on your model
        except ProductCategory.DoesNotExist:
            return JsonResponse({'error': 'Invalid category'}, status=400)

        product = Product(name=name, price=price, category=category, isAvailable = isAvailable)
        if productImage:
            product.product_image = productImage
        product.save()
        return JsonResponse({'success': 'Product created', 'id': product.id}, status=201)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

def get_product(request, product_id):
    if request.method == 'GET':
        product = get_object_or_404(Product, id=product_id)
        productData = {
            'id' :product_id,
            'name':product.name,
            'price':product.price,
            'category':product.category.category,
            'category_id':product.category.id,
            'isAvailable':product.isAvailable,
            'image':product.product_image.url if product.product_image else None,
        }
        return JsonResponse(productData, safe=False, status=200)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)
@login_required
@user_passes_test(is_manager)
def update_product(request, product_id):
    if request.method == 'POST':
        print('updating product...')
        name = request.POST.get('name')
        print('newname= '+name)
        category = request.POST.get('category') #id form
        isAvailable = request.POST.get('isAvailable', False) #boolean
        price = request.POST.get('price')
        productImage = request.FILES.get('image')
        NAmessage = request.POST.get('NAMessage')

        product = get_object_or_404(Product, id=product_id)
        with transaction.atomic():
            if name:
                product.name = name
            if category:
                product.category = ProductCategory.objects.get(id=category)
            if isAvailable:
                print("#DEBUG: Availability status change detected.")
                order_items_to_delete = OrderItem.objects.filter(product=product, order__status__in=[Orders.ORDERED, Orders.NOT_ORDERED])
                affected_orders = set(order_items_to_delete.values_list('order_id', flat=True))
                order_items_to_delete.delete()
                print(f'#DEBUG: OrderItems with Product {product.name} has been deleted.')

                #TO_IMPLEMENT: Notify users of availability change

                orders_to_check = Orders.objects.filter(id__in=affected_orders, status=Orders.ORDERED)
                for order in orders_to_check:
                    if not order.orderitem_set.exists():  # If no OrderItems left
                        print(f'#DEBUG: Order ID {order.id} has been deleted as it has no remaining OrderItems.')
                        order.delete()
                product.isAvailable = isAvailable
                product.NAmessage = NAmessage
            if price:
                product.price = price
                order_items_to_modify = product.orderitem_set.filter(order__status__in=[Orders.NOT_ORDERED, Orders.ORDERED])
                for order_item in order_items_to_modify:
                    order_item.product_price = price
                    order_item.save()
                print(f'#DEBUG: Updated price for {order_items_to_modify.count()} order items.')
                #TO_IMPLEMENT: Notification for price change
            if productImage:
                product.product_image = productImage
            product.save()
            return JsonResponse({'success': 'Product updated', 'id': product.id}, status=201)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
@user_passes_test(is_manager)
def delete_product(request, product_id):
    if request.method == 'DELETE':
        try:
            product = Product.objects.get(id=product_id)

            with transaction.atomic():
                product.isDeleted = True
                product.save()

                #Delete only orderItem with order status NORD or ORD then check if corresponding order is empty, delete if empty
                order_items_to_delete = OrderItem.objects.filter(product=product, order__status__in=[Orders.ORDERED, Orders.NOT_ORDERED])
                if order_items_to_delete.exists():

                    affected_orders = set(order_items_to_delete.values_list('order_id', flat=True))
                    order_items_to_delete.delete()
                    print(f'#DEBUG: OrderItems with Product {product.name} has been deleted.')

                    orders_to_check = Orders.objects.filter(id__in=affected_orders, status=Orders.ORDERED)
                    for order in orders_to_check:
                        if not order.orderitem_set.exists():  # If no OrderItems left
                            print(f'#DEBUG: Order ID {order.id} has been deleted as it has no remaining OrderItems.')
                            order.delete()


                order_items_to_delete = product.orderitem_set.all()
                if order_items_to_delete.exists():
                    return JsonResponse({'success': f'Product {product.name} has been marked for deletion but still present in active orders.'}, status=200)
                else:
                    product.delete()
                    return JsonResponse({'success': f'Product {product.name} has been is not present in any orders and have been fully deleted.'}, status=200)

            #TO_IMPLEMENT: Notifiy corresponding users


        except Product.DoesNotExist:
            return JsonResponse({'error': f'Product with ID {product_id} not found.'}, status=404)
        except Exception as e:
             return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)




@login_required
def add_order_message(request, order_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        order = get_object_or_404(Orders, id=order_id)
        message = data.get('message')

        if message:
            OrderMessage.objects.create(
                order=order,
                sender=request.user,
                message=message,
            )
            return JsonResponse({'success': True, 'message': 'Message added successfully'}, status=201)
        else:
            return JsonResponse({'success': False, 'error': 'Message content is required'}, status=400)

    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)
'''
const requestData = {
  message: messageContent,
};
fetch(`/your-add-order-message-url/${orderId}/`, { // Replace with the correct URL and orderId
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': getCSRFToken() // Include the CSRF token if your app uses CSRF protection
  },
  body: JSON.stringify(requestData) // Convert the data to a JSON string
})
.then(response => {
  if (!response.ok) {
    throw new Error('Network response was not ok');
  }
  return response.json();
})
.then(data => {
  console.log('Success:', data);
  // Handle success - you can update the UI or notify the user
})
.catch(error => {
  console.error('Error:', error);
  // Handle error - show an error message or take appropriate action
});
'''
@login_required
def get_order_messages(request, order_id):
   # Get the current user
    user = request.user

    # Fetch the order, with different access rules for manager and non-manager
    if is_manager(user):
        # Manager has access to all orders
        order = get_object_or_404(Orders, id=order_id)
    else:
        # Non-manager can only access orders where they are the customer
        order = get_object_or_404(Orders, id=order_id, customer=user)

    # Get all messages related to the order
    messages = OrderMessage.objects.filter(order=order).order_by('-timestamp')

    # Set up pagination
    page_number = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', 10)
    paginator = Paginator(messages, page_size)
    page_messages = paginator.get_page(page_number)

    # Prepare the data for JSON response
    message_data = [
        {
            'id': message.id,
            'sender': message.sender.username,
            'message': message.message,
            'timestamp': message.timestamp.isoformat()
        }
        for message in page_messages
    ]

    # Create the response object
    response_data = {
        'total_messages': paginator.count,
        'total_pages': paginator.num_pages,
        'current_page': page_messages.number,
        'messages': message_data
    }

    return JsonResponse(response_data, safe=False)
@login_required
def get_orders(request):
    if request.method == "POST":

        # Extract query parameters
        page_number = request.GET.get('page', 1)
        page_size = request.GET.get('page_size', 10)
        sort_by = request.GET.get('sort_by', 'date_delivery')

        # Validate sort_by parameter
        if sort_by not in ['date_delivery', 'customer', 'status', 'date_ordered']:
            return JsonResponse({'error': 'Invalid sort field'}, status=400)

        # Define custom ordering for statuses
        status_priority = Case(
            When(status='ORD', then=1),  # ORDERED first
            When(status='APR', then=2),  # APPROVED next
            When(status='PAID', then=3),  # PAID
            When(status='FIN', then=4),  # FINISHED
            When(status='REJ', then=5),  # REJECTED
            When(status='CANC', then=6),  # CANCELLED last
            default=7,  # Default for unknown statuses
            output_field=IntegerField()
        )

        # Check if the user is a manager
        user = request.user
        is_manager = user.groups.filter(name="manager").exists()
        # Filter orders based on user's permissions
        if is_manager:
            orders = Orders.objects.exclude(status='NORD')
        else:
            orders = Orders.objects.filter(customer=user).exclude(status='NORD')


        # Order the query results
        if sort_by == 'status':
            orders = orders.order_by(status_priority, 'date_delivery')
        else:
            orders = orders.annotate(status_priority=status_priority)
            orders = orders.order_by(sort_by)

        exclude_statuses = []
        if request.GET.get('hide_concluded', 'true').lower() == 'true':
            exclude_statuses.append('FIN')
            exclude_statuses.append('REJ')
            exclude_statuses.append('CANC')
        if exclude_statuses:
            orders = orders.exclude(status__in=exclude_statuses)
        # Paginate the results
        paginator = Paginator(orders, page_size)
        page_orders = paginator.get_page(page_number)

        # Structure the order data
        order_data = []
        for order in page_orders:
            order_items = order.orderitem_set.all()

            items_data = []
            for item in order_items:
                items_data.append({
                    'product_id': item.product.id,
                    'product_name': item.product_name,
                    'product_price': item.product_price,
                    'quantity': item.quantity,
                    'orderItemMessage': item.orderItemMessage,
                })
            receipt_url = order.receipt_image.url if order.receipt_image else None
            order_data.append({
                'id': order.id,
                'customer': order.customer.username if order.customer else None,
                'customer_contact' : get_customer_phone(order),
                'total_price':get_order_total(order),
                'receipt_url': receipt_url,
                'date_ordered': order.date_ordered.isoformat(),
                'date_delivery': order.date_delivery.isoformat(),
                'status': order.status,
                'order_items': items_data,
            })

        # Prepare and return JSON response
        response_data = {
            'total_orders': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page_orders.number,
            'orders': order_data,
        }

        return JsonResponse(response_data)
def get_order_total(order):
    # Calculate the total price by summing the price of all items in the order
    total_price = sum(item.product_price * item.quantity for item in order.orderitem_set.all())
    return total_price
def get_customer_phone(order):
    try:
        user_profile = UserProfile.objects.get(user=order.customer)
        phone_number = user_profile.phone_number
        return phone_number
    except UserProfile.DoesNotExist:
        return None

def get_user_phone_number(request, order_id):
    """
    GET endpoint to retrieve the user's phone number for a given order.
    """
    if request.method == "GET":
        # Fetch the order by ID, return 404 if not found
        order = get_object_or_404(Orders, id=order_id)

        # Use the helper function to get the phone number
        phone_number = get_customer_phone(order)

        if phone_number:
            return JsonResponse({
                "success": True,
                "phone_number": phone_number
            })
        else:
            return JsonResponse({
                "success": False,
                "message": "Phone number not found for the customer."
            }, status=404)

    return JsonResponse({
        "success": False,
        "message": "Invalid request method."
    }, status=405)




class CustomLoginView(auth_views.LoginView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add your custom context values
        custom_context = get_standard_context(self.request)
        context.update(custom_context)
        return context

def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        profile_form = UserProfileForm(request.POST, request.FILES)  # Handle file uploads

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)  # Do not save to DB yet
            if user_form.cleaned_data['password'] == user_form.cleaned_data['confirm_password']:
                user.set_password(user_form.cleaned_data['password'])  # Hash the password
                user.save()  # Now save the user

                customer_group = Group.objects.get(name='customer')  # Get the "customer" group
                user.groups.add(customer_group)  # Add the user to the group
                # Now create the UserProfile
                profile = profile_form.save(commit=False)
                profile.user = user
                profile.save()

                messages.success(request, 'Your account has been created successfully!')
                return redirect('login')  # Redirect to login or any other page
            else:
                messages.error(request, 'Please fix the errors below.')
    else:
        user_form = UserRegistrationForm()
        profile_form = UserProfileForm()
    context = {'user_form': user_form, 'profile_form': profile_form}
    context.update(get_standard_context(request))
    return render(request, 'registration/register.html', context)


