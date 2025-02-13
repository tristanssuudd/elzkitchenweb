function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

//vars

// --- Kitchen open and closed behavior.
var kitchenIsOpen = true;

function onKitchenStatusSettingToggled(){
    confirmMsg = kitchenIsOpen ? "Apakah anda yakin ingin menutup toko?" : "Apakah anda yakin ingin membuka toko?";
    if (!confirm(confirmMsg)) {
        return;
    }
    toggleKitchenStatus()
}

function toggleKitchenStatus(){

    fetch('/settings/toggle_kitchen_status', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken(),  
        }
    }).then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log("Kitchen Open Status:", data.kitchenOpen);
            getKitchenStatus();
        } else {
            console.error("Failed to toggle kitchen status");
        }
    });
}

function getKitchenStatus(){
    const kitchenStatusToggleButton = document.getElementById('toggle-kitchen-status');
    const kitchenStatusIndicator = document.getElementById('kitchen-status-indicator');

    fetch('/settings/get_kitchen_status',{
        method: 'GET',
        headers: {
            'X-CSRFToken': getCSRFToken(),  
        }
    }).then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.kitchen_status !== undefined) {
            console.log("Kitchen status:", data.kitchen_status ? "Open" : "Closed");
            kitchenIsOpen = data.kitchen_status
            
            if (data.kitchen_status) {
                kitchenStatusIndicator.textContent = 'Buka';
                kitchenStatusIndicator.style.color = 'green';

                kitchenStatusToggleButton.style.backgroundColor = 'red';
                kitchenStatusToggleButton.textContent = 'Tutup toko'
            } else {
                kitchenStatusIndicator.textContent = 'Tutup';
                kitchenStatusIndicator.style.color = 'red';
                
                kitchenStatusToggleButton.style.backgroundColor = 'green';
                kitchenStatusToggleButton.textContent = 'Buka toko';
            }
            

        } else if (data.error) {
            console.error("Error fetching kitchen status:", data.error);
        }
    })
    .catch(error => {
        console.error("Network or server error:", error);
    });
}
// ---


function init(){
    //Settings init
    getKitchenStatus();


}
init();