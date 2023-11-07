from .models import *
from .forms import FeedbackForm
from oauth2client.service_account import ServiceAccountCredentials
import gspread

def cart_items_count(request):
    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(user=request.user, is_purchased=False)
        favorited_builds = FavouritedPC.objects.filter(user=request.user)
        pending_order = CartItem.objects.filter(
        user=request.user, is_purchased=True, is_completed=False)

        return {'cart_items_count': cart_items.count(),
                'favorited_builds_count': favorited_builds.count(),
                'pending_order_count': pending_order.count(),
                }
    return {}

def feedback_form_context(request):
    # Feedback form
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            # Add code to send data to Google Sheets/Google Form here
            feedback_instance = form.save(commit=False)
            feedback_instance.user = request.user

            # Get only the user's name or ID to send to sheets
            #feedback_instance.save()

            # Send data to Google Sheets
            scope = ["https://spreadsheets.google.com/feeds",
                     "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                'your-credentials.json', scope)
            client = gspread.authorize(creds)
            sheet = client.open('Feedback').sheet1
            sheet.append_row(
                [feedback_instance.rating, feedback_instance.feedbacks, feedback_instance.user.username])
            # return redirect('thank_you') feedback_instance.user, 
    else:
        form = FeedbackForm()
    return {'feedback_form': form}
