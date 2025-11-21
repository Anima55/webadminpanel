// ==========================================================
// ФУНКЦІОНАЛ ЕКСПОРТУ В EXCEL (HelperInfo)
// ==========================================================
window.exportHelperInfoToExcel = function() {
    // 1. Створюємо тимчасову форму для відправки GET-запиту на експорт
    const exportForm = document.createElement('form');
    exportForm.method = 'GET';
    exportForm.action = '/export-helperinfo'; // Маршрут, доданий в app.py
    
    // 2. Отримуємо значення з поточних полів пошуку/сортування
    const searchQuery = document.getElementById('searchQuery').value;
    const activeSortBy = document.getElementById('active_sort_by').value;
    const activeSortType = document.getElementById('active_sort_type').value;

    // 3. Додаємо поля до тимчасової форми
    
    // Додаємо query
    const queryInput = document.createElement('input');
    queryInput.type = 'hidden';
    queryInput.name = 'query';
    queryInput.value = searchQuery;
    exportForm.appendChild(queryInput);
    
    // Додаємо sort_by (якщо є)
    if (activeSortBy) {
        const sortByInput = document.createElement('input');
        sortByInput.type = 'hidden';
        sortByInput.name = 'sort_by';
        sortByInput.value = activeSortBy;
        exportForm.appendChild(sortByInput);
    }
    
    // Додаємо sort_type (якщо є)
    if (activeSortType) {
        const sortTypeInput = document.createElement('input');
        sortTypeInput.type = 'hidden';
        sortTypeInput.name = 'sort_type';
        sortTypeInput.value = activeSortType;
        exportForm.appendChild(sortTypeInput);
    }

    // 4. Відправляємо форму для запуску завантаження
    document.body.appendChild(exportForm);
    exportForm.submit();
    document.body.removeChild(exportForm);
};

// ==========================================================
// ФУНКЦІОНАЛ ЕКСПОРТУ В EXCEL (TicketInfo)
// ==========================================================
window.exportTicketInfoToExcel = function() {
    // 1. Створюємо тимчасову форму для відправки GET-запиту на експорт
    const exportForm = document.createElement('form');
    exportForm.method = 'GET';
    exportForm.action = '/export-ticketinfo'; // Маршрут, доданий в app.py
    
    // 2. Отримуємо значення з поточних полів пошуку/сортування
    const searchQuery = document.getElementById('searchQuery').value;
    const activeSortBy = document.getElementById('active_sort_by').value;
    const activeSortType = document.getElementById('active_sort_type').value;

    // 3. Додаємо поля до тимчасової форми
    
    // Додаємо query
    const queryInput = document.createElement('input');
    queryInput.type = 'hidden';
    queryInput.name = 'query';
    queryInput.value = searchQuery;
    exportForm.appendChild(queryInput);
    
    // Додаємо sort_by (якщо є)
    if (activeSortBy) {
        const sortByInput = document.createElement('input');
        sortByInput.type = 'hidden';
        sortByInput.name = 'sort_by';
        sortByInput.value = activeSortBy;
        exportForm.appendChild(sortByInput);
    }
    
    // Додаємо sort_type (якщо є)
    if (activeSortType) {
        const sortTypeInput = document.createElement('input');
        sortTypeInput.type = 'hidden';
        sortTypeInput.name = 'sort_type';
        sortTypeInput.value = activeSortType;
        exportForm.appendChild(sortTypeInput);
    }

    // 4. Відправляємо форму для запуску завантаження
    document.body.appendChild(exportForm);
    exportForm.submit();
    document.body.removeChild(exportForm);
};