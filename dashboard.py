import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from folium.features import GeoJsonTooltip
import plotly.express as px

# Configuration de la page avec un thème sombre
st.set_page_config(layout="wide", page_title="Tableau de bord interactif", page_icon="🌍")

st.markdown("""
    <style>
    /* Personnalisation générale */
    body { 
        background-color: #1e1e2f; 
        color: #e0e0e0; 
        font-family: 'Roboto', sans-serif; 
    }
    .stat-card {
        background: linear-gradient(135deg, #2a2a3d, #1e1e2f);
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    .stat-card h4 {
        color: #ff9800;
    }
    .stat-card p {
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

class Card:
    def __init__(self, title, content, attribute):
        self.title = title
        self.content = content
        self.attribute = attribute

    def create_map(self, shp, attribute, color):
        m = folium.Map(location=[43.923988, 7.157704], zoom_start=9, tiles="cartodbdark_matter")
        data = pd.DataFrame({'NOM': shp['NOM'], attribute: shp[attribute]})
        choropleth = folium.Choropleth(
            geo_data=shp,
            data=data,
            columns=['NOM', attribute],
            key_on='feature.properties.NOM',
            fill_color=color,
            fill_opacity=0.7,
            line_opacity=0.2,
            legend_name=f'{attribute}',
            name=f'Carte - {attribute}'
        )
        choropleth.geojson.add_child(GeoJsonTooltip(fields=['NOM', attribute], aliases=['Nom', f'{attribute}']))
        choropleth.add_to(m)
        return m

    def create_interactive_histogram(self, shp, attribute):
        fig = px.histogram(shp, x=attribute, nbins=10, 
                           title=f"Distribution : {attribute}",
                           color_discrete_sequence=px.colors.sequential.Plasma)
        fig.update_layout(template="plotly_dark", 
                          plot_bgcolor="#2f2f3f", 
                          paper_bgcolor="#2f2f3f", 
                          font=dict(color="white"))
        return fig

    def display_statistics(self, shp, attribute):
        mean_value = shp[attribute].mean()
        std_dev = shp[attribute].std()
        min_value = shp[attribute].min()
        max_value = shp[attribute].max()
        
        st.markdown(f"""
        <div class='stat-card'>
            <h4>Statistiques Clés</h4>
            <p><b>Moyenne</b> : {mean_value:.2f}</p>
            <p><b>Écart-type</b> : {std_dev:.2f}</p>
            <p><b>Minimum</b> : {min_value:.2f}</p>
            <p><b>Maximum</b> : {max_value:.2f}</p>
        </div>
        """, unsafe_allow_html=True)

def create_dashboard(cards, shp_communes, shp_dfci, colors):
    # Choix entre "Communes" ou "DFCI"
    data_type = st.sidebar.radio("Choisissez le type de données :", options=["Communes", "DFCI"])

    # Charger les shapefiles correspondants
    if data_type == "Communes":
        shp = shp_communes
        title = "Communes"
    else:
        shp = shp_dfci
        title = "Zones DFCI"

    st.title(f"🌍 Tableau de bord interactif : {title}")

    # Sélection de l'indicateur
    selected_card = st.selectbox("📊 Sélectionnez un indicateur :", [card.title for card in cards])

    for card in cards:
        if card.title == selected_card:
            attribute = card.attribute
            attribute_min = int(shp[attribute].min())
            attribute_max = int(shp[attribute].max())

            # Filtrage dynamique
            with st.sidebar:
                st.header("Filtres")
                max_value = st.slider(f"Filtre maximal pour {card.title} :", 
                                      min_value=attribute_min, 
                                      max_value=attribute_max, 
                                      value=attribute_max)
                filtered_shp = shp[shp[attribute] <= max_value]

            # Création des colonnes pour affichage
            col1, col2 = st.columns([2, 1])
            with col1:
                color = colors[attribute]
                m = card.create_map(filtered_shp, attribute, color)
                st_folium(m, width=700, height=450)
            with col2:
                card.display_statistics(filtered_shp, attribute)

            # Affichage de l'histogramme
            st.subheader(f"Histogramme : {attribute}")
            fig = card.create_interactive_histogram(filtered_shp, attribute)
            st.plotly_chart(fig)

# Chargement des shapefiles
shp_communes = gpd.read_file('Data/insee_stats_python.shp')
shp_dfci = gpd.read_file('Data/dfci_stats_python.shp')

# Déclaration des cartes
cards = [
    Card("Nombre d'incendies", "Cette carte montre où les incendies sont les plus fréquents.", "Nombre d'i"),
    Card("Ratio de végétation", "Cette carte illustre l'importance relative de la végétation.", "Ratio"),
    Card("Climat", "Cette carte montre les variations climatiques par région.", "climat_majority"),
    Card("Altitude", "Cette carte donne une vue des altitudes moyennes.", "mnt_mean")
]

# Couleurs associées
colors = {
    "Nombre d'i": "Reds",
    "Ratio": "Greens",
    "climat_majority": "YlOrBr",
    "mnt_mean": "Blues"
}

# Création du tableau de bord
create_dashboard(cards, shp_communes, shp_dfci, colors)
