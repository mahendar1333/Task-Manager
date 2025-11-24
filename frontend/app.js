let token = null;
let currentUserName = "Guest";
const API = "http://localhost:5000";

/* Store tasks globally */
let allTasks = [];

/* ====================== TOAST NOTIFICATION ====================== */
function showToast(message, type = "info") {
    const toast = document.getElementById("toast");
    toast.innerText = message;

    toast.style.background =
        type === "success" ? "#16a34a" :
        type === "error"   ? "#dc2626" :
        "#2563eb";

    toast.classList.add("show");
    toast.classList.remove("hidden");

    setTimeout(() => {
        toast.classList.remove("show");
        setTimeout(() => toast.classList.add("hidden"), 300);
    }, 2500);
}

/* ======================================================
   BASIC HELPERS
====================================================== */
function hideAllPages() {
    document.getElementById("auth-section").classList.add("hidden");
    document.getElementById("register-section").classList.add("hidden");
    document.getElementById("task-section").classList.add("hidden");
    document.getElementById("edit-modal").classList.add("hidden");
}

function updateUserNameUI() {
    document.getElementById("welcome-user").innerText = currentUserName;
    document.getElementById("sidebar-user").innerText = currentUserName;
}

/* ======================================================
   NAVIGATION
====================================================== */
function showLogin() {
    hideAllPages();
    document.getElementById("auth-section").classList.remove("hidden");
}

function showRegister() {
    hideAllPages();
    document.getElementById("register-section").classList.remove("hidden");
}

function showTasksPage() {
    if (!token) return showToast("Please login first", "error");
    hideAllPages();
    document.getElementById("task-section").classList.remove("hidden");
    loadTasks();
}

/* ======================================================
   REGISTER USER
====================================================== */
async function register() {
    const name = document.getElementById("reg-name").value.trim();
    const email = document.getElementById("reg-email").value.trim();
    const phone = document.getElementById("reg-phone").value.trim();
    const password = document.getElementById("reg-password").value.trim();

    if (!name || !email || !password)
        return showToast("Name, email, password are required", "error");

    const res = await fetch(`${API}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, phone, password })
    });

    const data = await res.json();
    showToast(data.message || data.error, data.message ? "success" : "error");
}

/* ======================================================
   LOGIN
====================================================== */
async function login() {
    const email = document.getElementById("login-email").value.trim();
    const password = document.getElementById("login-password").value.trim();

    if (!email || !password) return showToast("Enter email & password", "error");

    const res = await fetch(`${API}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
    });

    const data = await res.json();

    if (!data.token) return showToast(data.error, "error");

    token = data.token;
    currentUserName = (data.user?.name) || email.split("@")[0];

    updateUserNameUI();
    showToast("Logged in successfully!", "success");
    showTasksPage();
}

/* ======================================================
   LOAD TASKS + DASHBOARD STATS
====================================================== */
async function loadTasks() {
    const res = await fetch(`${API}/tasks/list`, {
        headers: { Authorization: "Bearer " + token }
    });

    const data = await res.json();
    allTasks = data.tasks || [];

    const list = document.getElementById("task-list");
    const countLabel = document.getElementById("tasks-count");

    list.innerHTML = "";

    if (allTasks.length === 0) {
        list.innerHTML = `<p>No tasks found.</p>`;
        updateStats(0, 0, 0, 0);
        countLabel.innerText = "0 tasks";
        return;
    }

    let total = allTasks.length;
    let pending = allTasks.filter(t => !t.is_completed).length;
    let completed = allTasks.filter(t => t.is_completed).length;
    let upcoming = allTasks.filter(t => new Date(t.due_datetime) > new Date()).length;

    updateStats(total, pending, completed, upcoming);

    countLabel.innerText = `${total} tasks`;

    allTasks.forEach(task => renderTaskCard(task, list));
}

/* ======================================================
   DASHBOARD FILTER FUNCTIONS
====================================================== */
function showAllTasks() {
    renderFiltered(allTasks);
}

function showPendingTasks() {
    renderFiltered(allTasks.filter(t => !t.is_completed));
}

function showCompletedTasks() {
    renderFiltered(allTasks.filter(t => t.is_completed));
}

function showUpcomingTasks() {
    let now = new Date();
    renderFiltered(allTasks.filter(t => new Date(t.due_datetime) > now));
}

function renderFiltered(listArray) {
    const container = document.getElementById("task-list");
    const countLabel = document.getElementById("tasks-count");

    container.innerHTML = "";
    countLabel.innerText = `${listArray.length} tasks`;

    if (listArray.length === 0) {
        container.innerHTML = `<p>No tasks in this category.</p>`;
        return;
    }

    listArray.forEach(task => renderTaskCard(task, container));
}

/* ======================================================
   UPDATE DASHBOARD STATS
====================================================== */
function updateStats(total, pending, completed, upcoming) {
    document.getElementById("stat-total").innerText = total;
    document.getElementById("stat-pending").innerText = pending;
    document.getElementById("stat-completed").innerText = completed;
    document.getElementById("stat-upcoming").innerText = upcoming;
}

/* ======================================================
   RENDER TASK CARD
====================================================== */
function renderTaskCard(task, container) {
    const card = document.createElement("div");
    card.className = "task-item fade-in";

    card.innerHTML = `
        <div class="task-title-line">
            <div class="task-title">${task.title}</div>
            <span class="status-pill ${task.is_completed ? "status-completed" : "status-pending"}">
                ${task.is_completed ? "Completed" : "Pending"}
            </span>
        </div>

        <p>${task.description || ""}</p>
        <p class="task-meta"><strong>Due:</strong> ${task.due_datetime}</p>

        <div class="progress-container">
            <div class="progress-bar" style="width:${task.is_completed ? "100%" : "40%"}"></div>
        </div>

        <div class="task-actions">
            <button class="btn-toggle">${task.is_completed ? "Mark Pending" : "Mark Complete"}</button>
            <button class="btn-edit">Edit</button>
            <button class="btn-delete">Delete</button>
        </div>
    `;

    card.querySelector(".btn-edit").onclick = () => openEditModal(task);
    card.querySelector(".btn-delete").onclick = () => deleteTask(task.id);
    card.querySelector(".btn-toggle").onclick =
        () => toggleTaskStatus(task.id, !task.is_completed);

    container.appendChild(card);
}

/* ======================================================
   TOGGLE COMPLETE / PENDING
====================================================== */
async function toggleTaskStatus(id, newStatus) {
    await fetch(`${API}/tasks/update/${id}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
            Authorization: "Bearer " + token
        },
        body: JSON.stringify({ is_completed: newStatus })
    });

    showToast(newStatus ? "Task marked complete!" : "Task marked pending", "success");
    loadTasks();
}

/* ======================================================
   CREATE TASK
====================================================== */
async function createTask() {
    const title = document.getElementById("task-title").value.trim();
    const desc = document.getElementById("task-desc").value.trim();
    const due = document.getElementById("task-due").value;
    const remind = document.getElementById("task-reminder").value;

    if (!title) return showToast("Task title required!", "error");

    await fetch(`${API}/tasks/create`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            Authorization: "Bearer " + token
        },
        body: JSON.stringify({
            title,
            description: desc,
            due_datetime: due,
            reminder_datetime: remind
        })
    });

    showToast("Task created successfully!", "success");
    loadTasks();
}

/* ======================================================
   DELETE TASK
====================================================== */
async function deleteTask(id) {
    if (!confirm("Delete this task?")) return;

    await fetch(`${API}/tasks/delete/${id}`, {
        method: "DELETE",
        headers: { Authorization: "Bearer " + token }
    });

    showToast("Task deleted!", "success");
    loadTasks();
}

/* ======================================================
   EDIT MODAL
====================================================== */
function openEditModal(task) {
    document.getElementById("edit-title").value = task.title;
    document.getElementById("edit-desc").value = task.description;
    document.getElementById("edit-due").value = task.due_datetime.replace(" ", "T");
    document.getElementById("edit-reminder").value =
        task.reminder_datetime.replace(" ", "T");

    document.getElementById("edit-modal").dataset.taskId = task.id;
    document.getElementById("edit-modal").classList.remove("hidden");
}

function closeEditModal() {
    document.getElementById("edit-modal").classList.add("hidden");
}

/* ======================================================
   SAVE EDITED TASK
====================================================== */
async function saveEditedTask() {
    const id = document.getElementById("edit-modal").dataset.taskId;

    const updated = {
        title: document.getElementById("edit-title").value.trim(),
        description: document.getElementById("edit-desc").value.trim(),
        due_datetime: document.getElementById("edit-due").value,
        reminder_datetime: document.getElementById("edit-reminder").value
    };

    await fetch(`${API}/tasks/update/${id}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
            Authorization: "Bearer " + token
        },
        body: JSON.stringify(updated)
    });

    showToast("Task updated!", "success");
    closeEditModal();
    loadTasks();
}

/* ======================================================
   SECURE LOGOUT
====================================================== */
function logout() {
    token = null;
    currentUserName = "Guest";
    updateUserNameUI();

    document.querySelectorAll("input").forEach(i => i.value = "");
    document.getElementById("task-list").innerHTML = "";
    document.getElementById("tasks-count").innerText = "0 tasks";

    showToast("Logged out", "info");

    hideAllPages();
    showLogin();
}

/* ======================================================
   PAGE LOAD
====================================================== */
window.onload = () => {
    hideAllPages();
    showLogin();
    updateUserNameUI();
};
