import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd
import json

# DATABASE HELPERS
DB_PATH = "database.db"
FEEDBACK_DB_PATH = "feedback.db"  # Path untuk database feedback

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

# Fungsi koneksi untuk feedback database
def get_feedback_connection():
    return sqlite3.connect(FEEDBACK_DB_PATH, check_same_thread=False)

def create_db():
    conn = get_connection()
    c = conn.cursor()
    # USERS - Enhanced dengan nickname, jurusan, mata_kuliah
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT,
            nickname TEXT,
            jurusan TEXT,
            mata_kuliah TEXT
        )
    """)
    # TASKS - Enhanced dengan target_jurusan (JSON array)
    c.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            mata_kuliah TEXT,
            target_jurusan TEXT,
            created_by TEXT,
            created_at TEXT,
            deadline TEXT
        )
    """)
    # ANSWERS - Enhanced dengan status (draft/submitted)
    c.execute("""
        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            user_id INTEGER,
            username TEXT,
            answer TEXT,
            score INTEGER,
            feedback TEXT,
            status TEXT DEFAULT 'draft',
            submitted_at TEXT,
            finalized_at TEXT,
            FOREIGN KEY(task_id) REFERENCES tasks(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    # MATERIALS - Enhanced dengan mata_kuliah dan target_jurusan
    c.execute("""
        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            link TEXT,
            mata_kuliah TEXT,
            target_jurusan TEXT,
            created_by TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

# ========== FEEDBACK DATABASE FUNCTIONS ==========
def create_feedback_db():
    """Create separate database for feedback"""
    conn = get_feedback_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            role TEXT,
            message TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_feedback(user_id, username, role, message):
    """Add feedback to separate database"""
    conn = get_feedback_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO feedback(user_id, username, role, message, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, username, role, message, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_all_feedback():
    """Get all feedback for admin view"""
    conn = get_feedback_connection()
    c = conn.cursor()
    c.execute("SELECT id, user_id, username, role, message, created_at FROM feedback ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows

# ========== USER FUNCTIONS ==========
def add_user(username, password, role="student", nickname="", jurusan="", mata_kuliah=""):
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO users(username, password, role, nickname, jurusan, mata_kuliah) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (username, password, role, nickname, jurusan, mata_kuliah))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def user_exists(username):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    return row is not None

def get_user_by_credentials(username, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, username, password, role, nickname, jurusan, mata_kuliah 
        FROM users WHERE username=? AND password=?
    """, (username, password))
    row = c.fetchone()
    conn.close()
    return row

def update_user_password(user_id, new_password):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET password=? WHERE id=?", (new_password, user_id))
    conn.commit()
    conn.close()

def update_user_info(user_id, username=None, nickname=None, jurusan=None, mata_kuliah=None):
    """Admin function to update user info"""
    conn = get_connection()
    c = conn.cursor()
    updates = []
    params = []
    if username:
        updates.append("username=?")
        params.append(username)
    if nickname is not None:
        updates.append("nickname=?")
        params.append(nickname)
    if jurusan is not None:
        updates.append("jurusan=?")
        params.append(jurusan)
    if mata_kuliah is not None:
        updates.append("mata_kuliah=?")
        params.append(mata_kuliah)
    if updates:
        params.append(user_id)
        query = f"UPDATE users SET {', '.join(updates)} WHERE id=?"
        c.execute(query, params)
        conn.commit()
    conn.close()

def list_users():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, username, role, nickname, jurusan, mata_kuliah FROM users ORDER BY id")
    rows = c.fetchall()
    conn.close()
    return rows

def get_user_by_id(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, username, role, nickname, jurusan, mata_kuliah FROM users WHERE id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

# ========== MATERIALS FUNCTIONS ==========
def add_material(title, link, mata_kuliah, target_jurusan, created_by):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO materials(title, link, mata_kuliah, target_jurusan, created_by, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (title, link, mata_kuliah, json.dumps(target_jurusan), created_by, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_materials_by_mata_kuliah_jurusan(mata_kuliah, jurusan):
    """Get materials filtered by mata kuliah and jurusan"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, title, link, mata_kuliah, target_jurusan, created_by, created_at 
        FROM materials 
        WHERE mata_kuliah=?
        ORDER BY id DESC
    """, (mata_kuliah,))
    rows = c.fetchall()
    conn.close()
    # Filter by jurusan
    filtered = []
    for row in rows:
        target = json.loads(row[4])
        if jurusan in target or "Semua Jurusan" in target:
            filtered.append(row)
    return filtered

def get_all_materials_by_lecturer(mata_kuliah):
    """Get all materials created by lecturer for their mata kuliah"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, title, link, mata_kuliah, target_jurusan, created_by, created_at 
        FROM materials 
        WHERE mata_kuliah=?
        ORDER BY id DESC
    """, (mata_kuliah,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_all_materials():
    """Admin: get all materials"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, title, link, mata_kuliah, target_jurusan, created_by, created_at 
        FROM materials 
        ORDER BY id DESC
    """)
    rows = c.fetchall()
    conn.close()
    return rows

def delete_material(material_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM materials WHERE id=?", (material_id,))
    conn.commit()
    conn.close()

def update_material(material_id, title=None, link=None, target_jurusan=None):
    """Admin function to update material"""
    conn = get_connection()
    c = conn.cursor()
    updates = []
    params = []
    if title:
        updates.append("title=?")
        params.append(title)
    if link:
        updates.append("link=?")
        params.append(link)
    if target_jurusan:
        updates.append("target_jurusan=?")
        params.append(json.dumps(target_jurusan))
    if updates:
        params.append(material_id)
        query = f"UPDATE materials SET {', '.join(updates)} WHERE id=?"
        c.execute(query, params)
        conn.commit()
    conn.close()

# ========== TASKS FUNCTIONS ==========
def add_task(title, description, mata_kuliah, target_jurusan, created_by, deadline=None):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO tasks(title, description, mata_kuliah, target_jurusan, created_by, created_at, deadline)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (title, description, mata_kuliah, json.dumps(target_jurusan), created_by, datetime.now().isoformat(), deadline))
    conn.commit()
    conn.close()

def get_tasks_by_mata_kuliah_jurusan(mata_kuliah, jurusan):
    """Get tasks filtered by mata kuliah and jurusan"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, title, description, mata_kuliah, target_jurusan, created_by, created_at, deadline 
        FROM tasks 
        WHERE mata_kuliah=?
        ORDER BY id
    """, (mata_kuliah,))
    rows = c.fetchall()
    conn.close()
    # Filter by jurusan
    filtered = []
    for row in rows:
        target = json.loads(row[4])
        if jurusan in target or "Semua Jurusan" in target:
            filtered.append(row)
    return filtered

def get_all_tasks_by_lecturer(mata_kuliah):
    """Get all tasks created by lecturer for their mata kuliah"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, title, description, mata_kuliah, target_jurusan, created_by, created_at, deadline 
        FROM tasks 
        WHERE mata_kuliah=?
        ORDER BY id
    """, (mata_kuliah,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_all_tasks():
    """Admin: get all tasks"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, title, description, mata_kuliah, target_jurusan, created_by, created_at, deadline 
        FROM tasks 
        ORDER BY id
    """)
    rows = c.fetchall()
    conn.close()
    return rows

def get_task(task_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, title, description, mata_kuliah, target_jurusan, created_by, created_at, deadline 
        FROM tasks WHERE id=?
    """, (task_id,))
    row = c.fetchone()
    conn.close()
    return row

def update_task(task_id, title=None, description=None, target_jurusan=None, deadline=None):
    """Admin function to update task"""
    conn = get_connection()
    c = conn.cursor()
    updates = []
    params = []
    if title:
        updates.append("title=?")
        params.append(title)
    if description:
        updates.append("description=?")
        params.append(description)
    if target_jurusan:
        updates.append("target_jurusan=?")
        params.append(json.dumps(target_jurusan))
    if deadline is not None:
        updates.append("deadline=?")
        params.append(deadline)
    if updates:
        params.append(task_id)
        query = f"UPDATE tasks SET {', '.join(updates)} WHERE id=?"
        c.execute(query, params)
        conn.commit()
    conn.close()

def delete_task(task_id):
    """Admin function to delete task"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    c.execute("DELETE FROM answers WHERE task_id=?", (task_id,))
    conn.commit()
    conn.close()

# ========== ANSWERS FUNCTIONS ==========
def get_or_create_answer(user_id, username, task_id):
    """Get existing draft or create new one"""
    conn = get_connection()
    c = conn.cursor()
    # Check if answer exists
    c.execute("""
        SELECT id, answer, status, submitted_at, finalized_at 
        FROM answers 
        WHERE user_id=? AND task_id=?
    """, (user_id, task_id))
    row = c.fetchone()
    if row:
        conn.close()
        return row
    else:
        # Create new draft
        c.execute("""
            INSERT INTO answers(task_id, user_id, username, answer, status, submitted_at)
            VALUES (?, ?, ?, '', 'draft', ?)
        """, (task_id, user_id, username, datetime.now().isoformat()))
        conn.commit()
        answer_id = c.lastrowid
        conn.close()
        return (answer_id, '', 'draft', datetime.now().isoformat(), None)

def save_answer_draft(answer_id, answer_text):
    """Save answer as draft (can be edited)"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE answers 
        SET answer=?, submitted_at=? 
        WHERE id=?
    """, (answer_text, datetime.now().isoformat(), answer_id))
    conn.commit()
    conn.close()

def finalize_answer(answer_id):
    """Finalize answer (lock from editing)"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE answers 
        SET status='submitted', finalized_at=? 
        WHERE id=?
    """, (datetime.now().isoformat(), answer_id))
    conn.commit()
    conn.close()

def get_answers_for_task(task_id):
    """Get all submitted answers for a task"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, task_id, user_id, username, answer, score, feedback, status, submitted_at, finalized_at 
        FROM answers 
        WHERE task_id=? AND status='submitted'
        ORDER BY id
    """, (task_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_answers_for_user_by_mata_kuliah(user_id, mata_kuliah):
    """Get user's answers filtered by mata kuliah"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT answers.id, tasks.title, answers.answer, answers.score, answers.feedback, 
               answers.status, answers.submitted_at, answers.finalized_at
        FROM answers 
        JOIN tasks ON answers.task_id = tasks.id
        WHERE answers.user_id=? AND tasks.mata_kuliah=?
        ORDER BY answers.id
    """, (user_id, mata_kuliah))
    rows = c.fetchall()
    conn.close()
    return rows

def update_answer_score(answer_id, score, feedback=None):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE answers SET score=?, feedback=? WHERE id=?", (score, feedback, answer_id))
    conn.commit()
    conn.close()

def get_all_answers():
    """Admin: get all answers"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT answers.id, answers.task_id, tasks.title, tasks.mata_kuliah, 
               answers.username, answers.answer, answers.score, answers.feedback, 
               answers.status, answers.submitted_at, answers.finalized_at
        FROM answers 
        JOIN tasks ON answers.task_id=tasks.id
        ORDER BY answers.id DESC
    """)
    rows = c.fetchall()
    conn.close()
    return rows

# ========== UI PAGES ==========
def login_page():
    st.title("🔐 Login E-Learning")
    st.write("Masuk dengan akun Anda")
    col1, col2 = st.columns([2, 1])
    with col1:
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
    with col2:
        st.write("")
        st.write("")
        if st.button("Login"):
            user = get_user_by_credentials(username, password)
            if user:
                st.session_state["user"] = user
                st.success(f"Login berhasil sebagai `{user[4] or user[1]}` (role: {user[3]})")
                st.rerun()
            else:
                st.error("Username atau password salah")

def dashboard_page(user):
    """Dashboard with user info and feedback section"""
    st.header("🏠 Dashboard")
    role = user[3]
    nickname = user[4] or user[1]
    st.write(f"Selamat datang, **{nickname}**!")
    if role == "admin":
        st.info("🔧 Anda adalah Admin. Gunakan menu di sidebar untuk mengelola sistem.")
    elif role == "lecturer":
        mata_kuliah = user[6]
        st.info(f"👨‍🏫 Anda adalah Dosen mata kuliah: **{mata_kuliah}**")
    else:  # student
        jurusan = user[5]
        st.info(f"🎓 Anda adalah Mahasiswa jurusan: **{jurusan}**")
    
    # ====== TAMBAHAN: Section Feedback ======
    st.markdown("---")
    st.subheader("📣 Kirim Feedback ke Admin")
    with st.form("feedback_form"):
        feedback_msg = st.text_area("Pesan feedback Anda (saran, masalah, dll)", height=100, 
                                   placeholder="Contoh: Saya kesulitan mengakses materi untuk mata kuliah Ekonomi...")
        if st.form_submit_button("📤 Kirim Feedback"):
            if not feedback_msg.strip():
                st.error("Pesan feedback tidak boleh kosong")
            else:
                add_feedback(user[0], user[1], user[3], feedback_msg.strip())
                st.success("✅ Feedback berhasil dikirim! Admin akan meninjau pesan Anda segera.")
                st.rerun()
    # ====== AKHIR TAMBAHAN ======
    
    st.markdown("---")
    st.subheader("🔑 Ganti Password")
    with st.form("change_password_form"):
        current_pass = st.text_input("Password Lama", type="password")
        new_pass = st.text_input("Password Baru", type="password")
        confirm_pass = st.text_input("Konfirmasi Password Baru", type="password")
        if st.form_submit_button("💾 Ubah Password"):
            if not current_pass or not new_pass or not confirm_pass:
                st.error("Semua field harus diisi")
            elif current_pass != user[2]:
                st.error("Password lama salah")
            elif new_pass != confirm_pass:
                st.error("Password baru tidak cocok")
            elif len(new_pass) < 4:
                st.error("Password baru minimal 4 karakter")
            else:
                update_user_password(user[0], new_pass)
                st.success("✅ Password berhasil diubah! Silakan login kembali.")
                st.session_state.clear()
                st.rerun()

# ========== ADMIN PAGES ==========
def manage_users_admin_page():
    """Admin page to manage all users"""
    st.header("👥 Manajemen User (Admin)")
    # List all users
    st.subheader("📋 Daftar User")
    users = list_users()
    if users:
        for u in users:
            user_id, username, role, nickname, jurusan, mata_kuliah = u
            with st.expander(f"👤 {nickname or username} ({role})", expanded=False):
                with st.form(f"edit_user_{user_id}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        new_username = st.text_input("Username", value=username, key=f"un_{user_id}")
                        new_nickname = st.text_input("Nickname", value=nickname or "", key=f"nn_{user_id}")
                    with col2:
                        if role == "student":
                            new_jurusan = st.text_input("Jurusan", value=jurusan or "", key=f"jr_{user_id}")
                            st.write("")
                        elif role == "lecturer":
                            new_mata_kuliah = st.text_input("Mata Kuliah", value=mata_kuliah or "", key=f"mk_{user_id}")
                            st.write("")
                        else:
                            st.write("Admin tidak perlu info tambahan")
                    if st.form_submit_button("💾 Update User"):
                        if role == "student":
                            update_user_info(user_id, new_username, new_nickname, new_jurusan, None)
                        elif role == "lecturer":
                            update_user_info(user_id, new_username, new_nickname, None, new_mata_kuliah)
                        else:
                            update_user_info(user_id, new_username, new_nickname, None, None)
                        st.success(f"✅ User {new_username} berhasil diupdate")
                        st.rerun()
    st.markdown("---")
    st.subheader("➕ Tambah User Baru")
    with st.form("add_user_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            new_username = st.text_input("Username")
            new_password = st.text_input("Password", type="password")
        with col2:
            new_role = st.selectbox("Role", ["student", "lecturer", "admin"])
            new_nickname = st.text_input("Nickname")
        with col3:
            if new_role == "student":
                new_jurusan = st.text_input("Jurusan")
                new_mata_kuliah = ""
            elif new_role == "lecturer":
                new_mata_kuliah = st.text_input("Mata Kuliah")
                new_jurusan = ""
            else:
                new_jurusan = ""
                new_mata_kuliah = ""
        if st.form_submit_button("✅ Buat User"):
            if not new_username or not new_password:
                st.error("Username dan password wajib diisi")
            elif user_exists(new_username):
                st.error("Username sudah ada")
            else:
                ok = add_user(new_username, new_password, new_role, new_nickname, new_jurusan, new_mata_kuliah)
                if ok:
                    st.success(f"✅ User '{new_username}' berhasil dibuat")
                    st.rerun()
                else:
                    st.error("Gagal membuat user")

def manage_tasks_admin_page():
    """Admin page to manage all tasks, grouped by mata kuliah"""
    st.header("📝 Manajemen Tugas (Admin)")
    # Get all tasks
    all_tasks = get_all_tasks()
    if not all_tasks:
        st.info("Belum ada tugas")
        return
        
    # Extract unique mata_kuliah
    mata_kuliah_list = sorted(list(set(task[3] for task in all_tasks)))
    
    # Add selectbox for filtering by mata_kuliah
    selected_mk = st.selectbox("Filter berdasarkan Mata Kuliah", ["Semua Mata Kuliah"] + mata_kuliah_list)
    
    # Filter tasks based on selection
    if selected_mk == "Semua Mata Kuliah":
        tasks_to_display = all_tasks
    else:
        tasks_to_display = [t for t in all_tasks if t[3] == selected_mk]
    
    if not tasks_to_display:
        st.info(f"Tidak ada tugas untuk mata kuliah {selected_mk}")
        return
        
    # Display tasks grouped by mata_kuliah if showing all
    if selected_mk == "Semua Mata Kuliah":
        # Group tasks by mata_kuliah
        from collections import defaultdict
        grouped_tasks = defaultdict(list)
        for t in tasks_to_display:
            grouped_tasks[t[3]].append(t)  # t[3] is mata_kuliah
            
        # Display each group
        for mk, mk_tasks in grouped_tasks.items():
            st.markdown("---")
            st.subheader(f"📚 Mata Kuliah: {mk}")
            
            # Display tasks for this mata_kuliah with local index
            for local_idx, t in enumerate(mk_tasks, 1):
                tid, title, desc, mata_kuliah, target_jurusan, created_by, created_at, deadline = t
                target_list = json.loads(target_jurusan)
                with st.expander(f"📄 Tugas {local_idx}: {title}", expanded=False):  # Diubah di sini
                    st.write(f"**Dibuat oleh:** {created_by}")
                    st.write(f"**Target Jurusan:** {', '.join(target_list)}")
                    if deadline:
                        st.write(f"**Deadline:** {deadline}")
                    st.caption(f"Dibuat pada {created_at}")
                    with st.form(f"edit_task_{tid}"):
                        new_title = st.text_input("Judul", value=title, key=f"title_all_{tid}")
                        new_desc = st.text_area("Deskripsi", value=desc, key=f"desc_all_{tid}")
                        new_deadline = st.date_input(
                            "Deadline", 
                            value=None if not deadline else datetime.fromisoformat(deadline).date(),
                            key=f"deadline_all_{tid}"
                        )
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            if st.form_submit_button("💾 Update", key=f"update_all_{tid}"):
                                update_task(tid, new_title, new_desc, None, new_deadline.isoformat() if new_deadline else None)
                                st.success("✅ Tugas berhasil diupdate")
                                st.rerun()
                        with col2:
                            if st.form_submit_button("🗑️ Hapus", type="secondary", key=f"delete_all_{tid}"):
                                delete_task(tid)
                                st.success("✅ Tugas dihapus")
                                st.rerun()
    else:
        # Display tasks for selected mata_kuliah with local index
        st.subheader(f"📚 Tugas untuk Mata Kuliah: {selected_mk}")
        for local_idx, t in enumerate(tasks_to_display, 1):
            tid, title, desc, mata_kuliah, target_jurusan, created_by, created_at, deadline = t
            target_list = json.loads(target_jurusan)
            with st.expander(f"📄 Tugas {local_idx}: {title}", expanded=False):  # Diubah di sini
                st.write(f"**Dibuat oleh:** {created_by}")
                st.write(f"**Target Jurusan:** {', '.join(target_list)}")
                if deadline:
                    st.write(f"**Deadline:** {deadline}")
                st.caption(f"Dibuat pada {created_at}")
                with st.form(f"edit_task_{tid}"):
                    new_title = st.text_input("Judul", value=title, key=f"title_sel_{tid}")
                    new_desc = st.text_area("Deskripsi", value=desc, key=f"desc_sel_{tid}")
                    new_deadline = st.date_input(
                        "Deadline", 
                        value=None if not deadline else datetime.fromisoformat(deadline).date(),
                        key=f"deadline_sel_{tid}"
                    )
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if st.form_submit_button("💾 Update", key=f"update_sel_{tid}"):
                            update_task(tid, new_title, new_desc, None, new_deadline.isoformat() if new_deadline else None)
                            st.success("✅ Tugas berhasil diupdate")
                            st.rerun()
                    with col2:
                        if st.form_submit_button("🗑️ Hapus", type="secondary", key=f"delete_sel_{tid}"):
                            delete_task(tid)
                            st.success("✅ Tugas dihapus")
                            st.rerun()

def manage_materials_admin_page():
    """Admin page to manage all materials"""
    st.header("📚 Manajemen Materi (Admin)")
    materials = get_all_materials()
    if materials:
        for m in materials:
            mid, title, link, mata_kuliah, target_jurusan, created_by, created_at = m
            target_list = json.loads(target_jurusan)
            with st.expander(f"📖 {title} ({mata_kuliah})", expanded=False):
                st.write(f"**Link:** {link}")
                st.write(f"**Dibuat oleh:** {created_by}")
                st.write(f"**Target Jurusan:** {', '.join(target_list)}")
                col1, col2 = st.columns([3, 1])
                with col2:
                    if st.button("🗑️ Hapus", key=f"del_mat_{mid}"):
                        delete_material(mid)
                        st.success("✅ Materi dihapus")
                        st.rerun()
    else:
        st.info("Belum ada materi")

def view_all_answers_admin_page():
    """Admin view all answers"""
    st.header("📊 Semua Jawaban (Admin)")
    rows = get_all_answers()
    if rows:
        df = pd.DataFrame(rows, columns=[
            "ID", "Task ID", "Task Title", "Mata Kuliah", 
            "Username", "Answer", "Score", "Feedback", 
            "Status", "Submitted", "Finalized"
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada jawaban")

# ========== ADMIN FEEDBACK PAGE ==========
def view_feedback_admin_page():
    """Admin page to view all feedback from users"""
    st.header("📣 Feedback dari Users")
    
    # Filter options
    col1, col2 = st.columns([2, 1])
    with col1:
        st.write("Daftar semua feedback yang dikirim oleh users")
    
    feedbacks = get_all_feedback()
    if feedbacks:
        # Stats
        total_feedback = len(feedbacks)
        student_feedback = len([f for f in feedbacks if f[3] == "student"])
        lecturer_feedback = len([f for f in feedbacks if f[3] == "lecturer"])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Feedback", total_feedback)
        with col2:
            st.metric("Dari Mahasiswa", student_feedback)
        with col3:
            st.metric("Dari Dosen", lecturer_feedback)
        
        st.markdown("---")
        
        # Display feedback
        for fb in feedbacks:
            fb_id, user_id, username, role, message, created_at = fb
            created_date = created_at.split("T")[0] if created_at else ""
            
            with st.expander(f"👤 **{username}** ({role}) - 📅 {created_date}", expanded=False):
                st.markdown(f"**Pesan:**\n{message}")
                
                # Add response button (could be expanded to actual response feature)
                if st.button("✅ Tandai sebagai Ditangani", key=f"handled_{fb_id}"):
                    # In a real system, you might add a "handled" status or delete the feedback
                    # For now, we'll just show a success message
                    st.success(f"Feedback dari {username} telah ditangani")
                    # You could implement deletion here if desired
    else:
        st.info("Belum ada feedback dari users")
        st.image("https://static.vecteezy.com/system/resources/previews/004/180/790/non_2x/illustration-of-people-giving-feedback-flat-design-style-vector.jpg", 
                width=300, caption="Belum ada feedback")

# ========== LECTURER PAGES ==========
def materials_page_lecturer(user):
    """Lecturer page to manage materials"""
    mata_kuliah = user[6]
    st.header(f"📚 Materi Tambahan - {mata_kuliah}")
    # Add new material (tidak berubah)
    with st.expander("➕ Tambah Materi Baru", expanded=False):
        with st.form("material_form"):
            title = st.text_input("Judul Materi")
            link = st.text_input("Link (YouTube/Google Drive/dll)")
            jurusan_input = st.text_input("Target Jurusan (pisahkan dengan koma, atau tulis 'Semua Jurusan')")
            submitted = st.form_submit_button("💾 Simpan Materi")
            if submitted:
                if not title or not link or not jurusan_input:
                    st.error("Semua field harus diisi")
                else:
                    # Parse jurusan
                    if jurusan_input.strip().lower() == "semua jurusan":
                        target_jurusan = ["Semua Jurusan"]
                    else:
                        target_jurusan = [j.strip() for j in jurusan_input.split(",")]
                    add_material(title, link, mata_kuliah, target_jurusan, user[4] or user[1])
                    st.success(f"✅ Materi '{title}' berhasil ditambahkan")
                    st.rerun()
    # List materials dengan index lokal per mata kuliah
    st.markdown("---")
    st.subheader("📖 Daftar Materi Saya")
    materials = get_all_materials_by_lecturer(mata_kuliah)
    if materials:
        # Gunakan enumerate untuk membuat index lokal yang dimulai dari 1
        for local_idx, mat in enumerate(materials, 1):
            mat_id, title, link, _, target_jurusan, created_by, created_at = mat
            target_list = json.loads(target_jurusan)
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"### 📌 #{local_idx}. {title}")
                st.write(f"🔗 Link: [{link}]({link})")
                st.write(f"🎯 Target: {', '.join(target_list)}")
                st.caption(f"Dibuat pada {created_at}")
            with col2:
                if st.button("🗑️ Hapus", key=f"del_{mat_id}"):
                    delete_material(mat_id)
                    st.success("Materi dihapus")
                    st.rerun()
            st.markdown("---")
    else:
        st.info("Belum ada materi")

def manage_tasks_lecturer_page(user):
    """Lecturer page to manage tasks"""
    mata_kuliah = user[6]
    st.header(f"📝 Manajemen Tugas - {mata_kuliah}")
    # Add new task (tidak berubah)
    with st.expander("➕ Tambah Soal Baru", expanded=False):
        with st.form("task_form"):
            title = st.text_input("Judul Soal")
            desc = st.text_area("Deskripsi / Soal")
            deadline = st.date_input("Deadline (opsional)", value=None)
            jurusan_input = st.text_input("Target Jurusan (pisahkan dengan koma, atau tulis 'Semua Jurusan')")
            submitted = st.form_submit_button("💾 Simpan Soal")
            if submitted:
                if not title or not desc or not jurusan_input:
                    st.error("Judul, deskripsi, dan target jurusan harus diisi")
                else:
                    # Parse jurusan
                    if jurusan_input.strip().lower() == "semua jurusan":
                        target_jurusan = ["Semua Jurusan"]
                    else:
                        target_jurusan = [j.strip() for j in jurusan_input.split(",")]
                    deadline_str = deadline.isoformat() if deadline else None
                    add_task(title, desc, mata_kuliah, target_jurusan, user[4] or user[1], deadline_str)
                    st.success(f"✅ Soal '{title}' berhasil disimpan")
                    st.rerun()
    # List tasks dengan format yang dimodifikasi
    st.markdown("---")
    st.subheader("📚 Daftar Soal Saya")
    tasks = get_all_tasks_by_lecturer(mata_kuliah)
    if tasks:
        # Gunakan enumerate untuk membuat index lokal yang dimulai dari 1
        for local_idx, t in enumerate(tasks, 1):
            tid, title, desc, _, target_jurusan, created_by, created_at, deadline = t
            target_list = json.loads(target_jurusan)
            with st.expander(f"📄 Soal {local_idx}: {title}", expanded=False):  # Diubah di sini
                st.write(f"**Deskripsi:** {desc}")
                st.write(f"**Target Jurusan:** {', '.join(target_list)}")
                if deadline:
                    st.write(f"**Deadline:** {deadline}")
                st.caption(f"Dibuat pada {created_at}")
                # Form untuk edit/hapus tetap menggunakan ID asli dari database
                with st.form(f"edit_task_{tid}"):
                    new_title = st.text_input("Judul", value=title, key=f"title_{tid}")
                    new_desc = st.text_area("Deskripsi", value=desc, key=f"desc_{tid}")
                    new_deadline = st.date_input(
                        "Deadline", 
                        value=None if not deadline else datetime.fromisoformat(deadline).date(),
                        key=f"deadline_{tid}"
                    )
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if st.form_submit_button("💾 Update", key=f"update_{tid}"):
                            update_task(tid, new_title, new_desc, None, new_deadline.isoformat() if new_deadline else None)
                            st.success("✅ Soal berhasil diupdate")
                            st.rerun()
                    with col2:
                        if st.form_submit_button("🗑️ Hapus", type="secondary", key=f"delete_{tid}"):
                            delete_task(tid)
                            st.success("✅ Soal dihapus")
                            st.rerun()
    else:
        st.info("Belum ada soal")

def grade_answers_lecturer_page(user):
    """Lecturer page to grade answers"""
    mata_kuliah = user[6]
    st.header(f"✏️ Penilaian Jawaban - {mata_kuliah}")
    tasks = get_all_tasks_by_lecturer(mata_kuliah)
    if not tasks:
        st.info("Belum ada tugas")
        return
    for t in tasks:
        tid, title = t[0], t[1]
        with st.expander(f"📝 {title} (ID: {tid})", expanded=False):
            answers = get_answers_for_task(tid)
            if not answers:
                st.info("Belum ada jawaban yang disubmit")
                continue
            for ans in answers:
                ans_id, _, _, username, answer_text, score, feedback, status, submitted_at, finalized_at = ans
                st.markdown(f"**Siswa:** {username} | **Status:** {status}")
                st.write(f"**Submitted:** {submitted_at}")
                if finalized_at:
                    st.write(f"**Finalized:** {finalized_at}")
                st.write(f"**Jawaban:** {answer_text}")
                with st.form(f"grade_{ans_id}"):
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        new_score = st.number_input(
                            "Score (0-100)", 
                            min_value=0, 
                            max_value=100, 
                            value=int(score) if score else 0,
                            key=f"score_{ans_id}"
                        )
                    with col2:
                        fb = st.text_input(
                            "Feedback", 
                            value=feedback if feedback else "",
                            key=f"fb_{ans_id}"
                        )
                    if st.form_submit_button("💾 Simpan Nilai"):
                        update_answer_score(ans_id, new_score, fb)
                        st.success("✅ Nilai tersimpan")
                        st.rerun()
                st.markdown("---")

# ========== STUDENT PAGES ==========
def get_available_mata_kuliah_for_student(jurusan):
    """Get list of mata kuliah that have tasks/materials for this jurusan"""
    conn = get_connection()
    c = conn.cursor()
    # Get from BOTH tasks AND materials
    c.execute("SELECT DISTINCT mata_kuliah FROM tasks UNION SELECT DISTINCT mata_kuliah FROM materials")
    all_mk = [row[0] for row in c.fetchall()]
    conn.close()
    # Filter by jurusan
    available_mk = []
    for mk in all_mk:
        # Check if any task OR material in this MK targets this jurusan
        tasks = get_tasks_by_mata_kuliah_jurusan(mk, jurusan)
        materials = get_materials_by_mata_kuliah_jurusan(mk, jurusan)
        if tasks or materials:  # ✅ Cek keduanya
            available_mk.append(mk)
    return available_mk

def materials_page_student(user):
    """Student page to view materials"""
    jurusan = user[5]
    st.header("📚 Materi Tambahan")
    available_mk = get_available_mata_kuliah_for_student(jurusan)
    if not available_mk:
        st.info("Belum ada materi tersedia untuk jurusan Anda")
        return
    selected_mk = st.selectbox("Pilih Mata Kuliah", available_mk)
    st.markdown("---")
    materials = get_materials_by_mata_kuliah_jurusan(selected_mk, jurusan)
    if materials:
        for mat in materials:
            mat_id, title, link, _, target_jurusan, created_by, created_at = mat
            with st.expander(f"📌 {title}", expanded=False):
                st.write(f"**Link:** [{link}]({link})")
                st.caption(f"Dibuat oleh: {created_by}")
                # Auto-embed YouTube videos
                if "youtube.com" in link or "youtu.be" in link:
                    st.video(link)
                else:
                    st.info("Klik link di atas untuk membuka materi")
    else:
        st.info("Belum ada materi untuk mata kuliah ini")

def student_tasks_page(user):
    """Student page to view and submit tasks"""
    jurusan = user[5]
    st.header("📚 Tugas Saya")
    available_mk = get_available_mata_kuliah_for_student(jurusan)
    if not available_mk:
        st.info("Belum ada tugas tersedia untuk jurusan Anda")
        return
    selected_mk = st.selectbox("Pilih Mata Kuliah", available_mk)
    st.markdown("---")
    tasks = get_tasks_by_mata_kuliah_jurusan(selected_mk, jurusan)
    if not tasks:
        st.info("Belum ada tugas untuk mata kuliah ini")
        return
    for t in tasks:
        tid, title, desc, _, target_jurusan, created_by, created_at, deadline = t
        with st.expander(f"📝 {title}", expanded=False):
            st.markdown(f"**Deskripsi:** {desc}")
            if deadline:
                st.write(f"⏰ **Deadline:** {deadline}")
            st.caption(f"Dibuat oleh: {created_by}")
            st.markdown("---")
            # Get or create answer
            answer_data = get_or_create_answer(user[0], user[1], tid)
            answer_id, answer_text, status, submitted_at, finalized_at = answer_data
            if status == "submitted":
                st.success("✅ Tugas ini sudah diselesaikan")
                st.info(f"**Jawaban Anda:** {answer_text}")
                st.caption(f"Difinalisasi pada: {finalized_at}")
                # Show score if graded
                conn = get_connection()
                c = conn.cursor()
                c.execute("SELECT score, feedback FROM answers WHERE id=?", (answer_id,))
                r = c.fetchone()
                conn.close()
                if r and r[0] is not None:
                    st.metric("Score", f"{r[0]}/100")
                    if r[1]:
                        st.write(f"**Feedback:** {r[1]}")
                else:
                    st.info("Menunggu penilaian dari dosen")
            else:  # draft
                st.info("📝 Status: Draft (belum diselesaikan)")
                with st.form(f"task_{tid}"):
                    user_answer = st.text_area(
                        "Jawaban Anda", 
                        value=answer_text,
                        key=f"input_{tid}",
                        height=150
                    )
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("💾 Simpan Draft"):
                            if not user_answer.strip():
                                st.error("Jawaban tidak boleh kosong")
                            else:
                                save_answer_draft(answer_id, user_answer)
                                st.success("✅ Draft tersimpan. Anda masih bisa mengubahnya.")
                                st.rerun()
                    with col2:
                        if st.form_submit_button("✔️ Selesai & Submit", type="primary"):
                            if not user_answer.strip():
                                st.error("Jawaban tidak boleh kosong")
                            else:
                                save_answer_draft(answer_id, user_answer)
                                finalize_answer(answer_id)
                                st.success("✅ Tugas berhasil diselesaikan dan disubmit!")
                                st.rerun()

def student_results_page(user):
    """Student page to view results"""
    jurusan = user[5]
    st.header("📊 Hasil & Nilai Saya")
    available_mk = get_available_mata_kuliah_for_student(jurusan)
    if not available_mk:
        st.info("Belum ada hasil tersedia")
        return
    selected_mk = st.selectbox("Pilih Mata Kuliah", available_mk)
    st.markdown("---")
    my_answers = get_answers_for_user_by_mata_kuliah(user[0], selected_mk)
    if my_answers:
        for ans in my_answers:
            ans_id, task_title, answer, score, feedback, status, submitted_at, finalized_at = ans
            with st.expander(f"📝 {task_title}", expanded=False):
                st.write(f"**Status:** {status}")
                st.write(f"**Jawaban:** {answer}")
                if status == "submitted":
                    st.caption(f"Submitted: {finalized_at}")
                    if score is not None:
                        st.metric("Score", f"{score}/100")
                        if feedback:
                            st.info(f"**Feedback:** {feedback}")
                    else:
                        st.warning("Menunggu penilaian dari dosen")
                else:
                    st.info("Draft - belum diselesaikan")
    else:
        st.info("Belum ada hasil untuk mata kuliah ini")

# ========== MAIN APP ==========
def main():
    st.set_page_config(page_title="E-Learning System", page_icon="🎓", layout="wide")
    create_db()
    create_feedback_db()  # Create feedback database
    
    # Ensure default admin exists
    if not user_exists("admin"):
        add_user("admin", "admin123", "admin", "Admin", "", "")
    
    # Session init
    if "user" not in st.session_state:
        st.session_state["user"] = None
    
    # Login check
    if st.session_state["user"] is None:
        login_page()
        return
    
    # User logged in
    user = st.session_state["user"]
    role = user[3]
    nickname = user[4] or user[1]
    
    # Sidebar
    st.sidebar.title("🎓 E-Learning")
    st.sidebar.write(f"👤 **{nickname}**")
    st.sidebar.caption(f"Role: {role}")
    if role == "student":
        st.sidebar.caption(f"Jurusan: {user[5]}")
    elif role == "lecturer":
        st.sidebar.caption(f"Mata Kuliah: {user[6]}")
    st.sidebar.markdown("---")
    
    # Menu based on role
    if role == "admin":
        menu = st.sidebar.radio("🧭 Navigasi", [
            "Dashboard",
            "👥 Manajemen User",
            "📚 Manajemen Materi",
            "📝 Manajemen Tugas",
            "📊 Semua Jawaban",
            "📣 Feedback Users"  # Menu baru untuk feedback
        ])
    elif role == "lecturer":
        menu = st.sidebar.radio("🧭 Navigasi", [
            "Dashboard",
            "📚 Materi Tambahan",
            "📝 Manajemen Tugas",
            "✏️ Penilaian Jawaban"
        ])
    else:  # student
        menu = st.sidebar.radio("🧭 Navigasi", [
            "Dashboard",
            "📚 Materi Tambahan",
            "📚 Tugas Saya",
            "📊 Hasil & Nilai"
        ])
    
    if st.sidebar.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()
    
    # ROUTING
    if menu == "Dashboard":
        dashboard_page(user)
    elif menu == "👥 Manajemen User":
        if role == "admin":
            manage_users_admin_page()
        else:
            st.error("🚫 Hanya admin yang dapat mengakses halaman ini")
    elif menu == "📚 Manajemen Materi":
        if role == "admin":
            manage_materials_admin_page()
        else:
            st.error("🚫 Hanya admin yang dapat mengakses halaman ini")
    elif menu == "📝 Manajemen Tugas":
        if role == "admin":
            manage_tasks_admin_page()
        elif role == "lecturer":
            manage_tasks_lecturer_page(user)
        else:
            st.error("🚫 Hanya admin/lecturer yang dapat mengakses halaman ini")
    elif menu == "✏️ Penilaian Jawaban":
        if role == "lecturer":
            grade_answers_lecturer_page(user)
        else:
            st.error("🚫 Hanya lecturer yang dapat mengakses halaman ini")
    elif menu == "📊 Semua Jawaban":
        if role == "admin":
            view_all_answers_admin_page()
        else:
            st.error("🚫 Hanya admin yang dapat mengakses halaman ini")
    elif menu == "📚 Materi Tambahan":
        if role == "student":
            materials_page_student(user)
        elif role == "lecturer":
            materials_page_lecturer(user)
    elif menu == "📚 Tugas Saya":   
        student_tasks_page(user)
    elif menu == "📊 Hasil & Nilai":
        student_results_page(user)
    elif menu == "📣 Feedback Users":
        if role == "admin":
            view_feedback_admin_page()
        else:
            st.error("🚫 Hanya admin yang dapat mengakses halaman ini")

if __name__ == "__main__":
    main()