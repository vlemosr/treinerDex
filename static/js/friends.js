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

document.querySelectorAll('[data-delete-friend]').forEach((button) => {
    button.addEventListener('click', async () => {
        const response = await fetch(button.dataset.deleteUrl, {
            method: 'DELETE',
            credentials: 'same-origin',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'Accept': 'application/json',
            },
        });

        if (response.ok) {
            button.closest('[data-friend-card]').remove();
            if (!document.querySelector('[data-friend-card]')) {
                document.querySelector('.friends-list').innerHTML = '<p class="empty-state dark-empty">Nenhum amigo registrado ainda.</p>';
            }
        }
    });
});
