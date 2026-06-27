const { createApp } = Vue;

createApp({
  data() {
    return {
      tasks: [],
      loading: false,
      message: "",
      editingId: null,
      filters: {
        status: "",
        priority: "",
        q: "",
      },
      form: {
        title: "",
        description: "",
        priority: "medium",
        due_date: "",
        completed: false,
      },
    };
  },
  computed: {
    summaryText() {
      const total = this.tasks.length;
      const active = this.tasks.filter((task) => !task.completed).length;
      return `${total}件表示中 / 未完了 ${active}件`;
    },
  },
  watch: {
    filters: {
      deep: true,
      handler() {
        this.loadTasks();
      },
    },
  },
  mounted() {
    this.loadTasks();
  },
  methods: {
    async request(path, options = {}) {
      const response = await fetch(path, {
        headers: { "Content-Type": "application/json" },
        ...options,
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || "リクエストに失敗しました");
      }
      if (response.status === 204) {
        return null;
      }
      return response.json();
    },
    async loadTasks() {
      this.loading = true;
      const params = new URLSearchParams();
      Object.entries(this.filters).forEach(([key, value]) => {
        if (value) params.set(key, value);
      });
      try {
        this.tasks = await this.request(`/api/tasks?${params.toString()}`);
        this.message = "";
      } catch (error) {
        this.message = error.message;
      } finally {
        this.loading = false;
      }
    },
    async saveTask() {
      if (!this.form.title.trim()) return;
      const payload = {
        ...this.form,
        due_date: this.form.due_date || null,
      };
      try {
        if (this.editingId) {
          await this.request(`/api/tasks/${this.editingId}`, {
            method: "PUT",
            body: JSON.stringify(payload),
          });
          this.message = "タスクを更新しました。";
        } else {
          await this.request("/api/tasks", {
            method: "POST",
            body: JSON.stringify(payload),
          });
          this.message = "タスクを追加しました。";
        }
        this.resetForm();
        await this.loadTasks();
      } catch (error) {
        this.message = error.message;
      }
    },
    editTask(task) {
      this.editingId = task.id;
      this.form = {
        title: task.title,
        description: task.description,
        priority: task.priority,
        due_date: task.due_date || "",
        completed: task.completed,
      };
      window.scrollTo({ top: 0, behavior: "smooth" });
    },
    async toggleTask(task) {
      try {
        await this.request(`/api/tasks/${task.id}/toggle`, { method: "PATCH" });
        await this.loadTasks();
      } catch (error) {
        this.message = error.message;
      }
    },
    async removeTask(task) {
      if (!confirm(`「${task.title}」を削除しますか？`)) return;
      try {
        await this.request(`/api/tasks/${task.id}`, { method: "DELETE" });
        if (this.editingId === task.id) this.resetForm();
        await this.loadTasks();
        this.message = "タスクを削除しました。";
      } catch (error) {
        this.message = error.message;
      }
    },
    resetForm() {
      this.editingId = null;
      this.form = {
        title: "",
        description: "",
        priority: "medium",
        due_date: "",
        completed: false,
      };
    },
    priorityLabel(priority) {
      return { high: "高", medium: "中", low: "低" }[priority] || priority;
    },
    formatDateTime(value) {
      return new Intl.DateTimeFormat("ja-JP", {
        dateStyle: "short",
        timeStyle: "short",
      }).format(new Date(value));
    },
  },
}).mount("#app");
