const missionsModal = document.querySelector('[data-missions-modal]');
const missionsOpenButton = document.querySelector('[data-missions-open]');
const missionsCloseButton = document.querySelector('[data-missions-close]');
const xpValueLabel = document.querySelector('.meter-label span:last-child');
const xpFill = document.querySelector('.meter-xp');

function getCsrfToken(form) {
    const tokenInput = form.querySelector('input[name="csrfmiddlewaretoken"]');
    if (tokenInput?.value) return tokenInput.value;
    const cookie = document.cookie.split('; ').find((row) => row.startsWith('csrftoken='));
    return cookie ? decodeURIComponent(cookie.split('=')[1]) : '';
}

function openMissionsModal() {
    missionsModal.classList.add('is-open');
    missionsModal.setAttribute('aria-hidden', 'false');
    missionsCloseButton.focus();
}

function closeMissionsModal() {
    missionsModal.classList.remove('is-open');
    missionsModal.setAttribute('aria-hidden', 'true');
    missionsOpenButton.focus();
}

function formatNumber(value) {
    return new Intl.NumberFormat('pt-BR').format(value);
}

function updateLevelText(level) {
    document.querySelectorAll('[data-active-level]').forEach((element) => {
        element.textContent = element.tagName === 'DD' ? level : `Lv. ${level}`;
    });

    const navInfo = document.querySelector('.nav-player span');
    if (navInfo) {
        navInfo.textContent = navInfo.textContent.replace(/Nivel \d+/, `Nivel ${level}`);
    }
}

function updateXpBar(progress) {
    if (!progress) {
        return;
    }

    if (xpValueLabel) {
        xpValueLabel.textContent = progress.needed_for_next_level > 0
            ? `${formatNumber(progress.gained_this_level)} / ${formatNumber(progress.needed_for_next_level)}`
            : 'Nivel maximo';
    }

    if (xpFill) {
        xpFill.style.width = `${progress.percent_css || progress.percent}%`;
    }

    updateLevelText(progress.level);
}

async function completeMission(event) {
    const form = event.currentTarget;
    const button = form.querySelector('button');
    const card = form.closest('[data-mission-card]');

    event.preventDefault();

    button.disabled = true;
    button.textContent = 'Concluida';

    const response = await fetch(form.action, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCsrfToken(form),
        },
        body: new FormData(form),
    });

    if (!response.ok) {
        button.disabled = false;
        button.textContent = 'Marcar concluida';
        return;
    }

    const payload = await response.json();
    card.classList.add('is-completed');
    updateXpBar(payload.xp_progress);
}

if (missionsModal && missionsOpenButton && missionsCloseButton) {
    missionsOpenButton.addEventListener('click', openMissionsModal);
    missionsCloseButton.addEventListener('click', closeMissionsModal);
    missionsModal.addEventListener('click', (event) => {
        if (event.target === missionsModal) {
            closeMissionsModal();
        }
    });
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && missionsModal.classList.contains('is-open')) {
            closeMissionsModal();
        }
    });
    missionsModal.querySelectorAll('[data-mission-complete-form]').forEach((form) => {
        form.addEventListener('submit', completeMission);
    });
}
