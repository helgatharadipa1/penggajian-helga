from flask import Blueprint, render_template, redirect, url_for, request, flash, make_response, Response
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from .models import User, Karyawan, Absensi, SlipGaji
from . import db
from datetime import datetime
from calendar import month_name
from xhtml2pdf import pisa
from io import BytesIO

main = Blueprint('main', __name__)

@main.route('/')
def home():
    return redirect(url_for('main.login'))

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        else:
            flash('Username atau password salah', 'danger')

    return render_template('login.html')

@main.route('/dashboard')
@login_required
def dashboard():
    total_karyawan = Karyawan.query.count()
    total_gaji_dibayar = db.session.query(db.func.sum(SlipGaji.total_gaji)).scalar() or 0
    total_lembur = db.session.query(db.func.sum(SlipGaji.lembur)).scalar() or 0
    total_izin = db.session.query(db.func.sum(SlipGaji.potongan)).scalar() or 0
    total_pajak = db.session.query(db.func.sum(SlipGaji.pajak)).scalar() or 0
    total_asuransi = db.session.query(db.func.sum(SlipGaji.asuransi)).scalar() or 0
    total_beban = total_gaji_dibayar + total_pajak + total_asuransi

    return render_template('dashboard.html', 
        total_karyawan=total_karyawan,
        total_gaji_dibayar=total_gaji_dibayar,
        total_lembur=total_lembur,
        total_izin=total_izin,
        total_pajak=total_pajak,
        total_asuransi=total_asuransi,
        total_beban=total_beban
    )

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

# (...rute lainnya tetap sama...)

@main.route('/karyawan')
@login_required
def karyawan_list():
    data = Karyawan.query.all()
    return render_template('karyawan_list.html', data=data)

@main.route('/karyawan/tambah', methods=['GET', 'POST'])
@login_required
def tambah_karyawan():
    if request.method == 'POST':
        nama = request.form['nama']
        jabatan = request.form['jabatan']
        gaji_pokok = request.form['gaji_pokok']
        tunjangan = request.form['tunjangan']

        k = Karyawan(
            nama=nama,
            jabatan=jabatan,
            gaji_pokok=int(gaji_pokok),
            tunjangan=int(tunjangan),
            status='Aktif'
        )
        db.session.add(k)
        db.session.commit()
        flash('Data karyawan berhasil ditambahkan!', 'success')
        return redirect(url_for('main.karyawan_list'))

    return render_template('karyawan_form.html', action='Tambah')

@main.route('/karyawan/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_karyawan(id):
    k = Karyawan.query.get_or_404(id)
    if request.method == 'POST':
        k.nama = request.form['nama']
        k.jabatan = request.form['jabatan']
        k.gaji_pokok = int(request.form['gaji_pokok'])
        k.tunjangan = int(request.form['tunjangan'])
        db.session.commit()
        flash('Data karyawan berhasil diperbarui!', 'info')
        return redirect(url_for('main.karyawan_list'))

    return render_template('karyawan_form.html', action='Edit', karyawan=k)

@main.route('/karyawan/hapus/<int:id>')
@login_required
def hapus_karyawan(id):
    k = Karyawan.query.get_or_404(id)
    db.session.delete(k)
    db.session.commit()
    flash('Data karyawan berhasil dihapus!', 'danger')
    return redirect(url_for('main.karyawan_list'))

@main.route('/absensi')
@login_required
def absensi_list():
    data = Absensi.query.order_by(Absensi.tanggal.desc()).all()
    return render_template('absensi_list.html', data=data)

@main.route('/absensi/tambah', methods=['GET', 'POST'])
@login_required
def tambah_absensi():
    karyawan_list = Karyawan.query.all()
    if request.method == 'POST':
        karyawan_id = request.form['karyawan_id']
        tanggal = datetime.strptime(request.form['tanggal'], '%Y-%m-%d')
        status = request.form['status']
        lembur = request.form.get('lembur') == 'on'
        jam_lembur = int(request.form['jam_lembur']) if lembur else 0

        absen = Absensi(
            karyawan_id=karyawan_id,
            tanggal=tanggal,
            status=status,
            lembur=lembur,
            jam_lembur=jam_lembur
        )
        db.session.add(absen)
        db.session.commit()
        flash('Data absensi berhasil ditambahkan!', 'success')
        return redirect(url_for('main.absensi_list'))

    return render_template('absensi_form.html', karyawan_list=karyawan_list, action='Tambah')

@main.route('/absensi/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_absensi(id):
    absen = Absensi.query.get_or_404(id)
    karyawan_list = Karyawan.query.all()
    if request.method == 'POST':
        absen.karyawan_id = request.form['karyawan_id']
        absen.tanggal = datetime.strptime(request.form['tanggal'], '%Y-%m-%d')
        absen.status = request.form['status']
        absen.lembur = request.form.get('lembur') == 'on'
        absen.jam_lembur = int(request.form['jam_lembur']) if absen.lembur else 0

        db.session.commit()
        flash('Data absensi berhasil diperbarui!', 'info')
        return redirect(url_for('main.absensi_list'))

    return render_template('absensi_form.html', absen=absen, karyawan_list=karyawan_list, action='Edit')

@main.route('/absensi/hapus/<int:id>')
@login_required
def hapus_absensi(id):
    absen = Absensi.query.get_or_404(id)
    db.session.delete(absen)
    db.session.commit()
    flash('Data absensi berhasil dihapus!', 'danger')
    return redirect(url_for('main.absensi_list'))

@main.route('/gaji')
@login_required
def gaji_list():
    bulan = request.args.get('bulan')
    tahun = request.args.get('tahun')

    query = SlipGaji.query.order_by(SlipGaji.tahun.desc(), SlipGaji.bulan.desc())
    if bulan and tahun:
        query = query.filter(SlipGaji.bulan == bulan, SlipGaji.tahun == tahun)

    data = query.all()
    return render_template('slipgaji_list.html', data=data, selected_bulan=bulan, selected_tahun=tahun)

@main.route('/gaji/detail/<int:id>')
@login_required
def gaji_detail(id):
    s = SlipGaji.query.get_or_404(id)
    return render_template('slipgaji_detail.html', s=s)

@main.route('/gaji/hitung')
@login_required
def hitung_gaji():
    bulan = datetime.now().month
    tahun = str(datetime.now().year)
    nama_bulan = month_name[bulan]

    SlipGaji.query.filter_by(bulan=nama_bulan, tahun=tahun).delete()
    db.session.commit()

    for k in Karyawan.query.all():
        absensi = Absensi.query.filter_by(karyawan_id=k.id).filter(
            db.extract('month', Absensi.tanggal) == bulan,
            db.extract('year', Absensi.tanggal) == int(tahun)
        ).all()

        total_izin = sum(1 for a in absensi if a.status in ['Izin', 'Cuti', 'Sakit'])
        total_jam_lembur = sum(a.jam_lembur for a in absensi if a.lembur)

        gaji_pokok = k.gaji_pokok
        tunjangan = k.tunjangan
        lembur = total_jam_lembur * 20000
        potongan = total_izin * 50000

        bruto = gaji_pokok + tunjangan + lembur
        pajak = int(0.05 * bruto)
        asuransi = int(0.01 * gaji_pokok)
        total = bruto - potongan - pajak - asuransi

        slip = SlipGaji(
            karyawan_id=k.id,
            bulan=nama_bulan,
            tahun=tahun,
            gaji_pokok=gaji_pokok,
            tunjangan=tunjangan,
            lembur=lembur,
            potongan=potongan,
            pajak=pajak,
            asuransi=asuransi,
            total_gaji=total
        )
        db.session.add(slip)

    db.session.commit()
    flash('Gaji bulan ini berhasil dihitung dan disimpan!', 'success')
    return redirect(url_for('main.gaji_list'))

from flask import make_response
from xhtml2pdf import pisa
from io import BytesIO
from flask import render_template_string

@main.route('/gaji/export/<int:id>')
@login_required
def export_pdf(id):
    s = SlipGaji.query.get_or_404(id)
    html = render_template('slipgaji_detail.html', s=s)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        response = make_response(result.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f"attachment; filename=Slip_Gaji_{s.karyawan.nama}_{s.bulan}_{s.tahun}.pdf"
        return response
    flash('Gagal membuat PDF', 'danger')
    return redirect(url_for('main.gaji_detail', id=id))

import csv
from flask import Response

@main.route('/gaji/export/excel')
@login_required
def export_excel():
    bulan = request.args.get('bulan')
    tahun = request.args.get('tahun')

    query = SlipGaji.query.join(Karyawan).order_by(SlipGaji.tahun.desc(), SlipGaji.bulan.desc())
    if bulan and tahun:
        query = query.filter(SlipGaji.bulan == bulan, SlipGaji.tahun == tahun)

    data = query.all()

    def generate():
        yield 'Nama,Bulan,Tahun,Gaji Pokok,Tunjangan,Lembur,Potongan,Pajak,Asuransi,Total Gaji\n'
        for s in data:
            row = [
                s.karyawan.nama,
                s.bulan,
                str(s.tahun),
                str(s.gaji_pokok),
                str(s.tunjangan),
                str(s.lembur),
                str(s.potongan),
                str(s.pajak),
                str(s.asuransi),
                str(s.total_gaji)
            ]
            yield ','.join(row) + '\n'

    return Response(generate(), mimetype='text/csv', headers={
        "Content-Disposition": "attachment; filename=rekap_slip_gaji.csv"
    })

# ... (import tetap sama)

@main.route('/laporan', methods=['GET'])
@login_required
def laporan_bulanan():
    bulan = request.args.get('bulan')
    tahun = request.args.get('tahun')

    data = []
    total_gaji = 0
    total_pajak = 0
    total_asuransi = 0
    jumlah_karyawan = 0

    if bulan and tahun:
        data = SlipGaji.query.filter(SlipGaji.bulan == bulan, SlipGaji.tahun == tahun).all()
        total_gaji = sum(s.total_gaji for s in data)
        total_pajak = sum(s.pajak for s in data)
        total_asuransi = sum(s.asuransi for s in data)
        jumlah_karyawan = len(data)

    return render_template('laporan.html',
                           data=data,
                           selected_bulan=bulan,
                           selected_tahun=tahun,
                           total_gaji=total_gaji,
                           total_pajak=total_pajak,
                           total_asuransi=total_asuransi,
                           jumlah_karyawan=jumlah_karyawan)

# ... (import tetap sama)
from flask import make_response
from xhtml2pdf import pisa
from io import BytesIO

@main.route('/laporan/export')
@login_required
def export_laporan_pdf():
    bulan = request.args.get('bulan')
    tahun = request.args.get('tahun')

    data = SlipGaji.query.filter(SlipGaji.bulan == bulan, SlipGaji.tahun == tahun).all()
    total_gaji = sum(s.total_gaji for s in data)
    total_pajak = sum(s.pajak for s in data)
    total_asuransi = sum(s.asuransi for s in data)
    jumlah_karyawan = len(data)

    html = render_template('laporan.html',
                           data=data,
                           selected_bulan=bulan,
                           selected_tahun=tahun,
                           total_gaji=total_gaji,
                           total_pajak=total_pajak,
                           total_asuransi=total_asuransi,
                           jumlah_karyawan=jumlah_karyawan)

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        response = make_response(result.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f"attachment; filename=Laporan_{bulan}_{tahun}.pdf"
        return response

    flash('Gagal membuat PDF', 'danger')
    return redirect(url_for('main.laporan_bulanan'))

@main.route('/gaji/hapus/<int:id>')
@login_required
def hapus_gaji(id):
    slip = SlipGaji.query.get_or_404(id)
    db.session.delete(slip)
    db.session.commit()
    flash('Slip gaji berhasil dihapus!', 'success')
    return redirect(url_for('main.gaji_list'))

