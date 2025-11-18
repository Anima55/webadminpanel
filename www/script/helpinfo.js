// ==========================================================
// ГЛОБАЛЬНІ ЗМІННІ ТА ФУНКЦІЇ ДЛЯ МОДАЛЬНИХ ВІКОН
// ==========================================================

// Оголошуємо функції відкриття та закриття глобально
// для доступу з onclick в HTML.

/**
 * Відкриває модальне вікно редагування та заповнює його даними.
 * @param {HTMLElement} button Кнопка "Редагувати", що була натиснута.
 */
window.openEditModal = function(button) {
    const editModal = document.getElementById('editModal');
    if (!editModal) return;

    const row = button.closest('tr');
    const id = row.dataset.id;
    const name = row.dataset.name;
    const rank = row.dataset.rank;
    const warnings = row.dataset.warnings;

    // Заповнюємо поля форми
    document.getElementById('modal_helper_id').value = id;
    document.getElementById('modal_admin_name').value = name;
    document.getElementById('modal_admin_rank').value = rank;
    document.getElementById('modal_warnings_count').value = warnings;
    
    // Заповнюємо приховане поле ID для форми видалення
    const deleteIdInput = document.getElementById('modal_delete_helper_id');
    if (deleteIdInput) {
        deleteIdInput.value = id;
    }

    editModal.style.display = 'block';
};

/**
 * Закриває модальне вікно редагування.
 */
window.closeEditModal = function() {
    const editModal = document.getElementById('editModal');
    if (editModal) {
        editModal.style.display = 'none';
    }
};

/**
 * Відкриває модальне вікно додавання.
 */
window.openAddModal = function() {
    const addModal = document.getElementById('addModal');
    if (addModal) {
        // Очищення форми при відкритті
        document.getElementById('add_admin_name').value = '';
        document.getElementById('add_admin_rank').value = '';
        document.getElementById('add_warnings_count').value = '0'; 
        
        addModal.style.display = 'block';
    }
};

/**
 * Закриває модальне вікно додавання.
 */
window.closeAddModal = function() {
    const addModal = document.getElementById('addModal');
    if (addModal) {
        addModal.style.display = 'none';
    }
};


// ==========================================================
// ОБРОБНИКИ ПОДІЙ (DOM READY)
// ==========================================================
document.addEventListener('DOMContentLoaded', (event) => {
    const editModal = document.getElementById('editModal');
    const addModal = document.getElementById('addModal');
    
    // Обробники для кнопки закриття (X)
    if (editModal) {
        const closeBtnEdit = editModal.querySelector('.close-btn');
        if (closeBtnEdit) {
            closeBtnEdit.addEventListener('click', window.closeEditModal);
        }
    }
    
    if (addModal) {
        const closeBtnAdd = addModal.querySelector('.close-btn');
        if (closeBtnAdd) {
            closeBtnAdd.addEventListener('click', window.closeAddModal);
        }
    }
    
    // Глобальний обробник для закриття при кліку поза вікном (оверлей)
    window.onclick = function(event) {
        // Закрити модальне вікно редагування
        if (editModal && event.target === editModal) {
            window.closeEditModal();
        }
        
        // Закрити модальне вікно додавання
        if (addModal && event.target === addModal) {
            window.closeAddModal();
        }
    }
});