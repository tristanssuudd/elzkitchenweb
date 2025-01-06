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
function displayJsonAsParagraph(jsonResponse) {
    // Flatten the JSON response into a readable string
    const text = jsonToReadableString(jsonResponse);

    // Create a paragraph element
    const paragraph = document.createElement("p");
    paragraph.textContent = text;

    // Append the paragraph to the target container
    const container = document.getElementById("json-display");
    if (container) {
        container.innerHTML = ""; // Clear existing content
        container.appendChild(paragraph);
    } else {
        console.error("Container element not found.");
    }
}

// Utility function to turn JSON into a readable string
function jsonToReadableString(jsonObj, prefix = "") {
    let readableString = "";
    for (let key in jsonObj) {
        if (jsonObj.hasOwnProperty(key)) {
            const value = jsonObj[key];
            if (typeof value === "object" && value !== null) {
                // Recursively handle nested objects
                readableString += `${prefix}${key}: { ${jsonToReadableString(value, prefix + "  ")} } `;
            } else {
                readableString += `${prefix}${key}: ${value} `;
            }
        }
    }
    return readableString.trim();
}
/*
function fetchOrdersAndDisplay() {
    fetch('/products/query', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken') // CSRF protection if needed
        },
        body: JSON.stringify({
            "category": "Masakan Indonesia",
            "sort_by": 'price',
            "ascending": 'true'

        })
    })
    .then(response => response.json())
    .then(data => {
        if (data) {
            displayJsonAsParagraph(data);
        } else {
            console.error('No orders found or error fetching orders.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}
*/
function fetchOrdersAndDisplay() {
    fetch('/products/categories', {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCookie('csrftoken') // CSRF protection if needed
        },
        
    })
    .then(response => response.json())
    .then(data => {
        if (data) {
            displayJsonAsParagraph(data);
        } else {
            console.error('No orders found or error fetching orders.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}
function createProduct(){
    const formData = new FormData(document.getElementById('createProductForm'));
    fetch('/products/create', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken') // CSRF protection if needed
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data) {
            console.log(data)
        } else {
            console.error('No orders found or error fetching orders.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });

}
function fetchAndDisplayCategories(){
    fetch('/products/categories', {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCookie('csrftoken') // CSRF protection if needed
        },
        
    })
    .then(response => response.json())
    .then(data => {
        if (data) {
            const categorySelect = document.getElementById("category-select");
            data.forEach(category => {
                const option = document.createElement("option");
                option.value = category.id;  // Set the category ID as the value
                option.textContent = category.category;  // Set the category name as the text
                categorySelect.appendChild(option);
            });
        } else {
            console.error('No orders found or error fetching orders.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });

}

function init(){
    fetchOrdersAndDisplay();
    fetchAndDisplayCategories();
}
window.onload = init();