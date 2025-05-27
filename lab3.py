import tkinter as tk
from tkinter import messagebox

# Класс рецепта
class Recipe:
    def __init__(self, name, ingredients, instructions, preparation_time):
        self.name = name
        self.ingredients = ingredients  # список строк
        self.instructions = instructions
        self.preparation_time = preparation_time

    def __str__(self):
        return self.name

    def create_memento(self):
        return RecipeMemento(self.name, self.ingredients, self.instructions, self.preparation_time)

    def restore_from_memento(self, memento):
        self.name = memento.name
        self.ingredients = memento.ingredients
        self.instructions = memento.instructions
        self.preparation_time = memento.preparation_time

# Класс снимка (Memento)
class RecipeMemento:
    def __init__(self, name, ingredients, instructions, preparation_time):
        self.name = name
        self.ingredients = ingredients
        self.instructions = instructions
        self.preparation_time = preparation_time

# Класс Null Object
class NullRecipe(Recipe):
    def __init__(self):
        super().__init__("Рецепт не найден", [], "", 0)

# Класс менеджера рецептов (Observer, Iterator, Strategy)
class RecipeManager:
    def __init__(self):
        self.recipes = []
        self.observers = []
        self.sort_strategy = SortByName()

    def add_recipe(self, recipe):
        self.recipes.append(recipe)
        self.sort_recipes()
        self.notify_observers()

    def remove_recipe(self, recipe):
        if recipe in self.recipes:
            self.recipes.remove(recipe)
            self.notify_observers()

    def update_recipe(self, old_recipe, new_recipe):
        if old_recipe in self.recipes:
            index = self.recipes.index(old_recipe)
            self.recipes[index] = new_recipe
            self.sort_recipes()
            self.notify_observers()

    def set_sort_strategy(self, strategy):
        self.sort_strategy = strategy
        self.sort_recipes()
        self.notify_observers()

    def sort_recipes(self):
        self.recipes = self.sort_strategy.sort(self.recipes.copy())

    def search_recipes(self, query):
        expression = KeywordExpression(query)
        return [r for r in self.recipes if expression.interpret(r)]

    def add_observer(self, observer):
        self.observers.append(observer)

    def remove_observer(self, observer):
        self.observers.remove(observer)

    def notify_observers(self):
        for observer in self.observers:
            observer.update()

    def __iter__(self):
        return RecipeIterator(self)

# Класс итератора
class RecipeIterator:
    def __init__(self, manager):
        self.manager = manager
        self.index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.index < len(self.manager.recipes):
            recipe = self.manager.recipes[self.index]
            self.index += 1
            return recipe
        else:
            raise StopIteration

# Классы стратегии сортировки
class SortStrategy:
    def sort(self, recipes):
        raise NotImplementedError("Subclasses must implement sort method")

class SortByName(SortStrategy):
    def sort(self, recipes):
        return sorted(recipes, key=lambda r: r.name.lower())  # Case-insensitive sorting

class SortByPreparationTime(SortStrategy):
    def sort(self, recipes):
        return sorted(recipes, key=lambda r: (r.preparation_time, r.name.lower()))  # Sort by time, then by name

# Классы команд
class Command:
    def execute(self):
        pass
    def undo(self):
        pass

class AddRecipeCommand(Command):
    def __init__(self, manager, recipe):
        self.manager = manager
        self.recipe = recipe

    def execute(self):
        self.manager.add_recipe(self.recipe)

    def undo(self):
        self.manager.remove_recipe(self.recipe)

class DeleteRecipeCommand(Command):
    def __init__(self, manager, recipe):
        self.manager = manager
        self.recipe = recipe

    def execute(self):
        self.manager.remove_recipe(self.recipe)

    def undo(self):
        self.manager.add_recipe(self.recipe)

class EditRecipeCommand(Command):
    def __init__(self, manager, old_recipe, new_recipe):
        self.manager = manager
        self.old_recipe = old_recipe
        self.new_recipe = new_recipe

    def execute(self):
        self.manager.update_recipe(self.old_recipe, self.new_recipe)

    def undo(self):
        self.manager.update_recipe(self.new_recipe, self.old_recipe)

# Классы валидаторов (Chain of Responsibility)
class Validator:
    def __init__(self, next_validator=None):
        self.next = next_validator

    def validate(self, recipe):
        if self.next:
            self.next.validate(recipe)

class NameValidator(Validator):
    def validate(self, recipe):
        if not recipe.name.strip():
            raise ValueError("Название обязательно")
        super().validate(recipe)

class IngredientsValidator(Validator):
    def validate(self, recipe):
        if not recipe.ingredients:
            raise ValueError("Ингредиенты обязательны")
        super().validate(recipe)

# Классы посетителей
class RecipeVisitor:
    def visit(self, recipe):
        pass

class TextExporter(RecipeVisitor):
    def visit(self, recipe):
        if isinstance(recipe, NullRecipe):
            return "Нет рецепта для экспорта"
            
        return f"""=== {recipe.name} ===

ИНГРЕДИЕНТЫ:
{chr(10).join('- ' + ing for ing in recipe.ingredients)}

ИНСТРУКЦИЯ ПО ПРИГОТОВЛЕНИЮ:
{recipe.instructions}

Время приготовления: {recipe.preparation_time} минут
"""

# Классы интерпретатора
class Expression:
    def interpret(self, recipe):
        pass

class KeywordExpression(Expression):
    def __init__(self, keyword):
        self.keyword = keyword.lower()

    def interpret(self, recipe):
        return self.keyword in recipe.name.lower() or any(self.keyword in ing.lower() for ing in recipe.ingredients)

# Классы состояний
class AppState:
    def __init__(self, app):
        self.app = app

    def handle_add(self):
        pass

    def handle_edit(self):
        pass

    def handle_delete(self):
        pass

class BrowsingState(AppState):
    def handle_add(self):
        add_dialog = AddRecipeDialog(self.app)
        self.app.wait_window(add_dialog)
        if add_dialog.result:
            command = AddRecipeCommand(self.app.manager, add_dialog.result)
            command.execute()

    def handle_edit(self):
        selected_recipe = self.app.get_selected_recipe()
        if selected_recipe and not isinstance(selected_recipe, NullRecipe):
            edit_dialog = EditRecipeDialog(self.app, selected_recipe)
            self.app.wait_window(edit_dialog)
            if edit_dialog.result:
                command = EditRecipeCommand(self.app.manager, selected_recipe, edit_dialog.result)
                command.execute()

    def handle_delete(self):
        selected_recipe = self.app.get_selected_recipe()
        if selected_recipe and not isinstance(selected_recipe, NullRecipe):
            command = DeleteRecipeCommand(self.app.manager, selected_recipe)
            command.execute()

# Класс посредника
class RecipeAppMediator:
    def __init__(self):
        self.list_view = None
        self.detail_view = None
        self.search_bar = None

    def set_list_view(self, list_view):
        self.list_view = list_view

    def set_detail_view(self, detail_view):
        self.detail_view = detail_view

    def set_search_bar(self, search_bar):
        self.search_bar = search_bar

    def recipe_selected(self, recipe):
        self.detail_view.display_recipe(recipe)

    def search_performed(self, query):
        results = self.app.manager.search_recipes(query)
        self.list_view.update_list(results)

# Диалог добавления рецепта
class AddRecipeDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Добавить рецепт")
        self.result = None

        tk.Label(self, text="Название:").pack()
        self.name_entry = tk.Entry(self)
        self.name_entry.pack()

        tk.Label(self, text="Ингредиенты (по одному на строку):").pack()
        self.ingredients_text = tk.Text(self, height=5)
        self.ingredients_text.pack()

        tk.Label(self, text="Инструкции:").pack()
        self.instructions_text = tk.Text(self, height=10)
        self.instructions_text.pack()

        tk.Label(self, text="Время приготовления (минуты):").pack()
        self.preparation_time_entry = tk.Entry(self)
        self.preparation_time_entry.pack()

        tk.Button(self, text="Сохранить", command=self.save).pack()

    def save(self):
        name = self.name_entry.get()
        ingredients = self.ingredients_text.get("1.0", tk.END).strip().split("\n")
        instructions = self.instructions_text.get("1.0", tk.END).strip()
        try:
            preparation_time = int(self.preparation_time_entry.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Время приготовления должно быть числом")
            return

        recipe = Recipe(name, ingredients, instructions, preparation_time)
        try:
            validator = NameValidator(IngredientsValidator())
            validator.validate(recipe)
        except ValueError as e:
            messagebox.showerror("Ошибка валидации", str(e))
            return

        self.result = recipe
        self.destroy()

# Диалог редактирования рецепта
class EditRecipeDialog(tk.Toplevel):
    def __init__(self, parent, recipe):
        super().__init__(parent)
        self.parent = parent
        self.recipe = recipe
        self.title("Редактировать рецепт")
        self.result = None

        tk.Label(self, text="Название:").pack()
        self.name_entry = tk.Entry(self)
        self.name_entry.insert(0, recipe.name)
        self.name_entry.pack()

        tk.Label(self, text="Ингредиенты (по одному на строку):").pack()
        self.ingredients_text = tk.Text(self, height=5)
        self.ingredients_text.insert("1.0", "\n".join(recipe.ingredients))
        self.ingredients_text.pack()

        tk.Label(self, text="Инструкции:").pack()
        self.instructions_text = tk.Text(self, height=10)
        self.instructions_text.insert("1.0", recipe.instructions)
        self.instructions_text.pack()

        tk.Label(self, text="Время приготовления (минуты):").pack()
        self.preparation_time_entry = tk.Entry(self)
        self.preparation_time_entry.insert(0, str(recipe.preparation_time))
        self.preparation_time_entry.pack()

        tk.Button(self, text="Сохранить", command=self.save).pack()

    def save(self):
        name = self.name_entry.get()
        ingredients = self.ingredients_text.get("1.0", tk.END).strip().split("\n")
        instructions = self.instructions_text.get("1.0", tk.END).strip()
        try:
            preparation_time = int(self.preparation_time_entry.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Время приготовления должно быть числом")
            return

        recipe = Recipe(name, ingredients, instructions, preparation_time)
        try:
            validator = NameValidator(IngredientsValidator())
            validator.validate(recipe)
        except ValueError as e:
            messagebox.showerror("Ошибка валидации", str(e))
            return

        self.result = recipe
        self.destroy()

# Главное окно приложения
class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Книга рецептов")
        self.manager = RecipeManager()
        self.manager.add_observer(self)
        self.state = BrowsingState(self)
        self.mediator = RecipeAppMediator()
        self.mediator.app = self

        # Создание интерфейса
        self.listbox = tk.Listbox(self)
        self.listbox.pack(side=tk.LEFT, fill=tk.Y)
        self.listbox.bind('<<ListboxSelect>>', self.on_select)
        self.mediator.set_list_view(self)

        self.detail_frame = tk.Frame(self)
        self.detail_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Label(self.detail_frame, text="Название:").pack()
        self.name_text = tk.Text(self.detail_frame, height=2)
        self.name_text.pack()

        tk.Label(self.detail_frame, text="Ингредиенты:").pack()
        self.ingredients_text = tk.Text(self.detail_frame, height=5)
        self.ingredients_text.pack()

        tk.Label(self.detail_frame, text="Инструкции:").pack()
        self.instructions_text = tk.Text(self.detail_frame, height=10)
        self.instructions_text.pack()

        tk.Label(self.detail_frame, text="Время приготовления (минуты):").pack()
        self.preparation_time_entry = tk.Entry(self.detail_frame)
        self.preparation_time_entry.pack()

        self.mediator.set_detail_view(self)

        self.search_entry = tk.Entry(self)
        self.search_entry.pack(side=tk.TOP, fill=tk.X)
        self.search_entry.bind("<Return>", self.perform_search)
        self.mediator.set_search_bar(self)

        # Меню
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)

        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Добавить рецепт", command=self.handle_add)
        file_menu.add_command(label="Редактировать рецепт", command=self.handle_edit)
        file_menu.add_command(label="Удалить рецепт", command=self.handle_delete)
        file_menu.add_command(label="Экспортировать рецепт", command=self.export_recipe)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.quit)

        sort_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Сортировка", menu=sort_menu)
        sort_menu.add_command(label="По названию", command=lambda: self.manager.set_sort_strategy(SortByName()))
        sort_menu.add_command(label="По времени приготовления", command=lambda: self.manager.set_sort_strategy(SortByPreparationTime()))

        # Начальная загрузка
        self.update_list()

        # Добавление тестовых данных
        self.manager.add_recipe(Recipe("Паста Карбонара", ["Спагетти", "Яйца", "Бекон"], "Сварить пасту, смешать с соусом.", 20))
        self.manager.add_recipe(Recipe("Салат Цезарь", ["Салат", "Курица", "Сухарики"], "Смешать ингредиенты с соусом.", 15))

    def update(self):
        self.update_list()

    def update_list(self):
        self.listbox.delete(0, tk.END)
        for recipe in self.manager:
            self.listbox.insert(tk.END, str(recipe))

    def get_selected_recipe(self):
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            return self.manager.recipes[index]
        return NullRecipe()

    def display_recipe(self, recipe):
        self.name_text.delete("1.0", tk.END)
        self.name_text.insert(tk.END, recipe.name)
        self.ingredients_text.delete("1.0", tk.END)
        self.ingredients_text.insert(tk.END, "\n".join(recipe.ingredients))
        self.instructions_text.delete("1.0", tk.END)
        self.instructions_text.insert(tk.END, recipe.instructions)
        self.preparation_time_entry.delete(0, tk.END)
        self.preparation_time_entry.insert(0, str(recipe.preparation_time))

    def on_select(self, event):
        recipe = self.get_selected_recipe()
        self.mediator.recipe_selected(recipe)

    def perform_search(self, event):
        query = self.search_entry.get()
        self.mediator.search_performed(query)

    def handle_add(self):
        self.state.handle_add()

    def handle_edit(self):
        self.state.handle_edit()

    def handle_delete(self):
        self.state.handle_delete()

    def export_recipe(self):
        selected_recipe = self.get_selected_recipe()
        if isinstance(selected_recipe, NullRecipe):
            messagebox.showwarning("Экспорт", "Пожалуйста, выберите рецепт для экспорта")
            return
            
        exporter = TextExporter()
        text = exporter.visit(selected_recipe)
        
        try:
            from tkinter import filedialog
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Сохранить рецепт как",
                initialfile=f"{selected_recipe.name}.txt"
            )
            
            if file_path:  # Если пользователь не отменил сохранение
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(text)
                messagebox.showinfo("Экспорт", f"Рецепт успешно экспортирован в {file_path}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось экспортировать рецепт: {str(e)}")

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
