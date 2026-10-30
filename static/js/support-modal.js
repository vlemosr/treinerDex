const supportModal = document.querySelector('[data-support-modal]');
const supportOpenButton = document.querySelector('[data-support-open]');
const supportCloseButton = document.querySelector('[data-support-close]');

function openSupportModal() {
    supportModal.classList.add('is-open');
    supportModal.setAttribute('aria-hidden', 'false');
    supportCloseButton.focus();
}

function closeSupportModal() {
    supportModal.classList.remove('is-open');
    supportModal.setAttribute('aria-hidden', 'true');
    supportOpenButton.focus();
}

if (supportModal && supportOpenButton && supportCloseButton) {
    supportOpenButton.addEventListener('click', openSupportModal);
    supportCloseButton.addEventListener('click', closeSupportModal);
    supportModal.addEventListener('click', (event) => {
        if (event.target === supportModal) {
            closeSupportModal();
        }
    });
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && supportModal.classList.contains('is-open')) {
            closeSupportModal();
        }
    });
}
