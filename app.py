from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from pymongo import MongoClient
from datetime import datetime

# Replace YOUR_URL with your MongoDB URL
cluster = MongoClient("mongodb+srv://Popsoko:Melman10@cluster0.zam6hab.mongodb.net/?retryWrites=true&w=majority")
db = cluster["medapp"]
users = db["users"]
appointments = db["appointments"]

app = Flask(__name__)

@app.route("/", methods=["POST"])
def reply():
    text = request.form.get("Body")
    number = request.form.get("From")
    number = number.replace("whatsapp:", "")[:-2]
    res = MessagingResponse()
    user = users.find_one({"number": number})

    if not user:
        # New user
        msg = res.message("Welcome to *Medapp*! How can we assist you today? Choose from the following options:\n\n"
                          "1️⃣ Schedule an appointment with a doctor\n"
                          "2️⃣ Ask a medical question\n"
                          "3️⃣ View your past appointments")
        users.insert_one({"number": number, "status": "main", "messages": []})

    elif user["status"] == "main":
        try:
            option = int(text)
        except ValueError:
            res.message("Please enter a valid response")
            return str(res)

        if option == 1:
            res.message("Please provide your preferred date and time for the appointment (e.g., 'Tomorrow at 3 PM').")
            users.update_one({"number": number}, {"$set": {"status": "schedule_appointment"}})
        elif option == 2:
            res.message("Please type your medical question, and a doctor will respond shortly.")
            users.update_one({"number": number}, {"$set": {"status": "ask_question"}})
        elif option == 3:
            appointments_history = list(appointments.find({"number": number}))
            if not appointments_history:
                res.message("You have no past appointments.")
            else:
                past_appointments = "\n".join([f"{a['date']}: {a['description']}" for a in appointments_history])
                res.message(f"Your past appointments:\n{past_appointments}")
        else:
            res.message("Please enter a valid response")

    elif user["status"] == "schedule_appointment":
        appointment_date = text
        appointments.insert_one({"number": number, "date": datetime.now(), "description": appointment_date})
        res.message(f"Your appointment request for '{appointment_date}' has been received. A doctor will confirm your appointment soon.")
        users.update_one({"number": number}, {"$set": "main"})

    elif user["status"] == "ask_question":
        # Handle the medical question and respond (you may need to integrate with a medical knowledge base or professionals).
        response = "Your medical question has been received, and a doctor will respond shortly."
        # Replace this with actual logic to handle medical questions.
        res.message(response)
        users.update_one({"number": number}, {"$set": "main"})

    users.update_one({"number": number}, {"$push": {"messages": {"text": text, "date": datetime.now()}})
    return str(res)

if __name__ == "__main__":
    app.run()
