document.addEventListener('DOMContentLoaded', async () => {
  if (!localStorage.getItem('accessToken')) {
    window.location.href = '/static/login.html';
    return;
  }

  const cartContainer = document.getElementById('cartContainer');
  const totalAmount = document.getElementById('totalAmount');
  const checkoutBtn = document.getElementById('checkoutBtn');
  const logoutBtn = document.getElementById('logoutBtn');

  logoutBtn.addEventListener('click', handleLogout);
  checkoutBtn.addEventListener('click', handleCheckout);

  async function loadCart() {
    try {
      const response = await fetch('/api/cart', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
        }
      });

      if (response.status === 401) {
        await refreshToken();
        return loadCart();
      }

      const cartItems = await response.json();
      displayCartItems(cartItems);
    } catch (error) {
      console.error('Error loading cart:', error);
    }
  }

  function displayCartItems(items) {
    cartContainer.innerHTML = '';
    let total = 0;

    if (items.length === 0) {
      cartContainer.innerHTML = '<p>Your cart is empty</p>';
      totalAmount.textContent = '0.00';
      return;
    }

    items.forEach(item => {
      const itemElement = document.createElement('div');
      itemElement.className = 'cart-item';
      itemElement.innerHTML = `
        <div class="item-info">
          <h3>${item.name}</h3>
          <p>$${item.price.toFixed(2)} × ${item.quantity}</p>
        </div>
        <button onclick="removeFromCart(${item.id})">Remove</button>
      `;
      cartContainer.appendChild(itemElement);
      total += item.price * item.quantity;
    });

    totalAmount.textContent = total.toFixed(2);
  }

  async function handleCheckout() {
    alert('Checkout functionality would be implemented here!');
    // In a real app, you would implement payment processing here
  }

  loadCart();
});

async function removeFromCart(itemId) {
  try {
    const response = await fetch(`/api/cart/${itemId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
      }
    });

    if (response.ok) {
      window.location.reload();
    } else {
      const error = await response.json();
      alert('Error: ' + error.error);
      console.error('Failed to remove item:', error);
    }
  } catch (error) {
    alert('Failed to remove item. Please try again.');
  }
}

function handleLogout(e) {
  e.preventDefault();
  localStorage.removeItem('accessToken');
  localStorage.removeItem('refreshToken');
  window.location.href = '/static/index.html';
}