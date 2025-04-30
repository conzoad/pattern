import tkinter as tk
from tkinter import ttk
from abc import ABC, abstractmethod
import json
import uuid

# Flyweight Pattern: Ingredient and IngredientFactory
class Ingredient:
    def __init__(self, name):
        self.name = name

    def get_description(self):
        return self.name

    def get_ingredients(self):
        return [self]

class IngredientFactory:
    def __init__(self):
        self.ingredients = {}

    def get_ingredient(self, name):
        if name not in self.ingredients:
            self.ingredients[name] = Ingredient(name)
        return self.ingredients[name]

# Composite Pattern: RecipeComponent, Ingredient, Recipe
class RecipeComponent(ABC):
    @abstractmethod
    def get_description(self):
        pass

    @abstractmethod
    def get_ingredients(self):
        pass

class Ingredient(RecipeComponent):
    def __init__(self, name):
        self.name = name

    def get_description(self):
        return self.name

    def get_ingredients(self):
        return [self]

class Recipe(RecipeComponent):
    def __init__(self, name, category=None, owner=None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.category = category
        self.owner = owner
        self.components = []

    def add_component(self, component):
        self.components.append(component)

    def get_description(self):
        description = f"{self.name} ({self.category})\n"
        for component in self.components:
            description += "- " + component.get_description() + "\n"
        return description

    def get_ingredients(self):
        ingredients = []
        for component in self.components:
            ingredients.extend(component.get_ingredients())
        return ingredients

# Adapter Pattern: RecipeSource and JSONRecipeSource
class RecipeSource(ABC):
    @abstractmethod
    def get_recipes(self):
        pass

class JSONRecipeSource(RecipeSource):
    def __init__(self, filename, ingredient_factory):
        self.filename = filename
        self.ingredient_factory = ingredient_factory

    def get_recipes(self):
        try:
            with open(self.filename, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            return []
        recipes = []
        for item in data:
            recipe = Recipe(item['name'], item.get('category', 'General'))
            for ing_name in item.get('ingredients', []):
                ingredient = self.ingredient_factory.get_ingredient(ing_name)
                recipe.add_component(ingredient)
            recipes.append(recipe)
        return recipes

# Bridge Pattern: RecipeRepository and InMemoryRecipeRepository
class RecipeRepository(ABC):
    @abstractmethod
    def save_recipe(self, recipe):
        pass

    @abstractmethod
    def get_recipe(self, recipe_id):
        pass



    @abstractmethod
    def get_all_recipes(self):
        pass

class InMemoryRecipeRepository(RecipeRepository):
    def __init__(self):
        self.recipes = {}

    def save_recipe(self, recipe):
        self.recipes[recipe.id] = recipe

    def get_recipe(self, recipe_id):
        return self.recipes.get(recipe_id)



    def get_all_recipes(self):
        return list(self.recipes.values())

# Facade Pattern: RecipeManager
class RecipeManager:
    def __init__(self, repository):
        self.repository = repository

    def add_recipe(self, recipe):
        self.repository.save_recipe(recipe)

    def get_recipe(self, recipe_id, user):
        recipe = self.repository.get_recipe(recipe_id)
        if recipe:
            return ProtectedRecipe(recipe, user)
        return None

    def delete_recipe(self, recipe_id):
        self.repository.delete_recipe(recipe_id)

    def search_recipes(self, search_object):
        all_recipes = self.repository.get_all_recipes()
        return search_object.search(all_recipes)

# Decorator Pattern: RecipeSearch and Filters
class RecipeSearch:
    def search(self, recipes):
        return recipes

class FilterDecorator(RecipeSearch):
    def __init__(self, wrapped):
        self.wrapped = wrapped

    def search(self, recipes):
        result = self.wrapped.search(recipes)
        return self.filter(result)

    @abstractmethod
    def filter(self, recipes):
        pass

class CategoryFilter(FilterDecorator):
    def __init__(self, wrapped, category):
        super().__init__(wrapped)
        self.category = category

    def filter(self, recipes):
        return [r for r in recipes if r.category == self.category]

# Proxy Pattern: ProtectedRecipe
class ProtectedRecipe(RecipeComponent):
    def __init__(self, recipe, user):
        self.recipe = recipe
        self.user = user

    def has_access(self):
        return self.recipe.owner is None or self.recipe.owner == self.user or self.user == "admin"

    def get_description(self):
        if self.has_access():
            return self.recipe.get_description()
        return "Доступ запрещен"

    def get_ingredients(self):
        if self.has_access():
            return self.recipe.get_ingredients()
        return []

# Tkinter GUI
class RecipeBookApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Книга рецептов")
        self.ingredient_factory = IngredientFactory()
        self.repository = InMemoryRecipeRepository()
        self.recipe_manager = RecipeManager(self.repository)
        self.current_user = "user1" 


        self.load_test_data()


        self.create_widgets()

    def load_test_data(self):
        # Пример JSON-данных
        json_data = [
            {"name": "Шоколадный торт", "category": "Десерт", "ingredients": ["Мука", "Сахар", "Какао"]},
            {"name": "Салат Цезарь", "category": "Салат", "ingredients": ["Салат", "Курица", "Сухарики"]}
        ]
        with open('recipes.json', 'w') as f:
            json.dump(json_data, f)
        json_source = JSONRecipeSource('recipes.json', self.ingredient_factory)
        recipes = json_source.get_recipes()
        for recipe in recipes:
            recipe.owner = "admin" if recipe.name == "Шоколадный торт" else None
            self.recipe_manager.add_recipe(recipe)

    def create_widgets(self):
        # Список рецептов
        self.recipe_list = tk.Listbox(self.root, width=30)
        self.recipe_list.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)
        self.recipe_list.bind('<<ListboxSelect>>', self.show_recipe)

        # Панель деталей
        self.details_text = tk.Text(self.root, height=20, width=50)
        self.details_text.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5, pady=5)

        # Панель поиска
        self.search_frame = tk.Frame(self.root)
        self.search_frame.pack(side=tk.TOP, fill=tk.X)
        tk.Label(self.search_frame, text="Категория:").pack(side=tk.LEFT)
        self.category_entry = tk.Entry(self.search_frame)
        self.category_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(self.search_frame, text="Поиск", command=self.search).pack(side=tk.LEFT)

        # Кнопки управления
        tk.Button(self.root, text="Добавить рецепт", command=self.add_recipe).pack(side=tk.BOTTOM, pady=5)

        self.update_listbox()

    def update_listbox(self):
        self.recipe_list.delete(0, tk.END)
        search = RecipeSearch()
        category = self.category_entry.get()
        if category:
            search = CategoryFilter(search, category)
        recipes = self.recipe_manager.search_recipes(search)
        for recipe in recipes:
            self.recipe_list.insert(tk.END, recipe.name)

    def show_recipe(self, event):
        selection = self.recipe_list.curselection()
        if selection:
            index = selection[0]
            recipe_name = self.recipe_list.get(index)
            recipes = self.recipe_manager.search_recipes(RecipeSearch())
            recipe = next((r for r in recipes if r.name == recipe_name), None)
            if recipe:
                protected_recipe = ProtectedRecipe(recipe, self.current_user)
                self.details_text.delete(1.0, tk.END)
                self.details_text.insert(tk.END, protected_recipe.get_description())

    def search(self):
        self.update_listbox()

    def add_recipe(self):
        # Окно для добавления рецепта
        add_window = tk.Toplevel(self.root)
        add_window.title("Добавить рецепт")
        tk.Label(add_window, text="Название:").pack()
        name_entry = tk.Entry(add_window)
        name_entry.pack()
        tk.Label(add_window, text="Категория:").pack()
        category_entry = tk.Entry(add_window)
        category_entry.pack()
        tk.Label(add_window, text="Ингредиенты (через запятую):").pack()
        ingredients_entry = tk.Entry(add_window)
        ingredients_entry.pack()
        def save():
            name = name_entry.get()
            category = category_entry.get()
            ingredients = [i.strip() for i in ingredients_entry.get().split(',') if i.strip()]
            recipe = Recipe(name, category, self.current_user)
            for ing in ingredients:
                ingredient = self.ingredient_factory.get_ingredient(ing)
                recipe.add_component(ingredient)
            self.recipe_manager.add_recipe(recipe)
            self.update_listbox()
            add_window.destroy()
        tk.Button(add_window, text="Сохранить", command=save).pack()

def main():
    root = tk.Tk()
    app = RecipeBookApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()