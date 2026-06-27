const { createApp } = Vue;

createApp({
  data() {
    return {
      apiOnline: false,
      loading: false,
      saving: false,
      error: "",
      tasks: [],
      summary: { total: 0, active: 0, completed: 0 },
      editingId: null,
      searchTimer: null,
      filters: {
        q: "",
        status: "all",
        priority: "all",
        sort: "created_desc",
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
  mounted() {
    this.checkHealth();
    this.loadTasks();
  },
  methods: {
    async checkHealth() {
      try {
        const response = await fetch("/api/health");
        this.apiOnline = response.ok;
      } catch {
        this.apiOnline = false;
      }
    },
    buildQuery() {
      const params = new URLSearchParams();
      params.set("status", this.filters.status);
      params.set("sort", this.filters.sort);
      if (this.filters.priority !== "all") {
        params.set("priority", this.filters.priority);
      }
      if (this.filters.q) {
        params.set("q", this.filters.q);
      }
      return params.toString();
    },
    async loadTasks() {
      this.loading = true;
      this.error = "";
      try {
        const response = await fetch(`/api/tasks?${this.buildQuery()}`);
        if (!response.ok) {
          throw new Error("タスク一覧を取得できませんでした。");
        }
        const data = await response.json();
        this.tasks = data.items;
        this.summary = {
          total: data.total,
          active: data.active,
          completed: data.completed,
        };
      } catch (error) {
        this.error = error.message;
      } finally {
        this.loading = false;
      }
    },
    debouncedLoad() {
      clearTimeout(this.searchTimer);
      this.searchTimer = setTimeout(() => this.loadTasks(), 250);
    },
    payload() {
      return {
        title: this.form.title,
        description: this.form.description,
        priority: this.form.priority,
        due_date: this.form.due_date || null,
        ...(this.editingId ? { completed: this.form.completed } : {}),
      };
    },
    async submitTask() {
      this.saving = true;
      this.error = "";
      try {
        const isEditing = Boolean(this.editingId);
        const response = await fetch(isEditing ? `/api/tasks/${this.editingId}` : "/api/tasks", {
          method: isEditing ? "PUT" : "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(this.payload()),
        });
        if (!response.ok) {
          throw new Error("タスクを保存できませんでした。入力内容を確認してください。");
        }
        this.resetForm();
        await this.loadTasks();
      } catch (error) {
        this.error = error.message;
      } finally {
        this.saving = false;
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
      this.error = "";
      try {
        const response = await fetch(`/api/tasks/${task.id}/toggle`, { method: "PATCH" });
        if (!response.ok) {
          throw new Error("完了状態を変更できませんでした。");
        }
        await this.loadTasks();
      } catch (error) {
        this.error = error.message;
      }
    },
    async deleteTask(task) {
      if (!confirm(`「${task.title}」を削除しますか？`)) {
        return;
      }
      this.error = "";
      try {
        const response = await fetch(`/api/tasks/${task.id}`, { method: "DELETE" });
        if (!response.ok) {
          throw new Error("タスクを削除できませんでした。");
        }
        if (this.editingId === task.id) {
          this.resetForm();
        }
        await this.loadTasks();
      } catch (error) {
        this.error = error.message;
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
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      }).format(new Date(value));
    },
  },
}).mount("#app");
