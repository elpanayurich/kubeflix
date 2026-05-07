const searchBtn = document.getElementById('searchBtn');
const resultsList = document.getElementById('results');
const queryInput = document.getElementById('query');

const API_URL = "/api/search";

async function buscar() {
    const q = queryInput.value;
    if (!q) return;

    resultsList.innerHTML = '<li>Buscando en el cluster...</li>';

    try {
        const response = await fetch(`${API_URL}?q=${q}`);
        const data = await response.json();
        
        resultsList.innerHTML = '';
        
        if (data.length === 0) {
            resultsList.innerHTML = '<li>No se encontraron películas.</li>';
            return;
        }

        data.forEach(movie => {
            const li = document.createElement('li');
            li.textContent = movie;
            resultsList.appendChild(li);
        });
    } catch (error) {
        console.error("Error:", error);
        resultsList.innerHTML = '<li>Error: ¿Has activado CORS en el backend?</li>';
    }
}

searchBtn.addEventListener('click', buscar);

queryInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') buscar();
});