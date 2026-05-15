// --- CONFIGURACIÓN DE ENDPOINTS ---
const AUTH_URL = "http://kubeflix.local/auth";
const SEARCH_URL = "http://kubeflix.local/api/search";

// --- 1. LÓGICA DE REDIRECCIÓN (EJECUCIÓN INMEDIATA) ---
const token = localStorage.getItem('token');
const path = window.location.pathname;

// Definimos si estamos en una página de "puertas" (login/register) o dentro de la "casa" (search)
const isAuthPage = path.includes('/login') || path.includes('/register');

// CASO A: No estoy logueado e intento entrar a la App -> Al Login
if (!token && !isAuthPage) {
    window.location.href = "/login";
}

// CASO B: Ya estoy logueado e intento volver al Login/Registro -> Al Buscador
if (token && isAuthPage) {
    window.location.href = "/";
}

// --- 2. UTILIDADES DE MENSAJERÍA ---
const showMsg = (text, isError = false) => {
    const msg = document.getElementById('message');
    if (msg) {
        msg.innerText = text;
        msg.style.color = isError ? "#e50914" : "#46d369";
    }
};

// --- 3. INICIALIZACIÓN DE BOTONES (CON SEGURIDAD) ---
// Solo intentamos añadir eventos si el elemento existe en la página actual

// --- LÓGICA DE LOGIN ---
const loginBtn = document.getElementById('loginBtn');
if (loginBtn) {
    loginBtn.addEventListener('click', async () => {
        const user = document.getElementById('username').value;
        const pass = document.getElementById('password').value;

        if (!user || !pass) return showMsg("Rellena los campos", true);

        try {
            const res = await fetch(`${AUTH_URL}/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: user, password: pass })
            });
            const data = await res.json();

            if (res.ok) {
                localStorage.setItem('token', data.token);
                window.location.href = "/"; // Redirigir al buscador tras éxito
            } else {
                showMsg(data.message || "Credenciales incorrectas", true);
            }
        } catch (e) {
            showMsg("Error de conexión con Auth Service", true);
        }
    });
}

// --- LÓGICA DE REGISTRO ---
const registerBtn = document.getElementById('registerBtn');
if (registerBtn) {
    registerBtn.addEventListener('click', async () => {
        const user = document.getElementById('reg-username').value;
        const pass = document.getElementById('reg-password').value;

        if (!user || !pass) return showMsg("Rellena los campos", true);

        try {
            const res = await fetch(`${AUTH_URL}/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: user, password: pass, tier: 'gold' })
            });

            if (res.ok) {
                alert("¡Cuenta creada! Inicia sesión.");
                window.location.href = "/login";
            } else {
                showMsg("Error: El usuario ya existe", true);
            }
        } catch (e) {
            showMsg("Error de conexión", true);
        }
    });
}

// --- LÓGICA DE BÚSQUEDA ---
const searchBtn = document.getElementById('searchBtn');
if (searchBtn) {
    const queryInput = document.getElementById('query');
    const resultsList = document.getElementById('results');

    const buscar = async () => {
        const q = queryInput.value;
        if (!q) return;

        resultsList.innerHTML = '<li class="movie-item">Buscando...</li>';
        
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
            resultsList.innerHTML = data.length ? '' : '<li class="movie-item">No hay resultados.</li>';
            
            data.forEach(movie => {
                const li = document.createElement('li');
                li.className = "movie-item";
                li.textContent = movie;
                resultsList.appendChild(li);
            });
        } catch (e) {
            resultsList.innerHTML = '<li class="movie-item">Error al conectar con Search API</li>';
        }
    };

    searchBtn.addEventListener('click', buscar);
    queryInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') buscar(); });
}

// --- LOGOUT ---
const logoutBtn = document.getElementById('logoutBtn');
if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
        localStorage.removeItem('token');
        window.location.href = "/login";
    });
}