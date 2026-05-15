from .models import FoodCategory
def customer_categories(request):
    return {
        'navbar_categories': FoodCategory.objects.all()
    }