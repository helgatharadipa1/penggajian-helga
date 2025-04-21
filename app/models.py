from . import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)

class Karyawan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(150), nullable=False)
    jabatan = db.Column(db.String(100), nullable=False)
    gaji_pokok = db.Column(db.Integer, nullable=False)
    tunjangan = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Aktif')

class Absensi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    karyawan_id = db.Column(db.Integer, db.ForeignKey('karyawan.id'), nullable=False)
    tanggal = db.Column(db.Date, default=datetime.utcnow)
    status = db.Column(db.String(50), nullable=False)  # Hadir, Izin, Cuti, Sakit
    lembur = db.Column(db.Boolean, default=False)
    jam_lembur = db.Column(db.Integer, default=0)
    
    karyawan = db.relationship('Karyawan', backref=db.backref('absensi', lazy=True))

class SlipGaji(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    karyawan_id = db.Column(db.Integer, db.ForeignKey('karyawan.id'), nullable=False)
    bulan = db.Column(db.String(20), nullable=False)
    tahun = db.Column(db.String(4), nullable=False)
    gaji_pokok = db.Column(db.Integer, nullable=False)
    tunjangan = db.Column(db.Integer, nullable=False)
    lembur = db.Column(db.Integer, nullable=False)
    potongan = db.Column(db.Integer, nullable=False)
    pajak = db.Column(db.Integer, nullable=False)
    asuransi = db.Column(db.Integer, nullable=False)
    total_gaji = db.Column(db.Integer, nullable=False)

    karyawan = db.relationship('Karyawan', backref=db.backref('slipgaji', lazy=True))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
