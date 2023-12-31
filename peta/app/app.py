import re
import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
from datetime import datetime
import logging

app = Flask(__name__)

app.secret_key = "abcdefgh"

logging.basicConfig(level=logging.DEBUG)

app.config["MYSQL_HOST"] = "db"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = "password"
app.config["MYSQL_DB"] = "AnimalShelter"

mysql = MySQL(app)

@app.route("/", methods=["GET"])
def home():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    message = ""
    if (
        request.method == "POST"
        and "email" in request.form
        and "password" in request.form
    ):
        email = request.form["email"]
        password = request.form["password"]
        print(email)
        print(password)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            "SELECT * FROM user WHERE Email = % s AND Password = % s",
            (
                email,
                password,
            ),
        )
        user = cursor.fetchone()
        if user:
            userId = user["User_ID"]

            cursor.execute(
                "SELECT * FROM Veterinarian WHERE User_ID = % s",
                (userId,),
            )
            veterinarian = cursor.fetchone()
            if veterinarian:
                session["userType"] = "Veterinarian"
                session["userid"] = userId
                return redirect(url_for("vet_page"))
            else:
                cursor.execute(
                    "SELECT * FROM AnimalShelter WHERE User_ID = % s",
                    (userId,),
                )
                animalShelter = cursor.fetchone()
                if animalShelter:
                    session["userType"] = "AnimalShelter"
                    session["userid"] = userId
                    return redirect(url_for("shelterAnimalList"))
                else:
                    cursor.execute(
                        "SELECT * FROM Administrator WHERE User_ID = % s",
                        (userId,),
                    )
                    if "AD" in userId :
                        session["userType"] = "Admin"
                        session["userid"] = userId
                        return redirect(url_for("admin_panel"))
                    else:
                        session["userType"] = "Adopter"
                        session["userid"] = userId
                        return redirect(url_for("pet_search"))
                        
        else:
            message = "Please enter correct password !"
    return render_template("auth/login.html", message=message)


@app.route("/suite", methods=["GET"])
def suite():
    return render_template("auth/suite.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    message = ""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        name = request.form["name"]
        surname = request.form["surname"]
        phone = request.form["phone"]
        role = request.form["role"]

        if role == "vet":
            specialization = request.form["specialization"]
            clinic_name = request.form["clinic_name"]
            clinic_id = request.form["clinic_id"]
            status = request.form["status"]

        if any(
            value == ""
            for value in (email, password, confirm_password, name, surname, phone, role)
        ):
            message = "Please fill out all the fields!"
            return render_template("auth/register.html", message=message)

        if password != confirm_password:
            message = "Passwords do not match!"
            return render_template("auth/register.html", message=message)

        if (
            len(password) > 40
            or len(name) > 60
            or len(surname) > 60
            or len(email) > 100
            or len(phone) > 20
        ):
            message = "Field length exceeds the limit!"
            return render_template("auth/register.html", message=message)

        try:
            new_user_id = "U" + str("123342")
            hashed_email = sum(ord(char) for char in email) % (10**9)
            new_user_id = "U" + str(hashed_email)
            cursor.execute(
                "INSERT INTO user (User_ID, Password, First_Middle_Name, Last_Name, Email, Phone_Number) VALUES (%s, %s, %s, %s, %s, %s)",
                (new_user_id, password, name, surname, email, phone),
            )
            mysql.connection.commit()

            if role == "vet":
                cursor.execute(
                    "INSERT INTO Veterinarian (User_ID, Specialization, Clinic_Name, Clinic_ID, Status) VALUES (%s, %s, %s, %s, %s)",
                    (new_user_id, specialization, clinic_name, clinic_id, status),
                )
            elif role == "adopter":
                cursor.execute(
                    "INSERT INTO Adopter (User_ID, Number_of_Adoptions) VALUES (%s, %s)",
                    (new_user_id, 0),
                )
            elif role == "shelter":
                cursor.execute(
                    "INSERT INTO AnimalShelter (User_ID, Number_of_Animals) VALUES (%s, %s)",
                    (new_user_id, 0),
                )

            mysql.connection.commit()
            message = "User successfully registered!" + new_user_id
        except Exception as e:
            message = f"Error: {str(e)}"

    else:
        message = "Please fill out all the fields!"

    return render_template("auth/register.html", message=message)


pets_data1 = [
    {
        "Pet_ID": "1",
        "Name": "Buddy",
        "Breed": "Labrador Retriever",
        "Date_of_Birth": "2020-01-15",
        "Age": 3,
        "Gender": "Male",
        "Description": "Friendly and active",
        "Adoption_Status": "Available",
        "Medical_History": "Vaccinated and dewormed",
    },
    {
        "Pet_ID": "2",
        "Name": "Buddy",
        "Breed": "Labrador Retriever",
        "Date_of_Birth": "2020-01-15",
        "Age": 3,
        "Gender": "Male",
        "Description": "Friendly and active",
        "Adoption_Status": "Available",
        "Medical_History": "Vaccinated and dewormed",
    },
    {
        "Pet_ID": "3",
        "Name": "Buddy",
        "Breed": "Labrador Retriever",
        "Date_of_Birth": "2020-01-15",
        "Age": 3,
        "Gender": "Male",
        "Description": "Friendly and active",
        "Adoption_Status": "Available",
        "Medical_History": "Vaccinated and dewormed",
    },
]


@app.route("/vet-appointment")
def user_pets():
    message = ""
    user_id = session["userid"]
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        "SELECT p.* FROM Pet p INNER JOIN Has_Pet hp ON p.Pet_ID = hp.Pet_ID WHERE hp.User_ID = %s",
        (user_id,),
    )
    user_pets = cursor.fetchall()
    return render_template("mypetlist.html", pets=user_pets)


@app.route("/petcare")
def petcare():
    message = ""
    user_id = session["userid"]
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        "SELECT p.* FROM Pet p INNER JOIN Has_Pet hp ON p.Pet_ID = hp.Pet_ID WHERE hp.User_ID = %s",
        (user_id,),
    )
    user_pets = cursor.fetchall()
    return render_template("petcareinfo.html", pets=user_pets)


@app.route("/petcare/<pet_type>")
def pet_care_info(pet_type):
    return render_template("typepetcare.html", pet_type=pet_type)


pet_details = {
    "Pet_ID": "1",
    "Name": "Buddy",
    "Breed": "Labrador Retriever",
    "Date_of_Birth": "2020-01-15",
    "Age": 3,
    "Gender": "Male",
    "Description": "Friendly and active",
    "Adoption_Status": "Available",
    "Medical_History": "Vaccinated and dewormed",
}


@app.route("/schedule_online_meeting/<pet_id>", methods=["GET", "POST"])
def schedule_online_meeting(pet_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute("SELECT * FROM Pet WHERE Pet_ID = %s", (pet_id,))
    pet_details = cursor.fetchone()

    cursor.execute(
        "SELECT u.User_ID, CONCAT(u.First_Middle_Name, ' ', u.Last_Name) AS Full_Name FROM user u, Veterinarian v WHERE u.User_ID = v.User_ID;"
    )
    veterinarians = cursor.fetchall()

    if request.method == "POST":
        email = request.form["email"]
        fullname = request.form["fullname"]
        problems = request.form["problems"]
        appointment_time = request.form["appointment-time"]
        selected_vet = request.form["veterinarian"]
        hash = sum(ord(char) for char in session["userid"] + pet_id + problems) % (
            10**9
        )
        random_number = "A" + str(hash)

        user_id = session["userid"]
        cursor.execute(
            "SELECT Email, CONCAT(First_Middle_Name, ' ', Last_Name) AS Full_Name FROM user WHERE User_ID = %s",
            (user_id,),
        )
        user_info = cursor.fetchone()

        if (
            str(user_info["Email"]).lower().strip() == str(email).lower().strip()
            and str(user_info["Full_Name"]).lower().strip()
            == str(fullname).lower().strip()
        ):
            cursor.execute(
                "INSERT INTO Appointment (Appointment_ID, Date, Time, Purpose) VALUES (%s, %s, %s, %s)",
                (
                    random_number,
                    appointment_time.split("T")[0],
                    appointment_time.split("T")[1],
                    problems,
                ),
            )
            mysql.connection.commit()
            cursor.execute(
                "INSERT INTO vet_appoint (Appointment_ID, Patient_ID) VALUES (%s, %s)",
                (random_number, user_id),
            )
            mysql.connection.commit()

            cursor.execute(
                "SELECT Appointment_ID FROM Appointment ORDER BY Appointment_ID DESC LIMIT 1"
            )
            appointment_id = cursor.fetchone()["Appointment_ID"]

            form_success = True
            return render_template(
                "online_meeting.html",
                pet=pet_details,
                veterinarians=veterinarians,
                form_success=form_success,
            )

        return render_template(
            "online_meeting.html",
            pet=pet_details,
            veterinarians=veterinarians,
            message="invalid fields"
            + email
            + fullname
            + user_info["Email"]
            + user_info["Full_Name"],
        )

    user_id = session["userid"]
    cursor.execute(
        "SELECT Email, CONCAT(First_Middle_Name, ' ', Last_Name) AS Full_Name FROM user WHERE User_ID = %s",
        (user_id,),
    )
    user_info = cursor.fetchone()
    return render_template(
        "online_meeting.html",
        pet=pet_details,
        veterinarians=veterinarians,
    )


@app.route("/schedule_vet_appointment/<pet_id>", methods=["GET", "POST"])
def schedule_vet_appointment(pet_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute("SELECT * FROM Pet WHERE Pet_ID = %s", (pet_id,))
    pet_details = cursor.fetchone()
    veterinarians = {}
    cursor.execute("SELECT DISTINCT Clinic_Name FROM Veterinarian")
    clinics = cursor.fetchall()

    if request.method == "POST":
        selected_clinic = request.form.get("clinic")

        cursor.execute(
            "SELECT u.User_ID, CONCAT(u.First_Middle_Name, ' ', u.Last_Name) AS Full_Name FROM user u "
            "JOIN Veterinarian v ON u.User_ID = v.User_ID WHERE v.Clinic_Name = %s",
            (selected_clinic,),
        )
        veterinarians = cursor.fetchall()
        email = request.form["email"]
        fullname = request.form["fullname"]
        problems = request.form["problems"]
        appointment_time = request.form["appointment-time"]
        selected_vet = ""
        if "veterinarian" in request.form:
            selected_vet = request.form["veterinarian"]
        hash = sum(ord(char) for char in session["userid"] + pet_id + problems) % (
            10**9
        )
        random_number = "A" + str(hash)

        user_id = session["userid"]
        cursor.execute(
            "SELECT Email, CONCAT(First_Middle_Name, ' ', Last_Name) AS Full_Name FROM user WHERE User_ID = %s",
            (user_id,),
        )
        user_info = cursor.fetchone()

        if (
            str(user_info["Email"]).lower().strip() == str(email).lower().strip()
            and str(user_info["Full_Name"]).lower().strip()
            == str(fullname).lower().strip()
        ):
            cursor.execute(
                "INSERT INTO Appointment (Appointment_ID, Date, Time, Purpose) VALUES (%s, %s, %s, %s)",
                (
                    random_number,
                    appointment_time.split("T")[0],
                    appointment_time.split("T")[1],
                    problems,
                ),
            )
            mysql.connection.commit()
            cursor.execute(
                "INSERT INTO vet_appoint (Appointment_ID, User_ID) VALUES (%s, %s)",
                (random_number, user_id),
            )

            cursor.execute(
                "SELECT Appointment_ID FROM Appointment ORDER BY Appointment_ID DESC LIMIT 1"
            )
            appointment_id = cursor.fetchone()["Appointment_ID"]

            cursor.execute(
                "INSERT INTO vet_appoint (Appointment_ID, User_ID) VALUES (%s, %s)",
                (appointment_id, user_id),
            )
            mysql.connection.commit()
            return render_template(
                "vet_meeting.html",
                pet=pet_details,
                clinics=clinics,
                veterinarians=veterinarians,
            )

        return render_template(
            "vet_meeting.html",
            pet=pet_details,
            clinics=clinics,
            veterinarians=veterinarians,
        )

    return render_template(
        "vet_meeting.html",
        pet=pet_details,
        clinics=clinics,
        veterinarians=veterinarians,
    )

pets_data = {
    1: {
        "Pet_ID": 1,
        "Name": "Fluffy",
        "Breed": "Golden Retriever",
    }
}

applications_data = {
    1: {
        "Application_ID": 1,
        "Pet_ID": 1,
        "Donation_Fee": 50,
        "Admin_Approved": True,
        "Shelter_Approved": True,
    }
}


@app.route("/current-vet-appointments")
def vet_appointments():
    user_id = session["userid"]
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        "SELECT * FROM vet_appoint JOIN Appointment ON vet_appoint.Appointment_ID = Appointment.Appointment_ID WHERE vet_appoint.Patient_ID = %s",
        (user_id,),
    )

    vet_appointment_data = cursor.fetchall()
    cursor.close()

    return render_template(
        "current_vet_appointments.html", vet_appointment_data=vet_appointment_data
    )


@app.route("/adoption-application/<id>", methods=["GET", "POST"])
def adoption_application(id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == "GET":
        user_id = session["userid"]
        if not user_id:
            return "User not logged in", 403

        cursor.execute(
            "SELECT p.*, aa.* "
            "FROM Pet p "
            "JOIN Pet_Adoption pa ON p.Pet_ID = pa.Pet_ID "
            "JOIN AdoptionApplication aa ON aa.Application_ID = pa.Application_ID "
            "WHERE aa.Application_ID = %s AND aa.User_ID = %s",
            (id, user_id),
        )
        pet_application = cursor.fetchone()
        cursor.execute(
            "SELECT * FROM Meet_And_Greet WHERE Pet_ID = %s AND User_ID = %s",
            (id, user_id),
        )
        meet_and_greet = cursor.fetchall()

        if not pet_application:
            return "Pet or application not found", 404

        return render_template(
            "adoption_application.html",
            pet=pet_application,
            application=pet_application,
            meet_and_greet=meet_and_greet,
        )

    elif request.method == "POST":
        if "schedule_meet" in request.form:
            date = request.form.get("date")
            phone_number = request.form.get("phone_number")

            cursor.execute(
                "INSERT INTO Meet_And_Greet (Date, Time, Pet_ID, User_ID) VALUES (%s, %s, %s, %s)",
                (date.split("T")[0], date.split("T")[1], id, session["userid"]),
            )
            mysql.connection.commit()

            return redirect(url_for("adoption_application", id=id))

        elif "cancel_application" in request.form:
            cursor.execute(
                "UPDATE AdoptionApplication SET Application_Status = 'Canceled' "
                "WHERE Application_ID = %s AND User_ID = %s",
                (id, session["userid"]),
            )
            mysql.connection.commit()

            return redirect(url_for("adoption_application", id=id))

        elif "delete_meet" in request.form:
            meet_date = request.form.get("meet_date")
            meet_time = request.form.get("meet_time")

            cursor.execute(
                "DELETE FROM Meet_And_Greet WHERE Date = %s AND Time = %s AND User_ID = %s",
                (meet_date, meet_time, session["userid"]),
            )
            mysql.connection.commit()
            return redirect(url_for("adoption_application", id=id))

        user_id = session["userid"]
        if not user_id:
            return "User not logged in", 403

        cursor.execute(
            "SELECT p.*, aa.* "
            "FROM Pet p "
            "JOIN Pet_Adoption pa ON p.Pet_ID = pa.Pet_ID "
            "JOIN AdoptionApplication aa ON aa.Application_ID = pa.Application_ID "
            "WHERE aa.Application_ID = %s",
            (id),
        )
        pet_application = cursor.fetchone()

        if not pet_application:
            return "Pet or application not found", 404

        return render_template(
            "adoption_application.html",
            pet=pet_application,
            application=pet_application,
        )

    return "Invalid Request", 400


@app.route("/current-applications")
def current_applications():
    user_id = session["userid"]
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute(
        "SELECT Application_ID, Application_Date, Application_Status FROM AdoptionApplication WHERE User_ID = %s",
        (user_id,),
    )
    applications = cursor.fetchall()

    return render_template("current_applications.html", applications=applications)


@app.route("/new-adoption-application/<pet_id>", methods=["GET", "POST"])
def new_adoption_application(pet_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute("SELECT * FROM Pet WHERE Pet_ID = %s", (pet_id,))
    pet_details = cursor.fetchone()

    if not pet_details:
        return "Pet or application not found", 404

    if pet_details["Adoption_Status"] == "Approved":
        return "Pet is approved for adoption", 401

    if request.method == "POST":
        applicant_name = request.form["applicant_name"]
        new_app_id = "A" + str("123342")
        hash = sum(
            ord(char) for char in session["userid"] + pet_id + applicant_name
        ) % (10**9)
        new_app_id = "A" + str(hash)

        cursor.execute(
            "INSERT INTO AdoptionApplication (Application_ID, User_ID, Application_Date, Application_Status) VALUES (%s, %s, CURDATE(), %s)",
            (new_app_id, session["userid"], "Unapproved"),
        )
        mysql.connection.commit()

        cursor.execute(
            "INSERT INTO Pet_Adoption (Application_ID, Pet_ID) VALUES (%s, %s)",
            (new_app_id, pet_id),
        )
        mysql.connection.commit()

        return render_template(
            "newadoption.html", pet_details=pet_details, submitted=True
        )

    return render_template("newadoption.html", pet_details=pet_details)


@app.route("/registerPet", methods=["GET", "POST"])
def registerPet():
    message = ""
    if (
        request.method == "POST"
        and "type" in request.form
        and "breed" in request.form
        and "dateOfBirth" in request.form
        and "vacCard" in request.form
        and "gender" in request.form
        and "description" in request.form
        and "name" in request.form
    ):
        # real
        # userid = session["userid"]

        # for dev purposes must be changed when in Use
        userid = "AS001"

        # get form info
        animalType = request.form["type"]
        animalBreed = request.form["breed"]
        dateOfBirth = request.form["dateOfBirth"]
        vacCard = request.form["vacCard"]
        gender = request.form["gender"]
        description = request.form["description"]
        animalName = request.form["name"]
        animalFee = request.form["fee"]
        # for test
        printer = (
            "animalType: ",
            animalType,
            "animalBreed: ",
            animalBreed,
            "dateOfBirth: ",
            dateOfBirth,
            "vacCard: ",
            vacCard,
            "gender: ",
            gender,
            "description: ",
            description,
            "animalName: ",
            animalName,
            "animalFee: ",
            animalFee,
        )
        message = printer
        if not animalFee:
            animalFee = 0
        # control missing info
        if (
            not animalType
            or not animalBreed
            or not dateOfBirth
            or not vacCard
            or not gender
            or not description
            or not animalName
        ):
            message = "Please fill out the form!"
            return render_template("shelter/registerPet.html", message=message)
        # control for db
        elif (
            len(animalType) > 11
            or len(animalBreed) > 50
            or len(gender) > 10
            or len(description) > 250
            or len(vacCard) > 250
            or len(animalName) > 50
        ):
            message = "Too long texts!"
            return render_template("register.html", message=message)

        today = datetime.now().date()
        birth_date = datetime.strptime(dateOfBirth, "%Y-%m-%d").date()
        age = (
            today.year
            - birth_date.year
            - ((today.month, today.day) < (birth_date.month, birth_date.day))
        )
        # control birth date
        if birth_date > today:
            message = "Invalid date of birth. Please enter a date in the past."
            return render_template("shelter/registerPet.html", message=message)

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM AnimalShelter WHERE User_ID = %s", (userid,))
        account = cursor.fetchone()

        # checks if this is a shelter account
        if account:
            cursor.execute("SELECT * FROM Pet")
            pets = cursor.fetchall()
            lastId = 354
            maxNum = 0
            for pet in pets:
                lastId = int(pet["Pet_ID"][1:])
                if maxNum < lastId:
                    maxNum = lastId
            nextId = "P" + str(maxNum + 1)

            # insert new Pet
            cursor.execute(
                "INSERT INTO Pet (Pet_ID, Type, Name, Breed, Date_of_Birth, Age, Gender, Description, Adoption_Status, Medical_History, adoption_Fee) VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    nextId,
                    animalType,
                    animalName,
                    animalBreed,
                    dateOfBirth,
                    age,
                    gender,
                    description,
                    "Unapproved",
                    vacCard,
                    animalFee,
                ),
            )
            mysql.connection.commit()
            # increment animal count of animal shelter
            current_number_of_animals = account["Number_of_Animals"]
            updated_number_of_animals = current_number_of_animals
            cursor.execute(
                "UPDATE AnimalShelter SET Number_of_Animals = %s WHERE User_ID = %s",
                (updated_number_of_animals, userid),
            )
            mysql.connection.commit()
            cursor.execute(
                "INSERT INTO lists (User_ID, Pet_ID) VALUES ( %s, %s)", (userid, nextId)
            )
            mysql.connection.commit()

        cursor.execute("SELECT * FROM Pet")
        allPets = cursor.fetchall()
        # must be changed in the prod
        message = allPets
        # message = 'Pet successfully created!'
    elif request.method == "POST":
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        message = "Please fill all the fields!"

    return render_template("shelter/registerPet.html", message=message)


@app.route("/current_adopted_pets", methods=["GET", "POST"])
def current_adopted_pets():
    if request.method == "GET":
        userid = session["userid"]
        message = userid
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        if userid:
            cursor.execute(
                """
                    SELECT P.*
                    FROM Pet P 
                    NATURAL JOIN Pet_Adoption PA 
                    NATURAL JOIN AdoptionApplication AA 
                    WHERE AA.User_ID = %s AND AA.Application_Status = 'Approved';
                """,
                (userid,),
            )

            pets = cursor.fetchall()
            message = pets
            return render_template(
                "adoptedPets.html", message=message
            ) 
        else:
            return redirect(url_for("login"))


@app.route("/vet_page", methods=["GET", "POST"])
def vet_page():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == "GET":
        userid = session["userid"]
        message = userid
        if userid:
            cursor.execute(
                """
                    SELECT *
                    FROM user U 
                    NATURAL JOIN vet_appoint V 
                    NATURAL JOIN Appointment A 
                    WHERE A.AppointmentStatus = 'Unconfirmed' AND U.User_ID = %s;
                """,
                (userid,),
            )
            notConfirmedAppointments = cursor.fetchall()
            message = notConfirmedAppointments
            cursor.execute(
                """
                    SELECT *
                    FROM user U 
                    NATURAL JOIN vet_appoint V 
                    NATURAL JOIN Appointment A 
                    WHERE A.AppointmentStatus = 'Confirmed' AND U.User_ID = %s;
                """,
                (userid,),
            )
            notConfirmedAppointments = cursor.fetchall()
            message2 = notConfirmedAppointments
            return render_template(
                "vet_page.html", message=message, message2=message2
            ) 
        else:
            return redirect(url_for("vet_page"))

    if request.method == "POST":
        userid = session["userid"]
        appointment_id = request.form["Appointment_ID"]
        cursor.execute(
            """
                SELECT *
                FROM user U 
                NATURAL JOIN vet_appoint V 
                NATURAL JOIN Appointment A 
                WHERE A.AppointmentStatus = 'Unconfirmed' AND U.User_ID = %s;
            """,
            (userid,),
        )
        notConfirmedAppointments = cursor.fetchall()
        message = notConfirmedAppointments
        cursor.execute(
            """
                SELECT *
                FROM user U 
                NATURAL JOIN vet_appoint V 
                NATURAL JOIN Appointment A 
                WHERE A.AppointmentStatus = 'Confirmed' AND U.User_ID = %s;
            """,
            (userid,),
        )
        notConfirmedAppointments = cursor.fetchall()
        message2 = notConfirmedAppointments
        if "approve" in request.form:
            cursor = mysql.connection.cursor()
            cursor.execute(
                "UPDATE Appointment SET AppointmentStatus = 'Confirmed' WHERE Appointment_ID = %s",
                (appointment_id,),
            )
            mysql.connection.commit()
            error = appointment_id
            return render_template(
                "vet_page.html",
                message=message,
                message2=message2,
                error=appointment_id,
            )

        else:
            appointment_id = request.form["Appointment_ID"]
            new_date = request.form["newDate"]
            new_time = request.form["newTime"]
            cursor.execute(
                "UPDATE Appointment SET Date = %s, Time = %s, AppointmentStatus = 'Confirmed' WHERE Appointment_ID = %s",
                (new_date, new_time, appointment_id),
            )
            mysql.connection.commit()
            return "Appointment rescheduled successfully", 200

    return render_template(
        "vet_page.html", message=message, message2=message2, error=appointment_id
    )


@app.route("/shelterAnimalList", methods=["GET", "POST"])
def shelterAnimalList():
    if request.method == "GET":
        shelterId = session["userid"]
        userType = session["userType"]
        if not userType == "AnimalShelter":
            return redirect(url_for("login"))
        if shelterId:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute(
                """
                SELECT P.*
                FROM Pet P
                NATURAL JOIN lists L
                WHERE L.User_ID = %s AND P.Adoption_Status = 'Unapproved'
            """,
                (shelterId,),
            )

            message = cursor.fetchall()
            cursor.execute(
                "SELECT * FROM AnimalShelter WHERE User_ID = %s", (shelterId,)
            )
            AnimalS = cursor.fetchall()
            return render_template(
                "shelter/shelterAnimalList.html", message=message, animalNumber=AnimalS
            )
        else:
            return redirect(url_for("login"))

@app.route("/tasks", methods=["GET", "POST"])
def tasks():
    if request.method == "GET":
        userid = session["userid"]
        if userid:
            username = session["username"]
            year = session["year"]
            gpa = session["gpa"]
            dept = session["dept"]
            bdate = session["bdate"]
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute(
                """
                SELECT *
                FROM apply
                NATURAL JOIN company
                WHERE sid = %s
            """,
                (userid,),
            )
            message = cursor.fetchall()
            return render_template(
                "tasks.html",
                message=message,
                userid=userid,
                username=username,
                dept=dept,
                bdate=bdate,
                year=year,
                gpa=gpa,
            )
        else:
            return redirect(url_for("login"))

@app.route("/cancelApplication", methods=["GET", "POST"])
def cancelApplication():
    if request.method == "POST":
        userid = session["userid"]
        if userid:
            companyId = request.form.get("cid")
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            try:
                cursor.execute(
                    "DELETE FROM apply WHERE sid = %s AND cid = %s", (userid, companyId)
                )
                mysql.connection.commit()
                return render_template("cancelSuccessMessage.html")
            except MySQLError as e:
                return render_template("cancelFailMessage.html")
        else:
            return redirect(url_for("login"))
    return render_template("cancelFailMessage.html")

@app.route("/companies", methods=["GET", "POST"])
def companies():
    if request.method == "GET":
        userid = session["userid"]
        if userid:
            gpa = session["gpa"]
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute(
                "SELECT COUNT(*) AS applicationNumber FROM apply WHERE sid = %s",
                [userid],
            )
            applicationNumber = cursor.fetchone()
            if applicationNumber:
                applicationNumberVal = applicationNumber["applicationNumber"]
                if applicationNumberVal < 3:
                    cursor.execute(
                        """
                        SELECT *
                        FROM company remain
                        WHERE remain.cid NOT IN (
                            SELECT comp.cid
                            FROM company comp
                            WHERE quota = (
                                SELECT COUNT(*)
                                FROM apply
                                WHERE cid = comp.cid
                            )
                            UNION
                            SELECT app.cid
                            FROM apply app
                            WHERE app.sid = %s
                            UNION
                            SELECT DISTINCT c.cid
                            FROM company c
                            WHERE %s < c.gpaThreshold
                        )
                    """,
                        (
                            userid,
                            gpa,
                        ),
                    )
                    results = cursor.fetchall()

                    return render_template(
                        "companies.html", message=results, userid=userid
                    )
                else:
                    return render_template("quotaFullMessage.html")
            else:
                return redirect(url_for("login"))
        else:
            return redirect(url_for("login"))
    if request.method == "POST":
        gpa = session["gpa"]
        userid = session["userid"]
        if userid:
            companyId = request.form.get("cid")
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute(
                """
                            SELECT * 
                            FROM (
                                    SELECT *
                                    FROM company remain
                                    WHERE remain.cid NOT IN (
                                        SELECT comp.cid
                                        FROM company comp
                                        WHERE quota = (
                                            SELECT COUNT(*)
                                            FROM apply
                                            WHERE cid = comp.cid
                                        )
                                        UNION
                                        SELECT app.cid
                                        FROM apply app
                                        WHERE app.sid = %s
                                        UNION
                                        SELECT DISTINCT c.cid
                                        FROM company c
                                        WHERE %s < c.gpaThreshold
                                    )
                                ) AS result
                            WHERE result.cid = %s
                        """,
                (userid, gpa, companyId),
            )
            applyresults = cursor.fetchall()
            if not applyresults:
                return render_template("applyFailMessage.html")
            else:
                cursor.execute(
                    "INSERT INTO apply (sid, cid) VALUES (%s, %s)", (userid, companyId)
                )
                mysql.connection.commit()
                return render_template("applySuccessMessage.html")
        else:
            return render_template("login.html")
    return render_template("companies.html")

@app.route("/appSum", methods=["GET", "POST"])
def appSum():
    if request.method == "GET":
        userid = session["userid"]
        if userid:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute(
                """
                SELECT c.cid, c.cname, c.quota, c.gpaThreshold
                FROM apply a
                NATURAL JOIN company c
                WHERE a.sid = %s AND a.cid = c.cid
                ORDER BY c.quota DESC
            """,
                (userid,),
            )
            msg1 = cursor.fetchall()
            if not msg1:
                return render_template("noDataMessage.html")
            cursor.execute(
                """
            SELECT MAX(c.gpaThreshold) AS maxGpaThreshold, MIN(c.gpaThreshold) AS minGpaThreshold
            FROM apply a
            NATURAL JOIN company c
            WHERE a.sid = %s AND a.cid = c.cid
            """,
                (userid,),
            )
            msg2 = cursor.fetchall()

            cursor.execute(
                """
            SELECT c.city, COUNT(*) AS applicationCount
            FROM apply a
            NATURAL JOIN company c
            WHERE a.sid = %s AND a.cid = c.cid
            GROUP BY c.city
            """,
                (userid,),
            )
            msg3 = cursor.fetchall()

            cursor.execute(
                """
            SELECT comp.cname, temp.companyWithMaxQuota
            FROM
            (    
                SELECT MAX(c.quota) AS companyWithMaxQuota
                FROM apply a
                NATURAL JOIN company c
                WHERE a.sid = %s AND a.cid = c.cid
            ) temp, company comp
            WHERE comp.quota= temp.companyWithMaxQuota
            """,
                (userid,),
            )
            msg4 = cursor.fetchall()

            cursor.execute(
                """
            SELECT comp.cname, temp.companyWithMinQuota
            FROM
            (    
                SELECT MIN(c.quota) AS companyWithMinQuota
                FROM apply a
                NATURAL JOIN company c
                WHERE a.sid = %s AND a.cid = c.cid
            ) temp, company comp
            WHERE comp.quota= temp.companyWithMinQuota
            """,
                (userid,),
            )
            msg5 = cursor.fetchall()

            return render_template(
                "stats.html",
                msg1=msg1,
                msg2=msg2,
                msg3=msg3,
                msg4=msg4,
                msg5=msg5,
                userid=userid,
            )
        else:
            return redirect(url_for("login"))
    return "stats.html"

@app.route("/logout", methods=["GET", "POST"])
def logout():
    if request.method == "POST":
        session["loggedin"] = False
        session["userid"] = None
        session["username"] = None
        session["gpa"] = None
        session["bdate"] = None
        session["year"] = None
        session["dept"] = None
        return render_template("login.html")
    if request.method == "GET":
        session["loggedin"] = False
        session["userid"] = None
        session["username"] = None
        session["gpa"] = None
        session["bdate"] = None
        session["year"] = None
        session["dept"] = None
        return render_template("login.html")
    return render_template("login.html")

@app.route("/analysis", methods=["GET", "POST"])
def analysis():
    return "Analysis page"


@app.route("/admin_panel", methods=["GET", "POST"])
def admin_panel():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        """
        SELECT P.*, AA.*
            FROM Pet P 
            JOIN Pet_Adoption PA ON P.Pet_ID = PA.Pet_ID
            JOIN AdoptionApplication AA ON PA.Application_ID = AA.Application_ID
            WHERE AA.Application_Status = 'Unapproved'
        """
    )

    pet_data = cursor.fetchall()

    cursor.execute(
        """
                    SELECT Pet.*
                    FROM Pet
                    LEFT JOIN Pet_Adoption ON Pet.Pet_ID = Pet_Adoption.Pet_ID
                    WHERE Pet_Adoption.Pet_ID IS NULL AND Pet.Adoption_Status = 'Unapproved'
                    """
    )

    pet_data2 = cursor.fetchall()

    cursor.execute(
        """
                    SELECT V.User_ID, U.First_Middle_Name, U.Last_Name, COUNT(A.Appointment_ID) AS NumAppointments
                    FROM Veterinarian V
                    LEFT JOIN vet_appoint VA ON V.User_ID = VA.User_ID
                    LEFT JOIN Appointment A ON VA.Appointment_ID = A.Appointment_ID
                    LEFT JOIN user U ON V.User_ID = U.User_ID
                    GROUP BY V.User_ID, U.First_Middle_Name, U.Last_Name
                    ORDER BY NumAppointments DESC
                    LIMIT 3
                    """
    )

    vet_data = cursor.fetchall()

    cursor.execute(
        """
                    SELECT U.User_ID, U.First_Middle_Name, U.Last_Name, COUNT(HP.Pet_ID) AS NumAdoptedPets
                        FROM user U
                        LEFT JOIN Has_Pet HP ON U.User_ID = HP.User_ID
                        GROUP BY U.User_ID
                        ORDER BY NumAdoptedPets DESC
                        LIMIT 3
                    """
    )

    adopt_data = cursor.fetchall()

    cursor.execute(
        """
                    SELECT P.Breed, COUNT(P.Pet_ID) AS NumAdoptions
                    FROM Pet P NATURAL JOIN Has_Pet
                    GROUP BY P.Breed
                    ORDER BY NumAdoptions DESC
                    LIMIT 3
                    """
    )

    breed_data = cursor.fetchall()
    if request.method == "GET":
        return render_template(
            "admin_panel.html",
            pet_data=pet_data,
            pet_data2=pet_data2,
            vet_data=vet_data,
            adopt_data=adopt_data,
            breed_data=breed_data,
        )

    if request.method == "POST":
        pet_id = request.form.get("pet_id")
        cursor.execute(
            "SELECT Application_ID FROM Pet_Adoption WHERE Pet_ID = %s", (pet_id,)
        )

        cursor = mysql.connection.cursor()
        if "pet_id" in request.form and "mark_unavailable" in request.form:
            pet_id = request.form.get("pet_id")

            cursor = mysql.connection.cursor()
            cursor.execute("DELETE FROM Pet WHERE Pet_ID = %s", (pet_id,))
            mysql.connection.commit()

        elif "approve" in request.form:
            status = "Approved"
        elif "reject" in request.form:
            status = "Rejected"
        else:
            pass

        cursor.execute(
            "SELECT Application_ID FROM Pet_Adoption WHERE Pet_ID = %s", (pet_id,)
        )
        result = cursor.fetchone()
        if result:
            application_id = result
            try:
                cursor.execute(
                    "UPDATE AdoptionApplication SET Application_Status = %s WHERE Application_ID = %s",
                    (status, application_id),
                )
                mysql.connection.commit()
                message = "Status updated successfully!"
            except Exception as e:
                mysql.connection.rollback()
                message = f"Error: {str(e)}"
        else:
            message = "No application found for this pet."
        
        return render_template(
            "admin_panel.html",
            pet_data=pet_data,
            pet_data2=pet_data2,
            vet_data=vet_data,
            adopt_data=adopt_data,
            breed_data=breed_data,
            message=message,
        )


@app.route("/pet_search_page", methods=["GET", "POST"])
def pet_search():
    sql_query = """
            SELECT *
            FROM Pet P
            NATURAL JOIN AnimalShelter
            NATURAL JOIN lists
            WHERE P.Adoption_Status = 'Unapproved'
        """

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if request.method == "POST":

        search_query = request.form.get("search-input")
        pet_type = request.form.get("pet_type")
        min_age = request.form.get("min_age")
        max_age = request.form.get("max_age")
        min_fee = request.form.get("min_fee")
        max_fee = request.form.get("max_fee")
        gender = request.form.get("gender")

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        sql_query = """
            SELECT *
            FROM Pet P
            NATURAL JOIN AnimalShelter
            NATURAL JOIN lists
            WHERE P.Adoption_Status = 'Unapproved'
        """

        if search_query:
            sql_query += f" AND (P.Breed LIKE '%{search_query}%')"

        if pet_type:
            sql_query += f" AND P.Type = '{pet_type}'"

        if min_age:
            sql_query += f" AND P.Age >= {min_age}"

        if max_age:
            sql_query += f" AND P.Age <= {max_age}"

        if min_fee:
            sql_query += f" AND P.Adoption_Fee >= {min_fee}"

        if max_fee:
            sql_query += f" AND P.Adoption_Fee <= {max_fee}"

        if gender:
            sql_query += f" AND P.Gender = '{gender}'"

        cursor.execute(sql_query)
        pets = cursor.fetchall()

        return render_template("pet_search_page.html", pets=pets)

    cursor.execute(sql_query)
    pets = cursor.fetchall()
    return render_template("pet_search_page.html", pets=pets)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
