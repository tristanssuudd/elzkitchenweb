function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

function submitDeliveryForm(event) {
    event.preventDefault();
    var button = event.target;
    const order_id = button.getAttribute('data-orderid')
    var deliveryTime = document.getElementById('delivery_time').value;
    var deliveryDate = document.getElementById('delivery_date').value;

    if (!deliveryDate || !deliveryTime) {
        alert("Tolong masukkan tanggal dan waktu pengantaran.");
        return;
    }
    var dateTimeString = `${deliveryDate}T${deliveryTime}`
    console.log(dateTimeString)
    
    var formData = {
        date_delivery: dateTimeString,
        status: 'ORD',
        csrfmiddlewaretoken: getCSRFToken()
    };

    
    fetch(`/orders/update-order/${order_id}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        // Handle success response
        window.location.href = "/user";
        //document.getElementById('response-message').innerText = 'Order submitted successfully!';
    })
    .catch(error => {
        // Handle error response
        //document.getElementById('response-message').innerText = 'Error submitting order: ' + error;
        console.error('Error:', error);
    });
}