function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}
let currentPage = 1;

function applyOrderHistoryFilters() {
    const status = document.getElementById("statusFilter").value;
    const customer = document.getElementById("customerFilter").value;
    const sortBy = document.getElementById("sortBy").value;

    console.log(status);
    filters = {
        'status' : status,
        'customer' : customer,
    }
    fetchOrderHistory(currentPage, 10, filters, sortBy)
        .then(data => updateOrderHistoryTable(data));
}

function prevPage() {
    if (currentPage > 1) {
        currentPage--;
        applyOrderHistoryFilters();
    }
}

function nextPage() {
    currentPage++;
    applyOrderHistoryFilters();
}

function updateOrderHistoryTable(data) {
    const tableBody = document.getElementById("orderHistoryTable").querySelector("tbody");
    tableBody.innerHTML = "";

    if (data.results.length === 0) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");
        cell.colSpan = 6;
        cell.textContent = "No order histories found.";
        row.appendChild(cell);
        tableBody.appendChild(row);
        return;
    }

    data.results.forEach(order => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${order.order_id}</td>
            <td>${order.customer}</td>
            <td>${order.total_price}</td>
            <td>${order.items}</td>
            <td>${order.date_completed}</td>
            <td>${order.status}</td>
        `;
        tableBody.appendChild(row);
    });

    // Update pagination controls
    document.getElementById("currentPage").textContent = `Page ${currentPage}`;
    document.getElementById("prevPage").disabled = currentPage === 1;
    document.getElementById("nextPage").disabled = data.results.length < 10;
}
function fetchOrderHistory(page = 1, itemsPerPage = 10, filters = {}, sortBy = '-date_completed') {
    const baseUrl = '/get_history';
    const urlParams = new URLSearchParams();

    urlParams.append('page', page);
    urlParams.append('items_per_page', itemsPerPage);

    if (sortBy) {
        urlParams.append('sort_by', sortBy);
    }

    for (const [key, value] of Object.entries(filters)) {
        if (value) {
            urlParams.append(key, value);
        }
    }

    const url = `${baseUrl}?${urlParams.toString()}`;

    return fetch(url, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken(),
        },
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        return response.json();
    })
    .then(data => {
        console.log('Order History Data:', data);
        return data;
    })
    .catch(error => {
        console.error('Error fetching order history:', error);
    });
}

function init(){
    applyOrderHistoryFilters();

}