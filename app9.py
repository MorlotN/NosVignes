from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import streamlit as st
import pandas as pd
import os
chemin_historique = "historique_actions.csv"
ADMIN_USER = "admin"
ADMIN_PASSWORD = "password"
chemin_aliments = "Aliments-Grid view.csv"
chemin_liste_aliments_manquants = "Liste aliment manquant-Grid view.csv"
import datetime
if not os.path.isfile(chemin_historique):
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
        action.to_csv(chemin_historique, index=False)
    else:
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
        liste_aliment_manquant_df = pd.DataFrame(columns=['Produit', 'MissingQuantity','Unité'])
    for index, row in required_ingredients.iterrows():
        produit, quantite_requise, unite = row['Produit'], row['TotalQuantity'], row['Unité']
        filtered_df = ingredients_df.loc[ingredients_df['Produit'] == produit, 'Quantité dispo']
        if not filtered_df.empty:
            stock_actuel = filtered_df.iloc[0]
            if stock_actuel < quantite_requise:
                quantite_manquante = quantite_requise - stock_actuel
                new_row = {'Produit': produit, 'MissingQuantity': quantite_manquante, 'Unité':unite}
                liste_aliment_manquant_df = pd.concat([liste_aliment_manquant_df, pd.DataFrame([new_row])], ignore_index=True)
                ingredients_df.loc[ingredients_df['Produit'] == produit, 'Quantité dispo'] = 0
            else:
                ingredients_df.loc[ingredients_df['Produit'] == produit, 'Quantité dispo'] -= quantite_requise
        else:
            new_row = {'Produit': produit, 'MissingQuantity': quantite_requise, 'Unité':unite}
            liste_aliment_manquant_df = pd.concat([liste_aliment_manquant_df, pd.DataFrame([new_row])], ignore_index=True)
            liste_aliment_manquant_df.groupby('Produit').sum()
    ingredients_df.to_csv(chemin_aliments, index=False)
    liste_aliment_manquant_df.to_csv(chemin_liste_aliments_manquants, index=False)
    return ingredients_df, liste_aliment_manquant_df
def lire_historique(chemin):
    try:
        df_historique = pd.read_csv(chemin)
        return df_historique
    except FileNotFoundError:
        return pd.DataFrame()
def verify_login(user, password):
    return user == ADMIN_USER and password == ADMIN_PASSWORD
def display_editable_stock_table(df, unique_key):
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_grid_options(enableRangeSelection=True)
    gb.configure_column("Produit", editable=False)
    gb.configure_column("Quantité dispo", editable=True)
    gb.configure_column("Date de péremption", editable=True)
    gb.configure_column("Catégorie", editable=True)
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

def gerer_menus():
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
            description_menu = st.text_area("Description du menu")
            ingredients_menu = st.multiselect("Ingrédients du menu", liste_aliments)
            quantites_par_personne = st.text_input("Quantité par personne (séparés par des virgules)")
            bouton_ajouter = st.form_submit_button("Ajouter le menu")
            if bouton_ajouter:
                # Convertir le dictionnaire en DataFrame avant la concaténation
                nouveau_menu = pd.DataFrame([{
                    "ID": id_menu,
                    "Description du menu": description_menu,
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
        
        if st.button("Supprimer le menu"):
            menu_df = menu_df[menu_df['ID'] != menu_a_modifier]
            menu_df.to_csv("Menu-Grid view.csv", index=False)
            st.success(f"Menu {menu_a_modifier} supprimé avec succès.")

st.sidebar.subheader("Connexion Administrateur")
username = st.sidebar.text_input("Nom d'utilisateur")
password = st.sidebar.text_input("Mot de passe", type="password")
login_button = st.sidebar.button("Se connecter")

def display_order_section(menu_df, menu_aliments_df, aliments_df):
    """Affiche la section pour la prise de nouvelles commandes."""
    st.subheader('Nouvelle Commande')
    
    # Crée un sélecteur pour choisir un menu
    selected_menu = st.selectbox('Choisir un menu', menu_df['ID'])
    
    # Nombre de personnes pour la commande
    number_of_people = st.number_input('Nombre de personnes', min_value=1, value=1)
    
    # Date de réservation
    submit_date = st.date_input('Date de réservation')
    
    # Bouton pour soumettre la nouvelle commande
    if st.button('Réserver'):
        # Calcul des ingrédients requis
        required_ingredients = calculate_required_ingredients(selected_menu, number_of_people, menu_aliments_df)
        aliments_df, new_missing_ingredients_df = update_stock_and_list(aliments_df, required_ingredients)
        
        # Enregistre l'action dans l'historique
        enregistrer_action("Nouvelle commande", utilisateur="Utilisateur", menu=selected_menu, nombre_personnes=number_of_people, date_reservation=submit_date)
        
        st.success('Commande enregistrée avec succès.')

def display_stock_management(aliments_df):
    """Affiche et permet la modification des stocks."""
    st.subheader("Modifier les Stocks")
    
    # Création d'un DataFrame éditable pour la gestion des stocks
    gb = GridOptionsBuilder.from_dataframe(aliments_df)
    gb.configure_grid_options(enableRangeSelection=True)
    gb.configure_column("Produit", editable=False)
    gb.configure_column("Quantité dispo", editable=True)
    gb.configure_column("Date de péremption", editable=True)
    gb.configure_column("Catégorie", editable=True)
    grid_options = gb.build()
    
    grid_response = AgGrid(
        aliments_df,
        grid_options=grid_options,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        fit_columns_on_grid_load=True,
        key='stock_table'
    )
    
    updated_aliments_df = grid_response['data']
    
    # Bouton pour sauvegarder les modifications
    if st.button("Sauvegarder les Modifications", key='save_changes'):
        updated_aliments_df.to_csv(chemin_aliments, index=False)
        st.success("Les modifications ont été sauvegardées.")
        
        # Optionnellement, enregistrer l'action de modification des stocks
        enregistrer_action("Modification des stocks", utilisateur="Admin", produit="Multiple", quantite="Varie")

def gerer_aliments():
    st.subheader("Gestion des Aliments")

    # Chargement des données des aliments
    try:
        aliments_df = pd.read_csv(chemin_aliments)
    except pd.errors.EmptyDataError:
        aliments_df = pd.DataFrame(columns=['Produit', 'Quantité dispo', 'Unité'])
    
    # Ajouter un nouvel aliment
    with st.form("ajout_aliment"):
        st.write("Ajouter un nouvel aliment")
        nouveau_produit = st.text_input("Nom du produit", key="nouveau_produit")
        nouvelle_quantite = st.number_input("Quantité disponible", min_value=0.0, key="nouvelle_quantite")
        nouvelle_unite = st.text_input("Unité (kg, pcs, etc.)", key="nouvelle_unite")
        soumettre_ajout = st.form_submit_button("Ajouter l'aliment")
        if soumettre_ajout:
            nouveau_aliment = pd.DataFrame([{
                'Produit': nouveau_produit,
                'Quantité dispo': nouvelle_quantite,
                'Unité': nouvelle_unite}])
            # aliments_df = aliments_df.append({'Produit': nouveau_produit, 'Quantité dispo': nouvelle_quantite, 'Unité': nouvelle_unite}, ignore_index=True)
            aliments_df = pd.concat([aliments_df, nouveau_aliment], ignore_index=True)
            aliments_df.to_csv(chemin_aliments, index=False)
            st.success("Aliment ajouté avec succès !")

    # Sélectionner un aliment pour modification ou suppression
    aliments_liste = aliments_df['Produit'].tolist()
    aliment_selectionne = st.selectbox("Sélectionnez un aliment à modifier ou supprimer", [""] + aliments_liste)

    # Modification de l'aliment sélectionné
    if aliment_selectionne:
        aliment_index = aliments_df[aliments_df['Produit'] == aliment_selectionne].index[0]
        
        modif_quantite = st.number_input("Modifier la quantité", value=float(aliments_df.loc[aliment_index, 'Quantité dispo']))
        modif_unite = st.text_input("Modifier l'unité", value=aliments_df.loc[aliment_index, 'Unité'])
        
        if st.button("Sauvegarder les modifications"):
            aliments_df.loc[aliment_index, 'Quantité dispo'] = modif_quantite
            aliments_df.loc[aliment_index, 'Unité'] = modif_unite
            aliments_df.to_csv(chemin_aliments, index=False)
            st.success("Modifications enregistrées !")

        if st.button("Supprimer l'aliment"):
            aliments_df = aliments_df.drop(aliment_index)
            aliments_df.to_csv(chemin_aliments, index=False)
            st.success("Aliment supprimé !")

#     # Vérifie si l'utilisateur est connecté
def main():

    
    # Vérifie si l'utilisateur est connecté
    if verify_login(username, password):
        # Charge les données nécessaires
        menu_df, menu_aliments_df, commandes_client_df, aliments_df, liste_aliment_manquant_df = load_data()

        # Affiche le titre principal de l'application
        st.title('Gestion de Stock et Commandes')

        # Section pour la liste des aliments à acheter et le bouton pour réinitialiser la liste
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader("Liste d'Aliments à Acheter")
            st.dataframe(liste_aliment_manquant_df)
        with col2:
            st.write("")  # Pour l'espacement
            st.write("")  # Plus d'espacement
            if st.button('Réinitialiser la Liste', key='reset_list'):
                liste_aliment_manquant_df = pd.DataFrame(columns=['Produit', 'MissingQuantity', 'Unité'])
                st.success('La liste des aliments à acheter a été réinitialisée.')
                liste_aliment_manquant_df.to_csv(chemin_liste_aliments_manquants, index=False)
                enregistrer_action("Réinitialisation liste d'achat", utilisateur=st.session_state.username)

        # Boutons pour gérer les menus et les aliments
        manage_actions()

        # Autres sections de l'application...
        display_order_section(menu_df, menu_aliments_df, aliments_df)
        display_stock_management(aliments_df)

def manage_actions():
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Gérer les menus"):
            st.session_state['action'] = 'gerer_menus'
    with col2:
        if st.button("Gérer les aliments"):
            st.session_state['action'] = 'gerer_aliments'

    if 'action' in st.session_state:
        if st.session_state['action'] == 'gerer_menus':
            gerer_menus()
        elif st.session_state['action'] == 'gerer_aliments':
            gerer_aliments()

# Exécution de la fonction principale
main()

            

st.title('Gestion de Stock et Commandes')
menu_df, menu_aliments_df, commandes_client_df, aliments_df, liste_aliment_manquant_df = load_data()
if verify_login(username, password):
    st.subheader("Liste d'Aliments à Acheter")
    st.dataframe(liste_aliment_manquant_df)
st.subheader('Nouvelle Commande')
name_cli = st.text_input('Nom')
selected_menu = st.selectbox('Choisir son menu', menu_df['ID'])
number_of_people = st.number_input('Nombre de personnes', min_value=1)
submit_date = st.date_input('Quand souhaiteriez vous réservez?')
if st.button('Réserver', key='submit_order'):
    required_ingredients = calculate_required_ingredients(selected_menu, number_of_people, menu_aliments_df)
    aliments_df, new_missing_ingredients_df = update_stock_and_list(aliments_df, required_ingredients)
    enregistrer_action("Nouvelle commande", utilisateur=name_cli, menu=selected_menu, nombre_personnes=number_of_people, date_reservation=submit_date)
    st.success(f'La commande a bien été enregistrée pour le {submit_date} pour {number_of_people} personnes.')
if verify_login(username, password):
    st.subheader("Modifier les Stocks")
    updated_aliments_df = display_editable_stock_table(aliments_df, 'aliments_editable_grid')    
    if st.button("Sauvegarder les Modifications", key='save_change'):
        updated_aliments_df.to_csv(chemin_aliments, index=False)
        st.success("Les modifications ont été sauvegardées.")
        aliments_df = pd.read_csv(chemin_aliments)  
        for index, row in updated_aliments_df.iterrows():
            enregistrer_action("Modification des stocks", utilisateur=username, produit=row['Produit'], quantite=row['Quantité dispo'])
        st.write("Nouveaux stocks après modification:")
        st.dataframe(aliments_df)      
    options_action = ["Tout afficher", "Nouvelle commande", "Modification des stocks", "Réinitialisation liste d'achat"]
    selection_action = st.selectbox("Choisir le type d'action à afficher :", options_action)   
    
    
    if st.button('Afficher l\'historique'):
        df_historique = lire_historique(chemin_historique)
        if not df_historique.empty:
            if selection_action != "Tout afficher":
                df_filtre = df_historique[df_historique["Type d'action"] == selection_action]
            else:
                df_filtre = df_historique
            
            if not df_filtre.empty:
                st.dataframe(df_filtre)
            else:
                st.write(f"Aucun enregistrement trouvé pour '{selection_action}'.")
        else:
            st.write("L'historique des commandes est vide ou le fichier n'existe pas.")    
    