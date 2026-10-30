const profileModal = document.querySelector('[data-profile-modal]');
const profileOpenButton = document.querySelector('[data-profile-open]');
const profileCloseButton = document.querySelector('[data-profile-close]');

function openProfileModal() {
    profileModal.classList.add('is-open');
    profileModal.setAttribute('aria-hidden', 'false');
    profileModal.querySelector('.modal-form input, .modal-form select, .modal-form button').focus();
}

function closeProfileModal() {
    profileModal.classList.remove('is-open');
    profileModal.setAttribute('aria-hidden', 'true');
    profileOpenButton.focus();
}

if (profileModal && profileOpenButton && profileCloseButton) {
    profileOpenButton.addEventListener('click', openProfileModal);
    profileCloseButton.addEventListener('click', closeProfileModal);
    profileModal.addEventListener('click', (event) => {
        if (event.target === profileModal) {
            closeProfileModal();
        }
    });
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && profileModal.classList.contains('is-open')) {
            closeProfileModal();
        }
    });
}
