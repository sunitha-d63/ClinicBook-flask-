from flask import Flask, render_template, request, redirect, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecret"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clinic.db'
db = SQLAlchemy(app)

app.config['MAIL_SERVER'] = 'sandbox.smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = "51648e062e59c2"  
app.config['MAIL_PASSWORD'] = "****4110" 
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
mail = Mail(app)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(15))
    doctor = db.Column(db.String(50))
    date = db.Column(db.String(20))
    time = db.Column(db.String(10))
    status = db.Column(db.String(20), default="Pending")

@app.route("/", methods=["GET", "POST"])
def book():
    if request.method == "POST":
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        doctor = request.form['doctor']
        date = request.form['date']
        time = request.form['time']

        if not name or not email or not phone or not date or not time:
            flash("All fields are required!", "danger")
            return redirect(url_for("book"))
        if not phone.isdigit() or len(phone) != 10:
            flash("Phone must be 10 digits", "danger")
            return redirect(url_for("book"))

        appt = Appointment(patient_name=name, email=email, phone=phone,
                           doctor=doctor, date=date, time=time)
        db.session.add(appt)
        db.session.commit()
        flash("Appointment booked successfully!", "success")
        try:
            msg = Message("Appointment Confirmation",
                          sender="clinic@example.com",
                          recipients=[email])
            msg.body = f"Dear {name}, your appointment with Dr. {doctor} is confirmed on {date} at {time}."
            mail.send(msg)
            print(f"Reminder email sent to {email}")
        except Exception as e:
            print("Email failed:", e)

        return redirect(url_for("book"))
    return render_template("book.html")

@app.route("/doctor")
def doctor_dashboard():
    appointments = Appointment.query.all()
    return render_template("doctor.html", appointments=appointments)

# -----------------------
# ✅ New Routes for Actions
# -----------------------

@app.route("/cancel/<int:appt_id>", methods=["POST"])
def cancel_appointment(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    appt.status = "Cancelled"
    db.session.commit()
    flash(f"Appointment {appt.id} cancelled.", "warning")
    return redirect(url_for("doctor_dashboard"))

@app.route("/approve/<int:appt_id>", methods=["POST"])
def approve_appointment(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    appt.status = "Approved"
    db.session.commit()
    flash(f"Appointment {appt.id} approved.", "success")
    return redirect(url_for("doctor_dashboard"))

@app.route("/postpone/<int:appt_id>", methods=["GET", "POST"])
def postpone_appointment(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    if request.method == "POST":
        new_date = request.form.get("date")
        new_time = request.form.get("time")
        if new_date and new_time:
            appt.date = new_date
            appt.time = new_time
            appt.status = "Postponed"
            db.session.commit()
            flash(f"Appointment {appt.id} postponed to {new_date} at {new_time}.", "info")
            return redirect(url_for("doctor_dashboard"))
        flash("Please provide new date and time.", "danger")
    return render_template("postpone.html", appt=appt)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
