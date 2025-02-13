function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
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

async function fetchOrders(page = 1, pageSize = 10) {
    const sortBySelect = document.getElementById('sort_by');
    const sortBy = sortBySelect ? sortBySelect.value : 'date_delivery'; 

    const requestData = {
        page: page,              // Current page number
        page_size: pageSize,     // Number of orders per page
        sort_by: sortBy,          // Sorting field from the <select>
        hide_concluded: true
    };

    fetch('/orders/query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify(requestData)
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json(); // Parse JSON response
        })
        .then(data => {
            const orders = data.orders; // Extract orders array
            renderOrders(orders); // Pass the resolved array to renderOrders
        })
        .catch(error => console.error('Error fetching orders:', error));
}
function rejectOrder(orderId) {
    if (!confirm(`Apakah anda yakin bahwa anda akan menolak pemesanan ini?`)) {
        return; 
    }
    fetch(`/orders/update-order/${orderId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({ status: 'REJ' })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Order telah ditolak.');
            location.reload();
        } else {
            alert('Error: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function getNextStatus(status) {
    const statusMap = {
        'ORD': 'APR',  // Ordered -> Approved
        'APR': 'PAID', // Approved -> Paid
        'PAID': 'FIN'  // Paid -> Finished
    };

    // Return the next status or null if no further status exists
    return statusMap[status] || null;
}
function getStatusActionLabel(status) {
    const statusMap = {
        'ORD': 'TERIMA PESANAN',  // Ordered -> Approved
        'APR': 'KONFIRMASI PEMBAYARAN', // Approved -> Paid
        'PAID': 'NYATAKAN SELESAI'  // Paid -> Finished
    };

    // Return the next status or null if no further status exists
    return statusMap[status] || null;
}


async function fetchCustomerPhoneNumber(orderId) {
    try {
        const response = await fetch(`/users/get_contact/${orderId}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const data = await response.json();
        console.log(data.phone_number);  // You can log the phone number here to confirm
        return data.phone_number; // The function will return the phone number here

    } catch (error) {
        console.error(`Failed to fetch phone number: ${error.message}`);
        return null; // Return null if there was an error
    }
}
function handleOrderContact(orderId) {
    fetchCustomerPhoneNumber(orderId)
        .then(phoneNumber => {
            console.log(phoneNumber);  // Now it will log the phone number

            const whatsappLink = `https://wa.me/${phoneNumber}`;
            const customerInfoContactLink = document.createElement('a');
            customerInfoContactLink.href = whatsappLink; // Set the href to the WhatsApp link
            customerInfoContactLink.target = '_blank'; // Open link in a new tab
            customerInfoContactLink.textContent = 'Hubungi pelanggan di whatsapp'; // Link text

            // Add the link to the DOM or wherever you need it
            const detailsDiv = document.getElementById(`details-${orderId}`);
            detailsDiv.appendChild(customerInfoContactLink);
        })
        .catch(error => {
            console.error('Error fetching phone number:', error);
        });
}
function advanceOrder(orderId, currentStatus){
    
    nextStatus = getNextStatus(currentStatus)
    if (!confirm(`Apakah anda yakin bahwa anda akan merubah status pemesanan dari (${getReadableStatus(currentStatus)}) menjadi (${getReadableStatus(nextStatus)})?`)) {
        return; 
    }
    fetch(`/orders/update-order/${orderId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({ status: nextStatus })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            //alert('Order telah ditolak.');
            refreshOrders;
        } else {
            alert('Error: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });

}
function formatStringNumberWithCommas(numberString) {
    const number = parseFloat(numberString); // Convert the string to a number
    if (isNaN(number)) {
        throw new Error("Invalid number string"); // Handle invalid input
    }
    return number.toLocaleString('en-US');
}
function renderOrders(orderData) {
    const container = document.getElementById("orders-manager-loader");
    container.innerHTML = ""; 
    console.log('Orders:', orderData);
    orderData.forEach(order => {
        // Create order card
        const orderCard = document.createElement("div");
        orderCard.classList.add("order-card");

        // Create details section
        const detailsDiv = document.createElement("div");
        detailsDiv.classList.add("order-card-details");
        detailsDiv.id = `details-${order.id}`;
        // Add order ID
        const orderId = document.createElement("p");
        orderId.textContent = `Order ID: ${order.id}`;
        detailsDiv.appendChild(orderId);

        const totalPrice = document.createElement("p");
        totalPrice.textContent = `Harga: Rp. ${formatStringNumberWithCommas(order.total_price)}`;
        totalPrice.style.fontWeight = 'bold';
        detailsDiv.appendChild(totalPrice);
        const orderStatus = document.createElement("p");
        orderStatus.textContent = `Status: ${getReadableStatus(order.status)}`;
        if (order.status == "REJ" || order.status == "CANC" ) {
            orderStatus.style.color = "red";

        } else if (order.status == "FIN") {
            orderStatus.style.color = "green";

        }

        detailsDiv.appendChild(orderStatus);

        // Add item preview
        const itemPreview = document.createElement("p");
        const items = order.order_items.slice(0, 3) // First 3 items
            .map(item => `${item.quantity}x ${item.product_name}`)
            .join(", ");
        itemPreview.textContent = items + (order.order_items.length > 3 ? ", ..." : "");
        detailsDiv.appendChild(itemPreview);


        const customerInfoCustomer = document.createElement("p");
        customerInfoCustomer.textContent = `Customer: ${order.customer}`;
        handleOrderContact(order.id);
        detailsDiv.appendChild(customerInfoCustomer);
        
        
        

        

        const customerInfoContact = document.createElement("p");
        
        customerInfoContact.textContent = `Contact: ${order.customer_contact}`;
        detailsDiv.appendChild(customerInfoContact);

        // Show All / Show Less toggle
        const showAllButton = document.createElement("button");
        showAllButton.classList.add("utility-button");
        showAllButton.textContent = "Lihat semua pesanan...";
        showAllButton.style.marginRight = "10px";
        showAllButton.onclick = function () {
            if (showAllButton.textContent === "Lihat semua pesanan...") {
                const fullItemList = order.order_items.map(item => `${item.quantity}x ${item.product_name}`).join(", ");
                itemPreview.textContent = fullItemList;
                showAllButton.textContent = "Lihat sekilas pesanan...";
            } else {
                const items = order.order_items.slice(0, 3)
                    .map(item => `${item.quantity}x ${item.product_name}`)
                    .join(", ");
                itemPreview.textContent = items + (order.order_items.length > 3 ? ", ..." : "");
                showAllButton.textContent = "Lihat semua pesanan...";
            }
        };
        detailsDiv.appendChild(showAllButton);

        // Add customer info
        

        // Append details to order card
        orderCard.appendChild(detailsDiv);

        if (order.status !== "CANC" && order.status !== "REJ" && order.status !== "FIN") {
            const orderActions = document.createElement("div");
            orderActions.classList.add("order-card-actions");
            
            const orderAdvanceAction = document.createElement("button");
            orderAdvanceAction.classList.add("generic-ok-button");
            orderAdvanceAction.textContent = getStatusActionLabel(order.status);
            orderAdvanceAction.onclick = function (){
                advanceOrder(order.id, order.status);
                refreshOrders();
            }
            orderActions.appendChild(orderAdvanceAction);
            
            const orderCancelAction = document.createElement("button");
            orderCancelAction.classList.add("generic-reject-button");

            orderCancelAction.textContent = "TOLAK";
            orderCancelAction.onclick = function () {
                rejectOrder(order.id); // Attach the rejectOrder function
            };
            orderActions.appendChild(orderCancelAction);

            orderCard.appendChild(orderActions);
        }
        // Append card to container
        container.appendChild(orderCard);
    });
}

function refreshOrders (){
    orders = fetchOrders();
    renderOrders(orders);
}

window.onload = refreshOrders();