from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import streamlit as st
import pandas as pd

# Identifiant et mot de passe pour l'admin (dans un cas réel, utilisez une méthode plus sécurisée pour stocker ces informations)
ADMIN_USER = "admin"
ADMIN_PASSWORD = "password"

# Chemin de fichier à modifier selon votre environnement
chemin_aliments = "/home/molrot/code/Anaconda/Vigneron/Aliments-Grid view.csv"
chemin_liste_aliments_manquants = "/home/molrot/code/Anaconda/Vigneron/Liste aliment manquant-Grid view.csv"

# Fonction pour charger les données
def load_data():
    menu_df = pd.read_csv("/home/molrot/code/Anaconda/Vigneron/Menu-Grid view.csv")
    menu_aliments_df = pd.read_csv("/home/molrot/code/Anaconda/Vigneron/Menu&Aliments-Grid view.csv")
    commandes_client_df = pd.read_csv("/home/molrot/code/Anaconda/Vigneron/Commandes client-Grid view.csv")
    aliments_df = pd.read_csv(chemin_aliments)
    liste_aliment_manquant_df = pd.read_csv(chemin_liste_aliments_manquants)
    return menu_df, menu_aliments_df, commandes_client_df, aliments_df, liste_aliment_manquant_df


def calculate_required_ingredients(selected_menu, num_people, menu_aliments_df):
    # Filter the menu_aliments_df to get the ingredients for the selected menu
    ingredients_needed = menu_aliments_df[menu_aliments_df['Menu'] == selected_menu]
    # Calculate the total quantity for each ingredient
    ingredients_needed['TotalQuantity'] = ingredients_needed['Quantité/pers'] * num_people
    return ingredients_needed

# Fonction pour mettre à jour le stock et la liste des ingrédients manquants
def update_stock_and_list(ingredients_df, required_ingredients):
    # Charger la liste existante des aliments manquants
    try:
        liste_aliment_manquant_df = pd.read_csv(chemin_liste_aliments_manquants)
    except pd.errors.EmptyDataError:  # Si le fichier est vide
        liste_aliment_manquant_df = pd.DataFrame(columns=['Produit', 'MissingQuantity'])

    # Ajout systématique des aliments manquants à la liste
    for index, row in required_ingredients.iterrows():
        ingredient_id = row['Produit']
        required_quantity = row['TotalQuantity']
        
        # Obtenir le stock actuel pour l'ingrédient
        current_stock_series = ingredients_df.loc[ingredients_df['Produit'] == ingredient_id, 'Quantité dispo']
        
        if not current_stock_series.empty:
            current_stock = current_stock_series.iloc[0]
            if current_stock < required_quantity:
                missing_quantity = required_quantity - current_stock
                
                # Ajouter la quantité manquante pour l'ingrédient
                new_row = pd.DataFrame({'Produit': [ingredient_id], 'MissingQuantity': [missing_quantity]})
                liste_aliment_manquant_df = pd.concat([liste_aliment_manquant_df, new_row], ignore_index=True)
                
                # Mettre à jour le stock à 0
                ingredients_df.loc[ingredients_df['Produit'] == ingredient_id, 'Quantité dispo'] = 0
            else:
                # Déduire la quantité requise du stock
                ingredients_df.loc[ingredients_df['Produit'] == ingredient_id, 'Quantité dispo'] -= required_quantity

    # Groupement et somme des quantités pour chaque produit manquant
    liste_aliment_manquant_grouped = liste_aliment_manquant_df.groupby('Produit', as_index=False)['MissingQuantity'].sum()

    return ingredients_df, liste_aliment_manquant_grouped

# Fonction de vérification des identifiants
def verify_login(user, password):
    return user == ADMIN_USER and password == ADMIN_PASSWORD

# Fonction pour afficher et éditer le DataFrame des stocks
def display_editable_stock_table(df):
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_grid_options(enableRangeSelection=True)
    gb.configure_column("Produit", editable=False)  # Mettre 'Produit' en non éditable si nécessaire
    gb.configure_column("Quantité dispo", editable=True)
    gridOptions = gb.build()

    grid_response = AgGrid(
        df,
        gridOptions=gridOptions,
        update_mode=GridUpdateMode.MODEL_CHANGED,  # Pour mettre à jour à chaque modification
        fit_columns_on_grid_load=True,
    )

    updated_df = grid_response['data']
    return updated_df

# Layout de l'app Streamlit
st.title('Gestion de Stock et Commandes')

# Demande de connexion
st.sidebar.subheader("Connexion Administrateur")
username = st.sidebar.text_input("Nom d'utilisateur")
password = st.sidebar.text_input("Mot de passe", type="password")
login_button = st.sidebar.button("Se connecter")

# Chargement des données
menu_df, menu_aliments_df, commandes_client_df, aliments_df, liste_aliment_manquant_df = load_data()

if login_button and verify_login(username, password):
    st.sidebar.success("Connecté en tant qu'administrateur.")
    # Placez ici les éléments d'interface utilisateur réservés à l'administrateur
    # Exemple : modification des stocks, réinitialisation des listes, etc.
else:
    st.sidebar.error("Non connecté.")

# Interface utilisateur publique (pour tous les utilisateurs)
st.subheader('Nouvelle Commande')
# Les éléments UI pour passer une commande restent ici...

selected_menu = st.selectbox('Choisir un menu', menu_df['ID'])
number_of_people = st.number_input('Nombre de personnes', min_value=1)
submit_order = st.button('Calculer les Ingrédients Requis et Mettre à Jour le Stock')
submit_date = st.date_input('Quand souhaiteriez vous réservez?')
if submit_order:
    # Calcul des ingrédients requis
    required_ingredients = calculate_required_ingredients(selected_menu, number_of_people, menu_aliments_df)
    
    # Mise à jour du stock et de la liste des ingrédients manquants
    aliments_df, new_missing_ingredients_df = update_stock_and_list(aliments_df, required_ingredients)
    
    # Ajout des nouveaux ingrédients manquants à la liste existante
    liste_aliment_manquant_df = pd.concat([liste_aliment_manquant_df, new_missing_ingredients_df], ignore_index=True)
    
    # Affichage des résultats
    st.success(f'La Commande à bien été enregistré en date du {submit_date} pour {number_of_people} personnes')
    st.write('Ingrédients Requis:', required_ingredients[['Produit', 'TotalQuantity']])
    st.write('Stock mis à jour:', aliments_df[['Produit', 'Quantité dispo']])
    st.write('Liste d\'aliments manquants mise à jour:', liste_aliment_manquant_df)
    

    # Sauvegarde du stock mis à jour et de la liste des ingrédients manquants
    aliments_df.to_csv(chemin_aliments, index=False)
    liste_aliment_manquant_df.to_csv(chemin_liste_aliments_manquants, index=False)


# Assurez-vous que les sections réservées à l'admin ne soient accessibles que si l'utilisateur est connecté en tant qu'admin
# Assurez-vous que cette section est accessible uniquement par l'administrateur
if verify_login(username, password):
    
    st.subheader("Modifier les Stocks")
    updated_aliments_df = display_editable_stock_table(aliments_df)
    
    # Bouton pour sauvegarder les modifications
    if st.button("Sauvegarder les Modifications"):
        updated_aliments_df.to_csv(chemin_aliments, index=False)
        st.success("Les modifications ont été sauvegardées.")
    
        # Sauvegarder les modifications dans le fichier CSV
        aliments_df.to_csv(chemin_aliments, index=False)
        st.success("Les stocks ont été mis à jour avec succès.")

        # Optionnel : recharger le DataFrame modifié pour affichage
        aliments_df = pd.read_csv(chemin_aliments)
        st.write("Nouveaux stocks après modification:")
        st.dataframe(aliments_df)

    # Sections réservées à l'administrateur
    # Ajout de fonctionnalités de gestion des stocks, réinitialisation des listes, etc.
    # Ajout de la fonctionnalité de modification des stocks

    
    # Bouton pour réinitialiser la liste des aliments à acheter
    st.subheader('Réinitialiser la Liste des Aliments à Acheter')
    if st.button('Réinitialiser la Liste'):
        liste_aliment_manquant_df = pd.DataFrame(columns=['Produit', 'MissingQuantity'])  # Réinitialisation
        st.write('La liste des aliments à acheter a été réinitialisée.')
        # Sauvegarde de la liste réinitialisée
        liste_aliment_manquant_df.to_csv(chemin_liste_aliments_manquants, index=False)




# Faire 2 partie, une pour le client et une pour le vigneoble
# Ajouter la date pour le client
# Pour la modification des stocks mettre un tableau
# 