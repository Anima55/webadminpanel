// ==========================================================
// ФУНКЦІОНАЛ ДЛЯ МОДАЛЬНОГО ВІКНА ФІЛЬТРАЦІЇ HELPERINFO
// ==========================================================

/**
 * Відкриває модальне вікно фільтрації для HelperInfo
 */
window.openFilterModal = function() {
    const modal = document.getElementById('filterModal');
    if (modal) {
        modal.style.display = 'block';
        // ОНОВЛЮЄМО ТЕКСТ КНОПОК ПРИ ВІДКРИТТІ МОДАЛЬНОГО ВІКНА
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

// ФУНКЦІЯ ДЛЯ ОНОВЛЕННЯ ТЕКСТУ КНОПОК СОРТУВАННЯ
window.updateSortButtonsText = function() {
    const activeSortBy = document.getElementById('active_sort_by').value;
    const activeSortType = document.getElementById('active_sort_type').value;
    
    // Оновлюємо всі кнопки сортування
    const sortButtons = document.querySelectorAll('.sort-toggle-btn');
    sortButtons.forEach(button => {
        const sortField = button.getAttribute('data-sort-field');
        
        if (sortField === activeSortBy) {
            // Якщо це активне поле сортування
            button.innerHTML = activeSortType === 'desc' ? '⬇️ Спадання' : '⬆️ Зростання';
            button.style.backgroundColor = '#0056b3'; // Підсвічуємо активну кнопку
        } else {
            // Якщо поле не активне
            button.innerHTML = '🔄 Сортувати';
            button.style.backgroundColor = '#007bff'; // Повертаємо стандартний колір
        }
    });
}

/**
 * Застосовує сортування для HelperInfo
 * @param {string} field - Поле для сортування
 * @param {string} buttonId - ID кнопки (необов'язково)
 */
window.applySort = function(field, buttonId) {
    const activeSortByInput = document.getElementById('active_sort_by');
    const activeSortTypeInput = document.getElementById('active_sort_type');
    const filterForm = document.getElementById('filterForm');
    
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
    
    // 3. Оновлюємо текст кнопки
    const button = document.getElementById(buttonId);
    if (button) {
        button.innerHTML = newType === 'desc' ? '⬇️ Спадання' : '⬆️ Зростання';
        // Підсвічуємо активну кнопку
        button.style.backgroundColor = '#0056b3';
        
        // Скидаємо інші кнопки
        document.querySelectorAll('.sort-toggle-btn').forEach(btn => {
            if (btn.id !== buttonId) {
                btn.innerHTML = '🔄 Сортувати';
                btn.style.backgroundColor = '#007bff';
            }
        });
    }
    
    // 4. Надсилаємо форму для застосування фільтра
    filterForm.submit();
}

/**
 * Застосовує фільтр за рангом
 */
window.applyRankFilter = function() {
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
    
    // 4. Надсилаємо форму. Це перезавантажить сторінку без фільтрів.
    filterForm.submit();
}

// ==========================================================
// ОБРОБНИКИ ПОДІЙ ПІСЛЯ ЗАВАНТАЖЕННЯ DOM
// ==========================================================

document.addEventListener('DOMContentLoaded', function() {
    const filterModal = document.getElementById('filterModal');
    const rankSelect = document.getElementById('rank_filter_select');
    
    // Обробник для закриття модального вікна при кліку на "X"
    if (filterModal) {
        const closeBtn = filterModal.querySelector('.close-btn');
        if (closeBtn) {
            closeBtn.addEventListener('click', closeFilterModal);
        }
    }
    
    // Обробник для фільтра за рангом - автоматичне застосування при виборі
    if (rankSelect) {
        rankSelect.addEventListener('change', function() {
            // Не застосовуємо автоматично, даємо користувачу можливість вибрати кілька параметрів
            // Застосування відбувається при закритті модального вікна або через окрему кнопку
        });
    }
    
    // Глобальний обробник для закриття модального вікна при кліку поза ним
    window.addEventListener('click', function(event) {
        if (filterModal && event.target === filterModal) {
            closeFilterModal();
        }
    });
    
    // Обробник для пошукової форми - дозволяє пошук по Enter
    const searchInput = document.getElementById('searchQuery');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(event) {
            if (event.key === 'Enter') {
                event.preventDefault();
                document.getElementById('filterForm').submit();
            }
        });
    }
    
    // Ініціалізація стану фільтрів при завантаженні сторінки
    initializeFilterState();
    // Оновлюємо стан кнопок при завантаженні сторінки
    updateSortButtonsText();
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
        searchQuery: document.getElementById('searchQuery').value
    };
}

// Функція для швидкого скидання тільки пошуку
window.resetSearchOnly = function() {
    const searchInput = document.getElementById('searchQuery');
    if (searchInput) {
        searchInput.value = '';
        document.getElementById('filterForm').submit();
    }
}

// Функція для застосування всіх фільтрів з модального вікна
window.applyAllFilters = function() {
    const rankSelect = document.getElementById('rank_filter_select');
    const activeRankFilterInput = document.getElementById('active_rank_filter');
    
    if (rankSelect && activeRankFilterInput) {
        activeRankFilterInput.value = rankSelect.value;
    }
    
    document.getElementById('filterForm').submit();
    closeFilterModal();
}