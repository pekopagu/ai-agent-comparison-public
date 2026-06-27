// タスク管理アプリ フロントエンド（Vue 3）
const { createApp, reactive, ref, onMounted } = Vue;

const API = "/api";

createApp({
  setup() {
    const tasks = ref([]);
    const stats = reactive({ total: 0, completed: 0, active: 0 });
    const loading = ref(false);
    const errorMessage = ref("");
    const editingId = ref(null);
    const currentFilter = ref("all");
    const searchQuery = ref("");

    const filters = [
      { label: "すべて", value: "all" },
      { label: "未完了", value: "active" },
      { label: "完了", value: "completed" },
    ];

    const form = reactive({
      title: "",
      description: "",
      priority: "medium",
      due_date: "",
    });

    // --- API 呼び出し ---
    async function fetchTasks() {
      loading.value = true;
      try {
        const params = new URLSearchParams({ filter: currentFilter.value });
        if (searchQuery.value.trim()) {
          params.append("search", searchQuery.value.trim());
        }
        const res = await fetch(`${API}/tasks?${params.toString()}`);
        if (!res.ok) throw new Error("一覧の取得に失敗しました");
        tasks.value = await res.json();
      } catch (e) {
        errorMessage.value = e.message;
      } finally {
        loading.value = false;
      }
    }

    async function fetchStats() {
      try {
        const res = await fetch(`${API}/stats`);
        if (res.ok) {
          const data = await res.json();
          stats.total = data.total;
          stats.completed = data.completed;
          stats.active = data.active;
        }
      } catch (e) {
        // 統計の失敗は致命的ではないので無視
      }
    }

    async function refresh() {
      await Promise.all([fetchTasks(), fetchStats()]);
    }

    function resetForm() {
      form.title = "";
      form.description = "";
      form.priority = "medium";
      form.due_date = "";
      editingId.value = null;
      errorMessage.value = "";
    }

    function buildPayload() {
      return {
        title: form.title.trim(),
        description: form.description.trim() || null,
        priority: form.priority,
        due_date: form.due_date || null,
      };
    }

    async function submitTask() {
      errorMessage.value = "";
      if (!form.title.trim()) {
        errorMessage.value = "タイトルを入力してください";
        return;
      }
      try {
        let res;
        if (editingId.value) {
          res = await fetch(`${API}/tasks/${editingId.value}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(buildPayload()),
          });
        } else {
          res = await fetch(`${API}/tasks`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(buildPayload()),
          });
        }
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(extractError(err) || "保存に失敗しました");
        }
        resetForm();
        await refresh();
      } catch (e) {
        errorMessage.value = e.message;
      }
    }

    function startEdit(task) {
      editingId.value = task.id;
      form.title = task.title;
      form.description = task.description || "";
      form.priority = task.priority;
      form.due_date = task.due_date || "";
      errorMessage.value = "";
      window.scrollTo({ top: 0, behavior: "smooth" });
    }

    function cancelEdit() {
      resetForm();
    }

    async function toggleTask(task) {
      try {
        const res = await fetch(`${API}/tasks/${task.id}/toggle`, {
          method: "PATCH",
        });
        if (!res.ok) throw new Error("状態の更新に失敗しました");
        await refresh();
      } catch (e) {
        errorMessage.value = e.message;
      }
    }

    async function deleteTask(task) {
      if (!confirm(`「${task.title}」を削除しますか？`)) return;
      try {
        const res = await fetch(`${API}/tasks/${task.id}`, { method: "DELETE" });
        if (!res.ok) throw new Error("削除に失敗しました");
        if (editingId.value === task.id) resetForm();
        await refresh();
      } catch (e) {
        errorMessage.value = e.message;
      }
    }

    function setFilter(value) {
      currentFilter.value = value;
      fetchTasks();
    }

    // 検索のデバウンス
    let debounceTimer = null;
    function debouncedFetch() {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(fetchTasks, 300);
    }

    function priorityLabel(priority) {
      return { low: "低", medium: "中", high: "高" }[priority] || priority;
    }

    function extractError(err) {
      if (!err || !err.detail) return null;
      if (typeof err.detail === "string") return err.detail;
      if (Array.isArray(err.detail)) {
        return err.detail.map((d) => d.msg).join(", ");
      }
      return null;
    }

    onMounted(refresh);

    return {
      tasks,
      stats,
      loading,
      errorMessage,
      editingId,
      currentFilter,
      searchQuery,
      filters,
      form,
      submitTask,
      startEdit,
      cancelEdit,
      toggleTask,
      deleteTask,
      setFilter,
      debouncedFetch,
      priorityLabel,
    };
  },
}).mount("#app");
