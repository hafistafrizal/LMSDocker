# Simple LMS API 🎓

Proyek ini adalah sistem *Learning Management System* (LMS) sederhana berbasis REST API yang dikembangkan menggunakan **Django** dan **Django Ninja**. Proyek ini merupakan gabungan dari modul praktikum PSS 5, PSS 6, dan PSS 7 yang mencakup manajemen *database*, pembuatan API CRUD, hingga sistem keamanan tingkat lanjut.

## 🛠️ Teknologi yang Digunakan
*   **Backend Framework**: Django 5.2
*   **API Framework**: Django Ninja
*   **Database**: PostgreSQL
*   **Caching & Rate Limiting**: Redis
*   **Authentication**: JSON Web Token (PyJWT)
*   **Environment**: Docker & Docker Compose

## ✨ Fitur Utama (Modul PSS 5 - 7)
1.  **Database & Caching (PSS 5)**: Migrasi dari SQLite ke PostgreSQL serta implementasi Redis untuk sistem *caching*.
2.  **REST API CRUD (PSS 6)**: Pengeksposan *endpoint* publik untuk membaca, menambah, mengubah, dan menghapus data kelas (*Course*).
3.  **Keamanan JWT & RBAC (PSS 7)**:
    *   Autentikasi menggunakan *Bearer Token* (Access & Refresh).
    *   Pembatasan akses berdasarkan peran (*Role-Based Access Control*):
        *   👑 **Admin**: Kontrol penuh atas semua sistem.
        *   👨‍🏫 **Teacher**: Dapat membuat kelas baru dan mengedit kelas miliknya.
        *   🎓 **Student**: Akses baca (*read-only*) terbatas pada kelas yang dipublikasikan.
    *   Fitur profil pengguna dan ubah password dengan pencabutan token aktif.
    *   *Rate-limiting* login tersentralisasi menggunakan Redis (Maksimal 5 percobaan/menit).

## 🚀 Cara Menjalankan Proyek (Local Development)

### Prasyarat
Pastikan **Docker Desktop** dan **Git** sudah terinstal di komputer Anda.

### 1. Clone Repositori
```bash
git clone https://github.com/hafistafrizal/LMSDocker.git
cd LMSDocker
```

### 2. Konfigurasi Environment
Salin file `.env.example` menjadi `.env`.
```bash
cp .env.example .env
```
*(Catatan: Pastikan untuk mengisi `JWT_SECRET` di dalam file `.env` dengan string acak yang kuat).*

### 3. Build & Run dengan Docker
Jalankan container untuk aplikasi, database, dan redis:
```bash
docker compose up -d --build
```

### 4. Migrasi & Seed Database
Jalankan migrasi tabel database dan buat data pengguna *dummy*:
```bash
docker compose exec app python manage.py migrate
docker compose exec app python manage.py seed_demo --password "PasswordPraktikum123!"
docker compose exec app python manage.py createsuperuser
```

## 📚 Dokumentasi API (Swagger UI)
Setelah aplikasi berjalan, dokumentasi interaktif API dapat diakses melalui browser pada:
👉 **`http://localhost:8000/api/docs`**

### Daftar Endpoint Utama
*   `POST /api/auth/token` : Login dan dapatkan token.
*   `POST /api/auth/refresh` : Perpanjang sesi token.
*   `GET /api/auth/me` : Cek identitas sesi.
*   `GET /api/auth/profile` : Lihat profil (*Role*, ID, Username).
*   `POST /api/auth/change-password` : Ganti kata sandi.
*   `GET /api/courses` : Lihat daftar kelas (Sesuai hak akses).
*   `POST /api/courses` : Buat kelas baru (Khusus Teacher/Admin).

## 🧪 Pengujian Otomatis (Unit Testing)
Proyek ini dilengkapi dengan serangkaian pengujian keamanan otomatis (25 Tests) yang mencakup uji pembatasan metode berdasarkan peran.
Untuk menjalankan pengujian, gunakan perintah berikut:
```bash
docker compose exec app python manage.py test -v 2
```

---
*Dibuat untuk Praktikum Pemrograman Sisi Server (PSS) - Universitas Dian Nuswantoro PSDKU Kediri.*