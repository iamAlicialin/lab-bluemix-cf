######################################################################
# Copyright 2016, 2022 John Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################

"""
Pet Store Service

Paths:
------
GET /pets - Returns a list all of the Pets
GET /pets/{id} - Returns the Pet with a given id number
POST /pets - creates a new Pet record in the database
PUT /pets/{id} - updates a Pet record in the database
DELETE /pets/{id} - deletes a Pet record in the database
"""

from flask import jsonify, request, url_for, make_response, abort
from service.models import Pet
from . import status  # HTTP Status Codes
from . import app  # Import Flask application

######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Root URL response"""
    app.logger.info("Request for Root URL")
    return app.send_static_file("index.html")


######################################################################
# LIST ALL PETS
######################################################################
@app.route("/pets", methods=["GET"])
def list_pets():
    """Returns all of the Pets"""
    app.logger.info("Request for pet list")

    pets = []

    category = request.args.get("category")
    name = request.args.get("name")
    available = request.args.get("available")
    gender = request.args.get("gender")

    if category:
        app.logger.info("Filtering by category: %s", category)
        pets = Pet.find_by_category(category)
    elif name:
        app.logger.info("Filtering by name:%s", name)
        pets = Pet.find_by_name(name)
    elif available:
        app.logger.info("Filtering by available: %s", available)
        is_available = available.lower() in ["yes", "y", "true", "t", "1"]
        pets = Pet.find_by_availability(is_available)
    elif gender:
        app.logger.info("Filtering by gender: %s", gender)
        pets = Pet.find_by_gender(gender)
    else:
        pets = Pet.all()

    results = [pet.serialize() for pet in pets]
    app.logger.info("Returning %d pets", len(results))
    return make_response(jsonify(results), status.HTTP_200_OK)


######################################################################
# RETRIEVE A PET
######################################################################
@app.route("/pets/<pet_id>", methods=["GET"])
def get_pets(pet_id):
    """
    Retrieve a single Pet

    This endpoint will return a Pet based on it's id
    """
    app.logger.info("Request for pet with id: %s", pet_id)
    pet = Pet.find(pet_id)

    if not pet:
        abort(status.HTTP_404_NOT_FOUND, f"Pet with id '{pet_id}' was not found.")

    app.logger.info("Returning pet: %s", pet.name)
    return jsonify(pet.serialize()), status.HTTP_200_OK


######################################################################
# CREATE A PET
######################################################################
@app.route("/pets", methods=["POST"])
def create_pets():
    """
    Creates a Pet

    This endpoint will create a Pet based the data in the body that is posted
    or data that is sent via an html form post.
    """
    app.logger.info("Request to Create a pet")
    content_type = request.headers.get("Content-Type")

    if not content_type:
        abort(status.HTTP_400_BAD_REQUEST, "No Content-Type set")

    data = {}
    # Check for form submission data
    if content_type == "application/x-www-form-urlencoded":
        app.logger.info("Processing FORM data")
        app.logger.info(type(request.form))
        app.logger.info(request.form)
        data = {
            "name": request.form["name"],
            "category": request.form["category"],
            "available": request.form["available"].lower() in ["yes", "y", "true", "t", "1"],
            "gender": request.form["gender"],
        }
        app.logger.info("Available: {} = {}".format(request.form["available"], data["available"]))
    elif content_type == "application/json":
        app.logger.info("Processing JSON data")
        data = request.get_json()
    else:
        message = "Unsupported Content-Type: {}".format(content_type)
        app.logger.info(message)
        abort(status.HTTP_400_BAD_REQUEST, message)

    # Create the Pet from the data
    pet = Pet()
    pet.deserialize(data)
    pet.create()

    message = pet.serialize()
    location_url = url_for("get_pets", pet_id=pet.id, _external=True)

    app.logger.info("Pet with ID [%s] created.", pet.id)
    return jsonify(pet.serialize()), status.HTTP_201_CREATED, {"Location": location_url}


######################################################################
# UPDATE AN EXISTING PET
######################################################################
@app.route("/pets/<pet_id>", methods=["PUT"])
def update_pets(pet_id):
    """
    Update a Pet

    This endpoint will update a Pet based the body that is posted
    """
    app.logger.info("Request to Update pet with id: %s", pet_id)
    check_content_type("application/json")

    pet = Pet.find(pet_id)
    if not pet:
        abort(status.HTTP_404_NOT_FOUND, f"Pet with id '{pet_id}' was not found.")

    pet.deserialize(request.get_json())
    pet.id = pet_id
    pet.update()

    app.logger.info("Pet with ID [%s] updated.", pet.id)
    return jsonify(pet.serialize()), status.HTTP_200_OK


######################################################################
# DELETE A PET
######################################################################
@app.route("/pets/<pet_id>", methods=["DELETE"])
def delete_pets(pet_id):
    """
    Delete a Pet

    This endpoint will delete a Pet based the id specified in the path
    """
    app.logger.info("Request to Delete pet with id: %s", pet_id)
    pet = Pet.find(pet_id)
    if pet:
        pet.delete()

    app.logger.info("Pet with ID [%s] delete complete.", pet_id)
    return make_response("", status.HTTP_204_NO_CONTENT)


######################################################################
# PURCHASE A PET
######################################################################
@app.route("/pets/<pet_id>/purchase", methods=["PUT"])
def purchase_pets(pet_id):
    """Endpoint to Purchase a Pet"""
    app.logger.info("Request to Purchase pet with id: %s", pet_id)

    pet = Pet.find(pet_id)
    if not pet:
        abort(status.HTTP_404_NOT_FOUND, f"Pet with id '{pet_id}' was not found.")

    if not pet.available:
        abort(status.HTTP_409_CONFLICT, f"Pet with id '{pet_id}' is not available.")

    pet.available = False
    pet.update()
    return jsonify(pet.serialize()), status.HTTP_200_OK


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################


def check_content_type(media_type: str) -> None:
    """Checks that the media type is correct"""
    content_type = request.headers.get("Content-Type")

    if not content_type:
        abort(status.HTTP_400_BAD_REQUEST, "No Content-Type set")

    if content_type == media_type:
        return  # Content-Type OK

    app.logger.error("Invalid Content-Type: %s", content_type)
    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        f"Content-Type must be {media_type}",
    )
