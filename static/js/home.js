document.addEventListener('DOMContentLoaded', async () => {
  // Check authentication status first
  await checkAuthStatus();
  
  // Then load other content
  await loadFeaturedProducts();
  await updateCartCount();
  
  // Smooth scrolling
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      e.preventDefault();
      document.querySelector(this.getAttribute('href')).scrollIntoView({
        behavior: 'smooth'
      });
    });
  });
});

// New function to check authentication status
async function checkAuthStatus() {
  const authSection = document.getElementById('authSection');
  const authSection2 = document.getElementById('authSection2');

  const accessToken = localStorage.getItem('accessToken');
  
  if (accessToken) {
    // User is logged in - show logout button
    authSection.innerHTML = `
      <button class="btn-outline" id="logoutBtn">Logout</button>
    `;
    authSection2.innerHTML = `
      <button class="btn-outline" id="logoutBtn">Logout</button>
    `;
    
    // Add logout event listener
    document.getElementById('logoutBtn').addEventListener('click', handleLogout);
  } else {
    // User is not logged in - show login/signup
    authSection.innerHTML = `
      <a href="/static/login.html" class="btn-outline">Login</a>
      <a href="/static/signup.html" class="btn-primary">Sign Up</a>
    `;
  }
}

// Logout handler
async function handleLogout() {
  localStorage.removeItem('accessToken');
  localStorage.removeItem('refreshToken');
  
  // Update UI immediately
  await checkAuthStatus();
  await updateCartCount();
  
  // Optional: Show logout confirmation
  alert('You have been logged out successfully');
  
  // Optional: Redirect to home
  window.location.href = '/static/index.html';
}

async function loadFeaturedProducts() {
  try {
    const response = await fetch('/api/products');
    const products = await response.json();
    
    // Display first 6 products as featured
    const featuredProducts = products.slice(0, 6);
    const productsContainer = document.getElementById('featuredProducts');
    
    featuredProducts.forEach(product => {
      const productCard = document.createElement('div');
      productCard.className = 'product-card';
      productCard.innerHTML = `
        <div class="product-image">
          <img src="https://via.placeholder.com/300x200?text=${encodeURIComponent(product.name)}" alt="${product.name}">
        </div>
        <div class="product-info">
          <h3>${product.name}</h3>
          <p>${product.description || 'No description available'}</p>
          <div class="product-price">$${product.price.toFixed(2)}</div>
          <div class="product-actions">
            <button class="btn-outline" onclick="viewProduct(${product.id})">View</button>
            <button class="btn-primary" onclick="addToCart(${product.id})">Add to Cart</button>
          </div>
        </div>
      `;
      productsContainer.appendChild(productCard);
    });
  } catch (error) {
    console.error('Error loading featured products:', error);
  }
}

async function updateCartCount() {
  const accessToken = localStorage.getItem('accessToken');
  if (!accessToken) {
    document.getElementById('cartCount').textContent = '0';
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
      document.getElementById('cartCount').textContent = cartItems.length;
    }
  } catch (error) {
    console.error('Error updating cart count:', error);
  }
}

// Global functions
window.viewProduct = function(productId) {
  window.location.href = `/static/products_view.html#product-${productId}`;
};

window.addToCart = async function(productId) {
  if (!localStorage.getItem('accessToken')) {
    alert('Please login to add items to cart');
    window.location.href = '/static/login.html';
    return;
  }

  try {
    const response = await fetch('/api/cart', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
      },
      body: JSON.stringify({ product_id: productId })
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
};