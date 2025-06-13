document.addEventListener('DOMContentLoaded', async () => {
  // Check authentication status
  await checkAuthStatus();
  await updateCartCount();
  
  // Get product ID from URL
  const productId = getProductIdFromUrl();
  if (!productId) {
    window.location.href = '/static/products_view.html';
    return;
  }
  
  // Load product details
  await loadProductDetails(productId);
  
  // Setup event listeners
  setupEventListeners(productId);
});

function getProductIdFromUrl() {
  const hash = window.location.hash;
  if (!hash) return null;
  
  // Expected format: #product-123
  const match = hash.match(/product-(\d+)/);
  return match ? match[1] : null;
}

async function loadProductDetails(productId) {
  try {
    const response = await fetch(`/api/products`);
    const products = await response.json();
    const product = products.find(p => p.id == productId);
    
    if (!product) {
      throw new Error('Product not found');
    }
    
    // Update the DOM with product details
    document.getElementById('productName').textContent = product.name;
    document.getElementById('productPrice').textContent = `$${product.price.toFixed(2)}`;
    document.getElementById('productDescription').textContent = product.description || 'No description available';
    document.getElementById('mainImage').alt = product.name;
    
    // You could also load additional images here if available
    // document.getElementById('mainImage').src = product.imageUrl || placeholderImage;
    
  } catch (error) {
    console.error('Error loading product:', error);
    alert('Product not found. Redirecting to products page...');
    window.location.href = '/static/products.html';
  }
}

function setupEventListeners(productId) {
  // Quantity controls
  document.getElementById('increaseQty').addEventListener('click', () => {
    const quantityInput = document.getElementById('quantity');
    quantityInput.value = parseInt(quantityInput.value) + 1;
  });
  
  document.getElementById('decreaseQty').addEventListener('click', () => {
    const quantityInput = document.getElementById('quantity');
    if (parseInt(quantityInput.value) > 1) {
      quantityInput.value = parseInt(quantityInput.value) - 1;
    }
  });
  
  // Add to cart button
  document.getElementById('addToCartBtn').addEventListener('click', async () => {
    await addToCart(productId);
  });
}

async function addToCart(productId) {
  if (!localStorage.getItem('accessToken')) {
    alert('Please login to add items to cart');
    window.location.href = '/static/login.html';
    return;
  }

  const quantity = parseInt(document.getElementById('quantity').value) || 1;

  try {
    const response = await fetch('/api/cart', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
      },
      body: JSON.stringify({ 
        product_id: productId,
        quantity: quantity
      })
    });

    if (response.ok) {
      alert('Product added to cart!');
      await updateCartCount();
    } else {
      const error = await response.json();
      alert('Error: ' + error.error);
    }
  } catch (error) {
    alert('Failed to add to cart. Please try again.');
  }
}

// Reuse these functions from your other pages
async function checkAuthStatus() {
  const authSection = document.getElementById('authSection');
  const accessToken = localStorage.getItem('accessToken');
  
  if (accessToken) {
    authSection.innerHTML = `
      <button class="btn-outline" id="logoutBtn">Logout</button>
    `;
    document.getElementById('logoutBtn').addEventListener('click', handleLogout);
  }
}

async function handleLogout() {
  localStorage.removeItem('accessToken');
  localStorage.removeItem('refreshToken');
  await checkAuthStatus();
  await updateCartCount();
  alert('You have been logged out successfully');
}

async function updateCartCount() {
  const accessToken = localStorage.getItem('accessToken');
  const cartCount = document.getElementById('cartCount');
  
  if (!accessToken) {
    cartCount.textContent = '0';
    return;
  }
  
  try {
    const response = await fetch('/api/cart', {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    });
    
    if (response.ok) {
      const cartItems = await response.json();
      cartCount.textContent = cartItems.length;
    }
  } catch (error) {
    console.error('Error updating cart count:', error);
  }
}