from flask import render_template
from app.routes import patient

@patient.route('/profile')
def profile():
    return render_template('patient/profile.html')
