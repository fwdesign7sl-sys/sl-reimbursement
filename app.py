from flask import Flask, request, render_template_string
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from datetime import datetime
import io
import os
import json

app = Flask(__name__)

# ======================
# 🔴 PUT YOUR IDS HERE
# ======================

SHEET_ID = "1CrixSB1yhAjfNxwqlZNqXM_UPOcPYoxOA2MnwrhCch0"
FOLDER_ID = "1TYdHK14lSunEArFG7dzXhoFiIMIZt3g6"

# ======================

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Load Service Account from Render Environment Variable
service_account_info = json.loads(os.environ["SERVICE_ACCOUNT_JSON"])

creds = Credentials.from_service_account_info(
    service_account_info,
    scopes=SCOPES
)

gc = gspread.authorize(creds)
sheet = gc.open_by_key(SHEET_ID).sheet1
drive_service = build("drive", "v3", credentials=creds)

HTML_FORM = """
<!DOCTYPE html>
<html>
<head>
<title>SL Reimbursement Form</title>
<style>
body { font-family: Arial; padding: 20px; max-width: 700px; margin:auto; }
input, textarea, select { width:100%; padding:8px; margin:6px 0; }
button { background: purple; color:white; padding:12px; border:none; width:100%; font-size:16px; }
.row { display:flex; gap:20px; }
.col { flex:1; }
h2 { text-align:center; }
</style>
</head>
<body>

<h2>SL Reimbursement Form</h2>

<form id="form" enctype="multipart/form-data">

<label>1. Paid By*</label>
<select name="paid_by" required>
<option value="Team">Team</option>
<option value="Praneeth">Praneeth</option>
</select>

<label>2. Payment Date*</label>
<input type="date" name="payment_date" required>

<label>3. Paid To*</label>
<input name="paid_to" required>

<label>4. Client Company*</label>
<input name="company" required>

<label>5. Project*</label>
<input name="project" required>

<div class="row">
<div class="col">
<label>6. Amount (INR)*</label>
<input type="number" name="amount" required>
</div>

<div class="col">
<label>GST</label>
<select name="gst">
<option value="Yes">Yes</option>
<option value="No">No</option>
</select>
</div>
</div>

<label>7. Shipping Charges</label>
<input type="number" name="shipping">

<label>8. Item Description</label>
<textarea name="details"></textarea>

<label>9. Comments</label>
<textarea name="comments"></textarea>

<label>10. Screenshot</label>
<input type="file" name="file">

<br><br>
<button type="submit">Submit</button>

</form>

<script>

// Move to next field on Enter
document.querySelectorAll("input, textarea, select").forEach(function(field) {
    field.addEventListener("keydown", function(e) {
        if (e.key === "Enter") {
            e.preventDefault();
            let form = e.target.form;
            let index = Array.prototype.indexOf.call(form, e.target);
            if (form.elements[index + 1]) {
                form.elements[index + 1].focus();
            }
        }
    });
});

// AJAX Submit
document.getElementById("form").addEventListener("submit", function(e){
    e.preventDefault();
    let data = new FormData(this);

    fetch("/", {
        method:"POST",
        body:data
    })
    .then(res=>res.text())
    .then(msg=>{
        if(msg === "Success"){
            alert("Submitted Successfully!");

            document.querySelector("input[name='amount']").value="";
            document.querySelector("input[name='shipping']").value="";
            document.querySelector("textarea[name='details']").value="";
            document.querySelector("textarea[name='comments']").value="";
            document.querySelector("input[name='file']").value="";
        } else {
            alert("Error: " + msg);
        }
    });
});

</script>

</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def form():
    if request.method == "POST":
        try:
            file_url = "No File"

            if "file" in request.files:
                file = request.files["file"]
                if file.filename != "":
                    media = MediaIoBaseUpload(
                        io.BytesIO(file.read()),
                        mimetype=file.content_type
                    )

                    uploaded = drive_service.files().create(
                        body={
                            "name": f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}",
                            "parents": [FOLDER_ID]
                        },
                        media_body=media,
                        fields="id"
                    ).execute()

                    file_id = uploaded["id"]
                    file_url = f"https://drive.google.com/file/d/{file_id}"

            sheet.append_row([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                request.form.get("paid_by"),
                request.form.get("payment_date"),
                request.form.get("paid_to"),
                request.form.get("company"),
                request.form.get("project"),
                request.form.get("amount"),
                request.form.get("gst"),
                request.form.get("shipping"),
                request.form.get("details"),
                request.form.get("comments"),
                file_url
            ])

            return "Success"

        except Exception as e:
            return str(e)

    return render_template_string(HTML_FORM)

if __name__ == "__main__":
    app.run()