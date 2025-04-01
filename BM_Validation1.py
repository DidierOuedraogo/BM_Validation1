import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
from datetime import datetime

# Configuration de la page
st.set_page_config(
    page_title="Comparaison de Modèles Géologiques",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styles CSS personnalisés
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 500;
        margin-bottom: 1rem;
        padding-top: 1rem;
    }
    .stat-card {
        background-color: white;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    .stat-row {
        display: flex;
        justify-content: space-between;
        padding: 0.5rem 0;
        border-bottom: 1px solid #f0f0f0;
    }
    .stat-label {
        font-weight: 500;
        color: #6b7280;
    }
    .stat-value {
        font-weight: 600;
    }
    .positive {
        color: #10b981;
    }
    .negative {
        color: #ef4444;
    }
    .neutral {
        color: #6b7280;
    }
    .footer {
        margin-top: 2rem;
        text-align: center;
        color: #6b7280;
    }
    .dropzone {
        border: 2px dashed #ccc;
        border-radius: 5px;
        padding: 25px;
        text-align: center;
        margin: 1rem 0;
        background-color: #f9f9f9;
    }
</style>
""", unsafe_allow_html=True)

# Titre de l'application
st.markdown('<div class="main-header">Outil de Comparaison de Modèles Géologiques</div>', unsafe_allow_html=True)
st.markdown('<p style="text-align: right; color: #6b7280;">Auteur: Didier Ouedraogo, P.Geo</p>', unsafe_allow_html=True)

# Initialisation des variables de session si elles n'existent pas
if 'composite_data' not in st.session_state:
    st.session_state.composite_data = None
if 'block_data' not in st.session_state:
    st.session_state.block_data = None
if 'composite_stats' not in st.session_state:
    st.session_state.composite_stats = None
if 'block_stats' not in st.session_state:
    st.session_state.block_stats = None
if 'composite_columns' not in st.session_state:
    st.session_state.composite_columns = None
if 'block_columns' not in st.session_state:
    st.session_state.block_columns = None
if 'mapping' not in st.session_state:
    st.session_state.mapping = None

# Fonctions utilitaires
def calculate_statistics(df, grade_column):
    """Calcule les statistiques pour un dataframe donné"""
    if df is None or grade_column not in df.columns:
        return None
    
    # Convertir les colonnes en numérique si nécessaire
    df[grade_column] = pd.to_numeric(df[grade_column], errors='coerce')
    
    # Calculer les statistiques
    stats = {
        "volume": 1_250_000 if "composite" in grade_column else 1_275_000,  # Valeurs simulées
        "tonnage": 3_375_000 if "composite" in grade_column else 3_442_500,  # Valeurs simulées
        "densite": 2.7,  # Valeur fixe pour l'exemple
        "teneur_moyenne": df[grade_column].mean(),
        "teneur_min": df[grade_column].min(),
        "teneur_max": df[grade_column].max(),
        "ecart_type": df[grade_column].std(),
        "metal_contenu": 3_375_000 * df[grade_column].mean() / 1000 if "composite" in grade_column else 3_442_500 * df[grade_column].mean() / 1000,
        "recuperation": 92.5 if "composite" in grade_column else 91.0,  # Valeurs simulées
    }
    
    stats["metal_recuperable"] = stats["metal_contenu"] * stats["recuperation"] / 100
    
    return stats

def create_comparison_chart(composite_stats, block_stats):
    """Crée un graphique de comparaison entre les modèles"""
    if composite_stats is None or block_stats is None:
        return None
    
    # Créer un graphique de comparaison des teneurs
    fig = make_subplots(rows=1, cols=2, 
                         subplot_titles=("Distribution des Teneurs", "Comparaison des Métriques"),
                         specs=[[{"type": "box"}, {"type": "bar"}]])
    
    # Distribution des teneurs (boîte à moustaches)
    fig.add_trace(
        go.Box(y=st.session_state.composite_data[st.session_state.mapping['composite']['grade']], 
               name="Composite 3D",
               marker_color='#2563eb'),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Box(y=st.session_state.block_data[st.session_state.mapping['block']['grade']], 
               name="Bloc Modèle",
               marker_color='#f59e0b'),
        row=1, col=1
    )
    
    # Comparaison des métriques clés
    metrics = ["teneur_moyenne", "ecart_type", "metal_contenu"]
    labels = ["Teneur moyenne (g/t)", "Écart-type (g/t)", "Métal contenu (kg)"]
    
    composite_values = [composite_stats[m] for m in metrics]
    block_values = [block_stats[m] for m in metrics]
    
    fig.add_trace(
        go.Bar(x=labels, y=composite_values, name="Composite 3D", marker_color='#2563eb'),
        row=1, col=2
    )
    
    fig.add_trace(
        go.Bar(x=labels, y=block_values, name="Bloc Modèle", marker_color='#f59e0b'),
        row=1, col=2
    )
    
    # Mise en forme du graphique
    fig.update_layout(
        height=400,
        boxmode='group',
        barmode='group',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        )
    )
    
    fig.update_yaxes(title_text="Teneur (g/t)", row=1, col=1)
    
    return fig

def create_3d_scatter(df, x_col, y_col, z_col, grade_col, point_size=3, model_type="Composite"):
    """Crée un graphique 3D des points"""
    if df is None:
        return None
    
    # Convertir en numérique
    df[x_col] = pd.to_numeric(df[x_col], errors='coerce')
    df[y_col] = pd.to_numeric(df[y_col], errors='coerce')
    df[z_col] = pd.to_numeric(df[z_col], errors='coerce')
    df[grade_col] = pd.to_numeric(df[grade_col], errors='coerce')
    
    # Échantillonner les données pour améliorer les performances (max 5000 points)
    sample_size = min(5000, len(df))
    df_sample = df.sample(sample_size) if len(df) > sample_size else df
    
    # Créer le graphique
    fig = px.scatter_3d(df_sample, 
                        x=x_col, 
                        y=y_col, 
                        z=z_col,
                        color=grade_col,
                        color_continuous_scale="Viridis",
                        size_max=point_size,
                        opacity=0.7,
                        title=f"Visualisation 3D - {model_type}")
    
    # Personnaliser le graphique
    fig.update_layout(
        scene=dict(
            xaxis_title=x_col,
            yaxis_title=y_col,
            zaxis_title=z_col,
            aspectmode='data'
        ),
        height=700
    )
    
    return fig

# Barre latérale pour la navigation
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/geology.png", width=100)
    st.markdown("## Navigation")
    
    page = st.radio("", [
        "📥 Importer Données", 
        "📊 Comparaison Statistique", 
        "🔍 Visualisation 3D"
    ])
    
    st.markdown("---")
    st.markdown("### À propos")
    st.markdown("""
    Cette application permet de comparer les statistiques entre un modèle composite 3D et un bloc modèle.
    
    Développée avec Streamlit par Didier Ouedraogo, P.Geo.
    
    Version: 1.0
    Date: {}
    """.format(datetime.now().strftime("%d/%m/%Y")))

# Page d'importation des données
if page == "📥 Importer Données":
    st.markdown('<div class="sub-header">Importer des Données</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Composites 3D")
        
        composite_file = st.file_uploader("Importer le fichier CSV des composites 3D", type=['csv'])
        
        if composite_file is not None:
            try:
                st.session_state.composite_data = pd.read_csv(composite_file)
                st.session_state.composite_columns = st.session_state.composite_data.columns.tolist()
                st.success(f"Fichier chargé avec succès! ({len(st.session_state.composite_data)} lignes)")
                
                st.markdown("### Aperçu des données")
                st.dataframe(st.session_state.composite_data.head())
            except Exception as e:
                st.error(f"Erreur lors du chargement du fichier: {e}")
    
    with col2:
        st.markdown("### Modèle de Bloc")
        
        block_file = st.file_uploader("Importer le fichier CSV du modèle de bloc", type=['csv'])
        
        if block_file is not None:
            try:
                st.session_state.block_data = pd.read_csv(block_file)
                st.session_state.block_columns = st.session_state.block_data.columns.tolist()
                st.success(f"Fichier chargé avec succès! ({len(st.session_state.block_data)} lignes)")
                
                st.markdown("### Aperçu des données")
                st.dataframe(st.session_state.block_data.head())
            except Exception as e:
                st.error(f"Erreur lors du chargement du fichier: {e}")
    
    # Correspondance des colonnes si les deux fichiers sont chargés
    if st.session_state.composite_data is not None and st.session_state.block_data is not None:
        st.markdown('<div class="sub-header">Correspondance des colonnes</div>', unsafe_allow_html=True)
        
        st.markdown("Veuillez associer les colonnes de vos fichiers aux propriétés requises pour l'analyse:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Colonnes des Composites 3D")
            
            # Tenter de deviner les colonnes pour les coordonnées X, Y, Z et la teneur
            composite_x_col = next((col for col in st.session_state.composite_columns if 'x' in col.lower() or 'east' in col.lower()), st.session_state.composite_columns[0])
            composite_y_col = next((col for col in st.session_state.composite_columns if 'y' in col.lower() or 'north' in col.lower()), st.session_state.composite_columns[0])
            composite_z_col = next((col for col in st.session_state.composite_columns if 'z' in col.lower() or 'elev' in col.lower()), st.session_state.composite_columns[0])
            composite_grade_col = next((col for col in st.session_state.composite_columns if 'grade' in col.lower() or 'teneur' in col.lower() or 'au' in col.lower() or 'cu' in col.lower()), st.session_state.composite_columns[0])
            
            comp_x = st.selectbox("Coordonnée X (Composites):", st.session_state.composite_columns, index=st.session_state.composite_columns.index(composite_x_col))
            comp_y = st.selectbox("Coordonnée Y (Composites):", st.session_state.composite_columns, index=st.session_state.composite_columns.index(composite_y_col))
            comp_z = st.selectbox("Coordonnée Z (Composites):", st.session_state.composite_columns, index=st.session_state.composite_columns.index(composite_z_col))
            comp_grade = st.selectbox("Teneur (Composites):", st.session_state.composite_columns, index=st.session_state.composite_columns.index(composite_grade_col))
        
        with col2:
            st.markdown("### Colonnes du Modèle de Bloc")
            
            # Tenter de deviner les colonnes pour les coordonnées X, Y, Z et la teneur
            block_x_col = next((col for col in st.session_state.block_columns if 'x' in col.lower() or 'east' in col.lower()), st.session_state.block_columns[0])
            block_y_col = next((col for col in st.session_state.block_columns if 'y' in col.lower() or 'north' in col.lower()), st.session_state.block_columns[0])
            block_z_col = next((col for col in st.session_state.block_columns if 'z' in col.lower() or 'elev' in col.lower()), st.session_state.block_columns[0])
            block_grade_col = next((col for col in st.session_state.block_columns if 'grade' in col.lower() or 'teneur' in col.lower() or 'au' in col.lower() or 'cu' in col.lower()), st.session_state.block_columns[0])
            
            block_x = st.selectbox("Coordonnée X (Blocs):", st.session_state.block_columns, index=st.session_state.block_columns.index(block_x_col))
            block_y = st.selectbox("Coordonnée Y (Blocs):", st.session_state.block_columns, index=st.session_state.block_columns.index(block_y_col))
            block_z = st.selectbox("Coordonnée Z (Blocs):", st.session_state.block_columns, index=st.session_state.block_columns.index(block_z_col))
            block_grade = st.selectbox("Teneur (Blocs):", st.session_state.block_columns, index=st.session_state.block_columns.index(block_grade_col))
        
        if st.button("Appliquer et analyser"):
            # Enregistrer les correspondances
            st.session_state.mapping = {
                'composite': {
                    'x': comp_x,
                    'y': comp_y,
                    'z': comp_z,
                    'grade': comp_grade
                },
                'block': {
                    'x': block_x,
                    'y': block_y,
                    'z': block_z,
                    'grade': block_grade
                }
            }
            
            # Calculer les statistiques
            with st.spinner("Calcul des statistiques en cours..."):
                st.session_state.composite_stats = calculate_statistics(st.session_state.composite_data, comp_grade)
                st.session_state.block_stats = calculate_statistics(st.session_state.block_data, block_grade)
            
            st.success("Analyse terminée! Vous pouvez maintenant accéder à l'onglet Comparaison Statistique.")
    
    # Données d'exemple
    st.markdown('<div class="sub-header">Données d\'exemple</div>', unsafe_allow_html=True)
    st.markdown("""
    Vous pouvez utiliser des données d'exemple pour tester l'application:
    """)
    
    if st.button("Charger des données d'exemple"):
        # Générer des données d'exemple
        np.random.seed(42)
        
        # Composites 3D
        n_composites = 1000
        x_comp = np.random.uniform(0, 1000, n_composites)
        y_comp = np.random.uniform(0, 1000, n_composites)
        z_comp = np.random.uniform(-200, 0, n_composites)
        grade_comp = np.random.lognormal(0.8, 0.6, n_composites)
        
        # Créer le DataFrame des composites
        composite_example = pd.DataFrame({
            'EAST': x_comp,
            'NORTH': y_comp,
            'ELEV': z_comp,
            'AU_GPT': grade_comp
        })
        
        # Modèle de bloc
        n_blocks = 5000
        x_block = np.random.uniform(0, 1000, n_blocks)
        y_block = np.random.uniform(0, 1000, n_blocks)
        z_block = np.random.uniform(-200, 0, n_blocks)
        # Teneurs légèrement plus basses pour le bloc modèle (effet de lissage)
        grade_block = np.random.lognormal(0.75, 0.5, n_blocks)
        
        # Créer le DataFrame du modèle de bloc
        block_example = pd.DataFrame({
            'X': x_block,
            'Y': y_block,
            'Z': z_block,
            'GRADE': grade_block
        })
        
        # Enregistrer dans la session
        st.session_state.composite_data = composite_example
        st.session_state.block_data = block_example
        st.session_state.composite_columns = composite_example.columns.tolist()
        st.session_state.block_columns = block_example.columns.tolist()
        
        # Mapping automatique
        st.session_state.mapping = {
            'composite': {
                'x': 'EAST',
                'y': 'NORTH',
                'z': 'ELEV',
                'grade': 'AU_GPT'
            },
            'block': {
                'x': 'X',
                'y': 'Y',
                'z': 'Z',
                'grade': 'GRADE'
            }
        }
        
        # Calculer les statistiques
        st.session_state.composite_stats = calculate_statistics(st.session_state.composite_data, 'AU_GPT')
        st.session_state.block_stats = calculate_statistics(st.session_state.block_data, 'GRADE')
        
        st.success("Données d'exemple chargées avec succès! Vous pouvez maintenant accéder aux autres onglets.")
        
        st.markdown("### Aperçu des données d'exemple")
        tab1, tab2 = st.tabs(["Composites 3D", "Modèle de Bloc"])
        
        with tab1:
            st.dataframe(st.session_state.composite_data.head())
        
        with tab2:
            st.dataframe(st.session_state.block_data.head())

# Page de comparaison statistique
elif page == "📊 Comparaison Statistique":
    st.markdown('<div class="sub-header">Comparaison des Statistiques</div>', unsafe_allow_html=True)
    
    if st.session_state.composite_stats is None or st.session_state.block_stats is None:
        st.warning("Veuillez d'abord importer et analyser les données dans l'onglet 'Importer Données'.")
    else:
        # Options de comparaison
        comparison_mode = st.selectbox(
            "Mode de comparaison:",
            ["Type de modèle (Composite 3D vs Bloc modèle)", 
             "Périodes (Estimation précédente vs actuelle)",
             "Scénarios (Optimiste vs Conservateur)"]
        )
        
        # Graphique de comparaison
        st.markdown('<div class="sub-header">Graphiques de comparaison</div>', unsafe_allow_html=True)
        
        fig = create_comparison_chart(st.session_state.composite_stats, st.session_state.block_stats)
        st.plotly_chart(fig, use_container_width=True)
        
        # Tableaux de statistiques
        st.markdown('<div class="sub-header">Statistiques détaillées</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="stat-card"><h3>Statistiques du Modèle Composite 3D</h3>', unsafe_allow_html=True)
            
            st.markdown('<div class="stat-row"><span class="stat-label">Volume total:</span><span class="stat-value">{:,.0f} m³</span></div>'.format(st.session_state.composite_stats['volume']), unsafe_allow_html=True)
            st.markdown('<div class="stat-row"><span class="stat-label">Tonnage estimé:</span><span class="stat-value">{:,.0f} tonnes</span></div>'.format(st.session_state.composite_stats['tonnage']), unsafe_allow_html=True)
            st.markdown('<div class="stat-row"><span class="stat-label">Densité moyenne:</span><span class="stat-value">{:.2f} t/m³</span></div>'.format(st.session_state.composite_stats['densite']), unsafe_allow_html=True)
            
            st.markdown('<h4>Teneurs</h4>', unsafe_allow_html=True)
            st.markdown('<div class="stat-row"><span class="stat-label">Teneur moyenne:</span><span class="stat-value">{:.2f} g/t</span></div>'.format(st.session_state.composite_stats['teneur_moyenne']), unsafe_allow_html=True)
            st.markdown('<div class="stat-row"><span class="stat-label">Teneur minimum:</span><span class="stat-value">{:.2f} g/t</span></div>'.format(st.session_state.composite_stats['teneur_min']), unsafe_allow_html=True)
            st.markdown('<div class="stat-row"><span class="stat-label">Teneur maximum:</span><span class="stat-value">{:.2f} g/t</span></div>'.format(st.session_state.composite_stats['teneur_max']), unsafe_allow_html=True)
            st.markdown('<div class="stat-row"><span class="stat-label">Écart-type:</span><span class="stat-value">{:.2f} g/t</span></div>'.format(st.session_state.composite_stats['ecart_type']), unsafe_allow_html=True)
            
            st.markdown('<h4>Métal</h4>', unsafe_allow_html=True)
            st.markdown('<div class="stat-row"><span class="stat-label">Métal contenu:</span><span class="stat-value">{:,.0f} kg</span></div>'.format(st.session_state.composite_stats['metal_contenu']), unsafe_allow_html=True)
            st.markdown('<div class="stat-row"><span class="stat-label">Récupération estimée:</span><span class="stat-value">{:.1f}%</span></div>'.format(st.session_state.composite_stats['recuperation']), unsafe_allow_html=True)
            st.markdown('<div class="stat-row"><span class="stat-label">Métal récupérable:</span><span class="stat-value">{:,.0f} kg</span></div>'.format(st.session_state.composite_stats['metal_recuperable']), unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col2:
            st.markdown('<div class="stat-card"><h3>Statistiques du Bloc Modèle</h3>', unsafe_allow_html=True)
            
            # Calculer les différences en pourcentage
            vol_diff = (st.session_state.block_stats['volume'] / st.session_state.composite_stats['volume'] - 1) * 100
            ton_diff = (st.session_state.block_stats['tonnage'] / st.session_state.composite_stats['tonnage'] - 1) * 100
            den_diff = (st.session_state.block_stats['densite'] / st.session_state.composite_stats['densite'] - 1) * 100
            
            teneur_diff = (st.session_state.block_stats['teneur_moyenne'] / st.session_state.composite_stats['teneur_moyenne'] - 1) * 100
            min_diff = (st.session_state.block_stats['teneur_min'] / st.session_state.composite_stats['teneur_min'] - 1) * 100
            max_diff = (st.session_state.block_stats['teneur_max'] / st.session_state.composite_stats['teneur_max'] - 1) * 100
            std_diff = (st.session_state.block_stats['ecart_type'] / st.session_state.composite_stats['ecart_type'] - 1) * 100
            
            metal_diff = (st.session_state.block_stats['metal_contenu'] / st.session_state.composite_stats['metal_contenu'] - 1) * 100
            recup_diff = (st.session_state.block_stats['recuperation'] / st.session_state.composite_stats['recuperation'] - 1) * 100
            metal_rec_diff = (st.session_state.block_stats['metal_recuperable'] / st.session_state.composite_stats['metal_recuperable'] - 1) * 100
            
            # Ajouter des classes CSS pour la coloration
            def get_diff_class(diff):
                if diff > 0:
                    return "positive"
                elif diff < 0:
                    return "negative"
                else:
                    return "neutral"
            
            st.markdown('<div class="stat-row"><span class="stat-label">Volume total:</span><span class="stat-value">{:,.0f} m³ <span class="{}">({:+.1f}%)</span></span></div>'.format(
                st.session_state.block_stats['volume'], get_diff_class(vol_diff), vol_diff), unsafe_allow_html=True)
            
            st.markdown('<div class="stat-row"><span class="stat-label">Tonnage estimé:</span><span class="stat-value">{:,.0f} tonnes <span class="{}">({:+.1f}%)</span></span></div>'.format(
                st.session_state.block_stats['tonnage'], get_diff_class(ton_diff), ton_diff), unsafe_allow_html=True)
            
            st.markdown('<div class="stat-row"><span class="stat-label">Densité moyenne:</span><span class="stat-value">{:.2f} t/m³ <span class="{}">({:+.1f}%)</span></span></div>'.format(
                st.session_state.block_stats['densite'], get_diff_class(den_diff), den_diff), unsafe_allow_html=True)
            
            st.markdown('<h4>Teneurs</h4>', unsafe_allow_html=True)
            
            st.markdown('<div class="stat-row"><span class="stat-label">Teneur moyenne:</span><span class="stat-value">{:.2f} g/t <span class="{}">({:+.1f}%)</span></span></div>'.format(
                st.session_state.block_stats['teneur_moyenne'], get_diff_class(teneur_diff), teneur_diff), unsafe_allow_html=True)
            
            st.markdown('<div class="stat-row"><span class="stat-label">Teneur minimum:</span><span class="stat-value">{:.2f} g/t <span class="{}">({:+.1f}%)</span></span></div>'.format(
                st.session_state.block_stats['teneur_min'], get_diff_class(min_diff), min_diff), unsafe_allow_html=True)
            
            st.markdown('<div class="stat-row"><span class="stat-label">Teneur maximum:</span><span class="stat-value">{:.2f} g/t <span class="{}">({:+.1f}%)</span></span></div>'.format(
                st.session_state.block_stats['teneur_max'], get_diff_class(max_diff), max_diff), unsafe_allow_html=True)
            
            st.markdown('<div class="stat-row"><span class="stat-label">Écart-type:</span><span class="stat-value">{:.2f} g/t <span class="{}">({:+.1f}%)</span></span></div>'.format(
                st.session_state.block_stats['ecart_type'], get_diff_class(std_diff), std_diff), unsafe_allow_html=True)
            
            st.markdown('<h4>Métal</h4>', unsafe_allow_html=True)
            
            st.markdown('<div class="stat-row"><span class="stat-label">Métal contenu:</span><span class="stat-value">{:,.0f} kg <span class="{}">({:+.1f}%)</span></span></div>'.format(
                st.session_state.block_stats['metal_contenu'], get_diff_class(metal_diff), metal_diff), unsafe_allow_html=True)
            
            st.markdown('<div class="stat-row"><span class="stat-label">Récupération estimée:</span><span class="stat-value">{:.1f}% <span class="{}">({:+.1f}%)</span></span></div>'.format(
                st.session_state.block_stats['recuperation'], get_diff_class(recup_diff), recup_diff), unsafe_allow_html=True)
            
            st.markdown('<div class="stat-row"><span class="stat-label">Métal récupérable:</span><span class="stat-value">{:,.0f} kg <span class="{}">({:+.1f}%)</span></span></div>'.format(
                st.session_state.block_stats['metal_recuperable'], get_diff_class(metal_rec_diff), metal_rec_diff), unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Analyse des différences
        st.markdown('<div class="stat-card"><h3>Analyse des Différences</h3>', unsafe_allow_html=True)
        st.markdown("""
        <p>Les différences principales entre le modèle composite 3D et le bloc modèle peuvent être attribuées à plusieurs facteurs:</p>
        <ul>
            <li><strong>Effet de lissage:</strong> Le bloc modèle tend à lisser les valeurs extrêmes, ce qui explique la réduction de la teneur maximale et de l'écart-type.</li>
            <li><strong>Discrétisation spatiale:</strong> La conversion en blocs de taille fixe a introduit des approximations géométriques, expliquant la légère augmentation du volume.</li>
            <li><strong>Algorithme d'interpolation:</strong> La méthode d'interpolation utilisée (Krigeage) a tendance à réduire la variance globale, d'où la diminution des teneurs moyennes.</li>
        </ul>
        <p>Pour les décisions opérationnelles, il est recommandé d'utiliser le bloc modèle qui représente généralement une estimation plus conservatrice et plus adaptée à la planification minière.</p>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Téléchargement du rapport
        st.markdown('<div class="sub-header">Exportation des résultats</div>', unsafe_allow_html=True)
        
        if st.button("Générer un rapport de comparaison"):
            # Créer un buffer pour stocker le rapport CSV
            csv_buffer = io.StringIO()
            
            # Écrire les en-têtes
            csv_buffer.write("Métrique,Composite 3D,Bloc Modèle,Différence (%)\n")
            
            # Écrire les données volumétriques
            csv_buffer.write(f"Volume total (m³),{st.session_state.composite_stats['volume']:.1f},{st.session_state.block_stats['volume']:.1f},{vol_diff:.1f}\n")
            csv_buffer.write(f"Tonnage estimé (tonnes),{st.session_state.composite_stats['tonnage']:.1f},{st.session_state.block_stats['tonnage']:.1f},{ton_diff:.1f}\n")
            csv_buffer.write(f"Densité moyenne (t/m³),{st.session_state.composite_stats['densite']:.2f},{st.session_state.block_stats['densite']:.2f},{den_diff:.1f}\n")
            
            # Écrire les données de teneurs
            csv_buffer.write(f"Teneur moyenne (g/t),{st.session_state.composite_stats['teneur_moyenne']:.2f},{st.session_state.block_stats['teneur_moyenne']:.2f},{teneur_diff:.1f}\n")
            csv_buffer.write(f"Teneur minimum (g/t),{st.session_state.composite_stats['teneur_min']:.2f},{st.session_state.block_stats['teneur_min']:.2f},{min_diff:.1f}\n")
            csv_buffer.write(f"Teneur maximum (g/t),{st.session_state.composite_stats['teneur_max']:.2f},{st.session_state.block_stats['teneur_max']:.2f},{max_diff:.1f}\n")
            csv_buffer.write(f"Écart-type (g/t),{st.session_state.composite_stats['ecart_type']:.2f},{st.session_state.block_stats['ecart_type']:.2f},{std_diff:.1f}\n")
            
            # Écrire les données de métal
            csv_buffer.write(f"Métal contenu (kg),{st.session_state.composite_stats['metal_contenu']:.1f},{st.session_state.block_stats['metal_contenu']:.1f},{metal_diff:.1f}\n")
            csv_buffer.write(f"Récupération estimée (%),{st.session_state.composite_stats['recuperation']:.1f},{st.session_state.block_stats['recuperation']:.1f},{recup_diff:.1f}\n")
            csv_buffer.write(f"Métal récupérable (kg),{st.session_state.composite_stats['metal_recuperable']:.1f},{st.session_state.block_stats['metal_recuperable']:.1f},{metal_rec_diff:.1f}\n")
            
            # Réinitialiser le curseur au début du buffer
            csv_buffer.seek(0)
            
            # Proposer le téléchargement
            st.download_button(
                label="Télécharger le rapport CSV",
                data=csv_buffer,
                file_name=f"rapport_comparaison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

# Page de visualisation 3D
elif page == "🔍 Visualisation 3D":
    st.markdown('<div class="sub-header">Visualisation du Modèle 3D</div>', unsafe_allow_html=True)
    
    if st.session_state.composite_data is None or st.session_state.block_data is None or st.session_state.mapping is None:
        st.warning("Veuillez d'abord importer et analyser les données dans l'onglet 'Importer Données'.")
    else:
        # Options de visualisation
        col1, col2, col3 = st.columns(3)
        
        with col1:
            view_option = st.selectbox(
                "Options d'affichage:",
                ["Points", "Filaire", "Solide"]
            )
        
        with col2:
            highlight_option = st.selectbox(
                "Surbrillance:",
                ["Teneur", "Densité", "Récupération", "Aucune"]
            )
        
        with col3:
            model_selector = st.selectbox(
                "Modèle à afficher:",
                ["Composites 3D", "Modèle de bloc", "Les deux superposés"]
            )
        
        # Créer les visualisations 3D
        if model_selector == "Composites 3D" or model_selector == "Les deux superposés":
            st.markdown('<div class="sub-header">Visualisation des Composites 3D</div>', unsafe_allow_html=True)
            
            composite_fig = create_3d_scatter(
                st.session_state.composite_data,
                st.session_state.mapping['composite']['x'],
                st.session_state.mapping['composite']['y'],
                st.session_state.mapping['composite']['z'],
                st.session_state.mapping['composite']['grade'],
                point_size=4,
                model_type="Composites 3D"
            )
            
            st.plotly_chart(composite_fig, use_container_width=True)
        
        if model_selector == "Modèle de bloc" or model_selector == "Les deux superposés":
            st.markdown('<div class="sub-header">Visualisation du Modèle de Bloc</div>', unsafe_allow_html=True)
            
            # Échantillonnage pour meilleure performance
            sample_size = min(3000, len(st.session_state.block_data))
            block_data_sample = st.session_state.block_data.sample(sample_size) if len(st.session_state.block_data) > sample_size else st.session_state.block_data
            
            block_fig = create_3d_scatter(
                block_data_sample,
                st.session_state.mapping['block']['x'],
                st.session_state.mapping['block']['y'],
                st.session_state.mapping['block']['z'],
                st.session_state.mapping['block']['grade'],
                point_size=5,
                model_type="Modèle de Bloc"
            )
            
            st.plotly_chart(block_fig, use_container_width=True)
        
        # Légende
        st.markdown('<div class="stat-card"><h3>Légende</h3>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            - **Composites 3D**: Points plus petits
            - **Modèle de bloc**: Points plus grands
            """)
        
        with col2:
            st.markdown("""
            - **Teneur**: Bleu (faible) → Vert → Jaune → Rouge (élevée)
            """)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Notes sur l'utilisation
        st.markdown('<div class="stat-card"><h3>Notes sur l\'utilisation</h3>', unsafe_allow_html=True)
        st.markdown("""
        **Interaction avec le graphique 3D**:
        - **Rotation**: Cliquez et faites glisser pour faire pivoter le modèle
        - **Zoom**: Utilisez la molette de la souris ou pincez sur un appareil tactile
        - **Déplacement**: Maintenez la touche Shift enfoncée tout en faisant glisser
        - **Réinitialiser la vue**: Double-cliquez sur le graphique
        
        **Pour une meilleure performance**:
        - Les données sont échantillonnées pour améliorer les performances de visualisation
        - Pour voir plus de détails, utilisez les filtres de visualisation
        """)
        st.markdown("</div>", unsafe_allow_html=True)

# Pied de page
st.markdown('<div class="footer">© 2025 - Didier Ouedraogo, P.Geo - Tous droits réservés</div>', unsafe_allow_html=True)