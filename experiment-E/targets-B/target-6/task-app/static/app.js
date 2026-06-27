const { createApp, ref, reactive, onMounted } = Vue;

createApp({
    setup() {
        const tasks = ref([]);
        const dragOverColumn = ref(null);
        let draggedTask = null;
        let debounceTimeout = null;

        // フィルター状態
        const filters = reactive({
            q: '',
            priority: ''
        });

        // フォーム状態
        const form = reactive({
            id: null,
            title: '',
            description: '',
            due_date: '',
            priority: 'medium',
            status: 'todo'
        });

        // モーダルの状態
        const modal = reactive({
            show: false,
            isEdit: false
        });

        // トースト通知の状態
        const toast = reactive({
            show: false,
            message: '',
            type: 'success'
        });

        // APIからタスクを取得
        const fetchTasks = async () => {
            try {
                let url = '/api/tasks?';
                const params = new URLSearchParams();
                if (filters.priority) params.append('priority', filters.priority);
                if (filters.q) params.append('q', filters.q);
                
                const response = await fetch(url + params.toString());
                if (!response.ok) throw new Error('タスクの取得に失敗しました');
                
                tasks.value = await response.json();
            } catch (error) {
                showToast(error.message, 'error');
            }
        };

        // 検索時のデバウンス処理
        const debouncedFetchTasks = () => {
            clearTimeout(debounceTimeout);
            debounceTimeout = setTimeout(() => {
                fetchTasks();
            }, 300);
        };

        // 検索窓クリア
        const clearSearch = () => {
            filters.q = '';
            fetchTasks();
        };

        // カラムごとのタスクフィルタ
        const getTasksByStatus = (status) => {
            return tasks.value.filter(task => task.status === status);
        };

        // カラムのタスク数をカウント
        const getTaskCount = (status) => {
            return getTasksByStatus(status).length;
        };

        // 優先度ラベル取得
        const getPriorityLabel = (priority) => {
            const labels = { high: '高', medium: '中', low: '低' };
            return labels[priority] || '中';
        };

        // 期限切れ判定
        const isOverdue = (dueDate) => {
            if (!dueDate) return false;
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            
            const due = new Date(dueDate);
            due.setHours(0, 0, 0, 0);
            
            return due < today;
        };

        // ドラッグ＆ドロップのイベントハンドラ
        const dragStartTask = (task) => {
            draggedTask = task;
            // ドラッグ中のクラス適用
            setTimeout(() => {
                const el = document.getElementById(`task-${task.id}`);
                if (el) el.classList.add('dragging');
            }, 0);
        };

        const dragEndTask = () => {
            if (draggedTask) {
                const el = document.getElementById(`task-${draggedTask.id}`);
                if (el) el.classList.remove('dragging');
            }
            draggedTask = null;
            dragOverColumn.value = null;
        };

        const dragEnterColumn = (status) => {
            dragOverColumn.value = status;
        };

        const dragLeaveColumn = (status) => {
            if (dragOverColumn.value === status) {
                dragOverColumn.value = null;
            }
        };

        const dropTask = async (status) => {
            if (!draggedTask) return;
            
            const oldStatus = draggedTask.status;
            if (oldStatus === status) {
                dragEndTask();
                return;
            }

            try {
                // 楽観的UI更新
                draggedTask.status = status;

                const response = await fetch(`/api/tasks/${draggedTask.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status })
                });

                if (!response.ok) throw new Error('ステータスの更新に失敗しました');
                
                showToast('タスクを移動しました', 'success');
                fetchTasks(); // 最新情報を再取得
            } catch (error) {
                // 失敗した場合は差し戻す
                draggedTask.status = oldStatus;
                showToast(error.message, 'error');
            } finally {
                dragEndTask();
            }
        };

        // モーダルの表示制御
        const openCreateModal = () => {
            modal.isEdit = false;
            form.id = null;
            form.title = '';
            form.description = '';
            form.due_date = '';
            form.priority = 'medium';
            form.status = 'todo';
            modal.show = true;
        };

        const openEditModal = (task) => {
            modal.isEdit = true;
            form.id = task.id;
            form.title = task.title;
            form.description = task.description || '';
            form.due_date = task.due_date || '';
            form.priority = task.priority;
            form.status = task.status;
            modal.show = true;
        };

        const closeModal = () => {
            modal.show = false;
        };

        // フォームの送信処理
        const submitForm = async () => {
            try {
                const payload = {
                    title: form.title,
                    description: form.description || null,
                    due_date: form.due_date || null,
                    priority: form.priority
                };

                if (modal.isEdit) {
                    payload.status = form.status;
                    const response = await fetch(`/api/tasks/${form.id}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });

                    if (!response.ok) throw new Error('タスクの更新に失敗しました');
                    showToast('タスクを更新しました', 'success');
                } else {
                    const response = await fetch('/api/tasks', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });

                    if (!response.ok) throw new Error('タスクの作成に失敗しました');
                    showToast('タスクを作成しました', 'success');
                }

                closeModal();
                fetchTasks();
            } catch (error) {
                showToast(error.message, 'error');
            }
        };

        // タスクの削除
        const deleteTask = async (id) => {
            if (!confirm('このタスクを削除してもよろしいですか？')) return;

            try {
                const response = await fetch(`/api/tasks/${id}`, {
                    method: 'DELETE'
                });

                if (!response.ok) throw new Error('タスクの削除に失敗しました');
                
                showToast('タスクを削除しました', 'success');
                fetchTasks();
            } catch (error) {
                showToast(error.message, 'error');
            }
        };

        // トースト通知の表示
        const showToast = (message, type = 'success') => {
            toast.message = message;
            toast.type = type;
            toast.show = true;
            setTimeout(() => {
                toast.show = false;
            }, 3000);
        };

        onMounted(() => {
            fetchTasks();
        });

        return {
            tasks,
            filters,
            form,
            modal,
            toast,
            dragOverColumn,
            fetchTasks,
            debouncedFetchTasks,
            clearSearch,
            getTasksByStatus,
            getTaskCount,
            getPriorityLabel,
            isOverdue,
            dragStartTask,
            dragEndTask,
            dragEnterColumn,
            dragLeaveColumn,
            dropTask,
            openCreateModal,
            openEditModal,
            closeModal,
            submitForm,
            deleteTask
        };
    }
}).mount('#app');
