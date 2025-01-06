function add_to_cartButtonOnClick (event) {
    console.log("Hello");
    const button = event.target;
    const productId = button.getAttribute('data-id');
    const quantity = button.getAttribute('data-quantity');
    add_to_cart(productId, quantity);
}

function fetchCart() {
    fetch('/get_cart/')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data) {
                console.log(data[0].order_items);
                updateCartDisplay(data[0].order_items); // Update cart display with fetched cart data
            }
        })
        .catch(error => {
            console.error('Error fetching cart:', error);
        });
}

function add_to_cart(productId, quantity) {
    console.log(`Adding product ${productId} with quantity ${quantity} to cart.`);
    body = {
        product_id: productId,
        amount: quantity,
        msg : '',
    }
    fetch(`/orders/customer/add_to_cart`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(body)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        
        return response.json();
    })
    .then(data => {
        if (data.success) {
            console.log('Product added to cart:', data.cart);

            fetchCart();
        } else {
            console.error('Failed to add item to cart');
        }
    })
    .catch(error => {
        console.error('Error adding product to cart:', error);
    });
}
function delete_from_cart(productId){
    console.log(`Deleting product ${productId} from cart.`);
    body = {
        product_id: productId,
    }
    fetch(`/orders/customer/delete_from_cart`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(body)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        
        return response.json();
    })
    .then(data => {
        if (data.success) {
            console.log('Product deleted from cart:');

            fetchCart();
        } else {
            console.error('Failed to delete item to cart');
        }
    })
    .catch(error => {
        console.error('Error deleting product from cart:', error);
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

// Example function to update the cart display (to be customized)
totalPriceElement = document.getElementById("total");
function updateCartDisplay(orderItems) {
    price_total = 0;
    const cartItemsContainer = document.getElementById('shopping-cart-list');
    cartItemsContainer.innerHTML = ''; 
    orderItems.forEach(item => {

        const div = document.createElement('div');
        const li = document.createElement('li');
        const deleteItem = document.createElement('a');


        const input = document.createElement('input');
        input.type = 'number';
        input.value = item.quantity; // Set the initial quantity
        input.min = '1'; // Set minimum value to 1
        input.style.width = '60px'; // Set a fixed width for the input

        deleteItem.textContent = 'Hapus';
        deleteItem.className = 'generic-reject-button';

        const label = document.createElement('label');
        label.textContent = `${item.product_name}`;
         // Append input to the label
        
        const label_quantity = document.createElement('label');
        label_quantity.textContent = `Jumlah: `;
        label_quantity.appendChild(input);
        

        div.appendChild(label);
        div.appendChild(label_quantity);
        div.appendChild(deleteItem);
        li.appendChild(div);
        
        div.className = "cart-item"
        input.addEventListener('change', function() {
            const newQuantity = parseInt(input.value, 10) || 0; // Parse the new quantity, default to 0
            if (newQuantity > 0) { // Ensure quantity is greater than 0
                add_to_cart(item.product_id, newQuantity); // Update cart with new quantity
            }
        });
        deleteItem.addEventListener('click', function() {
            console.log("Hello");
            delete_from_cart(item.product_id); // delete item from cart.
        });


        cartItemsContainer.appendChild(li);
        price_total += item.price * item.quantity;
    });

    totalPriceElement.textContent = "Total: Rp. " + price_total.toLocaleString();
}

function actionMenuOpen(event){
    event.preventDefault();

}
function toggleMenu(event) {
    event.stopPropagation(); // Prevents the click event from closing the menu

    // Check if the menu already exists
    let menu = document.getElementById('actionMenus');

    // If it doesn't exist, create it
    if (!menu) {
        menu = createMenu();
        document.body.appendChild(menu);
    }

    // Position the menu next to the button
    const buttonRect = event.target.getBoundingClientRect();
    menu.style.left = `${buttonRect.right + window.scrollX}px`;
    menu.style.top = `${buttonRect.top + window.scrollY}px`;

    // Toggle menu visibility
    menu.classList.toggle('hidden');
}
function createMenu() {
    const menu = document.createElement('div');
    menu.id = 'actionMenus';
    menu.classList.add('actionMenu');

    // Create action buttons
    const action1 = document.createElement('button');
    action1.textContent = 'Action 1';
    action1.onclick = () => alert("Action 1 performed!");

    const action2 = document.createElement('button');
    action2.textContent = 'Action 2';
    action2.onclick = () => alert("Action 2 performed!");

    const action3 = document.createElement('button');
    action3.textContent = 'Action 3';
    action3.onclick = () => alert("Action 3 performed!");

    // Append action buttons to the menu
    menu.appendChild(action1);
    menu.appendChild(action2);
    menu.appendChild(action3);

    return menu;
}
function init(){
    fetchCart();
    document.addEventListener('click', (event) => {
        const menu = document.getElementById('actionMenus');
        console.log(menu.classList.contains('hidden'));
        if (menu && !menu.contains(event.target)) {
            menu.remove();
        }
    });
}

window.onload = init();