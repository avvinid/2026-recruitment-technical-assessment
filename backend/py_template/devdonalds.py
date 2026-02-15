from dataclasses import dataclass
from typing import List, Dict, Union
from flask import Flask, request, jsonify
import re

# ==== Type Definitions, feel free to add or modify ===========================
@dataclass
class CookbookEntry:
	name: str

@dataclass
class RequiredItem():
	name: str
	quantity: int

@dataclass
class Recipe(CookbookEntry):
	required_items: List[RequiredItem]

@dataclass
class Ingredient(CookbookEntry):
	cook_time: int


# =============================================================================
# ==== HTTP Endpoint Stubs ====================================================
# =============================================================================
app = Flask(__name__)

# Store your recipes here!
cookbook = {}

# Task 1 helper (don't touch)
@app.route("/parse", methods=['POST'])
def parse():
	data = request.get_json()
	recipe_name = data.get('input', '')
	parsed_name = parse_handwriting(recipe_name)
	if parsed_name is None:
		return 'Invalid recipe name', 400
	return jsonify({'msg': parsed_name}), 200

# [TASK 1] ====================================================================
# Takes in a recipeName and returns it in a form that 
def parse_handwriting(recipeName: str) -> Union[str | None]:
	parsedRecipeName = ""
	shouldCapitalise = True
	for char in recipeName:
		if char == "-" or char == "_" or char.isspace():
			parsedRecipeName += " "
			shouldCapitalise = True
		elif char.isalpha():
			if shouldCapitalise:
				parsedRecipeName += char.upper()
				shouldCapitalise = False
			else:
				parsedRecipeName += char.lower()

	if len(parsedRecipeName) <= 0:
		return None
	
	return re.sub(r'\s+', ' ', parsedRecipeName).strip()


# [TASK 2] ====================================================================
# Endpoint that adds a CookbookEntry to your magical cookbook
@app.route('/entry', methods=['POST'])
def create_entry():
	entry = request.get_json()

	entry_type = entry.get("type")
	name = entry.get("name")

	if entry_type not in ("recipe", "ingredient"):
		return '', 400
	
	if entry_type == "ingredient" and ("cookTime" not in entry or entry.get("cookTime") < 0):
		return '', 400
	
	if name in cookbook:
		return '', 400
	
	if entry_type == "recipe":
		if "requiredItems" not in entry:
			return '', 400

		names = set()
		for item in entry["requiredItems"]:
			if item.get("name") in names:
				return '', 400
			names.add(item.get("name"))

	cookbook[name] = entry
	return jsonify({}), 200


# [TASK 3] ====================================================================
# Endpoint that returns a summary of a recipe that corresponds to a query name
@app.route('/summary', methods=['GET'])
def summary():
	recipeName = request.args.get("name")
	entry = cookbook.get(recipeName)

	if entry is None or entry["type"] != "recipe":
		return '', 400
	
	ingredientTotals = {}
	ingredients = []
	cookTime = 0
	try:
		for item in entry["requiredItems"]:
			buildRecursive(item, ingredientTotals)
	except ValueError:
		return '', 400
	
	for name, quantity in ingredientTotals.items():
		ingredient = cookbook.get(name)
		if ingredient is None:
			return '', 400

		cookTime += quantity * ingredient["cookTime"]
		ingredients.append({"name": name, "quantity": quantity})
	
	result = {
		"name": recipeName,
		"cookTime": cookTime,
		"ingredients": ingredients
	}

	return jsonify(result), 200

def buildRecursive(item, ingredientTotals, multiplier=1):
	name = item["name"]
	entry = cookbook.get(name)
	if entry is None:
		raise ValueError("Missing item")
	
	quantity = item["quantity"] * multiplier
	
	if entry["type"] == "ingredient":
		ingredientTotals[name] = ingredientTotals.get(name, 0) + quantity
	else:
		for child in entry["requiredItems"]:
			buildRecursive(child, ingredientTotals, quantity)


# =============================================================================
# ==== DO NOT TOUCH ===========================================================
# =============================================================================

if __name__ == '__main__':
	app.run(debug=True, port=8080)
