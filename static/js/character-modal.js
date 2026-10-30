const characterModal = document.querySelector('[data-character-modal]');
const characterOpenButton = document.querySelector('[data-character-open]');
const characterCloseButton = document.querySelector('[data-character-close]');
const characterDeleteModal = document.querySelector('[data-character-delete-modal]');
const characterDeleteName = document.querySelector('[data-character-delete-name]');
const characterDeleteCancel = document.querySelector('[data-character-delete-cancel]');
const characterDeleteConfirm = document.querySelector('[data-character-delete-confirm]');
let pendingDeleteForm = null;

function openCharacterModal() {
    characterModal.classList.add('is-open');
    characterModal.setAttribute('aria-hidden', 'false');
    characterModal.querySelector('.modal-form input, .modal-form select, .modal-form button').focus();
}

function openCharacterDeleteModal(form) {
    pendingDeleteForm = form;
    characterDeleteName.textContent = form.dataset.characterName;
    characterDeleteModal.classList.add('is-open');
    characterDeleteModal.setAttribute('aria-hidden', 'false');
    characterDeleteCancel.focus();
}

function closeCharacterDeleteModal() {
    characterDeleteModal.classList.remove('is-open');
    characterDeleteModal.setAttribute('aria-hidden', 'true');
    pendingDeleteForm?.querySelector('button').focus();
    pendingDeleteForm = null;
}

function closeCharacterModal() {
    characterModal.classList.remove('is-open');
    characterModal.setAttribute('aria-hidden', 'true');
    characterOpenButton.focus();
}

if (characterDeleteModal && characterDeleteName && characterDeleteCancel && characterDeleteConfirm) {
    document.querySelectorAll('[data-character-delete-form]').forEach((form) => {
        form.addEventListener('submit', (event) => {
            event.preventDefault();
            openCharacterDeleteModal(form);
        });
    });
    characterDeleteCancel.addEventListener('click', closeCharacterDeleteModal);
    characterDeleteConfirm.addEventListener('click', () => pendingDeleteForm?.submit());
    characterDeleteModal.addEventListener('click', (event) => {
        if (event.target === characterDeleteModal) closeCharacterDeleteModal();
    });
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && characterDeleteModal.classList.contains('is-open')) {
            closeCharacterDeleteModal();
        }
    });
}

if (characterModal && characterOpenButton && characterCloseButton) {
    characterOpenButton.addEventListener('click', openCharacterModal);
    characterCloseButton.addEventListener('click', closeCharacterModal);
    characterModal.addEventListener('click', (event) => {
        if (event.target === characterModal) {
            closeCharacterModal();
        }
    });
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && characterModal.classList.contains('is-open')) {
            closeCharacterModal();
        }
    });
}
