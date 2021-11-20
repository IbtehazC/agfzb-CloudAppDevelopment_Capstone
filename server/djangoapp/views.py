from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
# from .models import related models
from .models import CarDealer, CarMake, CarModel
# from .restapis import related methods
from .restapis import get_dealers_from_cf, get_dealer_reviews_from_cf, post_review_to_cf
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from datetime import datetime
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


# Create your views here.


# Create an `about` view to render a static about page
def about(request):
    context = {}
    return render(request, 'djangoapp/about.html', context)


# Create a `contact` view to return a static contact page
def contact(request):
    context = {}
    return render(request, 'djangoapp/contact.html', context)

# Create a `login_request` view to handle sign in request


def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            print(user)
            login(request, user)
            return redirect('djangoapp:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'djangoapp/user_login.html', context)
    else:
        return render(request, 'djangoapp/user_login.html', context)

# Create a `logout_request` view to handle sign out request


def logout_request(request):
    logout(request)
    return redirect('djangoapp:index')

# Create a `registration_request` view to handle sign up request


def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'djangoapp/registration.html', context)
    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            login(request, user)
            return redirect("djangoapp:index")
        else:
            context['message'] = "User already exists."
            return render(request, 'djangoapp/registration.html', context)

# Update the `get_dealerships` view to render the index page with a list of dealerships


def get_dealerships(request):
    if request.method == "GET":
        context = {}
        url = "https://48f307eb.us-south.apigw.appdomain.cloud/djangoapp/api/dealership"
        # Get dealers from the URL
        dealerships_list = get_dealers_from_cf(url)
        # Concat all dealer's short name
        # Return a list of dealer short name
        context = {"dealerships_list": dealerships_list}
        return render(request, 'djangoapp/index.html', context)


# Create a `get_dealer_details` view to render the reviews of a dealer
def get_dealer_details(request, dealer_id):
    if request.method == "GET":
        url = "https://48f307eb.us-south.apigw.appdomain.cloud/djangoapp/api/review?dealerId=" + \
            str(dealer_id)
        # Get dealers from the URL
        reviews_list = get_dealer_reviews_from_cf(url)
        # Concat all dealer's short name
        context = {"reviews_list": reviews_list, "dealer_id": dealer_id}
        return render(request, 'djangoapp/dealer_details.html', context)

# Create a `add_review` view to submit a review


def add_review(request, dealer_id):
    if request.method == "POST":
        url = "https://48f307eb.us-south.apigw.appdomain.cloud/djangoapp/api/review"
        review = request.POST["content"]
        if request.POST["purchasecheck"] == "on":
            purchase = True
            purchase_date = request.POST["purchasedate"]
        else:
            purchase = False
            purchase_date = ""
        car_id = request.POST["car"]
        car = CarModel.objects.filter(id=car_id)
        car_model = car[0].name
        car_make = car[0].car_make.name
        car_year = car[0].year
        car_type = car[0].car_type
        car_object = {
            "id": 9,
            "name": car_model,
            "dealership": int(dealer_id),
            "review": review,
            "purchase": purchase,
            "another": "Field",
            "purchase_date": purchase_date,
            "car_make": car_make,
            "car_model": car_model,
            "car_type": car_type,
            "car_year": car_year
        }
        response = post_review_to_cf(url, car_object)
        print(response)
        return HttpResponseRedirect(reverse(viewname='djangoapp:dealer_details', args=(dealer_id,)))
    else:
        cars = CarModel.objects.filter(dealer_id=dealer_id)
        car = []
        for car_object in cars.iterator():
            car.append(car_object)
        return render(request, 'djangoapp/add_review.html', {"cars": car, "dealer_id": dealer_id})
