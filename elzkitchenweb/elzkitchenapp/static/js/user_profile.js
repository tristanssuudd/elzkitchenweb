document.addEventListener('DOMContentLoaded', () => {
    fetchOrdersAndDisplay();
});

// Function to fetch orders and display them
function fetchOrdersAndDisplay() {
    fetch('/orders/query', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken') // CSRF protection if needed
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.orders) {
            displayOrders(data.orders);
        } else {
            console.error('No orders found or error fetching orders.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}
function getReadableStatus(statusCode) {
    const statusMapping = {
        'NORD': 'Belum dipesan',
        'ORD': 'Telah dipesan',
        'APR': 'Diterima',
        'REJ': 'Ditolak',
        'PAID': 'Telah dibayar',
        'FIN': 'Selesai',
        'CANC': 'Dibatalkan'
    };
    
    return statusMapping[statusCode] || 'Unknown Status';
}
// Function to display orders
function displayOrders(orders) {
    const ordersContainer = document.getElementById('orders-container');
    ordersContainer.innerHTML = ''; // Clear any existing content

    // Separate active and inactive orders
    const activeOrders = orders.filter(order => !['FIN', 'REJ', 'CANC'].includes(order.status));
    const inactiveOrders = orders.filter(order => ['FIN', 'REJ', 'CANC'].includes(order.status));

    // Function to create order elements
    const createOrderElement = (order) => {
        const orderCard = document.createElement('div');
        orderCard.className = `order-card ${['FIN', 'REJ', 'CANC'].includes(order.status) ? 'inactive-order' : 'active-order'}`;

        const orderTitle = document.createElement('h2');
        orderTitle.textContent = `Order ID: ${order.id}`;
        orderCard.appendChild(orderTitle);

        const orderStatus = document.createElement('p');
        orderStatus.textContent = `Status: ${getReadableStatus(order.status)}`;
        orderCard.appendChild(orderStatus);

        const dateOrdered = document.createElement('p');
        dateOrdered.textContent = `Date Ordered: ${new Date(order.date_ordered).toLocaleString()}`;
        orderCard.appendChild(dateOrdered);

        const dateDelivery = document.createElement('p');
        dateDelivery.textContent = `Delivery Date: ${new Date(order.date_delivery).toLocaleString()}`;
        orderCard.appendChild(dateDelivery);

        const itemsList = document.createElement('ul');
        order.order_items.forEach(item => {
            const itemElement = document.createElement('li');
            itemElement.innerHTML = `<strong>${item.product_name}</strong> - Quantity: ${item.quantity}`;
            if (item.orderItemMessage) {
                const message = document.createElement('p');
                message.textContent = `Message: ${item.orderItemMessage}`;
                itemElement.appendChild(message);
            }
            itemsList.appendChild(itemElement);
        });
        orderCard.appendChild(itemsList);

        if (order.status === 'ORD') {
            const cancelButton = document.createElement('button');
            cancelButton.className = 'generic-reject-button';
            cancelButton.textContent = 'Batalkan Order';
            cancelButton.setAttribute('data-order-id', order.id);
            cancelButton.addEventListener('click', () => cancelOrder(order.id));
            orderCard.appendChild(cancelButton);
        }

        return orderCard;
    };

    activeOrders.forEach(order => {
        const orderElement = createOrderElement(order);
        ordersContainer.appendChild(orderElement);
    });

    inactiveOrders.forEach(order => {
        const orderElement = createOrderElement(order);
        ordersContainer.appendChild(orderElement);
    });
}

function cancelOrder(orderId) {
    fetch(`/orders/update-order/${orderId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ status: 'CANC' })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Order telah dibatalkan.');
            location.reload();
        } else {
            alert('Error: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}