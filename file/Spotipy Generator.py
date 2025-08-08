# -*- coding: utf-8 -*-

"""
Ce script Python utilise l'API Spotify pour créer une playlist de recommandations
basée sur les artistes les plus écoutés d'un utilisateur.

Pour que ce script fonctionne, vous devez d'abord :
1. Installer la bibliothèque spotipy :
   pip install spotipy

2. Créer une application sur le Spotify Developer Dashboard :
   a. Allez sur https://developer.spotify.com/dashboard/
   b. Connectez-vous et cliquez sur "CREATE AN APP".
   c. Donnez un nom et une description à votre application.
   d. Une fois l'application créée, vous obtiendrez un "Client ID" et un "Client Secret".
   e. Allez dans les paramètres de l'application ("Edit Settings").
   f. Dans le champ "Redirect URIs", ajoutez exactement : http://127.0.0.1:8888/callback
      (Note : Spotify n'accepte plus "localhost", il faut utiliser l'adresse IP 127.0.0.1)
   g. Sauvegardez les changements.

3. Lancez le script. Il vous demandera votre Client ID et votre Client Secret.
"""

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import getpass

# --- CONFIGURATION ---
# L'adresse de redirection est maintenant la seule constante de configuration.
# Spotify a mis à jour ses exigences. "localhost" n'est plus accepté.
# Il faut utiliser l'adresse IP de loopback explicite.
REDIRECT_URI = "http://127.0.0.1:8888/callback"

# Les "scopes" définissent les permissions que votre script demande à l'utilisateur.
SCOPES = "user-top-read playlist-modify-public playlist-modify-private"

def authenticate_spotify(client_id, client_secret):
    """
    Gère l'authentification de l'utilisateur via OAuth2.
    La première fois que vous lancez le script, une page de votre navigateur
    s'ouvrira pour vous demander d'autoriser l'application.
    """
    print("Authentification auprès de Spotify...")
    try:
        sp_oauth = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=REDIRECT_URI,
            scope=SCOPES
        )
        # Crée un objet Spotipy authentifié
        sp = spotipy.Spotify(auth_manager=sp_oauth)
        print("Authentification réussie !")
        return sp
    except Exception as e:
        print(f"Erreur lors de l'authentification : {e}")
        print("Veuillez vérifier votre Client ID, Client Secret et Redirect URI.")
        return None

def get_top_artists(sp, limit=5, time_range='medium_term'):
    """
    Récupère les artistes les plus écoutés de l'utilisateur.
    - time_range peut être 'short_term' (4 sem.), 'medium_term' (6 mois), 'long_term' (plusieurs années).
    """
    print(f"\nRécupération de vos {limit} artistes préférés...")
    try:
        results = sp.current_user_top_artists(time_range=time_range, limit=limit)
        top_artists = results['items']
        artist_ids = [artist['id'] for artist in top_artists]
        artist_names = [artist['name'] for artist in top_artists]
        
        print("Vos artistes favoris sont : " + ", ".join(artist_names))
        return artist_ids
    except Exception as e:
        print(f"Erreur lors de la récupération des artistes : {e}")
        return []

def get_recommendations(sp, seed_artists, limit=20):
    """
    Obtient des recommandations de titres basées sur des artistes "graines" (seeds).
    """
    print("\nRecherche de recommandations musicales...")
    if not seed_artists:
        print("Aucun artiste de base fourni, impossible d'obtenir des recommandations.")
        return []
    
    try:
        recommendations = sp.recommendations(seed_artists=seed_artists, limit=limit)
        track_ids = [track['id'] for track in recommendations['tracks']]
        print(f"{len(track_ids)} recommandations trouvées.")
        return track_ids
    except Exception as e:
        print(f"Erreur lors de la recherche de recommandations : {e}")
        return []

def create_playlist(sp, user_id, track_ids, playlist_name="Recommandations Python"):
    """
    Crée une nouvelle playlist et y ajoute les titres recommandés.
    """
    if not track_ids:
        print("Aucun titre à ajouter, la playlist ne sera pas créée.")
        return

    print(f"\nCréation de la playlist '{playlist_name}'...")
    try:
        # Crée une playlist privée
        playlist = sp.user_playlist_create(
            user=user_id,
            name=playlist_name,
            public=False,
            description="Playlist générée par un script Python avec Spotipy."
        )
        playlist_id = playlist['id']
        
        # Ajoute les titres à la playlist
        sp.playlist_add_items(playlist_id, track_ids)
        
        print("-" * 40)
        print(f"🎉 Succès ! La playlist '{playlist_name}' a été créée sur votre compte Spotify.")
        print(f"URL de la playlist : {playlist['external_urls']['spotify']}")
        print("-" * 40)

    except Exception as e:
        print(f"Erreur lors de la création de la playlist : {e}")


def main():
    """
    Fonction principale qui orchestre le processus.
    """
    print("--- Lancement du générateur de playlist Spotify ---")
    
    # Demande à l'utilisateur de saisir ses identifiants
    client_id = input("Veuillez entrer votre Client ID Spotify : ")
    # getpass cache la saisie pour plus de sécurité
    client_secret = getpass.getpass("Veuillez entrer votre Client Secret Spotify : ")

    if not client_id or not client_secret:
        print("\nERREUR : Le Client ID et le Client Secret ne peuvent pas être vides.")
        return

    # 1. Authentification
    sp = authenticate_spotify(client_id, client_secret)
    if not sp:
        return

    # 2. Récupérer l'ID de l'utilisateur actuel
    try:
        user_info = sp.current_user()
        user_id = user_info['id']
        print(f"\nConnecté en tant que : {user_info['display_name']} (ID: {user_id})")
    except Exception as e:
        print(f"Impossible de récupérer les informations de l'utilisateur : {e}")
        return

    # 3. Obtenir les artistes favoris pour les utiliser comme base
    # On prend les 5 artistes les plus écoutés des 6 derniers mois
    top_artist_ids = get_top_artists(sp, limit=5, time_range='medium_term')

    # 4. Obtenir des recommandations basées sur ces artistes
    recommended_track_ids = get_recommendations(sp, seed_artists=top_artist_ids, limit=25)

    # 5. Créer la playlist
    create_playlist(sp, user_id, recommended_track_ids, playlist_name="Découvertes Python 🤖")


if __name__ == "__main__":
    main()
