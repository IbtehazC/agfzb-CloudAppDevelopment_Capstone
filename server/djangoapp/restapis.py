from django.http import response
import requests
import json
# import related models here
from .models import CarDealer, DealerReview
from requests.auth import HTTPBasicAuth
# ibm watson
from ibm_watson import NaturalLanguageUnderstandingV1, ApiException
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson.natural_language_understanding_v1 import Features, SentimentOptions
import dateutil.parser as parser


# Create a `get_request` to make HTTP GET requests
# e.g., response = requests.get(url, params=params, headers={'Content-Type': 'application/json'},
#                                     auth=HTTPBasicAuth('apikey', api_key))
def get_request(url, **kwargs):
    print("GET from {} ".format(url))
    try:
        # Call get method of requests library with URL and parameters
        response = requests.get(
            url, headers={'Content-Type': 'application/json'}, params=kwargs)
    except:
        # If any error occurs
        print("Network exception occurred")
    status_code = response.status_code
    print("With status {} ".format(status_code))
    json_data = json.loads(response.text)
    return json_data

# Create a `post_request` to make HTTP POST requests
# e.g., response = requests.post(url, params=kwargs, json=payload)


def post_review_to_cf(url, data):
    response = requests.post(url, data=data)
    return response


# Create a get_dealers_from_cf method to get dealers from a cloud function
# def get_dealers_from_cf(url, **kwargs):
# - Call get_request() with specified arguments
# - Parse JSON results into a CarDealer object list
def get_dealers_from_cf(url, **kwargs):
    results = []
    # Call get_request with a URL parameter
    json_result = get_request(url)
    if json_result:
        # Get the row list in JSON as dealers
        dealers = json_result["dealerships"]
        # For each dealer object
        for dealer in dealers:
            # Get its content in `doc` object
            dealer_doc = dealer
            # Create a CarDealer object with values in `doc` object
            dealer_obj = CarDealer(
                address=dealer_doc["address"], city=dealer_doc["city"], full_name=dealer_doc["full_name"], id=dealer_doc["id"],
                lat=dealer_doc["lat"],
                long=dealer_doc["long"],
                short_name=dealer_doc["short_name"],
                st=dealer_doc["st"],
                zip=dealer_doc["zip"])
            results.append(dealer_obj)

    return results


# Create a get_dealer_reviews_from_cf method to get reviews by dealer id from a cloud function
# def get_dealer_by_id_from_cf(url, dealerId):
# - Call get_request() with specified arguments
# - Parse JSON results into a DealerView object list
def get_dealer_reviews_from_cf(url, **kwargs):
    results = []
    # Call get_request with a URL parameter
    json_result = get_request(url)
    if json_result:
        # Get the row list in JSON as dealers
        reviews = json_result["reviews"]
        # For each dealer object
        for review in reviews:
            # Get its content in `doc` object
            review_doc = review
            sentiment = analyze_review_sentiments(review_doc["review"])
            if sentiment == "error":
                sentiment = "neutral"
            if review_doc["purchase"] is False:
                review_obj = DealerReview(
                    name=review_doc["name"],
                    purchase=review_doc["purchase"],
                    dealership=review_doc["dealership"],
                    review=review_doc["review"],
                    purchase_date=None,
                    car_make="",
                    car_model="",
                    car_year="",
                    id=review_doc["id"],
                    sentiment=sentiment
                )
                results.append(review_obj)
            else:
                review_obj = DealerReview(
                    name=review_doc["name"],
                    purchase=review_doc["purchase"],
                    dealership=review_doc["dealership"],
                    review=review_doc["review"],
                    purchase_date=parser.parse(str(review_doc["purchase_date"])).year,
                    car_make=review_doc["car_make"],
                    car_model=review_doc["car_model"],
                    car_year=review_doc["car_year"],
                    id=review_doc["id"],
                    sentiment=sentiment
                )
                results.append(review_obj)

    return results


# Create an `analyze_review_sentiments` method to call Watson NLU and analyze text
# def analyze_review_sentiments(text):
# - Call get_request() with specified arguments
# - Get the returned sentiment label such as Positive or Negative
def analyze_review_sentiments(text):
    authenticator = IAMAuthenticator(
        "fu_fWTMq-pGK1nqqxIfm7sEaHncqRSjjSIaRn6PlHcH1")
    natural_language_understanding = NaturalLanguageUnderstandingV1(
        version='2021-03-25',
        authenticator=authenticator)

    natural_language_understanding.set_service_url(
        "https://api.us-south.natural-language-understanding.watson.cloud.ibm.com/instances/588f87bf-76f4-45f3-8e85-78391d2216a6")

    try:
        response = natural_language_understanding.analyze(text=text, features=Features(
            sentiment=SentimentOptions()), language='en').get_result()
    except ApiException as ex:
        response = "error"
        print(ex.message)
        return response

    return (response["sentiment"]["document"]["label"])
