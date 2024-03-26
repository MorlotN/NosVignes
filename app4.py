from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import streamlit as st
import pandas as pd
import os

# Chemin vers le fichier historique
chemin_historique = "historique_actions.csv"


ADMIN_USER = "admin"
ADMIN_PASSWORD = "password"

chemin_aliments = "Aliments-Grid view.csv"
chemin_liste_aliments_manquants = "Liste aliment manquant-Grid view.csv"

import datetime
# Vérifier si le fichier existe déjà
if not os.path.isfile(chemin_historique):
    # Créer un DataFrame avec les colonnes nécessaires
    df_historique = pd.DataFrame(columns=[
        "Type d'action", 
        "Date", 
        "Utilisateur", 
        "Menu", 
        "Nombre de personnes", 
        "Produit", 
        "Quantité", 
        "Date de réservation"
    ])
    # Enregistrer le DataFrame comme fichier CSV
    df_historique.to_csv(chemin_historique, index=False)
chemin_historique = "historique_actions.csv"

def enregistrer_action(type_action, utilisateur=None, menu=None, nombre_personnes=None, produit=None, quantite=None, date_reservation=None):
    action = pd.DataFrame({
        "Type d'action": [type_action],
        "Date": [datetime.datetime.now()],
        "Utilisateur": [utilisateur or "N/A"],
        "Menu": [menu or "N/A"],
        "Nombre de personnes": [nombre_personnes or "N/A"],
        "Produit": [produit or "N/A"],
        "Quantité": [quantite or "N/A"],
        "Date de réservation": [date_reservation or "N/A"],
    })
    
    if not os.path.isfile(chemin_historique):
        # Si le fichier n'existe pas, créez-le avec les en-têtes
        action.to_csv(chemin_historique, index=False)
    else:
        # Si le fichier existe déjà, chargez-le, concaténez la nouvelle action, et sauvegardez
        historique_df = pd.read_csv(chemin_historique)
        historique_df = pd.concat([historique_df, action], ignore_index=True)
        historique_df.to_csv(chemin_historique, index=False)


def load_data():
    menu_df = pd.read_csv("Menu-Grid view.csv")
    menu_aliments_df = pd.read_csv("Menu&Aliments-Grid view.csv")
    commandes_client_df = pd.read_csv("Commandes client-Grid view.csv")
    aliments_df = pd.read_csv(chemin_aliments)
    liste_aliment_manquant_df = pd.read_csv(chemin_liste_aliments_manquants)
    return menu_df, menu_aliments_df, commandes_client_df, aliments_df, liste_aliment_manquant_df

def calculate_required_ingredients(selected_menu, num_people, menu_aliments_df):
    ingredients_needed = menu_aliments_df[menu_aliments_df['Menu'] == selected_menu]
    ingredients_needed['TotalQuantity'] = ingredients_needed['Quantité/pers'] * num_people
    return ingredients_needed

def update_stock_and_list(ingredients_df, required_ingredients):
    try:
        liste_aliment_manquant_df = pd.read_csv(chemin_liste_aliments_manquants)
    except pd.errors.EmptyDataError:
        liste_aliment_manquant_df = pd.DataFrame(columns=['Produit', 'MissingQuantity'])

    for index, row in required_ingredients.iterrows():
        produit, quantite_requise = row['Produit'], row['TotalQuantity']
        filtered_df = ingredients_df.loc[ingredients_df['Produit'] == produit, 'Quantité dispo']

        if not filtered_df.empty:
            stock_actuel = filtered_df.iloc[0]
            if stock_actuel < quantite_requise:
                quantite_manquante = quantite_requise - stock_actuel
                new_row = {'Produit': produit, 'MissingQuantity': quantite_manquante}
                liste_aliment_manquant_df = pd.concat([liste_aliment_manquant_df, pd.DataFrame([new_row])], ignore_index=True)

                ingredients_df.loc[ingredients_df['Produit'] == produit, 'Quantité dispo'] = 0
            else:
                ingredients_df.loc[ingredients_df['Produit'] == produit, 'Quantité dispo'] -= quantite_requise
        else:
            # Gérer le cas où le produit n'est pas trouvé dans ingredients_df
            # Par exemple, vous pouvez décider d'ajouter directement l'ingrédient à la liste des manquants
            new_row = {'Produit': produit, 'MissingQuantity': quantite_requise}
            # liste_aliment_manquant_df = liste_aliment_manquant_df.append(new_row, ignore_index=True)
            liste_aliment_manquant_df = pd.concat([liste_aliment_manquant_df, pd.DataFrame([new_row])], ignore_index=True)
            liste_aliment_manquant_df.groupby('Produit').sum()


    ingredients_df.to_csv(chemin_aliments, index=False)
    liste_aliment_manquant_df.to_csv(chemin_liste_aliments_manquants, index=False)

    return ingredients_df, liste_aliment_manquant_df

# Fonction pour lire et retourner le contenu du fichier d'historique
def lire_historique(chemin):
    try:
        # Tenter de lire le fichier d'historique
        df_historique = pd.read_csv(chemin)
        return df_historique
    except FileNotFoundError:
        # Retourner un DataFrame vide si le fichier n'existe pas
        return pd.DataFrame()

def verify_login(user, password):
    return user == ADMIN_USER and password == ADMIN_PASSWORD

def display_editable_stock_table(df, unique_key):
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_grid_options(enableRangeSelection=True)
    gb.configure_column("Produit", editable=False)
    gb.configure_column("Quantité dispo", editable=True)
    gridOptions = gb.build()

    grid_response = AgGrid(
        df,
        gridOptions=gridOptions,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        fit_columns_on_grid_load=True,
        key=unique_key  # Utilisez l'argument key pour éviter les erreurs DuplicateWidgetID
    )
    data = grid_response['data'].groupby('Produit').sum().reset_index(names=['Produit'])
    return data


st.title('Gestion de Stock et Commandes')

# Authentification de l'administrateur
st.sidebar.subheader("Connexion Administrateur")
username = st.sidebar.text_input("Nom d'utilisateur")
password = st.sidebar.text_input("Mot de passe", type="password")
login_button = st.sidebar.button("Se connecter")

# Chargement des données
menu_df, menu_aliments_df, commandes_client_df, aliments_df, liste_aliment_manquant_df = load_data()

# if login_button and verify_login(username, password):
#     st.sidebar.success("Connecté en tant qu'administrateur.")
#     # Affichage du tableau des stocks (éditable par l'admin)
#     st.subheader("Modifier les Stocks")
#     updated_aliments_df = display_editable_stock_table(aliments_df, 'unique_key_for_aliments_df')
#     if st.button("Sauvegarder les Modifications du Stock", key='save_stock_changes'):
#         updated_aliments_df.to_csv(chemin_aliments, index=False)
#         st.success("Les modifications ont été sauvegardées.")
#         aliments_df = pd.read_csv(chemin_aliments)
    
    # # Bouton pour réinitialiser la liste des aliments à acheter
    # st.subheader('Réinitialiser la Liste des Aliments à Acheter')
    # if st.button('Réinitialiser la Liste des Aliments à Acheter', key='reset_list'):
    #     liste_aliment_manquant_df = pd.DataFrame(columns=['Produit', 'MissingQuantity'])
    #     liste_aliment_manquant_df.to_csv(chemin_liste_aliments_manquants, index=False)
    #     st.success('La liste des aliments à acheter a été réinitialisée.')
# else:
#     st.sidebar.error("Non connecté.")

# Si l'utilisateur est authentifié en tant qu'admin, afficher toujours la liste d'aliments à acheter
if verify_login(username, password):
    st.subheader("Liste d'Aliments à Acheter")
    st.dataframe(liste_aliment_manquant_df)

# Interface utilisateur pour nouvelle commande
st.subheader('Nouvelle Commande')
selected_menu = st.selectbox('Choisir un menu', menu_df['ID'])
number_of_people = st.number_input('Nombre de personnes', min_value=1)
submit_date = st.date_input('Quand souhaiteriez vous réservez?')
if st.button('Réserver', key='submit_order'):
    required_ingredients = calculate_required_ingredients(selected_menu, number_of_people, menu_aliments_df)
    aliments_df, new_missing_ingredients_df = update_stock_and_list(aliments_df, required_ingredients)
    enregistrer_action("Nouvelle commande", utilisateur=username, menu=selected_menu, nombre_personnes=number_of_people, date_reservation=submit_date)
    st.success(f'La commande a bien été enregistrée pour le {submit_date} pour {number_of_people} personnes.')
    if verify_login(username, password):
        st.write('Ingrédients Requis:', required_ingredients[['Produit', 'TotalQuantity']])
        st.write('Stock mis à jour:', aliments_df[['Produit', 'Quantité dispo']])
        st.write("Liste d'aliments manquants mise à jour:", new_missing_ingredients_df)
# submit_order = st.button('Calculer les Ingrédients Requis et Mettre à Jour le Stock')

# if submit_order:
#     required_ingredients = calculate_required_ingredients(selected_menu, number_of_people, menu_aliments_df)
#     # required_ingredients.groupby('Produit').sum()
#     aliments_df, new_missing_ingredients_df = update_stock_and_list(aliments_df, required_ingredients)
#     # new_missing_ingredients_df.groupby('Produit').sum()
#     st.success(f'La Commande à bien été enregistré en date du {submit_date} pour {number_of_people} personnes')
#     st.write('Ingrédients Requis:', required_ingredients[['Produit', 'TotalQuantity']])
#     st.write('Stock mis à jour:', aliments_df[['Produit', 'Quantité dispo']])
#     st.write("Liste d'aliments manquants mise à jour:", new_missing_ingredients_df.groupby('Produit').sum())

if verify_login(username, password):
    st.subheader("Modifier les Stocks")
    updated_aliments_df = display_editable_stock_table(aliments_df, 'aliments_editable_grid')

    
        # Bouton pour sauvegarder les modifications
    if st.button("Sauvegarder les Modifications", key='save_changes'):
        updated_aliments_df.to_csv(chemin_aliments, index=False)
        st.success("Les modifications ont été sauvegardées.")
        aliments_df = pd.read_csv(chemin_aliments)  # Recharger les données pour affichage
        for index, row in updated_aliments_df.iterrows():
            enregistrer_action("Modification des stocks", utilisateur=username, produit=row['Produit'], quantite=row['Quantité dispo'])
        st.write("Nouveaux stocks après modification:")
        st.dataframe(aliments_df)
        
    # Afficher un sélecteur pour le type d'action à filtrer
    options_action = ["Tout afficher", "Nouvelle commande", "Modification des stocks", "Réinitialisation liste d'achat"]
    selection_action = st.selectbox("Choisir le type d'action à afficher :", options_action)
    
    # Bouton pour afficher l'historique filtré des commandes
    if st.button('Afficher l\'historique'):
        df_historique = lire_historique(chemin_historique)
        if not df_historique.empty:
            if selection_action != "Tout afficher":
                # Filtrer le DataFrame pour afficher uniquement le type d'action sélectionné
                df_filtre = df_historique[df_historique["Type d'action"] == selection_action]
            else:
                df_filtre = df_historique
            
            if not df_filtre.empty:
                # Afficher l'historique filtré si le DataFrame n'est pas vide
                st.dataframe(df_filtre)
            else:
                # Message si aucun enregistrement ne correspond au filtre
                st.write(f"Aucun enregistrement trouvé pour '{selection_action}'.")
        else:
            # Message si l'historique est vide ou le fichier n'existe pas
            st.write("L'historique des commandes est vide ou le fichier n'existe pas.")
    
    st.subheader('Réinitialiser la Liste des Aliments à Acheter')
    if st.button('Réinitialiser la Liste', key='reset_list'):
        liste_aliment_manquant_df = pd.DataFrame(columns=['Produit', 'MissingQuantity'])
        st.write('La liste des aliments à acheter a été réinitialisée.')
        liste_aliment_manquant_df.to_csv(chemin_liste_aliments_manquants, index=False)
        enregistrer_action("Réinitialisation liste d'achat", utilisateur=username)

        
        
# admine afficher tout le temps les tableau et celui du stock a acheter//
# ne pas afficher pour le client les tableaux des màj//
# sauvgarder la date//
# permettre de voir tout l'historique des commandes
# Changer le bouton du nom pour commander//
# afficher les réservations
# mettre le nom de celui qui fait les modifications//
 