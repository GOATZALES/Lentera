from django.shortcuts import render

# Create your views here.
def show_test(request):
    """
    Render the main page of the application.
    """
    return render(request, 'test.html')