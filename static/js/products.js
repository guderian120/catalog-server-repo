// DOM Elements
const productsContainer = document.getElementById('productsContainer');
const searchInput = document.getElementById('searchInput');
const addProductBtn = document.getElementById('addProductBtn');
const productModal = document.getElementById('productModal');
const closeModal = document.querySelector('.close');
const productForm = document.getElementById('productForm');

const logoutBtn = document.getElementById('logoutBtn');

let allProducts = [];
// Add this with the other DOM element selectors at the top

// Add this with the other event listeners
logoutBtn?.addEventListener('click', handleLogout);

// Add this function with your other functions
function handleLogout(e) {
  e.preventDefault();
  localStorage.removeItem('accessToken');
  localStorage.removeItem('refreshToken');
  window.location.href = '/static/index.html';
}
// Check authentication on page load
document.addEventListener('DOMContentLoaded', () => {
  if (!localStorage.getItem('accessToken') && window.location.pathname.includes('products.html')) {
    window.location.href = '/static/login.html';
  }
  
  if (productsContainer) {
    loadProducts();
  }
});

// Load products from API
async function loadProducts() {
  try {
    const response = await fetch('/api/products', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
      }
    });
    
    if (response.status === 401) {
      await refreshToken();
      return loadProducts();
    }
    
    allProducts = await response.json();
    displayProducts(allProducts);
  } catch (error) {
    console.error('Error loading products:', error);
  }
}

// Display products in the grid
function displayProducts(products) {
  productsContainer.innerHTML = '';
  
  if (products.length === 0) {
    productsContainer.innerHTML = '<p>No products found.</p>';
    return;
  }
  
  products.forEach(product => {
    const productCard = document.createElement('div');
    productCard.className = 'product-card';
    productCard.innerHTML = `
      <h3>${product.name}</h3>
      <p>${product.description || 'No description available'}</p>
      <p class="product-price">$${product.price.toFixed(2)}</p>
      <p><small>Added by: ${product.owner || 'Unknown'}</small></p>
      ${product.user_id === getCurrentUserId() ? 
        `<button onclick="deleteProduct(${product.id})">Delete</button>` : ''}
    `;
    productsContainer.appendChild(productCard);
  });
}

// Search functionality
searchInput?.addEventListener('input', (e) => {
  const term = e.target.value.toLowerCase();
  const filtered = allProducts.filter(p => 
    p.name.toLowerCase().includes(term) || 
    (p.description && p.description.toLowerCase().includes(term))
  );
  displayProducts(filtered);
});

// Modal handling
addProductBtn?.addEventListener('click', () => {
  productModal.style.display = 'block';
});

closeModal?.addEventListener('click', () => {
  productModal.style.display = 'none';
});

window.addEventListener('click', (e) => {
  if (e.target === productModal) {
    productModal.style.display = 'none';
  }
});

// Add new product
productForm?.addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const name = document.getElementById('productName').value;
  const description = document.getElementById('productDesc').value;
  const price = document.getElementById('productPrice').value;
  console.log(name, description, price);
  console.log('Token:', localStorage.getItem('accessToken'));

  try {
    const response = await fetch('/api/products', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
      },
      body: JSON.stringify({ name, description, price })
    });
    
    if (response.ok) {
      productModal.style.display = 'none';
      productForm.reset();
      loadProducts();
    } else {
      const error = await response.json();
      alert('Error: ' + error);
      console.error('Error adding product:', error);
    }
  } catch (error) {
    alert('Failed to add product. Please try again.');
  }
});

// Delete product
window.deleteProduct = async (id) => {
  if (!confirm('Are you sure you want to delete this product?')) return;
  
  try {
    const response = await fetch(`/api/products/${id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
      }
    });
    
    if (response.ok) {
      loadProducts();
    } else {
      alert('Failed to delete product.');
    }
  } catch (error) {
    alert('Failed to delete product. Please try again.');
  }
};

// Helper functions
async function refreshToken() {
  const refreshToken = localStorage.getItem('refreshToken');
  if (!refreshToken) {
    window.location.href = '/static/login.html';
    return;
  }
  
  try {
    const response = await fetch('/api/auth/refresh', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${refreshToken}`
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      localStorage.setItem('accessToken', data.access_token);
    } else {
      throw new Error('Token refresh failed');
    }
  } catch (error) {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    window.location.href = '/static/login.html';
  }
}

function getCurrentUserId() {
  const token = localStorage.getItem('accessToken');
  if (!token) return null;
  
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.sub; // Assuming the user ID is in the 'sub' claim
  } catch (error) {
    return null;
  }
}