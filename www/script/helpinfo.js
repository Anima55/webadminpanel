// ==========================================================
// ГЛОБАЛЬНІ ЗМІННІ ТА ФУНКЦІЇ ДЛЯ МОДАЛЬНИХ ВІКОН
// ==========================================================

// Ієрархія рангів (від нижчого до вищого)
const RANK_HIERARCHY = {
    'Moder': 1,
    'Admin': 2,
    'Curator': 3,
    'Manager': 4,
    'SuperAdmin': 5
};

// Оголошуємо функції відкриття та закриття глобально
// для доступу з onclick в HTML.

/**
 * Перевіряє, чи може користувач редагувати співробітника з вказаним рангом
 * @param {string} userRank - Ранг користувача
 * @param {string} targetRank - Ранг співробітника для редагування
 * @returns {boolean} - Чи може редагувати
 */
window.canEditRank = function(userRank, targetRank) {
    const userLevel = RANK_HIERARCHY[userRank] || 0;
    const targetLevel = RANK_HIERARCHY[targetRank] || 0;
    
    // Користувач може редагувати тільки співробітників з рівнем НИЖЧЕ або РІВНИМ його рівню
    return targetLevel <= userLevel;
}

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

    // Отримуємо ранг користувача
    const userRank = document.body.getAttribute('data-user-rank') || 'Curator';
    
    // Перевіряємо права на редагування
    if (!window.canEditRank(userRank, rank)) {
        alert('Недостатньо прав для редагування співробітника з вищим рангом.');
        return;
    }

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

    // Оновлюємо доступні ранги відповідно до прав користувача
    updateAvailableRanks();

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
 * Відкриває модальне вікно додавання та очищає форму.
 */
window.openAddModal = function() {
    const addModal = document.getElementById('addModal');
    if (addModal) {
        
        // 1. Очищення текстового поля імені
        document.getElementById('add_admin_name').value = '';
        
        // 2. ВИПРАВЛЕННЯ: Коректне скидання поля Рангу (<select>)
        const rankSelect = document.getElementById('add_admin_rank');
        if (rankSelect && rankSelect.options.length > 0) {
            rankSelect.selectedIndex = 0; // Обираємо першу опцію
        }
        
        // 3. Скидання лічильника попереджень на 0
        document.getElementById('add_warnings_count').value = '0'; 
        
        // 4. Оновлюємо доступні ранги відповідно до прав користувача
        updateAvailableRanks();
        
        // 5. Відображення модального вікна
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

/**
 * Оновлює доступні ранги у формах відповідно до прав користувача
 */
window.updateAvailableRanks = function() {
    // Отримуємо поточний ранг користувача з атрибута body
    const userRank = document.body.getAttribute('data-user-rank') || 'Curator';
    const userLevel = RANK_HIERARCHY[userRank] || 0;
    
    // Фільтруємо ранги, щоб користувач міг встановлювати тільки ранги <= його рівню
    const availableRanks = Object.keys(RANK_HIERARCHY).filter(rank => {
        return RANK_HIERARCHY[rank] <= userLevel;
    });
    
    console.log('Доступні ранги для користувача', userRank, ':', availableRanks);
    
    // Оновлюємо селекти в формах редагування та додавання
    const rankSelects = document.querySelectorAll('select[name="admin_rank"]');
    rankSelects.forEach(select => {
        const currentValue = select.value;
        const isEditModal = select.id === 'modal_admin_rank';
        
        // Зберігаємо поточне значення для форми редагування
        let preservedValue = currentValue;
        
        // Очищуємо селект
        select.innerHTML = '';
        
        // Додаємо доступні опції
        availableRanks.forEach(rank => {
            const option = document.createElement('option');
            option.value = rank;
            option.textContent = rank;
            
            // Для форми редагування зберігаємо вибране значення, якщо воно доступне
            if (isEditModal && rank === preservedValue && availableRanks.includes(preservedValue)) {
                option.selected = true;
            }
            
            select.appendChild(option);
        });
        
        // Для форми додавання завжди вибираємо першу доступну опцію
        if (!isEditModal && availableRanks.length > 0) {
            select.value = availableRanks[0];
        }
        
        // Для форми редагування: якщо поточне значення не в списку доступних, вибираємо перше доступне
        if (isEditModal && !availableRanks.includes(preservedValue) && availableRanks.length > 0) {
            select.value = availableRanks[0];
        }
    });
}

/**
 * Перевіряє права доступу для дій з співробітниками
 */
window.checkUserPermissions = function() {
    const userRank = document.body.getAttribute('data-user-rank') || 'Curator';
    const userLevel = RANK_HIERARCHY[userRank] || 0;
    
    return {
        canAdd: ['Manager', 'SuperAdmin'].includes(userRank),
        canDelete: ['Manager', 'SuperAdmin'].includes(userRank),
        canSetManager: userLevel >= RANK_HIERARCHY['Manager'],
        canSetSuperAdmin: userLevel >= RANK_HIERARCHY['SuperAdmin'],
        userLevel: userLevel
    };
}

/**
 * Валідація форми додавання/редагування співробітника
 */
window.validateHelperForm = function(form) {
    const userRank = document.body.getAttribute('data-user-rank') || 'Curator';
    const selectedRank = form.querySelector('select[name="admin_rank"]').value;
    const helperId = form.querySelector('input[name="helper_id"]')?.value;
    
    // Для форми редагування: перевіряємо, чи не намагається користувач підвищити ранг співробітника вище свого
    if (helperId && !window.canEditRank(userRank, selectedRank)) {
        alert('Недостатньо прав для встановлення цього рангу. Ви не можете встановлювати ранги вище за свій.');
        return false;
    }
    
    // Для форми додавання: перевіряємо, чи не намагається користувач створити співробітника з рангом вище за свій
    if (!helperId && !window.canEditRank(userRank, selectedRank)) {
        alert('Недостатньо прав для створення співробітника з таким рангом. Ви не можете створювати співробітників з рангом вище за свій.');
        return false;
    }
    
    return true;
}

/**
 * Ініціалізує кнопки редагування на сторінці
 */
window.initializeEditButtons = function() {
    const userRank = document.body.getAttribute('data-user-rank') || 'Curator';
    const editButtons = document.querySelectorAll('.edit-btn');
    
    editButtons.forEach(button => {
        const row = button.closest('tr');
        if (row) {
            const targetRank = row.dataset.rank;
            
            // Перевіряємо, чи може користувач редагувати цього співробітника
            if (!window.canEditRank(userRank, targetRank)) {
                button.disabled = true;
                button.title = 'Недостатньо прав для редагування співробітників вище за рангом';
                button.style.opacity = '0.5';
                button.style.cursor = 'not-allowed';
            }
        }
    });
}

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
    
    // Обробники для форм
    const addForm = document.getElementById('addForm');
    const editForm = document.getElementById('editForm');
    
    if (addForm) {
        addForm.addEventListener('submit', function(e) {
            if (!window.validateHelperForm(this)) {
                e.preventDefault();
            }
        });
    }
    
    if (editForm) {
        editForm.addEventListener('submit', function(e) {
            if (!window.validateHelperForm(this)) {
                e.preventDefault();
            }
        });
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
    
    // Ініціалізація доступних рангів при завантаженні сторінки
    window.updateAvailableRanks();
    
    // Ініціалізація кнопок редагування
    window.initializeEditButtons();
    
    // Додаємо логування для дебагу
    console.log('Завантаження сторінки завершено');
    console.log('Ранг користувача:', document.body.getAttribute('data-user-rank'));
    console.log('Права доступу:', window.checkUserPermissions());
});

/**
 * Додаткові утилітні функції
 */

// Функція для підтвердження видалення з додатковими перевірками
window.confirmDeleteWithChecks = function(helperId, helperName) {
    const permissions = window.checkUserPermissions();
    
    if (!permissions.canDelete) {
        alert('Недостатньо прав для видалення співробітників.');
        return false;
    }
    
    return confirm(`Ви впевнені, що хочете видалити співробітника "${helperName}" (ID: ${helperId})?`);
}

// Функція для обмеження введення в числові поля
window.setupNumberInputValidation = function() {
    const numberInputs = document.querySelectorAll('input[type="number"][name="warnings_count"]');
    numberInputs.forEach(input => {
        input.addEventListener('input', function() {
            if (this.value < 0) {
                this.value = 0;
            }
        });
    });
}

// Ініціалізація додаткових функцій при завантаженні
document.addEventListener('DOMContentLoaded', function() {
    window.setupNumberInputValidation();
});