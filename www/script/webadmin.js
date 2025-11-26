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
    if (!editModal) {
        console.error("❌ Модальне вікно редагування не знайдено");
        return;
    }

    const row = button.closest('tr');
    // Отримуємо дані з data-атрибутів
    const id = row.dataset.id;
    const name = row.dataset.name;
    const rank = row.dataset.rank;
    
    console.log("📤 Заповнення форми редагування:", {id, name, rank});
    
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
    console.log("✅ Модальне вікно відкрито");
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
            rankSelect.selectedIndex = 0; // Обираємо першу опцію ("Curator")
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

/**
 * Функція для видалення веб-адміністратора
 */
window.deleteWebadmin = function() {
    const webadminId = document.getElementById('modal_webadmin_id').value;
    const webadminName = document.getElementById('modal_webadmin_name').value;
    
    if (confirm(`Ви впевнені, що хочете видалити веб-адміністратора "${webadminName}" (ID: ${webadminId})? Цю дію неможливо скасувати.`)) {
        // Створюємо тимчасову форму для видалення
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/delete-webadmin';
        
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'webadmin_id';
        input.value = webadminId;
        
        form.appendChild(input);
        document.body.appendChild(form);
        form.submit();
    }
}

// ==========================================================
// ФУНКЦІОНАЛ ДЛЯ ФІЛЬТРАЦІЇ ЗА РАНГОМ НА ADMIN-PAGE
// ==========================================================

/**
 * Застосовує фільтр за рангом для адмін-сторінки
 */
window.applyRankFilterAdmin = function() {
    const rankSelect = document.getElementById('rank_filter_select');
    const activeRankFilterInput = document.getElementById('active_rank_filter');
    const filterForm = document.getElementById('filterForm');
    
    if (rankSelect && activeRankFilterInput) {
        // Оновлюємо значення прихованого поля
        activeRankFilterInput.value = rankSelect.value;
        
        // Надсилаємо форму
        filterForm.submit();
    }
}

/**
 * Скидає всі фільтри для адмін-сторінки
 */
window.resetAdminFilters = function() {
    const activeSortByInput = document.getElementById('active_sort_by');
    const activeSortTypeInput = document.getElementById('active_sort_type');
    const activeRankFilterInput = document.getElementById('active_rank_filter');
    const rankSelect = document.getElementById('rank_filter_select');
    const searchInput = document.querySelector('input[name="query"]');
    const filterForm = document.getElementById('filterForm');
    
    // 1. Очищаємо параметри сортування та фільтрації
    activeSortByInput.value = '';
    activeSortTypeInput.value = 'asc';
    activeRankFilterInput.value = '';
    
    // 2. Скидаємо вибір у селекті
    if (rankSelect) {
        rankSelect.value = '';
    }
    
    // 3. Скидаємо пошуковий запит
    if (searchInput) {
        searchInput.value = '';
    }
    
    // 4. Скидаємо текст всіх кнопок сортування
    document.querySelectorAll('.sort-toggle-btn').forEach(button => {
        button.innerHTML = '🔄 Сортувати';
        button.style.backgroundColor = '#007bff';
    });
    
    // 5. Надсилаємо форму
    filterForm.submit();
}

/**
 * Застосовує всі фільтри для адмін-сторінки
 */
window.applyAllAdminFilters = function() {
    const rankSelect = document.getElementById('rank_filter_select');
    const activeRankFilterInput = document.getElementById('active_rank_filter');
    
    if (rankSelect && activeRankFilterInput) {
        activeRankFilterInput.value = rankSelect.value;
    }
    
    document.getElementById('filterForm').submit();
    closeFilterModal();
}

/**
 * Застосовує сортування для адмін-сторінки
 * @param {string} field - Поле для сортування
 * @param {string} buttonId - ID кнопки
 */
window.applySort = function(field, buttonId) {
    const activeSortByInput = document.getElementById('active_sort_by');
    const activeSortTypeInput = document.getElementById('active_sort_type');
    const filterForm = document.getElementById('filterForm');
    
    const currentSortBy = activeSortByInput.value;
    let currentSortType = activeSortTypeInput.value || 'asc';

    // Визначаємо новий тип сортування
    let newType = 'asc';
    
    if (field === currentSortBy) {
        newType = (currentSortType === 'asc') ? 'desc' : 'asc';
    } else {
        newType = 'asc';
    }

    // Оновлюємо приховані поля у формі
    activeSortByInput.value = field;
    activeSortTypeInput.value = newType;
    
    // Оновлюємо текст кнопки
    const button = document.getElementById(buttonId);
    if (button) {
        button.innerHTML = newType === 'desc' ? '⬇️ Спадання' : '⬆️ Зростання';
        button.style.backgroundColor = '#0056b3';
        
        // Скидаємо інші кнопки
        document.querySelectorAll('.sort-toggle-btn').forEach(btn => {
            if (btn.id !== buttonId) {
                btn.innerHTML = '🔄 Сортувати';
                btn.style.backgroundColor = '#007bff';
            }
        });
    }
    
    // Надсилаємо форму для застосування фільтра
    filterForm.submit();
}

/**
 * Відкриває модальне вікно фільтрації
 */
window.openFilterModal = function() {
    const modal = document.getElementById('filterModal');
    if (modal) {
        modal.style.display = 'block';
        updateSortButtonsText();
    }
}

/**
 * Закриває модальне вікно фільтрації
 */
window.closeFilterModal = function() {
    const modal = document.getElementById('filterModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

/**
 * Оновлює текст кнопок сортування
 */
window.updateSortButtonsText = function() {
    const activeSortBy = document.getElementById('active_sort_by').value;
    const activeSortType = document.getElementById('active_sort_type').value;
    
    const sortButtons = document.querySelectorAll('.sort-toggle-btn');
    sortButtons.forEach(button => {
        const sortField = button.getAttribute('data-sort-field');
        
        if (sortField === activeSortBy) {
            button.innerHTML = activeSortType === 'desc' ? '⬇️ Спадання' : '⬆️ Зростання';
            button.style.backgroundColor = '#0056b3';
        } else {
            button.innerHTML = '🔄 Сортувати';
            button.style.backgroundColor = '#007bff';
        }
    });
}

/**
 * Застосовує всі фільтри (загальна функція)
 */
window.applyAllFilters = function() {
    const rankSelect = document.getElementById('rank_filter_select');
    const activeRankFilterInput = document.getElementById('active_rank_filter');
    
    if (rankSelect && activeRankFilterInput) {
        activeRankFilterInput.value = rankSelect.value;
    }
    
    document.getElementById('filterForm').submit();
    closeFilterModal();
}

/**
 * Скидає всі фільтри сортування та фільтрації за рангом
 */
window.resetSortFilters = function() {
    const activeSortByInput = document.getElementById('active_sort_by');
    const activeSortTypeInput = document.getElementById('active_sort_type');
    const activeRankFilterInput = document.getElementById('active_rank_filter');
    const rankSelect = document.getElementById('rank_filter_select');
    const filterForm = document.getElementById('filterForm');
    
    // 1. Очищаємо параметри сортування та фільтрації
    activeSortByInput.value = '';
    activeSortTypeInput.value = 'asc';
    activeRankFilterInput.value = '';
    
    // 2. Скидаємо вибір у селекті
    if (rankSelect) {
        rankSelect.value = '';
    }
    
    // 3. Скидаємо текст всіх кнопок сортування
    document.querySelectorAll('.sort-toggle-btn').forEach(button => {
        button.innerHTML = '🔄 Сортувати';
        button.style.backgroundColor = '#007bff';
    });
    
    // 4. Надсилаємо форму
    filterForm.submit();
}

// ==========================================================
// ОБРОБНИКИ ПОДІЙ (DOM READY)
// ==========================================================
document.addEventListener('DOMContentLoaded', (event) => {
    const editModal = document.getElementById('editWebadminModal');
    const addModal = document.getElementById('addWebadminModal');
    const filterModal = document.getElementById('filterModal');
    
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
    
    if (filterModal) {
        const closeBtnFilter = filterModal.querySelector('.close-btn');
        if (closeBtnFilter) {
            closeBtnFilter.addEventListener('click', window.closeFilterModal);
        }
    }
    
    // Обробник для фільтра за рангом
    const rankSelect = document.getElementById('rank_filter_select');
    if (rankSelect) {
        rankSelect.addEventListener('change', function() {
            // Не застосовуємо автоматично
        });
    }
    
    // Обробник для пошукової форми - дозволяє пошук по Enter
    const searchInput = document.querySelector('input[name="query"]');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(event) {
            if (event.key === 'Enter') {
                event.preventDefault();
                document.getElementById('filterForm').submit();
            }
        });
    }
    
    // Глобальний обробник для закриття при кліку поза вікном (оверлей)
    window.addEventListener('click', function(event) {
        // Закрити модальне вікно редагування
        if (editModal && event.target === editModal) {
            window.closeEditWebadminModal();
        }
        
        // Закрити модальне вікно додавання
        if (addModal && event.target === addModal) {
            window.closeAddWebadminModal();
        }
        
        // Закрити модальне вікно фільтрації
        if (filterModal && event.target === filterModal) {
            window.closeFilterModal();
        }
    });
    
    // Ініціалізація стану фільтрів при завантаженні сторінки
    initializeFilterState();
    
    // Оновлюємо кнопки при завантаженні сторінки
    if (typeof updateSortButtonsText === 'function') {
        updateSortButtonsText();
    }
});

/**
 * Ініціалізує стан фільтрів при завантаженні сторінки
 */
function initializeFilterState() {
    const activeSortBy = document.getElementById('active_sort_by').value;
    const activeSortType = document.getElementById('active_sort_type').value;
    const activeRankFilter = document.getElementById('active_rank_filter').value;
    const rankSelect = document.getElementById('rank_filter_select');
    
    // Встановлюємо вибраний ранг у селекті
    if (rankSelect && activeRankFilter) {
        rankSelect.value = activeRankFilter;
    }
    
    console.log('Поточний стан фільтрів:', {
        sortBy: activeSortBy,
        sortType: activeSortType,
        rankFilter: activeRankFilter
    });
}

/**
 * Додаткові утилітні функції для роботи з фільтрами
 */

// Функція для отримання поточного стану фільтрів (для дебагу)
window.getCurrentFilterState = function() {
    return {
        sortBy: document.getElementById('active_sort_by').value,
        sortType: document.getElementById('active_sort_type').value,
        rankFilter: document.getElementById('active_rank_filter').value,
        searchQuery: document.querySelector('input[name="query"]').value
    };
}

// Функція для швидкого скидання тільки пошуку
window.resetSearchOnly = function() {
    const searchInput = document.querySelector('input[name="query"]');
    if (searchInput) {
        searchInput.value = '';
        document.getElementById('filterForm').submit();
    }
}