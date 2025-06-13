// Global functions and event listeners
document.addEventListener('DOMContentLoaded', () => {
  // Check if user is logged in
  const accessToken = localStorage.getItem('accessToken');
  const logoutLinks = document.querySelectorAll('.logout-link');
  
  if (logoutLinks) {
    logoutLinks.forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        window.location.href = '/static/index.html';
      });
    });
  }
  
  // Highlight current page in navigation
  const currentPage = window.location.pathname.split('/').pop();
  const navLinks = document.querySelectorAll('nav a');
  
  navLinks.forEach(link => {
    if (link.getAttribute('href').includes(currentPage)) {
      link.classList.add('active');
    }
  });
});