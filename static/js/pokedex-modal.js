const modal = document.querySelector('[data-pokedex-modal]');
const openButton = document.querySelector('[data-pokedex-open]');
const closeButton = document.querySelector('[data-pokedex-close]');
const form = document.querySelector('[data-pokedex-form]');
const results = document.querySelector('[data-pokedex-results]');
const meta = document.querySelector('[data-pokedex-meta]');
const input = document.querySelector('#pokemon-search');
const registeredFilter = document.querySelector('[data-registered-filter]');
const registerForm = document.querySelector('[data-pokedex-register-form]');
const registerInput = document.querySelector('#pokemon-register-name');
const registerFeedback = document.querySelector('[data-register-feedback]');
let currentQuery = '';

function openPokedex() {
    modal.classList.add('is-open');
    modal.setAttribute('aria-hidden', 'false');
    input.focus();
    fetchPokemon();
}

function closePokedex() {
    modal.classList.remove('is-open');
    modal.setAttribute('aria-hidden', 'true');
    openButton.focus();
}

function renderPokemon(pokemonList) {
    if (!pokemonList.length) {
        results.innerHTML = '<p class="empty-state">Nenhum Pokemon encontrado.</p>';
        return;
    }

    results.innerHTML = pokemonList.map((pokemon) => `
        <article class="pokedex-card ${pokemon.registered ? 'is-registered' : 'is-locked'}">
            <div class="pokemon-image-wrap">
                ${pokemon.image ? `<img src="${pokemon.image}" alt="${pokemon.registered ? pokemon.name : 'Pokemon nao registrado'}">` : '<span class="unknown-pokemon">?</span>'}
            </div>
            <div>
                <span class="pokemon-number">#${String(pokemon.number).padStart(3, '0')}</span>
                <h3>${pokemon.registered ? pokemon.name : '???'}</h3>
                <p>${pokemon.registered ? pokemon.types.join(' / ') : 'Nao registrado'}</p>
                ${pokemon.registered ? '<span class="registered-badge">Registrado</span>' : ''}
            </div>
        </article>
    `).join('');
}

function getCsrfToken() {
    const tokenInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (tokenInput) {
        return tokenInput.value;
    }

    const cookie = document.cookie
        .split('; ')
        .find((row) => row.startsWith('csrftoken='));
    return cookie ? decodeURIComponent(cookie.split('=')[1]) : '';
}

async function fetchPokemon() {
    results.innerHTML = '<p class="empty-state">Consultando Pokedex...</p>';
    const params = new URLSearchParams({
        q: currentQuery,
        registered: registeredFilter.checked ? '1' : '0',
    });
    const url = `${modal.dataset.searchUrl}?${params.toString()}`;
    const response = await fetch(url, { headers: { 'Accept': 'application/json' } });
    if (!response.ok) {
        results.innerHTML = '<p class="empty-state">Nao foi possivel carregar a Pokedex agora.</p>';
        return;
    }

    const payload = await response.json();
    meta.textContent = `${payload.registered_count} de ${payload.total_count} Pokemon registrados`;
    renderPokemon(payload.results);
}

async function registerPokemon(pokemonName) {
    registerFeedback.textContent = '';
    const formData = new FormData(registerForm);
    formData.set('pokemon_name', pokemonName.trim());

    const response = await fetch(registerForm.action, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
            'X-CSRFToken': getCsrfToken(),
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
        },
        body: formData,
    });

    if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        registerFeedback.textContent = payload.error || 'Nao foi possivel registrar este Pokemon.';
        return false;
    }

    const payload = await response.json();
    registerFeedback.textContent = `${payload.pokemon_name} registrado na Pokedex.`;
    registerInput.value = '';
    window.dispatchEvent(new CustomEvent('pokemon-registered', {detail: payload.pokemon}));
    fetchPokemon();
    return true;
}

if (modal && openButton && closeButton && form && results && meta && input && registeredFilter && registerForm && registerInput && registerFeedback) {
    openButton.addEventListener('click', openPokedex);
    closeButton.addEventListener('click', closePokedex);
    modal.addEventListener('click', (event) => {
        if (event.target === modal) {
            closePokedex();
        }
    });
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && modal.classList.contains('is-open')) {
            closePokedex();
        }
    });
    form.addEventListener('submit', (event) => {
        event.preventDefault();
        currentQuery = input.value;
        fetchPokemon();
    });
    registeredFilter.addEventListener('change', fetchPokemon);
    registerForm.addEventListener('submit', async (event) => {
        if (!window.fetch || !registerForm.action) {
            return;
        }

        event.preventDefault();
        try {
            await registerPokemon(registerInput.value);
        } catch (error) {
            registerForm.submit();
        }
    });

    const params = new URLSearchParams(window.location.search);
    if (params.get('pokedex') === 'open') {
        openPokedex();
        params.delete('pokedex');
        const cleanQuery = params.toString();
        const cleanUrl = `${window.location.pathname}${cleanQuery ? `?${cleanQuery}` : ''}${window.location.hash}`;
        window.history.replaceState({}, '', cleanUrl);
    }
}
