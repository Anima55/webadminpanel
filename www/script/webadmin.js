// ==========================================================
// ГЛОБАЛЬНІ ЗМІННІ ТА ФУНКЦІЇ ДЛЯ МОДАЛЬНИХ ВІКОН WEBADMIN
// ==========================================================

// Оголошуємо функції відкриття та закриття глобально
// для доступу з onclick в HTML.

/**
 * Відкриває модальне вікно редагування та заповнює його даними.
 * @param {HTMLElement} button Кнопка "Редагувати", що була натиснута.
 */
window.openEditWebadminModal = function(button) {
    const editModal = document.getElementById('editWebadminModal');
    if (!editModal) return;

    const row = button.closest('tr');
    // Отримуємо дані з data-атрибутів
    const id = row.dataset.id;
    const name = row.dataset.name;
    const rank = row.dataset.rank;
    
    // Заповнюємо поля форми редагування
    document.getElementById('modal_webadmin_id').value = id;
    document.getElementById('modal_webadmin_name').value = name;
    document.getElementById('modal_webadmin_rank').value = rank;
    
    // Заповнюємо приховане поле ID для форми видалення
    const deleteIdInput = document.getElementById('modal_delete_webadmin_id');
    if (deleteIdInput) {
        deleteIdInput.value = id;
    }
    
    editModal.style.display = 'block';
};

/**
 * Закриває модальне вікно редагування.
 */
window.closeEditWebadminModal = function() {
    const editModal = document.getElementById('editWebadminModal');
    if (editModal) {
        editModal.style.display = 'none';
    }
};

/**
 * Відкриває модальне вікно додавання та очищає форму.
 */
window.openAddWebadminModal = function() {
    const addModal = document.getElementById('addWebadminModal');
    if (addModal) {
        // Очищення полів форми при відкритті
        document.getElementById('add_webadmin_name').value = '';
        
        // ВИПРАВЛЕННЯ: Коректне скидання поля Рангу (<select>)
        const rankSelect = document.getElementById('add_webadmin_rank');
        if (rankSelect && rankSelect.options.length > 0) {
            rankSelect.selectedIndex = 0; // Обираємо першу опцію ("Moder")
        }
        
        document.getElementById('add_webadmin_password').value = ''; 
        
        addModal.style.display = 'block';
    }
};
/**
 * Закриває модальне вікно додавання.
 */
window.closeAddWebadminModal = function() {
    const addModal = document.getElementById('addWebadminModal');
    if (addModal) {
        addModal.style.display = 'none';
    }
};


// ==========================================================
// ОБРОБНИКИ ПОДІЙ (DOM READY)
// ==========================================================
document.addEventListener('DOMContentLoaded', (event) => {
    const editModal = document.getElementById('editWebadminModal');
    const addModal = document.getElementById('addWebadminModal');
    
    // Обробники для кнопки закриття (X)
    if (editModal) {
        const closeBtnEdit = editModal.querySelector('.close-btn');
        if (closeBtnEdit) {
            closeBtnEdit.addEventListener('click', window.closeEditWebadminModal);
        }
    }
    
    if (addModal) {
        const closeBtnAdd = addModal.querySelector('.close-btn');
        if (closeBtnAdd) {
            closeBtnAdd.addEventListener('click', window.closeAddWebadminModal);
        }
    }
    
    // Глобальний обробник для закриття при кліку поза вікном (оверлей)
    window.onclick = function(event) {
        // Закрити модальне вікно редагування
        if (editModal && event.target === editModal) {
            window.closeEditWebadminModal();
        }
        
        // Закрити модальне вікно додавання
        if (addModal && event.target === addModal) {
            window.closeAddWebadminModal();
        }
    };
});