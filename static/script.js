// Lets the user open the Dropdown
function toggleDropdown() {
    var dropdown = document.getElementById("profileDropdown");
    if (dropdown.style.display === "block") {
        dropdown.style.display = "none";
    } else {
        dropdown.style.display = "block";
    }
}

// Closes the dropdown if the user clicks anywhere outside of it
window.onclick = function(event) {
    if (!event.target.matches('.profile-btn') && !event.target.closest('.profile-btn')) {
        var dropdowns = document.getElementsByClassName("dropdown-content");
        for (var i = 0; i < dropdowns.length; i++) {
            var openDropdown = dropdowns[i];
            if (openDropdown.style.display === "block") {
                openDropdown.style.display = "none";
            }
        }
    }
};

// Used to keep track of prices of each product the user wants to buy
let unitPrice = 0;

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.open-modal-btn').forEach(button => {
        button.addEventListener('click', function() {
            const id = this.getAttribute('data-id');
            const name = this.getAttribute('data-name');
            const price = parseFloat(this.getAttribute('data-price'));
            const stock = parseInt(this.getAttribute('data-stock'));

            openOrderModal(id, name, price, stock);
        });
    });
});

function openOrderModal(id, name, price, stock) {
    document.getElementById('modalProductID').value = id;
    document.getElementById('modalProductName').innerText = "Buy " + name;
    document.getElementById('modalMaxStock').innerText = stock;
    document.getElementById('modalQuantity').max = stock;
    document.getElementById('modalQuantity').value = 1;
    unitPrice = price;
    calculateTotal();
    document.getElementById('orderModal').style.display = 'flex';
}

function closeOrderModal() {
    document.getElementById('orderModal').style.display = 'none';
}

// Used to automatically calculate the total price a customer would have to pay based on how many products they buy.
function calculateTotal() {
    let qty = document.getElementById('modalQuantity').value;
    let total = qty * unitPrice;
    document.getElementById('modalTotalPrice').innerText = total.toFixed(2);
}