// ==========================================================
// ФУНКЦІОНАЛ ДЛЯ МОДАЛЬНОГО ВІКНА ФІЛЬТРАЦІЇ
// ==========================================================
window.openFilterTicketModal = function() {
    const modal = document.getElementById('ticketFilterModal');
    if (modal) {
        modal.style.display = 'block';
        // ОНОВЛЮЄМО ТЕКСТ КНОПОК ПРИ ВІДКРИТТІ МОДАЛЬНОГО ВІКНА
        updateSortButtonsText();
    }
}

window.closeFilterTicketModal = function() {
    const modal = document.getElementById('ticketFilterModal');
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

window.applyTicketSort = function(field, buttonId) {
    const activeSortByInput = document.getElementById('active_sort_by');
    const activeSortTypeInput = document.getElementById('active_sort_type');
    
    const currentSortBy = activeSortByInput.value;
    const currentSortType = activeSortTypeInput.value || 'asc';

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
    document.getElementById('filterForm').submit();
}

// ==========================================================
// ФУНКЦІОНАЛ СКИДАННЯ ФІЛЬТРІВ СОРТУВАННЯ
// ==========================================================

window.resetSortTicketFilters = function() {
    const activeSortByInput = document.getElementById('active_sort_by');
    const activeSortTypeInput = document.getElementById('active_sort_type');
    const filterForm = document.getElementById('filterForm');
    
    // 1. Очищаємо параметри сортування
    activeSortByInput.value = '';
    activeSortTypeInput.value = '';
    
    // 2. Скидаємо текст всіх кнопок
    document.querySelectorAll('.sort-toggle-btn').forEach(button => {
        button.innerHTML = '🔄 Сортувати';
        button.style.backgroundColor = '#007bff';
    });
    
    // 3. Надсилаємо форму
    filterForm.submit();
    
    // 4. Закриваємо модальне вікно
    closeFilterTicketModal();
}

// ОНОВЛЮЄМО КНОПКИ ПРИ ЗАВАНТАЖЕННІ СТОРІНКИ
document.addEventListener('DOMContentLoaded', function() {
    updateSortButtonsText();
});