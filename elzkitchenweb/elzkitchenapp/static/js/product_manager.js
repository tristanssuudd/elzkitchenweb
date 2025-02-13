const categoryDict = {};
const itemsPerPage = 5;

function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}
function formatStringNumberWithCommas(numberString) {
    const number = parseFloat(numberString); // Convert the string to a number
    if (isNaN(number)) {
        throw new Error("Invalid number string"); // Handle invalid input
    }
    return number.toLocaleString('en-US');
}

function getCategoryIdByText(categoryName) {
    if (categoryName in categoryDict) {
        return categoryDict[categoryName];
    } else {
        console.error(`Category "${categoryName}" not found.`);
        return null;
    }
}
function toggleCreateForm() {
    const formContainer = document.getElementById('createProductContainer');
    
    formContainer.style.display = formContainer.style.display === 'none' ? 'flex' : 'none';
}

function toggleSelectAll(source) {
    const checkboxes = document.querySelectorAll('.productCheckbox');
    checkboxes.forEach(checkbox => {
        checkbox.checked = source.checked;
        toggleRowHighlight(checkbox);
    });
}
function toggleRowHighlight(checkbox) {
    const row = checkbox.closest('tr'); // Get the closest table row
    if (checkbox.checked) {
        row.classList.add('highlighted-row'); // Add the highlight class
    } else {
        row.classList.remove('highlighted-row'); // Remove the highlight class
    }
}
function setupPagination(totalItems, currentPage) {
    const paginationDiv = document.getElementById('pagination');
    paginationDiv.innerHTML = ''; // Clear existing buttons

    const totalPages = Math.ceil(totalItems / itemsPerPage);

    for (let i = 1; i <= totalPages; i++) {
        const button = document.createElement('button');
        button.textContent = i;
        if (i === currentPage) {
            button.disabled = true;
        }
        button.onclick = () => fetchProducts(i);
        paginationDiv.appendChild(button);
    }
}
function createProduct() {
    const formData = new FormData(document.getElementById('createProductForm'));
    fetch('/products/create', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken()
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data) {
            console.log(data);
            location.reload();
            toggleCreateForm();
            
        } else {
            console.error('Error creating product.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function editProduct(pid){
    
    const EditformData = new FormData(document.getElementById('editProductForm'));
    fetch(`/products/update/${pid}`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken()
        },
        body: EditformData
    })
    .then(response => response.json())
    .then(data => {
        if (data) {
            console.log(data);
            toggleEditForm();
        } else {
            console.error('Error editing product.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });

}

function deleteProduct(pid){
    if (!confirm(`Apakah anda yakin bahwa anda akan menghapus produk ini?`)) {
        return; 
    }
    fetch(`/products/delete/${pid}`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data) {
            console.log(data);
            location.reload();
        } else {
            console.error('Error editing product.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });

}

function toggleEditForm(product) {
    const formContainer = document.getElementById('editProductContainer');
    
    formContainer.style.display = formContainer.style.display === 'none' ? 'flex' : 'none';

    document.getElementById('edit-name').value = product.name;
    document.getElementById('edit-category-select').value = getCategoryIdByText(product.category);
    document.getElementById('edit-isAvailable').checked = product.is_Available;
    const NAMessageField = document.getElementById('NAMessage');
    NAMessageField.value = product.NAMessage || '';
    document.getElementById('edit-price').value = product.price;

    const editSubmitButton = document.getElementById('editProductSubmitButton');
    const clonedButton = editSubmitButton.cloneNode(true);
    editSubmitButton.parentNode.replaceChild(clonedButton, editSubmitButton);
    
    clonedButton.addEventListener('click', () => {
        editProduct(product.id);
        location.reload();

    });
    
}
function populateCategories() {
    fetch('/products/categories', {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (Array.isArray(data)) {
            const categorySelect = document.getElementById('product_category_select');
            const createProductCategorySelect = document.getElementById('create-category-select');
            const editProductCategorySelect = document.getElementById('edit-category-select')
            categorySelect.innerHTML = '<option value="">Semua</option>'; // Reset options
            
            Object.keys(categoryDict).forEach(key => delete categoryDict[key]);

            data.forEach(category => {

                categoryDict[category.category] = category.id

                const option1 = document.createElement('option');
                option1.value = category.id; // Use category ID as the value
                option1.textContent = category.category; // Display category name
                categorySelect.appendChild(option1);

                const option2 = document.createElement('option');
                option2.value = category.id; // Use category ID as the value
                option2.textContent = category.category; // Display category name
                createProductCategorySelect.appendChild(option2);

                const option3 = document.createElement('option');
                option3.value = category.id; // Use category ID as the value
                option3.textContent = category.category; // Display category name
                editProductCategorySelect.appendChild(option3);
            });
        } else {
            console.error('Invalid data received:', data);
        }
    })
    .catch(error => {
        console.error('Error fetching categories:', error);
    });
}
function fetchProducts(page) {
    const sortBy = document.getElementById('sort_by').value;
    const ascending = document.getElementById('ascending').checked;
    const categorySelector = document.getElementById('product_category_select');
    const category = categorySelector.value === 'semua' ? '' : categorySelector.value;
    fetch('/products/query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken() // Include CSRF token if needed
        },
        body: JSON.stringify({
            sort_by: sortBy,
            ascending: ascending.toString(),
            category: category
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data && Array.isArray(data)) {
            displayProducts(data, page);
            setupPagination(data.length, page);
        } else {
            console.error('Invalid data received:', data);
        }
    })
    .catch(error => {
        console.error('Error fetching products:', error);
    });
}

const isAnythingSelected = false

function displayProducts(products, page) {
    const tableBody = document.getElementById('productTableBody');
    tableBody.innerHTML = ''; // Clear existing rows

    const start = (page - 1) * itemsPerPage;
    const end = start + itemsPerPage;

    products.slice(start, end).forEach(product => {
        const row = document.createElement('tr');
        compiledProductInfo = JSON.stringify(product)
        row.innerHTML = `
            <td><input type="checkbox" class="productCheckbox" value="${product.id}" onchange="toggleRowHighlight(this)"></td>
            <td><img class="productImage" src="${product.image_url || '/path/to/placeholder.jpg'}" alt="${product.name}"></td>
            <td>${product.name}</td>

            <td>Rp. ${formatStringNumberWithCommas(product.price)}</td>
            <td>${product.is_Available ? 'Ada' : 'Tidak ada'}</td>
            <td>${product.category}</td>
            <td>
                <button class="generic-edit-button">Edit</button>
                <button class="generic-reject-button" onclick="deleteProduct(${product.id})">Delete</button>
            </td>
        `;
        const editButton = row.querySelector('.generic-edit-button');
        editButton.addEventListener('click', () => toggleEditForm(product));
        tableBody.appendChild(row);
    });
}



function init(){
    populateCategories();
    fetchProducts(1);
}
window.onload = init();