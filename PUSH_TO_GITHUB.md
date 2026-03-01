# Cara Mengupload File ke GitHub Secara Otomatis (Manual Trigger)

## Langkah 1: Install Git

1. **Download Git**: Kunjungi https://git-scm.com/downloads
2. **Install Git**: Jalankan installer yang sudah di-download
3. **Penting saat install**: 
   - Pilih "Git from the command line and also from 3rd-party software"
   - Biarkan opsi lainnya sesuai default

## Langkah 2: Verifikasi Installasi Git

Buka Command Prompt baru dan ketik:
```
cmd
git --version
```

Jika berhasil, akan muncul seperti: `git version 2.x.x`

## Langkah 3: Konfigurasi Git

Buka Command Prompt dan jalankan:
```
cmd
git config --global user.name "Nama_Anda"
git config --global user.email "email@anda.com"
```

## Langkah 4: Setup Repository Git di Folder Proyek

Buka Command Prompt di folder proyek Anda (Tubes pds), lalu jalankan:

```
cmd
cd c:\Users\mdavi\Downloads\Tubes pds
git init
git add .
git commit -m "Initial commit"
```

## Langkah 5: Hubungkan ke GitHub Repository

1. Buat repository di GitHub.com terlebih dahulu (lewati jika sudah ada)
2. Copy URL repository Anda, contoh: `https://github.com/username/nama-repo.git`
3. Di Command Prompt, jalankan:
```
cmd
git remote add origin https://github.com/username/nama-repo.git
```

## Langkah 6: Push ke GitHub

Setiap kali ingin mengupload perubahan ke GitHub, jalankan:
```
cmd
git add .
git commit -m "Deskripsi perubahan"
git push origin main
```

## Cara Lebih Mudah: Batch Script

Buat file `push.bat` di folder proyek:

```
batch
@echo off
echo Adding files to Git...
git add .
set /p commit_msg="Enter commit message: "
git commit -m "%commit_msg%"
echo Pushing to GitHub...
git push origin main
echo Done!
pause
```

Sekarang tinggal double-click `push.bat` setiap kali ingin upload!

## Catatan Penting
- Pastikan setiap kali mau push, Anda sudah berada di folder proyek
- Atau bisa juga menggunakan GitHub Desktop (https://desktop.github.com/) yang lebih GUI-friendly
