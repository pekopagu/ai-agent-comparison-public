const { createApp, ref, onMounted, watch } = Vue;

createApp({
    setup() {
        const tasks = ref([]);
        const tags = ref([]);
        const analytics = ref({
            total_tasks: 0,
            todo_tasks: 0,
            in_progress_tasks: 0,
            done_tasks: 0,
            completion_rate: 0,
            high_priority_tasks: 0,
            overdue_tasks: 0
        });

        const loading = ref(false);
        
        // Filter states
        const searchQuery = ref('');
        const filterStatus = ref('');
        const filterPriority = ref('');
        const filterTag = ref('');
        
        // Modals
        const showTaskModal = ref(false);
        const showTagModal = ref(false);
        
        // Form states
        const isEditing = ref(false);
        const currentTask = ref({
            id: null,
            title: '',
            description: '',
            status: 'todo',
            priority: 'medium',
            due_date: '',
            tags: []
        });
        const tagInputText = ref('');
        
        // Tag Manager Form
        const newTagName = ref('');
        const newTagColor = ref('#6366f1');

        const API_BASE = '/api';

        // Fetch tasks with filters
        const fetchTasks = async () => {
            loading.value = true;
            try {
                const params = new URLSearchParams();
                if (searchQuery.value) params.append('search', searchQuery.value);
                if (filterStatus.value) params.append('status', filterStatus.value);
                if (filterPriority.value) params.append('priority', filterPriority.value);
                if (filterTag.value) params.append('tag', filterTag.value);

                const response = await fetch(`${API_BASE}/tasks?${params.toString()}`);
                if (!response.ok) throw new Error('Failed to fetch tasks');
                tasks.value = await response.json();
            } catch (error) {
                console.error('Error fetching tasks:', error);
            } finally {
                loading.value = false;
            }
        };

        // Fetch all tags
        const fetchTags = async () => {
            try {
                const response = await fetch(`${API_BASE}/tags`);
                if (!response.ok) throw new Error('Failed to fetch tags');
                tags.value = await response.json();
            } catch (error) {
                console.error('Error fetching tags:', error);
            }
        };

        // Fetch statistics
        const fetchAnalytics = async () => {
            try {
                const response = await fetch(`${API_BASE}/analytics`);
                if (!response.ok) throw new Error('Failed to fetch analytics');
                analytics.value = await response.json();
            } catch (error) {
                console.error('Error fetching analytics:', error);
            }
        };

        const fetchData = () => {
            fetchTasks();
            fetchTags();
            fetchAnalytics();
        };

        // Watchers to trigger search and filter automatically
        // Debounce search slightly to avoid excessive API requests
        let searchTimeout;
        watch(searchQuery, () => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                fetchTasks();
            }, 300);
        });

        watch([filterStatus, filterPriority, filterTag], () => {
            fetchTasks();
        });

        const clearFilters = () => {
            searchQuery.value = '';
            filterStatus.value = '';
            filterPriority.value = '';
            filterTag.value = '';
        };

        // Task Modal Handlers
        const openCreateTaskModal = (colStatus = 'todo') => {
            isEditing.value = false;
            currentTask.value = {
                id: null,
                title: '',
                description: '',
                status: colStatus,
                priority: 'medium',
                due_date: '',
                tags: []
            };
            tagInputText.value = '';
            showTaskModal.value = true;
        };

        const openEditTaskModal = (task) => {
            isEditing.value = true;
            currentTask.value = {
                id: task.id,
                title: task.title,
                description: task.description || '',
                status: task.status,
                priority: task.priority,
                due_date: task.due_date || '',
                tags: task.tags.map(t => t.name) // Map tag objects to name strings
            };
            tagInputText.value = '';
            showTaskModal.value = true;
        };

        // Manage inline tag tags array in Form
        const addTagToCurrentTask = () => {
            const name = tagInputText.value.trim();
            if (name && !currentTask.value.tags.includes(name)) {
                currentTask.value.tags.push(name);
            }
            tagInputText.value = '';
        };

        const removeTagFromCurrentTask = (index) => {
            currentTask.value.tags.splice(index, 1);
        };

        // Save Task (Create or Update)
        const saveTask = async () => {
            if (!currentTask.value.title.trim()) return;
            
            // Add any text remaining in the tag input field
            if (tagInputText.value.trim()) {
                addTagToCurrentTask();
            }

            const url = isEditing.value 
                ? `${API_BASE}/tasks/${currentTask.value.id}`
                : `${API_BASE}/tasks`;
            
            const method = isEditing.value ? 'PUT' : 'POST';

            try {
                const response = await fetch(url, {
                    method: method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(currentTask.value)
                });

                if (!response.ok) throw new Error('Failed to save task');
                
                showTaskModal.value = false;
                fetchData();
            } catch (error) {
                console.error('Error saving task:', error);
                alert('タスクの保存に失敗しました。');
            }
        };

        // Delete Task
        const deleteTask = async (taskId) => {
            if (!confirm('このタスクを削除してもよろしいですか？')) return;
            try {
                const response = await fetch(`${API_BASE}/tasks/${taskId}`, {
                    method: 'DELETE'
                });
                if (!response.ok) throw new Error('Failed to delete task');
                fetchData();
            } catch (error) {
                console.error('Error deleting task:', error);
                alert('タスクの削除に失敗しました。');
            }
        };

        // Drag & Drop Functionality
        const dragStart = (task, event) => {
            event.dataTransfer.setData('text/plain', task.id);
            event.dataTransfer.effectAllowed = 'move';
        };

        const dropCard = async (newStatus, event) => {
            const taskId = event.dataTransfer.getData('text/plain');
            if (!taskId) return;
            
            const task = tasks.value.find(t => t.id == taskId);
            if (!task || task.status === newStatus) return;

            // Optimistic Update
            const oldStatus = task.status;
            task.status = newStatus;

            try {
                const response = await fetch(`${API_BASE}/tasks/${taskId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status: newStatus })
                });

                if (!response.ok) throw new Error('Failed to update task status');
                
                // Fetch stats and update list properly
                fetchAnalytics();
                fetchTasks(); // Refresh to ensure tag order & server consistency
            } catch (error) {
                console.error('Error dragging task:', error);
                // Revert
                task.status = oldStatus;
                alert('ステータスの更新に失敗しました。');
            }
        };

        // Quick status updater (clicks for mobile or fallback)
        const moveStatus = async (task, newStatus) => {
            try {
                const response = await fetch(`${API_BASE}/tasks/${task.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status: newStatus })
                });

                if (!response.ok) throw new Error('Failed to update task status');
                fetchData();
            } catch (error) {
                console.error('Error changing status:', error);
                alert('ステータスの更新に失敗しました。');
            }
        };

        // Tag Manager operations
        const createTag = async () => {
            const name = newTagName.value.trim();
            if (!name) return;

            try {
                const response = await fetch(`${API_BASE}/tags`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, color: newTagColor.value })
                });

                if (!response.ok) throw new Error('Failed to create tag');
                
                newTagName.value = '';
                newTagColor.value = '#6366f1';
                fetchTags();
            } catch (error) {
                console.error('Error creating tag:', error);
                alert('タグの作成に失敗しました（重複している可能性があります）。');
            }
        };

        const deleteTag = async (tagId) => {
            if (!confirm('このタグを削除しますか？このタグはすべてのタスクから外されます。')) return;

            try {
                const response = await fetch(`${API_BASE}/tags/${tagId}`, {
                    method: 'DELETE'
                });

                if (!response.ok) throw new Error('Failed to delete tag');
                
                fetchTags();
                fetchTasks(); // Refresh tasks as some tags might be removed
            } catch (error) {
                console.error('Error deleting tag:', error);
                alert('タグの削除に失敗しました。');
            }
        };

        // Date Helpers
        const formatDate = (dateStr) => {
            if (!dateStr) return '';
            const d = new Date(dateStr);
            return `${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()}`;
        };

        const isOverdue = (task) => {
            if (!task.due_date || task.status === 'done') return false;
            const today = new Date();
            today.setHours(0,0,0,0);
            const due = new Date(task.due_date);
            due.setHours(0,0,0,0);
            return due < today;
        };

        // Filter lists for Kanban columns
        const getColumnTasks = (status) => {
            return tasks.value.filter(t => t.status === status);
        };

        onMounted(() => {
            fetchData();
        });

        return {
            tasks,
            tags,
            analytics,
            loading,
            
            // Filters
            searchQuery,
            filterStatus,
            filterPriority,
            filterTag,
            clearFilters,
            
            // Modals
            showTaskModal,
            showTagModal,
            openCreateTaskModal,
            openEditTaskModal,
            
            // Forms
            isEditing,
            currentTask,
            tagInputText,
            addTagToCurrentTask,
            removeTagFromCurrentTask,
            saveTask,
            deleteTask,
            
            // Tag Manager
            newTagName,
            newTagColor,
            createTag,
            deleteTag,
            
            // Drag Drop & Actions
            dragStart,
            dropCard,
            moveStatus,
            getColumnTasks,
            
            // Helpers
            formatDate,
            isOverdue
        };
    }
}).mount('#app');
