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
