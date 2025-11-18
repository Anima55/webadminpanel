// ==========================================================
// ФУНКЦІОНАЛ ДЛЯ МОДАЛЬНОГО ВІКНА РЕДАГУВАННЯ (HelperInfo)
// ==========================================================

document.addEventListener('DOMContentLoaded', (event) => {
    // Перевіряємо, чи існує кнопка "Редагувати", щоб визначити, чи це сторінка HelperInfo
    const editButtonExists = document.querySelector('.edit-btn');

    if (editButtonExists) {
        const modal = document.getElementById('editModal');
        const closeBtn = document.querySelector('.close-btn');
        // Додаємо посилання на приховане поле ID для видалення
        const deleteIdInput = document.getElementById('modal_delete_helper_id'); 

        // 1. Функція для відкриття модального вікна
        window.openEditModal = function(button) {
            // Отримуємо рядок (<tr>), який є найближчим батьківським елементом кнопки
            const row = button.closest('tr');

            // Отримуємо дані з data-атрибутів рядка
            const id = row.dataset.id;
            const name = row.dataset.name;
            const rank = row.dataset.rank;
            const warnings = row.dataset.warnings;

            // Заповнюємо поля форми модального вікна
            document.getElementById('modal_helper_id').value = id;
            document.getElementById('modal_admin_name').value = name;
            document.getElementById('modal_admin_rank').value = rank;
            document.getElementById('modal_warnings_count').value = warnings;
            
            // НОВА ЛОГІКА: Заповнюємо приховане поле ID для форми видалення
            if (deleteIdInput) {
                deleteIdInput.value = id;
            }

            // Відображаємо модальне вікно
            modal.style.display = 'block';
        }

        // 2. Функція для закриття модального вікна
        window.closeEditModal = function() {
            modal.style.display = 'none';
        }

        // 3. Обробник для кнопки закриття (X)
        if (closeBtn) {
            closeBtn.addEventListener('click', closeEditModal);
        }

        // 4. Обробник для закриття при кліку поза вікном
        window.onclick = function(event) {
            if (event.target === modal) {
                closeEditModal();
            }
        }
    }
});

// ==========================================================
// ФУНКЦІОНАЛ ДЛЯ МОДАЛЬНОГО ВІКНА ФІЛЬТРАЦІЇ
// ==========================================================
window.openFilterModal = function() {
    const modal = document.getElementById('filterModal');
    if (modal) {
        modal.style.display = 'block';
    }
}

window.closeFilterModal = function() {
    const modal = document.getElementById('filterModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// ==========================================================
// ФУНКЦІОНАЛ АВТОМАТИЧНОГО СОРТУВАННЯ
// ==========================================================

window.applySort = function(field, buttonId) {
    const activeSortByInput = document.getElementById('active_sort_by');
    const activeSortTypeInput = document.getElementById('active_sort_type');
    
    const currentSortBy = activeSortByInput.value;
    let currentSortType = activeSortTypeInput.value || 'asc';

    // 1. Визначаємо новий тип сортування
    let newType = 'asc';
    
    if (field === currentSortBy) {
        // Якщо клікнули на той самий фільтр, перемикаємо напрямок
        newType = (currentSortType === 'asc') ? 'desc' : 'asc';
    } else {
        // Якщо обрали новий фільтр, починаємо із зростання (asc)
        newType = 'asc';
    }

    // 2. Оновлюємо приховані поля у формі
    activeSortByInput.value = field;
    activeSortTypeInput.value = newType;
    
    // 3. Надсилаємо форму для застосування фільтра
    document.getElementById('filterForm').submit();
    
    // 4. Закриваємо модальне вікно (опціонально, можна залишити відкритим, щоб було видно зміни)
    closeFilterModal();
}

// ==========================================================
// ФУНКЦІОНАЛ СКИДАННЯ ФІЛЬТРІВ СОРТУВАННЯ
// ==========================================================

window.resetSortFilters = function() {
    const activeSortByInput = document.getElementById('active_sort_by');
    const activeSortTypeInput = document.getElementById('active_sort_type');
    const filterForm = document.getElementById('filterForm');
    
    // 1. Очищаємо параметри сортування
    activeSortByInput.value = '';
    activeSortTypeInput.value = '';
    
    // 2. Надсилаємо форму. Це перезавантажить сторінку, використовуючи лише існуючий query (пошук).
    filterForm.submit();
    
    // 3. Закриваємо модальне вікно
    closeFilterModal();
}

// ==========================================================
// ФУНКЦІОНАЛ ДЛЯ МОДАЛЬНОГО ВІКНА ДОДАВАННЯ (HelperInfo)
// ==========================================================
document.addEventListener('DOMContentLoaded', () => {
    // Зберігаємо посилання на обидва модальні вікна
    const editModal = document.getElementById('editModal');
    const addModal = document.getElementById('addModal');

    // 1. Функція для відкриття модального вікна додавання
    window.openAddModal = function() {
        if (addModal) {
            addModal.style.display = 'block';
            
            // Очищення форми при відкритті
            document.getElementById('add_admin_name').value = '';
            document.getElementById('add_admin_rank').value = '';
            document.getElementById('add_warnings_count').value = '0'; 
        }
    };

    // 2. Функція для закриття модального вікна додавання
    window.closeAddModal = function() {
        if (addModal) {
            addModal.style.display = 'none';
        }
    };
    
    // 3. Оновлення обробника window.onclick для коректного закриття обох модальних вікон
    window.onclick = function(event) {
        if (editModal && event.target === editModal) {
            window.closeEditModal();
        }
        if (addModal && event.target === addModal) {
            window.closeAddModal();
        }
    };

    // Додаємо обробник для кнопки закриття (X) на AddModal
    if (addModal) {
        const closeBtnAdd = addModal.querySelector('.close-btn');
        if (closeBtnAdd) {
            closeBtnAdd.addEventListener('click', window.closeAddModal);
        }
    }
});