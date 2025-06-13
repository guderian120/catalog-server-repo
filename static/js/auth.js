// Handle login form submission
document.getElementById('loginForm')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const username = document.getElementById('username').value;
  const password = document.getElementById('password').value;
  
  try {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ username, password })
    });
    
    const data = await response.json();
    
    if (response.ok) {
      localStorage.setItem('accessToken', data.access_token);
      localStorage.setItem('refreshToken', data.refresh_token);
      window.location.href = '/static/products.html';
    } else {
      document.getElementById('errorMessage').textContent = data.error || 'Login failed';
    }
  } catch (error) {
    document.getElementById('errorMessage').textContent = 'An error occurred. Please try again.';
  }
});

// Handle signup form submission
document.getElementById('signupForm')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const username = document.getElementById('newUsername').value;
  const email = document.getElementById('email').value;
  const password = document.getElementById('newPassword').value;
  
  try {
    const response = await fetch('/api/auth/signup', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ username, email, password })
    });
    
    const data = await response.json();
    
    if (response.ok) {
      localStorage.setItem('accessToken', data.access_token);
      localStorage.setItem('refreshToken', data.refresh_token);
      window.location.href = '/static/products.html';
    } else {
      document.getElementById('signupError').textContent = data.error || 'Signup failed';
    }
  } catch (error) {
    document.getElementById('signupError').textContent = 'An error occurred. Please try again.';
  }
});

// Logout functionality
document.getElementById('logoutLink')?.addEventListener('click', (e) => {
  e.preventDefault();
  localStorage.removeItem('accessToken');
  localStorage.removeItem('refreshToken');
  window.location.href = '/static/index.html';
});