const inventoryModal = document.querySelector('[data-inventory-modal]');
const inventoryOpenButton = document.querySelector('[data-inventory-open]');
const inventoryCloseButton = document.querySelector('[data-inventory-close]');
const teamForm = document.querySelector('[data-team-form]');
const teamFeedback = document.querySelector('[data-team-feedback]');
const teamActionInput = document.querySelector('[data-team-action]');
const teamPokemonNumberInput = document.querySelector('[data-team-pokemon-number]');
const depositToggle = document.querySelector('[data-deposit-toggle]');
const depositPanel = document.querySelector('[data-pokemon-deposit]');
const depositGrid = document.querySelector('[data-deposit-grid]');
const depositCount = document.querySelector('[data-deposit-count]');
const inventoryDeleteModal = document.querySelector('[data-inventory-delete-modal]');
const inventoryDeleteName = document.querySelector('[data-inventory-delete-name]');
const inventoryDeleteCancel = document.querySelector('[data-inventory-delete-cancel]');
const inventoryDeleteConfirm = document.querySelector('[data-inventory-delete-confirm]');
let pendingInventoryDeleteForm = null;

function getCsrfToken() {
    const tokenInput = teamForm?.querySelector('input[name="csrfmiddlewaretoken"]');
    if (tokenInput?.value) return tokenInput.value;
    const cookie = document.cookie.split('; ').find((row) => row.startsWith('csrftoken='));
    return cookie ? decodeURIComponent(cookie.split('=')[1]) : '';
}

function openInventoryModal() {
    inventoryModal.classList.add('is-open');
    inventoryModal.setAttribute('aria-hidden', 'false');
    inventoryCloseButton.focus();
}

function closeInventoryModal() {
    inventoryModal.classList.remove('is-open');
    inventoryModal.setAttribute('aria-hidden', 'true');
    inventoryOpenButton.focus();
}

function openInventoryDeleteModal(form) {
    pendingInventoryDeleteForm = form;
    inventoryDeleteName.textContent = form.dataset.itemName;
    inventoryDeleteModal.classList.add('is-open');
    inventoryDeleteModal.setAttribute('aria-hidden', 'false');
    inventoryDeleteCancel.focus();
}

function closeInventoryDeleteModal() {
    inventoryDeleteModal.classList.remove('is-open');
    inventoryDeleteModal.setAttribute('aria-hidden', 'true');
    pendingInventoryDeleteForm?.querySelector('button').focus();
    pendingInventoryDeleteForm = null;
}

function pokemonImage(pokemon) {
    return pokemon.image ? `<img src="${pokemon.image}" alt="${pokemon.name}">` : '';
}

function renderTeamSlot(slotButton, pokemon) {
    const slotNumber = slotButton.dataset.teamSlot;
    const symbol = '<span class="pokeball-symbol" aria-hidden="true"></span>';
    slotButton.dataset.pokemonNumber = pokemon ? pokemon.number : '';
    slotButton.classList.toggle('has-pokemon', Boolean(pokemon));
    slotButton.setAttribute('aria-label', pokemon ? `Slot ${slotNumber}: ${pokemon.name}` : `Slot ${slotNumber}, vazio`);
    slotButton.innerHTML = pokemon
        ? `${symbol}${pokemonImage(pokemon)}<strong>${pokemon.name}</strong>`
        : `${symbol}<small>Slot ${slotNumber}</small>`;

    const profileSlot = document.querySelector(`[data-profile-team-slot="${slotNumber}"]`);
    if (profileSlot) {
        profileSlot.title = pokemon ? pokemon.name : 'Slot vazio';
        profileSlot.innerHTML = `${symbol}${pokemon ? pokemonImage(pokemon) : ''}`;
    }
}

function createDepositButton(pokemon) {
    const button = document.createElement('button');
    button.className = 'deposit-pokemon';
    button.type = 'button';
    button.dataset.depositPokemon = pokemon.number;
    button.innerHTML = `${pokemonImage(pokemon)}<strong>${pokemon.name}</strong><small>#${String(pokemon.number).padStart(3, '0')}</small>`;
    return button;
}

function updateDepositState() {
    const pokemonButtons = depositGrid.querySelectorAll('[data-deposit-pokemon]');
    depositCount.textContent = pokemonButtons.length;
    const empty = depositGrid.querySelector('[data-deposit-empty]');
    if (!pokemonButtons.length && !empty) {
        depositGrid.insertAdjacentHTML('beforeend', '<p class="deposit-empty" data-deposit-empty>Nenhum Pokémon no depósito.</p>');
    } else if (pokemonButtons.length && empty) {
        empty.remove();
    }
}

async function movePokemon(action, pokemonNumber) {
    teamFeedback.textContent = '';
    teamActionInput.value = action;
    teamPokemonNumberInput.value = pokemonNumber;

    const formData = new FormData(teamForm);
    const response = await fetch(teamForm.action, {
        method: 'POST',
        credentials: 'same-origin',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCsrfToken(),
        },
    });
    const payload = await response.json();
    if (!response.ok) {
        teamFeedback.textContent = payload.error || 'Não foi possível mover este Pokémon.';
        return;
    }

    const slotButton = document.querySelector(`[data-team-slot="${payload.slot_number}"]`);
    if (action === 'add') {
        renderTeamSlot(slotButton, payload.pokemon);
        depositGrid.querySelector(`[data-deposit-pokemon="${payload.pokemon.number}"]`)?.remove();
    } else {
        renderTeamSlot(slotButton, null);
        depositGrid.appendChild(createDepositButton(payload.pokemon));
    }
    updateDepositState();
}

function submitTeamMove(action, pokemonNumber) {
    if (!window.fetch || !teamForm.action) {
        teamActionInput.value = action;
        teamPokemonNumberInput.value = pokemonNumber;
        teamForm.submit();
        return;
    }

    movePokemon(action, pokemonNumber).catch(() => {
        teamActionInput.value = action;
        teamPokemonNumberInput.value = pokemonNumber;
        teamForm.submit();
    });
}

if (inventoryModal && inventoryOpenButton && inventoryCloseButton) {
    inventoryOpenButton.addEventListener('click', openInventoryModal);
    inventoryCloseButton.addEventListener('click', closeInventoryModal);
    inventoryModal.addEventListener('click', (event) => {
        if (event.target === inventoryModal) closeInventoryModal();
    });
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && inventoryModal.classList.contains('is-open')) closeInventoryModal();
    });
}

if (inventoryDeleteModal && inventoryDeleteName && inventoryDeleteCancel && inventoryDeleteConfirm) {
    document.querySelectorAll('[data-inventory-delete-form]').forEach((form) => {
        form.addEventListener('submit', (event) => {
            event.preventDefault();
            openInventoryDeleteModal(form);
        });
    });
    inventoryDeleteCancel.addEventListener('click', closeInventoryDeleteModal);
    inventoryDeleteConfirm.addEventListener('click', () => pendingInventoryDeleteForm?.submit());
    inventoryDeleteModal.addEventListener('click', (event) => {
        if (event.target === inventoryDeleteModal) closeInventoryDeleteModal();
    });
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && inventoryDeleteModal.classList.contains('is-open')) {
            closeInventoryDeleteModal();
        }
    });
}

if (teamForm && teamFeedback && teamActionInput && teamPokemonNumberInput && depositGrid && depositCount) {
    document.querySelector('.team-slots').addEventListener('click', (event) => {
        const slot = event.target.closest('[data-team-pokemon]');
        if (slot?.dataset.pokemonNumber) submitTeamMove('remove', slot.dataset.pokemonNumber);
    });
    depositGrid.addEventListener('click', (event) => {
        const pokemon = event.target.closest('[data-deposit-pokemon]');
        if (pokemon) submitTeamMove('add', pokemon.dataset.depositPokemon);
    });
    window.addEventListener('pokemon-registered', (event) => {
        const pokemon = event.detail;
        if (!depositGrid.querySelector(`[data-deposit-pokemon="${pokemon.number}"]`) &&
            !document.querySelector(`[data-team-pokemon][data-pokemon-number="${pokemon.number}"]`)) {
            depositGrid.appendChild(createDepositButton(pokemon));
            updateDepositState();
        }
    });

    const params = new URLSearchParams(window.location.search);
    if (params.get('inventory') === 'open') {
        openInventoryModal();
        depositPanel.hidden = false;
        depositToggle?.classList.add('is-open');
        params.delete('inventory');
        const cleanQuery = params.toString();
        const cleanUrl = `${window.location.pathname}${cleanQuery ? `?${cleanQuery}` : ''}${window.location.hash}`;
        window.history.replaceState({}, '', cleanUrl);
    }
}

if (depositToggle && depositPanel) {
    depositToggle.addEventListener('click', () => {
        depositPanel.hidden = !depositPanel.hidden;
        depositToggle.classList.toggle('is-open', !depositPanel.hidden);
    });
}
