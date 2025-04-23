from flask import Flask, render_template, request, redirect, url_for, flash, session, g, send_file
import psycopg2, csv, io, smtplib
from email.mime.text import MIMEText
import os

app = Flask(__name__)
app.secret_key = 'supersecurekey'

DATABASE_URL = os.environ.get("DATABASE_URL")

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'fuelboss123'

EMAIL_FROM = 'raphaelhaddadny@gmail.com'
EMAIL_TO = 'raphaelhaddadny@gmail.com'
EMAIL_PASSWORD = 'aqjlchgfppunbhch'

def get_db():
    if not hasattr(g, 'db_conn'):
        g.db_conn = psycopg2.connect(DATABASE_URL)
        g.db_cursor = g.db_conn.cursor()
    return g.db_conn, g.db_cursor

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, 'db_conn', None)
    if db:
        db.close()

def send_email(subject, body):
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = EMAIL_FROM
        msg['To'] = EMAIL_TO
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
    except Exception as e:
        print("Failed to send email:", e)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/book', methods=['GET', 'POST'])
def book():
    if request.method == 'POST':
        data = (
            request.form['name'],
            request.form['email'],
            request.form['phone'],
            request.form['address'],
            request.form['car_model'],
            request.form['license_plate'],
            request.form['fuel_type'],
            request.form['instructions']
        )
        conn, cur = get_db()
        cur.execute("""
            INSERT INTO bookings (name, email, phone, address, car_model, license_plate, fuel_type, instructions)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, data)
        conn.commit()
        send_email("New Booking", str(data))
        flash('Booking submitted!')
        return redirect(url_for('home'))
    return render_template('book.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        data = (
            request.form['name'],
            request.form['email'],
            request.form['phone'],
            request.form['subject'],
            request.form['message']
        )
        conn, cur = get_db()
        cur.execute("""
            INSERT INTO contacts (name, email, phone, subject, message)
            VALUES (%s,%s,%s,%s,%s)
        """, data)
        conn.commit()
        send_email("New Contact Message", str(data))
        flash("Message sent successfully!")
        return redirect(url_for('home'))
    return render_template('contact.html')

@app.route('/locations')
def locations():
    return render_template('locations.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if request.form['username'] == ADMIN_USERNAME and request.form['password'] == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('dashboard'))
        flash('Invalid login')
    return render_template('admin.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin'))
    conn, cur = get_db()
    cur.execute("SELECT * FROM bookings ORDER BY id DESC")
    bookings = cur.fetchall()
    return render_template('dashboard.html', bookings=bookings)

@app.route('/booking/<int:id>')
def view_booking(id):
    if not session.get('admin'):
        return redirect(url_for('admin'))
    conn, cur = get_db()
    cur.execute("SELECT * FROM bookings WHERE id = %s", (id,))
    booking = cur.fetchone()
    return render_template('view_booking.html', booking=booking)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_booking(id):
    if not session.get('admin'):
        return redirect(url_for('admin'))
    conn, cur = get_db()
    cur.execute("DELETE FROM bookings WHERE id = %s", (id,))
    conn.commit()
    flash("Booking deleted")
    return redirect(url_for('dashboard'))

@app.route('/export')
def export_csv():
    if not session.get('admin'):
        return redirect(url_for('admin'))
    conn, cur = get_db()
    cur.execute("SELECT * FROM bookings ORDER BY id DESC")
    bookings = cur.fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Name', 'Email', 'Phone', 'Address', 'Car Model', 'License Plate', 'Fuel Type', 'Instructions'])
    for b in bookings:
        writer.writerow(b)
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv', as_attachment=True, download_name='bookings.csv')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
