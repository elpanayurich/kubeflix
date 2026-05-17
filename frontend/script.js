// -- config --
const AUTH_URL = "/auth";
const SEARCH_URL = "/api/search";
const PAYMENTS_URL = "";

// -- redirection logic --
const token = localStorage.getItem('token');
const path = window.location.pathname;

const isAuthPage = path.includes('/login') || path.includes('/register');
const isPremiumPage = path.includes('/premium');

if (!token && !isAuthPage) {
    window.location.href = "/login";
}

if (token && isAuthPage) {
    window.location.href = "/";
}

// -- messaging utilities --
const showMsg = (text, isError = false) => {
    const msg = document.getElementById('message');
    if (msg) {
        msg.innerText = text;
        msg.style.color = isError ? "#e50914" : "#46d369";
    }
};

// -- login --
const loginBtn = document.getElementById('loginBtn');
if (loginBtn) {
    loginBtn.addEventListener('click', async () => {
        const user = document.getElementById('username').value;
        const pass = document.getElementById('password').value;

        if (!user || !pass) return showMsg("Fill in all fields", true);

        try {
            const res = await fetch(`${AUTH_URL}/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: user, password: pass })
            });
            const data = await res.json();

            if (res.ok) {
                localStorage.setItem('token', data.token);
                window.location.href = "/"; 
            } else {
                showMsg(data.message || "Invalid credentials", true);
            }
        } catch (e) {
            showMsg("Connection error with Auth Service", true);
        }
    });
}

// -- register --
const registerBtn = document.getElementById('registerBtn');
if (registerBtn) {
    registerBtn.addEventListener('click', async () => {
        const user = document.getElementById('reg-username').value;
        const pass = document.getElementById('reg-password').value;

        if (!user || !pass) return showMsg("Fill in all fields", true);

        try {
            const res = await fetch(`${AUTH_URL}/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: user, password: pass, tier: 'free' })
            });

            if (res.ok) {
                alert("Account created! Please log in.");
                window.location.href = "/login";
            } else {
                showMsg("Error: User already exists", true);
            }
        } catch (e) {
            showMsg("Connection error", true);
        }
    });
}

// -- search --
const searchBtn = document.getElementById('searchBtn');
if (searchBtn) {
    const queryInput = document.getElementById('query');
    const resultsList = document.getElementById('results');



    const searchMovies = async () => {
        const q = queryInput.value;
        if (!q) return;

        resultsList.innerHTML = '<li class="movie-item">Searching...</li>';
        
        try {
            const res = await fetch(`${SEARCH_URL}?q=${q}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            
            if (res.status === 401) {
                localStorage.removeItem('token');
                window.location.href = "/login";
                return;
            }

            const data = await res.json();
            resultsList.innerHTML = data.length ? '' : '<li class="movie-item">No results found.</li>';
            
            data.forEach(movie => {
                const li = document.createElement('li');
                li.className = "movie-item";
                li.textContent = movie;
                resultsList.appendChild(li);
            });
        } catch (e) {
            resultsList.innerHTML = '<li class="movie-item">Error connecting to Search API</li>';
        }
    };

    searchBtn.addEventListener('click', searchMovies);
    queryInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') searchMovies(); });
}

// -- payments (Upgrade/Downgrade) --
const upgradeBtn = document.getElementById('upgradeBtn');
const downgradeBtn = document.getElementById('downgradeBtn');

if (upgradeBtn && downgradeBtn) {
    upgradeBtn.addEventListener('click', async () => {
        showMsg("Processing payment...", false);
        try {
            const res = await fetch(`${PAYMENTS_URL}/upgrade`, {
                method: 'POST',
                headers: { 
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            const data = await res.json();
            
            if (res.ok) {
                showMsg("Success! You are now Premium", false);
            } else if (res.status === 402) {
                showMsg(data.message, true); // El mensaje de la "trampa" de pobreza
            } else {
                showMsg(data.message || "Payment failed", true);
            }
        } catch (e) {
            showMsg("Connection error with Payments Gateway", true);
        }
    });

    downgradeBtn.addEventListener('click', async () => {
        showMsg("Processing downgrade...", false);
        try {
            const res = await fetch(`${PAYMENTS_URL}/downgrade`, {
                method: 'POST',
                headers: { 
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            const data = await res.json();
            
            if (res.ok) {
                showMsg("Account downgraded to Free tier", false);
            } else {
                showMsg(data.message || "Downgrade failed", true);
            }
        } catch (e) {
            showMsg("Connection error with Payments Gateway", true);
        }
    });
}

// -- logout --
const logoutBtn = document.getElementById('logoutBtn');
if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
        localStorage.removeItem('token');
        window.location.href = "/login";
    });
}

// -- settings dropdown & profile --
const settingsBtn = document.getElementById('settingsBtn');
const settingsDropdown = document.getElementById('settingsDropdown');
const profileBtn = document.getElementById('profileBtn');

if (settingsBtn && settingsDropdown) {
    // Toggle dropdown
    settingsBtn.addEventListener('click', (e) => {
        e.stopPropagation(); // Evita que el clic se propague al window
        settingsDropdown.classList.toggle('show-dropdown');
    });

    // Close dropdown when clicking anywhere else on the screen
    window.addEventListener('click', (e) => {
        if (!e.target.matches('.settings-btn')) {
            if (settingsDropdown.classList.contains('show-dropdown')) {
                settingsDropdown.classList.remove('show-dropdown');
            }
        }
    });
}

if (profileBtn) {
    profileBtn.addEventListener('click', (e) => {
        e.preventDefault();
        alert("View Profile feature coming soon to KubeFlix! 🍿");
    });
}