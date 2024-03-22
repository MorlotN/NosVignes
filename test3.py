import streamlit as st
import pandas as pd

# Placeholder function to load data
def load_data():
    menu_df = pd.read_csv("/home/molrot/code/Anaconda/Vigneron/Menu-Grid view.csv")  # Replace with pd.read_csv() in the actual implementation
    menu_aliments_df = pd.read_csv("/home/molrot/code/Anaconda/Vigneron/Menu&Aliments-Grid view.csv")  # Replace with pd.read_csv()
    commandes_client_df = pd.read_csv("/home/molrot/code/Anaconda/Vigneron/Commandes client-Grid view.csv")  # Replace with pd.read_csv()
    aliments_df = pd.read_csv("/home/molrot/code/Anaconda/Vigneron/Aliments-Grid view.csv")  # Replace with pd.read_csv()
    liste_aliment_manquant_df = pd.read_csv("/home/molrot/code/Anaconda/Vigneron/Liste aliment manquant-Grid view.csv")  # Replace with pd.read_csv()
    return menu_df, menu_aliments_df, commandes_client_df, aliments_df, liste_aliment_manquant_df
# Function to calculate required ingredients for a menu
def calculate_required_ingredients(selected_menu, num_people, menu_aliments_df):
    # Filter the menu_aliments_df to get the ingredients for the selected menu
    ingredients_needed = menu_aliments_df[menu_aliments_df['Menu'] == selected_menu]
    # Calculate the total quantity for each ingredient
    ingredients_needed['TotalQuantity'] = ingredients_needed['Quantité/pers'] * num_people
    return ingredients_needed


# Fonction modifiée pour la mise à jour du stock et la liste des ingrédients manquants
def update_stock_and_list(ingredients_df, required_ingredients):
    # Initialiser un DataFrame pour contenir les ingrédients manquants
    missing_ingredients_df = pd.DataFrame(columns=['Produit', 'MissingQuantity'])

    for index, row in required_ingredients.iterrows():
        ingredient_id = row['Produit']
        required_quantity = row['TotalQuantity']
        
        # Obtenir le stock actuel pour l'ingrédient
        current_stock_series = ingredients_df.loc[ingredients_df['Produit'] == ingredient_id, 'Quantité dispo']
        
        # Vérifier s'il existe des informations de stock pour l'ingrédient
        if not current_stock_series.empty:
            current_stock = current_stock_series.iloc[0]
            if current_stock < required_quantity:
                # Calculer la quantité manquante
                missing_quantity = required_quantity - current_stock
                # Ajouter à DataFrame des ingrédients manquants
                missing_ingredients_df = pd.concat([missing_ingredients_df, pd.DataFrame({'Produit': [ingredient_id], 'MissingQuantity': [missing_quantity]})], ignore_index=True)
                # Définir le stock à 0 puisqu'il n'est pas suffisant
                ingredients_df.loc[ingredients_df['Produit'] == ingredient_id, 'Quantité dispo'] = 0
            else:
                # Déduire la quantité requise du stock
                ingredients_df.loc[ingredients_df['Produit'] == ingredient_id, 'Quantité dispo'] -= required_quantity

    # Grouper les ingrédients manquants par Produit et sommer les quantités manquantes
    if not missing_ingredients_df.empty:
        missing_ingredients_df = missing_ingredients_df.groupby('Produit').sum().reset_index()

    return ingredients_df, missing_ingredients_df



# Streamlit app layout
st.title('Gestion de Stock et Commandes')

# Load data
menu_df, menu_aliments_df, commandes_client_df, aliments_df, liste_aliment_manquant_df = load_data()

# User input for new order
st.subheader('Nouvelle Commande')
selected_menu = st.selectbox('Choisir un menu', menu_df['ID'])
number_of_people = st.number_input('Nombre de personnes', min_value=1)
submit_order = st.button('Calculer les Ingrédients Requis et Mettre à Jour le Stock')

if submit_order:
    # Calculate required ingredients
    required_ingredients = calculate_required_ingredients(selected_menu, number_of_people, menu_aliments_df)
    
    # Update stock and list of missing ingredients
    aliments_df, new_missing_ingredients_df = update_stock_and_list(aliments_df, required_ingredients)
    
    # Append new missing ingredients to the existing list
    liste_aliment_manquant_df = pd.concat([liste_aliment_manquant_df, new_missing_ingredients_df], ignore_index=True)
    
    # Display results
    st.write('Ingrédients Requis:', required_ingredients[['Produit', 'TotalQuantity']])
    st.write('Stock mis à jour:', aliments_df[['Produit', 'Quantité dispo']])
    st.write('Liste d\'aliments manquants mise à jour:', liste_aliment_manquant_df)

    # Save the updated stock and missing ingredients list back to CSV
    aliments_df.to_csv("/home/molrot/code/Anaconda/Vigneron/Aliments-Grid view.csv", index=False)
    liste_aliment_manquant_df.to_csv("/home/molrot/code/Anaconda/Vigneron/Liste aliment manquant-Grid view.csv", index=False)

