from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import streamlit as st
import pandas as pd

ADMIN_USER = "admin"
ADMIN_PASSWORD = "password"

chemin_aliments = "Aliments-Grid view.csv"
chemin_liste_aliments_manquants = "Liste aliment manquant-Grid view.csv"

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

if login_button and verify_login(username, password):
    st.sidebar.success("Connecté en tant qu'administrateur.")
    # Affichage du tableau des stocks (éditable par l'admin)
    st.subheader("Modifier les Stocks")
    updated_aliments_df = display_editable_stock_table(aliments_df)
    if st.button("Sauvegarder les Modifications du Stock", key='save_stock_changes'):
        updated_aliments_df.to_csv(chemin_aliments, index=False)
        st.success("Les modifications ont été sauvegardées.")
        aliments_df = pd.read_csv(chemin_aliments)
    
    # Bouton pour réinitialiser la liste des aliments à acheter
    st.subheader('Réinitialiser la Liste des Aliments à Acheter')
    if st.button('Réinitialiser la Liste des Aliments à Acheter', key='reset_list'):
        liste_aliment_manquant_df = pd.DataFrame(columns=['Produit', 'MissingQuantity'])
        liste_aliment_manquant_df.to_csv(chemin_liste_aliments_manquants, index=False)
        st.success('La liste des aliments à acheter a été réinitialisée.')
else:
    st.sidebar.error("Non connecté.")

# Si l'utilisateur est authentifié en tant qu'admin, afficher toujours la liste d'aliments à acheter
if verify_login(username, password):
    st.subheader("Liste d'Aliments à Acheter")
    st.dataframe(liste_aliment_manquant_df)

# Interface utilisateur pour nouvelle commande
st.subheader('Nouvelle Commande')
selected_menu = st.selectbox('Choisir un menu', menu_df['ID'])
number_of_people = st.number_input('Nombre de personnes', min_value=1)
submit_date = st.date_input('Quand souhaiteriez vous réservez?')
if st.button('Calculer les Ingrédients Requis et Mettre à Jour le Stock', key='submit_order'):
    required_ingredients = calculate_required_ingredients(selected_menu, number_of_people, menu_aliments_df)
    aliments_df, new_missing_ingredients_df = update_stock_and_list(aliments_df, required_ingredients)
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
        st.write("Nouveaux stocks après modification:")
        st.dataframe(aliments_df)


    
    st.subheader('Réinitialiser la Liste des Aliments à Acheter')
    if st.button('Réinitialiser la Liste', key='reset_list'):
        liste_aliment_manquant_df = pd.DataFrame(columns=['Produit', 'MissingQuantity'])
        st.write('La liste des aliments à acheter a été réinitialisée.')
        liste_aliment_manquant_df.to_csv(chemin_liste_aliments_manquants, index=False)
        
        
# admine afficher tout le temps les tableau et celui du stock a acheter//
# ne pas afficher pour le client les tableaux des màj//
# sauvgarder la date
# permettre de voir tout l'historique des commandes
# Changer le bouton du nom pour commander
# afficher les réservations
# mettre le nom de celui qui fait les modifications
 