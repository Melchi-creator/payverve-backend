# Create your views here.
from django.shortcuts import render
from pyrebase import pyrebase

from backend.core.config.firebase import config

firebase = pyrebase.initialize_app(config)
authentication = firebase.auth()
database = firebase.database()


def sign_in(request):
    return render(request, auth)


def home(request):
    return render(request, "Home.html")


def post_sign_in(request):
    email = request.POST.get('email')
    pasw = request.POST.get('pass')
    try:
        # if there is no error then signin the user with given email and password
        user = authentication.sign_in_with_email_and_password(email, pasw)
    except:
        message = "Invalid Credentials!!Please ChecK your Data"
        return render(request, "Login.html", {"message": message})
    session_id = user['idToken']
    request.session['uid'] = str(session_id)
    return render(request, "Home.html", {"email": email})


def logout(request):
    try:
        del request.session['uid']
    except:
        pass
    return render(request, "Login.html")


def sign_up(request):
    return render(request, "Registration.html")


def post_sign_up(request):
    email = request.POST.get('email')
    passwd = request.POST.get('pass')
    name = request.POST.get('name')
    try:
        # creating a user with the given email and password
        user = authentication.create_user_with_email_and_password(email, passwd)
        uid = user['localId']
        idtoken = request.session['uid']
        print(uid)
    except:
        return render(request, "Registration.html")
    return render(request, "Login.html")
