from django.shortcuts import render, redirect
from tasties_app.models import Recipe, Rating, Ingredient
from django.db.models import Avg
from collections import OrderedDict
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.decorators import login_required
from .forms import CreateUserForm, CreateRecipeForm
from django.forms import inlineformset_factory
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.shortcuts import redirect, render
from tasties_app.models import Category, Recipe

from .forms import CreateUserForm
from django.core.exceptions import ObjectDoesNotExist


def base(request):
    return render(
        request,
        "tasties_app/base.html",
    )


@login_required(login_url="login")
def recipes(request):
    recipes_list = Recipe.objects.annotate(
        recipe_rating=Avg("rating__rating")
    ).order_by("-recipe_rating")
    categories_list = Category.objects.all()
    selected_category = request.GET.get("category")
    if selected_category:
        if selected_category == "remove_filter":
            return redirect("recipes")
        try:
            category = Category.objects.get(category_name=selected_category)
        except ObjectDoesNotExist:
            return redirect("recipes")
        recipes_list = (
            Category.get_recipes_by_category(category)
            .annotate(recipe_rating=Avg("rating__rating"))
            .order_by("-recipe_rating")
        )
    context = {
        "recipes_list": recipes_list,
        "categories_list": categories_list,
    }
    return render(request, "tasties_app/recipes.html", context)


def login_user(request):
    if request.user.is_authenticated:
        return redirect("/")
    else:
        if request.method == "POST":
            username = request.POST.get("username")
            password = request.POST.get("password")
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("/")
            else:
                messages.info(request, "Username OR password is incorrect")
    return render(
        request,
        "tasties_app/login.html",
    )


def logout_user(request):
    logout(request)
    return redirect("login")


def register(request):
    if request.user.is_authenticated:
        return redirect("index")

    form = CreateUserForm()
    if request.method == "POST":
        form = CreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get("username")
            messages.success(request, "Account was created for " + username)
            return redirect("login")
        else:
            for error_message in form.errors.values():
                messages.error(request, error_message)

    context = {'form': form}
    return render(request, 'tasties_app/register.html', context)


@login_required(login_url='login')
def view_recipe(request, recipe_id=None):
    if not Recipe.objects.filter(pk=recipe_id).exists():
        return redirect('recipes')
    recipe = Recipe.objects.get(pk=recipe_id)
    ingredients = recipe.ingredient_set.all()
    rating = recipe.rating_set.aggregate(Avg('rating'))['rating__avg']
    categories = recipe.categories.all()
    context = {'recipe': recipe, 'ingredients': ingredients, 'rating': rating, 'categories': categories}
    return render(request, 'tasties_app/view_recipe.html', context)


@login_required(login_url='login')
def create_recipe(request):
    recipe = Recipe(author_id=request.user)
    IngredientFormSet = inlineformset_factory(Recipe,
                                              Ingredient,
                                              fields=('description', 'measurement_unit', 'amount'),
                                              min_num=1,
                                              validate_min=True,
                                              extra=4)

    if request.method == 'POST':
        recipe_form = CreateRecipeForm(request.POST, request.FILES, instance=recipe)
        ingredient_formset = IngredientFormSet(request.POST, instance=recipe)
        if recipe_form.is_valid():
            recipe = recipe_form.save(commit=False)
            rating = Rating(author_id=recipe.author_id, recipe_id=recipe, rating=5)
            if ingredient_formset.is_valid():
                recipe = recipe_form.save()
                ingredient_formset.save()
                rating.save()
                return redirect(f'/view_recipe/{recipe.id}/')
            else:
                for ingredient_form_errors in ingredient_formset.errors:
                    for error_message in ingredient_form_errors.values():
                        messages.error(request, error_message)
        else:
            for error_message in recipe_form.errors.values():
                messages.error(request, error_message)
    else:
        recipe_form = CreateRecipeForm(instance=recipe)
        ingredient_formset = IngredientFormSet(instance=recipe)

    context = {'recipe_form': recipe_form, 'ingredient_formset': ingredient_formset}
    return render(request, 'tasties_app/create_recipe.html', context)
