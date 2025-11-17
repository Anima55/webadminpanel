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