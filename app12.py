from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import streamlit as st
import pandas as pd
import os
import datetime
import numpy as np

# Chemins vers les fichiers
chemin_historique = "historique_actions.csv"
chemin_aliments = "Aliments-Grid view.csv"
chemin_liste_aliments_manquants = "Liste aliment manquant-Grid view.csv"
ADMIN_USER = "admin"
ADMIN_PASSWORD = "password"

def initialiser_application():
    if not os.path.isfile(chemin_historique):
        df_historique = pd.DataFrame(columns=[
            "Type d'action", "Date", "Utilisateur", "Menu", "Nombre de personnes", 
            "Produit", "Quantité", "Date de réservation"
        ])
        df_historique.to_csv(chemin_historique, index=False)

def charger_donnees():
    menu_df = pd.read_csv("Menu-Grid view.csv")
    menu_aliments_df = pd.read_csv("Menu&Aliments-Grid view.csv")
    commandes_client_df = pd.read_csv("Commandes client-Grid view.csv")
    aliments_df = pd.read_csv(chemin_aliments)
    liste_aliment_manquant_df = pd.read_csv(chemin_liste_aliments_manquants)
    return menu_df, menu_aliments_df, commandes_client_df, aliments_df, liste_aliment_manquant_df

def verifier_login(user, password):
    return user == ADMIN_USER and password == ADMIN_PASSWORD

def afficher_section_commandes(menu_df, menu_aliments_df, aliments_df):
    st.subheader('Nouvelle Commande')
    selected_menu = st.selectbox('Choisir un menu', menu_df['ID'])
    number_of_people = st.number_input('Nombre de personnes', min_value=1, value=1)
    submit_date = st.date_input('Date de réservation')
    if st.button('Réserver'):
        required_ingredients = calculate_required_ingredients(selected_menu, number_of_people, menu_df, aliments_df)
        aliments_df, new_missing_ingredients_df = update_stock_and_list(aliments_df, required_ingredients)
        enregistrer_action("Nouvelle commande", utilisateur="Utilisateur", menu=selected_menu, nombre_personnes=number_of_people, date_reservation=submit_date)
        st.success('Commande enregistrée avec succès.')
        return new_missing_ingredients_df

def afficher_gestion_stocks(aliments_df):
    st.subheader("Modifier les Stocks")
    updated_aliments_df = display_editable_stock_table(aliments_df, 'aliments_editable_grid')
    if st.button("Sauvegarder les Modifications", key='save_changes'):
        updated_aliments_df.to_csv(chemin_aliments, index=False)
        st.success("Les modifications ont été sauvegardées.")


def gerer_aliments(username, password):
    st.subheader("Gestion des Aliments")

    # Chargement des données des aliments
    try:
        aliments_df = pd.read_csv(chemin_aliments)
    except pd.errors.EmptyDataError:
        aliments_df = pd.DataFrame(columns=['Produit',"Quantité", "Catégorie", 'Unité'])
    # Ajouter un nouvel aliment
    with st.form("ajout_aliment"):
        st.write("Ajouter un nouvel aliment")
        nouveau_produit = st.text_input("Nom du produit", key="nouveau_produit")
        nouvelle_categorie = st.selectbox("Catégorie", (np.array(aliments_df["Catégorie"].unique()).tolist()), key="nouvelle_categorie")
        nouvelle_unite = st.selectbox("Unité (kg, pcs, etc.)", (np.array(aliments_df["Unité"].unique()).tolist()), key="nouvelle_unite")
        soumettre_ajout = st.form_submit_button("Ajouter l'aliment")
        if soumettre_ajout:
            nouveau_aliment = pd.DataFrame([{
                'Produit': nouveau_produit,
                'Quantité': 0,
                "Catégorie":nouvelle_categorie,
                'Unité': nouvelle_unite}])
            # aliments_df = aliments_df.append({'Produit': nouveau_produit, 'Quantité dispo': nouvelle_quantite, 'Unité': nouvelle_unite}, ignore_index=True)
            aliments_df = pd.concat([aliments_df, nouveau_aliment], ignore_index=True)
            aliments_df.to_csv(chemin_aliments, index=False)
            st.success("Aliment ajouté avec succès !")

    # Sélectionner un aliment pour modification ou suppression
    aliments_liste = aliments_df['Produit'].tolist()
    
    if verifier_login(username, password):
        aliment_selectionne = st.selectbox("Sélectionnez un aliment à modifier ou supprimer", [""] + aliments_liste)
        # Modification de l'aliment sélectionné
        if aliment_selectionne:
            aliment_index = aliments_df[aliments_df['Produit'] == aliment_selectionne].index[0]
            
            modif_quantite = st.number_input("Modifier la quantité", value=float(aliments_df.loc[aliment_index, 'Quantité']))
            modif_unite = st.text_input("Modifier l'unité", value=aliments_df.loc[aliment_index, 'Unité'])
            
            if st.button("Sauvegarder les modifications"):
                aliments_df.loc[aliment_index, 'Quantité'] = modif_quantite
                aliments_df.loc[aliment_index, 'Unité'] = modif_unite
                aliments_df.to_csv(chemin_aliments, index=False)
                st.success("Modifications enregistrées !")
            if st.button("Supprimer l'aliment"):
                aliments_df = aliments_df.drop(aliment_index)
                aliments_df.to_csv(chemin_aliments, index=False)
                st.success("Aliment supprimé !")

def gerer_menus(username, password):
    st.subheader("Gestion des Menus")
    
    # Chargement des données des menus et des aliments
    menu_df = pd.read_csv("Menu-Grid view.csv")
    aliments_df = pd.read_csv("Aliments-Grid view.csv")  # Assurez-vous que le chemin est correct
    
    # Liste des aliments pour le multiselect
    liste_aliments = aliments_df['Produit'].unique()  # Assurez-vous que la colonne est correctement nommée
    
    # Ajouter un nouveau menu
    with st.expander("Ajouter un nouveau menu"):
        with st.form(key='form_ajout_menu'):
            id_menu = st.text_input("Nom du menu")
            des_entre_menu = st.text_area("Entée")
            des_plat_menu = st.text_area("Plat")
            des_desert_menu = st.text_area("Désert")
            description_menu = st.text_area("Commentaire du menu")
            ingredients_menu = st.multiselect("Ingrédients du menu", liste_aliments)
            quantites_par_personne = st.text_input("Quantité par personne (séparés par des virgules)")
            bouton_ajouter = st.form_submit_button("Ajouter le menu")
            if bouton_ajouter:
                # Convertir le dictionnaire en DataFrame avant la concaténation
                nouveau_menu = pd.DataFrame([{
                    "ID": id_menu,
                    "Entrée":des_entre_menu,
                    "Plat":des_plat_menu,
                    "Désert":des_desert_menu,
                    "Commentaire du menu": description_menu,
                    "Ingrédients menu": ", ".join(ingredients_menu),
                    "Quantité/pers (from Ingrédients menu)": quantites_par_personne,
                }])
                menu_df = pd.concat([menu_df, nouveau_menu], ignore_index=True)
                menu_df.to_csv("Menu-Grid view.csv", index=False)
                st.success("Menu ajouté avec succès !")

    
    # Modifier/Supprimer un menu existant
    menu_a_modifier = st.selectbox("Choisir un menu à modifier ou supprimer", menu_df['ID'].unique(), format_func=lambda x: 'Sélectionnez' if x == '' else x)
    if menu_a_modifier:
        menu_selectionne = menu_df[menu_df['ID'] == menu_a_modifier].iloc[0]
        with st.form(key='form_modif_menu'):
            description_menu = st.text_area("Description du menu", value=menu_selectionne['Description du menu'])
            # Préparation des ingrédients actuels pour la sélection multiple
            ingredients_actuels = menu_selectionne['Ingrédients menu'].split(", ") if pd.notna(menu_selectionne['Ingrédients menu']) else []
            ingredients_actuels = [ing for ing in ingredients_actuels if ing in liste_aliments]  # On filtre les ingrédients qui ne sont pas dans la liste
            ingredients_menu = st.multiselect("Ingrédients du menu", liste_aliments, default=ingredients_actuels)
            quantites_par_personne = st.text_input("Quantité par personne", value=menu_selectionne['Quantité/pers (from Ingrédients menu)'])
            bouton_modifier = st.form_submit_button("Modifier le menu")
            if bouton_modifier:
                menu_df.loc[menu_df['ID'] == menu_a_modifier, ['Description du menu', 'Ingrédients menu', 'Quantité/pers (from Ingrédients menu)']] = [description_menu, ", ".join(ingredients_menu), quantites_par_personne]
                menu_df.to_csv("Menu-Grid view.csv", index=False)
                st.success(f"Menu {menu_a_modifier} modifié avec succès.")
        if verifier_login(username, password):
            if st.button("Supprimer le menu"):
                menu_df = menu_df[menu_df['ID'] != menu_a_modifier]
                menu_df.to_csv("Menu-Grid view.csv", index=False)
                st.success(f"Menu {menu_a_modifier} supprimé avec succès.")

def afficher_historique(chemin_historique):
    st.subheader("Historique des Actions")
    df_historique = lire_historique(chemin_historique)
    if not df_historique.empty:
        st.dataframe(df_historique)
    else:
        st.write("L'historique des actions est vide.")


def reinitialiser_liste_achats(chemin_liste_aliments_manquants):
    if st.button('Réinitialiser la Liste', key='reset_list'):
        liste_aliment_manquant_df = pd.DataFrame(columns=['Produit', 'Quantité', 'Unité', 'Catégorie'])
        liste_aliment_manquant_df.to_csv(chemin_liste_aliments_manquants, index=False)
        st.success('La liste des aliments à acheter a été réinitialisée.')


def calculate_required_ingredients(selected_menu, num_people, menu_df, aliments_df):
    # Trouver la ligne du menu sélectionné dans menu_df
    menu_selected_row = menu_df[menu_df['ID'] == selected_menu]
    
    if not menu_selected_row.empty:
        # Séparer les ingrédients et leurs quantités
        ingredients = menu_selected_row['Ingrédients menu'].values[0].split(", ")
        quantities_per_person_str = menu_selected_row['Quantité/pers (from Ingrédients menu)'].values[0]
        quantities_per_person = [int(q) for q in quantities_per_person_str.split(", ")]

        # Vérifier que nous avons le même nombre d'ingrédients et de quantités
        if len(ingredients) != len(quantities_per_person):
            st.error("Le nombre d'ingrédients et de quantités par personne ne correspond pas.")
            return pd.DataFrame()

        # Calculer la quantité totale requise pour chaque ingrédient
        total_quantities = [q * num_people for q in quantities_per_person]

        # Obtenir les unités et catégories pour chaque ingrédient à partir de aliments_df
        units = []
        categories = []
        for ingredient in ingredients:
            aliments_row = aliments_df[aliments_df['Produit'] == ingredient]
            if not aliments_row.empty:
                units.append(aliments_row['Unité'].values[0])
                categories.append(aliments_row['Catégorie'].values[0])
            else:
                units.append('Unité non trouvée')
                categories.append('Catégorie non trouvée')

        # Créer un DataFrame pour les ingrédients nécessaires avec les quantités totales, unités et catégories
        ingredients_needed = pd.DataFrame({
            'Produit': ingredients,
            'TotalQuantity': total_quantities,
            'Unité': units,
            'Catégorie': categories
        })

        return ingredients_needed
    else:
        st.error(f"Menu sélectionné '{selected_menu}' introuvable.")
        return pd.DataFrame()


def update_stock_and_list(ingredients_df, required_ingredients):
    try:
        liste_aliment_manquant_df = pd.read_csv(chemin_liste_aliments_manquants)
    except pd.errors.EmptyDataError:
        liste_aliment_manquant_df = pd.DataFrame(columns=['Produit', 'Quantité','Unité', 'Catégorie'])
    for index, row in required_ingredients.iterrows():
        produit, quantite_requise, unite, categories = row['Produit'], row['TotalQuantity'], row['Unité'], row[ 'Catégorie']
        filtered_df = ingredients_df.loc[ingredients_df['Produit'] == produit, 'Quantité']
        if not filtered_df.empty:
            stock_actuel = filtered_df.iloc[0]
            if stock_actuel < quantite_requise:
                quantite_manquante = quantite_requise - stock_actuel
                new_row = {'Produit': produit, 'Quantité': quantite_manquante, 'Unité':unite, 'Catégorie':categories}
                liste_aliment_manquant_df = pd.concat([liste_aliment_manquant_df, pd.DataFrame([new_row])], ignore_index=True)
                ingredients_df.loc[ingredients_df['Produit'] == produit, 'Quantité'] = 0
            else:
                ingredients_df.loc[ingredients_df['Produit'] == produit, 'Quantité'] -= quantite_requise
        else:
            new_row = {'Produit': produit, 'Quantité': quantite_requise, 'Unité':unite, 'Catégorie':categories}
            liste_aliment_manquant_df = pd.concat([liste_aliment_manquant_df, pd.DataFrame([new_row])], ignore_index=True)
            liste_aliment_manquant_df.groupby('Produit').sum()
    ingredients_df.to_csv(chemin_aliments, index=False)
    liste_aliment_manquant_df.to_csv(chemin_liste_aliments_manquants, index=False)
    st.dataframe(liste_aliment_manquant_df)
    return ingredients_df, liste_aliment_manquant_df

def display_editable_stock_table(df, unique_key):
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_grid_options(enableRangeSelection=True)
    gb.configure_column("Produit", editable=False)
    gb.configure_column("Quantité", editable=True)
    gb.configure_column("Unité", editable=True)
    gb.configure_column("Péremption", editable=True)
    gb.configure_column("Catégorie", editable=True)
    gb.configure_column("Prix", editable=True)
    gb.configure_column("Ouverture", editable=True)
    gridOptions = gb.build()
    grid_response = AgGrid(
        df,
        gridOptions=gridOptions,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        fit_columns_on_grid_load=True,
        key=unique_key
    )
    data = grid_response['data'].groupby('Produit').sum().reset_index(names=['Produit'])
    return data

def lire_historique(chemin):
    try:
        df_historique = pd.read_csv(chemin)
        return df_historique
    except FileNotFoundError:
        return pd.DataFrame()
       
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
        action.to_csv(chemin_historique, index=False)
    else:
        historique_df = pd.read_csv(chemin_historique)
        historique_df = pd.concat([historique_df, action], ignore_index=True)
        historique_df.to_csv(chemin_historique, index=False)

def manage_actions(username, password):
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Gérer les menus"):
            st.session_state['action'] = 'gerer_menus'
    with col2:
        if st.button("Gérer les aliments"):
            st.session_state['action'] = 'gerer_aliments'

    if 'action' in st.session_state:
        if st.session_state['action'] == 'gerer_menus':
            gerer_menus(username, password)
        elif st.session_state['action'] == 'gerer_aliments':
            gerer_aliments(username, password)
            

def main():
    initialiser_application()
    st.sidebar.subheader("Connexion Administrateur")
    username = st.sidebar.text_input("Nom d'utilisateur")
    password = st.sidebar.text_input("Mot de passe", type="password")
    # login_button = st.sidebar.button("Se connecter")
    if verifier_login(username, password):
        menu_df, menu_aliments_df, commandes_client_df, aliments_df, liste_aliment_manquant_df = charger_donnees()
        
        st.subheader("Liste d'Aliments à Acheter")
        grouped_list = liste_aliment_manquant_df.groupby('Produit').agg({
            'Quantité': 'sum',  # Somme des quantités
            'Unité': 'first',  # Conserve la première unité trouvée
            'Catégorie': 'first'
        }).reset_index()
        # st.dataframe(grouped_list)
        # Création de la grille éditable
        gb = GridOptionsBuilder.from_dataframe(grouped_list)
        gb.configure_grid_options(enableRangeSelection=True)
        gb.configure_column("Quantité", editable=True)  # Rendre la colonne 'Quantité' éditable
        grid_options = gb.build()
        
        # Affichage de la grille
        grid_response = AgGrid(
            grouped_list,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.MODEL_CHANGED,
            fit_columns_on_grid_load=False,
            height=300,
            key='aliments_grid'
        )
        
        updated_liste_aliment_manquant_df = grid_response['data']
        # st.dataframe(updated_liste_aliment_manquant_df)
        
        # Ajout de nouveaux aliments
        with st.form("new_item_form"):
            new_produit = st.text_input("Produit")
            new_quantite = st.number_input("Quantité", min_value=0)
            new_unite = st.selectbox("Unité", (aliments_df["Unité"].unique()))
            new_categorie = st.selectbox("Catégorie", (aliments_df["Catégorie"].unique()))
            submit_new_item = st.form_submit_button("Ajouter l'aliment à liste achat")
            if submit_new_item:
                # Ajoutez la nouvelle entrée à la dataframe existante
                new_entry = pd.DataFrame([[new_produit, new_quantite, new_unite, new_categorie]], columns=['Produit', 'Quantité', 'Unité',"Catégorie"])
                liste_aliment_manquant_df = pd.concat([liste_aliment_manquant_df, new_entry], ignore_index=True)
                # Mettre à jour la grille pour afficher le nouvel aliment
                liste_aliment_manquant_df.to_csv(chemin_liste_aliments_manquants, index=False)
                st.rerun()
        afficher_section_commandes(menu_df, menu_aliments_df, aliments_df)
        # Appeler les autres fonctions de gestion ici
        afficher_gestion_stocks(aliments_df)
        manage_actions(username, password)
        # Plus d'appels de fonctions selon les besoins
    else:
        manage_actions(username, password)

if __name__ == "__main__":
    main()





































# chemin_historique = "historique_actions.csv"
# ADMIN_USER = "admin"
# ADMIN_PASSWORD = "password"
# chemin_aliments = "Aliments-Grid view.csv"
# chemin_liste_aliments_manquants = "Liste aliment manquant-Grid view.csv"

# if not os.path.isfile(chemin_historique):
#     df_historique = pd.DataFrame(columns=[
#         "Type d'action", 
#         "Date", 
#         "Utilisateur", 
#         "Menu", 
#         "Nombre de personnes", 
#         "Produit", 
#         "Quantité", 
#         "Date de réservation"
#     ])
#     df_historique.to_csv(chemin_historique, index=False)
# chemin_historique = "historique_actions.csv"

# def load_data():
#     menu_df = pd.read_csv("Menu-Grid view.csv")
#     menu_aliments_df = pd.read_csv("Menu&Aliments-Grid view.csv")
#     commandes_client_df = pd.read_csv("Commandes client-Grid view.csv")
#     aliments_df = pd.read_csv(chemin_aliments)
#     liste_aliment_manquant_df = pd.read_csv(chemin_liste_aliments_manquants)
#     return menu_df, menu_aliments_df, commandes_client_df, aliments_df, liste_aliment_manquant_df



# def verify_login(user, password):
#     return user == ADMIN_USER and password == ADMIN_PASSWORD




# st.sidebar.subheader("Connexion Administrateur")
# username = st.sidebar.text_input("Nom d'utilisateur")
# password = st.sidebar.text_input("Mot de passe", type="password")
# login_button = st.sidebar.button("Se connecter")

# def display_order_section(menu_df, menu_aliments_df, aliments_df):
#     """Affiche la section pour la prise de nouvelles commandes."""
#     st.subheader('Nouvelle Commande')
    
#     # Crée un sélecteur pour choisir un menu
#     selected_menu = st.selectbox('Choisir un menu', menu_df['ID'])
    
#     # Nombre de personnes pour la commande
#     number_of_people = st.number_input('Nombre de personnes', min_value=1, value=1)
    
#     # Date de réservation
#     submit_date = st.date_input('Date de réservation')
    
#     # Bouton pour soumettre la nouvelle commande
#     if st.button('Réserver'):
#         # Calcul des ingrédients requis
#         required_ingredients = calculate_required_ingredients(selected_menu, number_of_people, menu_aliments_df)
#         aliments_df, new_missing_ingredients_df = update_stock_and_list(aliments_df, required_ingredients)
        
#         # Enregistre l'action dans l'historique
#         enregistrer_action("Nouvelle commande", utilisateur="Utilisateur", menu=selected_menu, nombre_personnes=number_of_people, date_reservation=submit_date)
        
#         st.success('Commande enregistrée avec succès.')




# #     # Vérifie si l'utilisateur est connecté
# def main():

    
#     # Vérifie si l'utilisateur est connecté
#     if verify_login(username, password):
#         # Charge les données nécessaires
#         menu_df, menu_aliments_df, commandes_client_df, aliments_df, liste_aliment_manquant_df = load_data()

#         # Affiche le titre principal de l'application
#         st.title('Gestion de Stock et Commandes')

#         # Section pour la liste des aliments à acheter et le bouton pour réinitialiser la liste
#         col1, col2 = st.columns([3, 1])
#         with col1:
#             st.subheader("Liste d'Aliments à Acheter")
#             st.dataframe(liste_aliment_manquant_df)
#         with col2:
#             st.write("")  # Pour l'espacement
#             st.write("")  # Plus d'espacement
#             if st.button('Réinitialiser la Liste', key='reset_list'):
#                 liste_aliment_manquant_df = pd.DataFrame(columns=['Produit', 'MissingQuantity', 'Unité'])
#                 st.success('La liste des aliments à acheter a été réinitialisée.')
#                 liste_aliment_manquant_df.to_csv(chemin_liste_aliments_manquants, index=False)
#                 enregistrer_action("Réinitialisation liste d'achat", utilisateur=st.session_state.username)

#         # Boutons pour gérer les menus et les aliments
#         manage_actions()

#         # Autres sections de l'application...
#         display_order_section(menu_df, menu_aliments_df, aliments_df)
#         display_stock_management(aliments_df)



# # Exécution de la fonction principale
# main()

            

# st.title('Gestion de Stock et Commandes')
# menu_df, menu_aliments_df, commandes_client_df, aliments_df, liste_aliment_manquant_df = load_data()
# if verify_login(username, password):
#     st.subheader("Liste d'Aliments à Acheter")
#     st.dataframe(liste_aliment_manquant_df)
# st.subheader('Nouvelle Commande')
# name_cli = st.text_input('Nom')
# selected_menu = st.selectbox('Choisir son menu', menu_df['ID'])
# number_of_people = st.number_input('Nombre de personnes', min_value=1)
# submit_date = st.date_input('Quand souhaiteriez vous réservez?')
# if st.button('Réserver', key='submit_order'):
#     required_ingredients = calculate_required_ingredients(selected_menu, number_of_people, menu_aliments_df)
#     aliments_df, new_missing_ingredients_df = update_stock_and_list(aliments_df, required_ingredients)
#     enregistrer_action("Nouvelle commande", utilisateur=name_cli, menu=selected_menu, nombre_personnes=number_of_people, date_reservation=submit_date)
#     st.success(f'La commande a bien été enregistrée pour le {submit_date} pour {number_of_people} personnes.')
# if verify_login(username, password):
#     st.subheader("Modifier les Stocks")
#     updated_aliments_df = display_editable_stock_table(aliments_df, 'aliments_editable_grid')    
#     if st.button("Sauvegarder les Modifications", key='save_change'):
#         updated_aliments_df.to_csv(chemin_aliments, index=False)
#         st.success("Les modifications ont été sauvegardées.")
#         aliments_df = pd.read_csv(chemin_aliments)  
#         for index, row in updated_aliments_df.iterrows():
#             enregistrer_action("Modification des stocks", utilisateur=username, produit=row['Produit'], quantite=row['Quantité dispo'])
#         st.write("Nouveaux stocks après modification:")
#         st.dataframe(aliments_df)      
#     options_action = ["Tout afficher", "Nouvelle commande", "Modification des stocks", "Réinitialisation liste d'achat"]
#     selection_action = st.selectbox("Choisir le type d'action à afficher :", options_action)   
    
    
#     if st.button('Afficher l\'historique'):
#         df_historique = lire_historique(chemin_historique)
#         if not df_historique.empty:
#             if selection_action != "Tout afficher":
#                 df_filtre = df_historique[df_historique["Type d'action"] == selection_action]
#             else:
#                 df_filtre = df_historique
            
#             if not df_filtre.empty:
#                 st.dataframe(df_filtre)
#             else:
#                 st.write(f"Aucun enregistrement trouvé pour '{selection_action}'.")
#         else:
#             st.write("L'historique des commandes est vide ou le fichier n'existe pas.")    
    