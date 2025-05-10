import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import os
import io

# Dossiers nécessaires
dossier_memes = "dossier_memes"
dossier_partage = "partage"
font_dir = "fonts"

os.makedirs(dossier_memes, exist_ok=True)
os.makedirs(dossier_partage, exist_ok=True)

# Lister les polices
font_files = [f for f in os.listdir(font_dir) if f.endswith(".ttf")] if os.path.exists(font_dir) else []

# Fonction pour afficher les liens de partage (version avec bouton natif de copie)
def display_share_links(meme_filename, base_meme_directory="dossier_memes"):
    """Affiche le lien de partage direct pour un mème donné, avec un bouton natif de copie Streamlit."""
    if 'SPACE_HOST' in os.environ:
        base_url = f"https://{os.environ['SPACE_HOST']}"
        full_meme_url = f"{base_url}/{base_meme_directory}/{meme_filename}"
        st.markdown(f"**Lien direct du mème :**")
        st.copy_to_clipboard(full_meme_url, "📋 Copier le lien pour partager")
    else:
        local_path = os.path.abspath(os.path.join(base_meme_directory, meme_filename))
        st.info(f"Application non hébergée sur HF Spaces. Lien local (pour votre machine) :")
        st.code(local_path)
        st.warning("Pour un partage web facile, hébergez sur Hugging Face Spaces.")

def add_text_to_image(image, text, position, font_path, font_size, color):
    img = image.copy()
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        st.warning(f"Police {font_path} non trouvée. Utilisation de la police système par défaut.")
        font = ImageFont.load_default() # La taille de la police par défaut n'est pas contrôlable

    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (img.width - text_width) / 2
    y = 10 if position == "Haut" else img.height - text_height - 10
    draw.text((x, y), text, font=font, fill=color, stroke_width=2, stroke_fill="black")
    return img

# Interface Streamlit avec onglets
#st.image("logo.jpeg", width=150)
tab1, tab2 = st.tabs(["🎨 Générateur", "🖼️ Galerie & Partage"])

with tab1:
    st.header("Générateur de Mèmes")

    uploaded_image = st.file_uploader("1. Téléverser une image :", type=["jpg", "png", "jpeg"], key="gen_uploader")

    if uploaded_image:
        image = Image.open(uploaded_image)
        img_width, img_height = image.size
        st.image(image, caption="Image originale", use_container_width=True)

        texte_meme = st.text_input("2. Ajoutez votre texte ici :", placeholder="Texte du mème", key="gen_text")

        font_path_to_use = "arial.ttf" # Police par défaut si aucune n'est trouvée/sélectionnée
        if font_files:
            selected_font = st.selectbox("3. Choisissez une police :", font_files, key="gen_font_select")
            font_path_to_use = os.path.join(font_dir, selected_font)
        else:
            st.warning("Aucune police trouvée dans le dossier 'fonts'. Utilisation d'une police par défaut. Ajoutez des .ttf dans 'fonts' pour plus d'options.")
            
        position = st.radio("4. Position du texte :", ["Haut", "Bas"], key="gen_position")
        color = st.color_picker("5. Choisissez la couleur du texte :", "#FFFFFF", key="gen_color_picker")

        if st.button("🚀 Générer le mème", key="gen_button"):
            font_size = int(img_height * 0.1)
            meme = add_text_to_image(image, texte_meme, position, font_path_to_use, font_size, color)

            st.subheader("Mème Généré")
            st.image(meme, caption="Mème généré", use_container_width=True)

            base_filename = os.path.splitext(uploaded_image.name)[0]
            safe_base_filename = "".join(c if c.isalnum() else "_" for c in base_filename)
            meme_count = len([name for name in os.listdir(dossier_memes) if os.path.isfile(os.path.join(dossier_memes, name))])
            meme_filename = f"{safe_base_filename}_meme_{meme_count + 1}.png"
            meme_path = os.path.join(dossier_memes, meme_filename)

            try:
                meme.save(meme_path)
                st.success(f"Mème sauvegardé dans la galerie : {meme_filename}")
                # Afficher le lien de partage directement après la génération
                with st.expander("Options de partage du nouveau mème", expanded=True):
                    display_share_links(meme_filename, dossier_memes)
            except Exception as e:
                st.error(f"Erreur lors de la sauvegarde : {e}")

            buf = io.BytesIO()
            meme.save(buf, format="PNG")
            st.download_button(
                label="💾 Télécharger le mème",
                data=buf.getvalue(),
                file_name=meme_filename, # Utiliser le nom de fichier correct
                mime="image/png",
                key="gen_download_button"
            )

with tab2:
    st.header("Galerie de Mèmes & Partage")

    images_in_gallery = [
        f for f in os.listdir(dossier_memes) 
        if os.path.isfile(os.path.join(dossier_memes, f)) 
        and f.lower().endswith(('.png', '.jpg', '.jpeg'))
        and not f.startswith('.')
    ]
    images_in_gallery.sort(key=lambda name: os.path.getmtime(os.path.join(dossier_memes, name)), reverse=True)

    if images_in_gallery:
        st.write(f"Il y a {len(images_in_gallery)} mème(s) dans la galerie.")
        
        # Affichage en grille
        num_cols = st.slider("Nombre de colonnes pour la galerie:", 1, 5, 3, key="gallery_cols_slider")
        cols = st.columns(num_cols)
        for idx, img_name in enumerate(images_in_gallery):
            col_index = idx % num_cols
            with cols[col_index]:
                try:
                    meme_path_gallery = os.path.join(dossier_memes, img_name)
                    st.image(meme_path_gallery, caption=img_name, use_container_width=True)
                    # Utiliser un expander pour les options de partage de chaque image
                    with st.expander(f"Partager {img_name[:20]}..."):
                        display_share_links(img_name, dossier_memes)
                except Exception as e:
                    cols[col_index].error(f"Erreur affichage {img_name}: {e}")
    else:
       st.info("La galerie est vide. Générez un mème pour commencer.")
    
    st.subheader("Partager sur les réseaux sociaux (lien générique)")
    # Ces boutons partagent un lien générique, pas le mème spécifique pour l'instant.
    # Pour partager le mème spécifique, l'URL du mème devrait être passée à ces fonctions.
    col1_social, col2_social, col3_social = st.columns(3)
    with col1_social:
        if st.button("💬 Partager sur WhatsApp", key="whatsapp_share"):
            # Il faudrait encoder l'URL du mème ici
            st.markdown(f'<meta http-equiv="refresh" content="0;URL=https://wa.me/?text=Regardez%20ce%20mème!">', unsafe_allow_html=True)
    with col2_social:
        if st.button("🐦 Partager sur Twitter", key="twitter_share"):
            st.markdown(f'<meta http-equiv="refresh" content="0;URL=https://twitter.com/intent/tweet?text=Regardez%20ce%20mème!">', unsafe_allow_html=True)
    with col3_social:
        if st.button("📘 Partager sur Facebook", key="facebook_share"):
            st.markdown(f'<meta http-equiv="refresh" content="0;URL=https://www.facebook.com/sharer/sharer.php?u=VOTRE_URL_DE_MEME_ICI">', unsafe_allow_html=True)
