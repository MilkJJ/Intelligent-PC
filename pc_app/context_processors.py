from .forms import FeedbackForm
from oauth2client.service_account import ServiceAccountCredentials
import gspread

def feedback_form_context(request):
    # Feedback form
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            # Add code to send data to Google Sheets/Google Form here
            feedback_instance = form.save(commit=False)
            feedback_instance.user = request.user
            #feedback_instance.save()

            # Send data to Google Sheets
            scope = ["https://spreadsheets.google.com/feeds",
                     "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                'your-credentials.json', scope)
            client = gspread.authorize(creds)
            sheet = client.open('Feedback').sheet1
            sheet.append_row(
                [feedback_instance.rating, feedback_instance.comments])
            # return redirect('thank_you') feedback_instance.user, 
    else:
        form = FeedbackForm()
    return {'feedback_form': form}
