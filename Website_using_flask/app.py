from flask import Flask, render_template,request

app = Flask(__name__)

@app.route('/')
def hello_world():
    return render_template('login.html')


@app.route('/register')
def register():
    return render_template('register.html') 

@app.route('/perform_registration',methods=['post'])
def perform_registration():
    name=request.form.get['user_name']
    email=request.form.get['user_email']
    password=request.form.get['user_password']
    return name+" "+email+" "+password

app.run(debug=True)