import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd

# ---------------------------
# DATABASE HELPERS
# ---------------------------
DB_PATH = "database.db"

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def create_db():
    conn = get_connection()
    c = conn.cursor()
    # USERS
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    """)
    # TASKS
    c.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            correct_answer TEXT,
            created_by TEXT,
            created_at TEXT,
            deadline TEXT
        )
    """)
    # ANSWERS
    c.execute("""
        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            user_id INTEGER,
            username TEXT,
            answer TEXT,
            score INTEGER,
            feedback TEXT,
            submitted_at TEXT,
            FOREIGN KEY(task_id) REFERENCES tasks(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    # MATERIALS (NEW)
    c.execute("""
        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            link TEXT,
            created_by TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

# ---------------------------
# USER / AUTH FUNCTIONS
# ---------------------------
def add_user(username, password, role="student"):
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO users(username, password, role) VALUES (?, ?, ?)",
                  (username, password, role))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        print("add_user error:", e)
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
    c.execute("SELECT id, username, password, role FROM users WHERE username=? AND password=?", (username, password))
    row = c.fetchone()
    conn.close()
    return row

def update_user_password(user_id, new_password):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET password=? WHERE id=?", (new_password, user_id))
    conn.commit()
    conn.close()

def list_users():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, username, role FROM users ORDER BY id")
    rows = c.fetchall()
    conn.close()
    return rows

# ---------------------------
# MATERIALS FUNCTIONS (NEW)
# ---------------------------
def add_material(title, link, created_by):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO materials(title, link, created_by, created_at)
        VALUES (?, ?, ?, ?)
    """, (title, link, created_by, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_all_materials():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, title, link, created_by, created_at FROM materials ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def delete_material(material_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM materials WHERE id=?", (material_id,))
    conn.commit()
    conn.close()

# ---------------------------
# TASKS & ANSWERS FUNCTIONS
# ---------------------------
def add_task(title, description, correct_answer, created_by, deadline=None):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO tasks(title, description, correct_answer, created_by, created_at, deadline)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (title, description, correct_answer, created_by, datetime.now().isoformat(), deadline))
    conn.commit()
    conn.close()

def get_all_tasks():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, title, description, correct_answer, created_by, created_at, deadline FROM tasks ORDER BY id")
    rows = c.fetchall()
    conn.close()
    return rows

def get_task(task_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, title, description, correct_answer, created_by, created_at, deadline FROM tasks WHERE id=?", (task_id,))
    row = c.fetchone()
    conn.close()
    return row

def user_answer_exists(user_id, task_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM answers WHERE user_id=? AND task_id=?", (user_id, task_id))
    row = c.fetchone()
    conn.close()
    return row is not None

def submit_answer(user_id, username, task_id, answer_text, score=None):
    conn = get_connection()
    c = conn.cursor()
    submitted_at = datetime.now().isoformat()
    c.execute("""
        INSERT INTO answers(task_id, user_id, username, answer, score, submitted_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (task_id, user_id, username, answer_text, score, submitted_at))
    conn.commit()
    conn.close()

def get_answers_for_task(task_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, task_id, user_id, username, answer, score, feedback, submitted_at FROM answers WHERE task_id=? ORDER BY id", (task_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_answers_for_user(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT answers.id, tasks.title, answers.answer, answers.score, answers.feedback, answers.submitted_at
        FROM answers JOIN tasks ON answers.task_id = tasks.id
        WHERE answers.user_id=?
        ORDER BY answers.id
    """, (user_id,))
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
    """Get all answers with task info for admin view"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT answers.id, answers.task_id, tasks.title, answers.username, 
               answers.answer, answers.score, answers.feedback, answers.submitted_at
        FROM answers JOIN tasks ON answers.task_id=tasks.id
        ORDER BY answers.id DESC
    """)
    rows = c.fetchall()
    conn.close()
    return rows

# ---------------------------
# UI: PAGES
# ---------------------------
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
                st.success(f"Login berhasil sebagai `{user[1]}` (role: {user[3]})")
                st.rerun()
            else:
                st.error("Username atau password salah")

def dashboard_page(user):
    """Dashboard with change password feature"""
    st.header("🏠 Dashboard")
    st.write(f"Selamat datang, **{user[1]}**!")
    
    role = user[3]
    if role == "admin":
        st.info("Anda adalah Admin. Gunakan menu di sidebar untuk mengelola sistem.")
    elif role == "lecturer":
        st.info("Anda adalah Dosen. Gunakan menu untuk membuat tugas dan menilai jawaban.")
    else:
        st.info("Anda adalah Mahasiswa. Lihat tugas dan hasil nilai Anda di menu sidebar.")
    
    st.markdown("---")
    st.subheader("🔐 Ganti Password")
    
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

def manage_users_page():
    """Admin page untuk manage users"""
    st.header("👥 Manajemen User")
    
    st.subheader("📋 Daftar User")
    users = list_users()
    if users:
        df = pd.DataFrame(users, columns=["ID", "Username", "Role"])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada user")

    st.markdown("---")
    st.subheader("➕ Tambah User Baru")
    with st.form("register_form"):
        new_username = st.text_input("Username")
        new_pass = st.text_input("Password", type="password")
        new_role = st.selectbox("Role", ["student", "lecturer", "admin"])
        submitted = st.form_submit_button("Buat User")
        
        if submitted:
            if not new_username or not new_pass:
                st.error("Username dan password tidak boleh kosong")
            elif user_exists(new_username):
                st.error("Username sudah ada")
            else:
                ok = add_user(new_username, new_pass, new_role)
                if ok:
                    st.success(f"✅ User '{new_username}' berhasil dibuat dengan role {new_role}")
                    st.rerun()
                else:
                    st.error("Gagal membuat user")

def materials_page_lecturer(user):
    """Lecturer page to manage materials"""
    st.header("📚 Manajemen Materi Tambahan")
    
    with st.expander("➕ Tambah Materi Baru", expanded=False):
        with st.form("material_form"):
            title = st.text_input("Judul Materi")
            link = st.text_input("Link (YouTube/Google Drive/dll)")
            submitted = st.form_submit_button("💾 Simpan Materi")
            
            if submitted:
                if not title or not link:
                    st.error("Judul dan link tidak boleh kosong")
                else:
                    add_material(title, link, user[1])
                    st.success(f"✅ Materi '{title}' berhasil ditambahkan")
                    st.rerun()
    
    st.markdown("---")
    st.subheader("📖 Daftar Materi Tambahan")
    materials = get_all_materials()
    
    if materials:
        for mat in materials:
            mat_id, title, link, created_by, created_at = mat
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.markdown(f"### 📌 {title}")
                st.write(f"🔗 Link: [{link}]({link})")
                st.caption(f"Dibuat oleh: {created_by} pada {created_at}")
            
            with col2:
                if st.button("🗑️ Hapus", key=f"del_{mat_id}"):
                    delete_material(mat_id)
                    st.success("Materi dihapus")
                    st.rerun()
            
            st.markdown("---")
    else:
        st.info("Belum ada materi tambahan")

def materials_page_student():
    """Student page to view materials"""
    st.header("📚 Materi Tambahan")
    st.write("Berikut adalah materi tambahan yang dapat Anda pelajari:")
    
    materials = get_all_materials()
    
    if materials:
        for mat in materials:
            mat_id, title, link, created_by, created_at = mat
            
            with st.expander(f"📌 {title}", expanded=False):
                st.write(f"**Link:** [{link}]({link})")
                st.caption(f"Dibuat oleh: {created_by}")
                
                # Auto-embed YouTube videos
                if "youtube.com" in link or "youtu.be" in link:
                    st.video(link)
                else:
                    st.info("Klik link di atas untuk membuka materi")
    else:
        st.info("Belum ada materi tambahan tersedia")

def manage_tasks_page(user):
    """Page untuk lecturer/admin manage tasks"""
    st.header("📝 Manajemen Tugas")
    
    with st.expander("➕ Tambah Soal Baru", expanded=False):
        with st.form("task_form"):
            title = st.text_input("Judul Soal")
            desc = st.text_area("Deskripsi / Soal")
            correct = st.text_input("Jawaban Benar (untuk auto-scoring, opsional)")
            deadline = st.date_input("Deadline (opsional)", value=None)
            submitted = st.form_submit_button("💾 Simpan Soal")
            
            if submitted:
                if not title or not desc:
                    st.error("Judul dan deskripsi tidak boleh kosong")
                else:
                    deadline_str = deadline.isoformat() if deadline else None
                    add_task(title, desc, correct, user[1], deadline_str)
                    st.success(f"✅ Soal '{title}' berhasil disimpan")
                    st.rerun()

    st.markdown("---")
    st.subheader("📚 Daftar Semua Soal")
    tasks = get_all_tasks()
    if tasks:
        for t in tasks:
            tid, title, desc, correct, created_by, created_at, deadline = t
            with st.expander(f"📄 Soal {tid}: {title}", expanded=False):
                st.write(f"**Deskripsi:** {desc}")
                st.write(f"**Dibuat oleh:** {created_by} pada {created_at}")
                if deadline:
                    st.write(f"**Deadline:** {deadline}")
                if correct:
                    st.write(f"**Jawaban Benar:** {correct}")
    else:
        st.info("Belum ada soal")

def grade_answers_page(user):
    """Page untuk lecturer grade jawaban"""
    st.header("✍️ Penilaian Jawaban")
    
    tasks = get_all_tasks()
    if not tasks:
        st.info("Belum ada tugas")
        return
    
    for t in tasks:
        tid, title = t[0], t[1]
        with st.expander(f"📝 {title} (ID: {tid})", expanded=False):
            answers = get_answers_for_task(tid)
            if not answers:
                st.info("Belum ada jawaban untuk soal ini")
                continue
            
            for ans in answers:
                ans_id, _, _, username, answer_text, score, feedback, submitted_at = ans
                st.markdown(f"**Siswa:** {username} | **Submitted:** {submitted_at}")
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

def view_all_answers_page():
    """Admin view all answers"""
    st.header("📊 Semua Jawaban (Admin)")
    
    rows = get_all_answers()
    if rows:
        # Convert to proper dataframe format
        import pandas as pd
        df = pd.DataFrame(rows, columns=[
            "Answer ID", 
            "Task ID", 
            "Task Title", 
            "Username", 
            "Answer", 
            "Score", 
            "Feedback", 
            "Submitted At"
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada jawaban")

def student_tasks_page(user):
    """Student view & submit tasks"""
    st.header("📚 Tugas Saya")
    
    tasks = get_all_tasks()
    if not tasks:
        st.info("Belum ada tugas tersedia")
        return
    
    for t in tasks:
        tid, title, desc, correct, created_by, created_at, deadline = t
        
        with st.expander(f"📝 {title}", expanded=False):
            st.markdown(f"**Deskripsi:** {desc}")
            if deadline:
                st.write(f"⏰ **Deadline:** {deadline}")
            st.caption(f"Dibuat oleh: {created_by}")
            
            # Check if already answered
            if user_answer_exists(user[0], tid):
                st.success("✅ Anda sudah menjawab soal ini")
                
                # Show their answer
                conn = get_connection()
                c = conn.cursor()
                c.execute("SELECT answer, score, feedback, submitted_at FROM answers WHERE user_id=? AND task_id=?", 
                         (user[0], tid))
                r = c.fetchone()
                conn.close()
                
                if r:
                    st.info(f"**Jawaban Anda:** {r[0]}")
                    st.metric("Score", f"{r[1]}/100" if r[1] is not None else "Belum dinilai")
                    if r[2]:
                        st.write(f"**Feedback:** {r[2]}")
                    st.caption(f"Submitted: {r[3]}")
            else:
                # Submit form
                with st.form(f"submit_{tid}"):
                    user_answer = st.text_area("Jawaban Anda", key=f"input_{tid}")
                    submit_btn = st.form_submit_button("📤 Kirim Jawaban")
                    
                    if submit_btn:
                        if not user_answer.strip():
                            st.error("Jawaban tidak boleh kosong")
                        else:
                            # Auto scoring jika ada correct answer (0-100)
                            auto_score = None
                            if correct and correct.strip():
                                # Exact match case-insensitive = 100, else 0
                                if user_answer.strip().lower() == correct.strip().lower():
                                    auto_score = 100
                                else:
                                    auto_score = 0
                            
                            submit_answer(user[0], user[1], tid, user_answer, auto_score)
                            
                            if auto_score is not None:
                                st.success(f"✅ Jawaban tersimpan! Nilai otomatis: {auto_score}/100")
                            else:
                                st.success("✅ Jawaban tersimpan. Menunggu penilaian dari dosen.")
                            st.rerun()

def student_results_page(user):
    """Student view their results"""
    st.header("📊 Hasil & Nilai Saya")
    
    my_answers = get_answers_for_user(user[0])
    if my_answers:
        for ans in my_answers:
            ans_id, task_title, answer, score, feedback, submitted_at = ans
            
            with st.expander(f"📝 {task_title}", expanded=False):
                st.write(f"**Jawaban:** {answer}")
                st.metric("Score", f"{score}/100" if score is not None else "Belum dinilai")
                if feedback:
                    st.info(f"**Feedback:** {feedback}")
                st.caption(f"Submitted: {submitted_at}")
    else:
        st.info("Anda belum mengerjakan tugas apapun")

# ---------------------------
# MAIN APP
# ---------------------------
def main():
    st.set_page_config(page_title="E-Learning System", page_icon="🎓", layout="wide")
    
    create_db()

    # Ensure default admin exists
    if not user_exists("admin"):
        add_user("admin", "admin123", "admin")

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

    # Sidebar
    st.sidebar.title("🎓 E-Learning")
    st.sidebar.write(f"👤 **{user[1]}**")
    st.sidebar.caption(f"Role: {role}")
    st.sidebar.markdown("---")

    # Menu based on role
    if role == "admin":
        menu = st.sidebar.radio("📍 Navigasi", [
            "Dashboard",
            "📚 Materi Tambahan",
            "👥 Manajemen User",
            "📝 Manajemen Tugas",
            "📊 Semua Jawaban"
        ])
    elif role == "lecturer":
        menu = st.sidebar.radio("📍 Navigasi", [
            "Dashboard",
            "📚 Materi Tambahan",
            "📝 Manajemen Tugas",
            "✍️ Penilaian Jawaban"
        ])
    else:  # student
        menu = st.sidebar.radio("📍 Navigasi", [
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
    
    elif menu == "📚 Materi Tambahan":
        if role in ("admin", "lecturer"):
            materials_page_lecturer(user)
        else:
            materials_page_student()
    
    elif menu == "👥 Manajemen User":
        if role == "admin":
            manage_users_page()
        else:
            st.error("🚫 Hanya admin yang dapat mengakses halaman ini")
    
    elif menu == "📝 Manajemen Tugas":
        if role in ("admin", "lecturer"):
            manage_tasks_page(user)
        else:
            st.error("🚫 Hanya admin/lecturer yang dapat mengakses halaman ini")
    
    elif menu == "✍️ Penilaian Jawaban":
        if role in ("admin", "lecturer"):
            grade_answers_page(user)
        else:
            st.error("🚫 Hanya admin/lecturer yang dapat mengakses halaman ini")
    
    elif menu == "📊 Semua Jawaban":
        if role == "admin":
            view_all_answers_page()
        else:
            st.error("🚫 Hanya admin yang dapat mengakses halaman ini")
    
    elif menu == "📚 Tugas Saya":
        student_tasks_page(user)
    
    elif menu == "📊 Hasil & Nilai":
        student_results_page(user)
    
    else:
        st.info("Menu belum diimplementasikan")

if __name__ == "__main__":
    main()