import spotipy
import os
import random
import pandas as pd
import json
import logging
from spotipy.oauth2 import SpotifyOAuth
from itertools import compress
from settings import Config

logging.basicConfig(level=logging.INFO)

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=Config.REQUIRED_SCOPE))

def find_hidden_gems(*, sample_size, target_popularity, max_popularity):
    # Get top tracks from user's library
    top_tracks = get_top_tracks()
    logging.info(f'Found {len(top_tracks)} top tracks to sample from')

    # Load target playlists
    with open('target_playlists.json', 'r') as file:
        target_playlists = json.load(file)
    file.close()

    # Score existing playlist before updating
    score_existing_playlists(target_playlists)

    # Create new playlists from randomly sampled seed tracks
    for i in range(len(target_playlists)):
        logging.info(f'On playlist {i+1}')
        sample_indices = random.sample(range(len(top_tracks)), sample_size)
        sample = [top_tracks[i] for i in sample_indices]
        recs = get_recommendations(sample, target_popularity=target_popularity, max_popularity=max_popularity)
        make_playlist_from_recs(recs, sample, target_playlists[i])
        update_seed_tracks(sample, target_playlists[i])

    # Write new target playlist info
    with open('target_playlists.json', 'w') as file:
        json.dump(target_playlists, file)
    file.close()

def get_top_tracks():
    response = sp.current_user_top_tracks(limit=50, time_range=Config.TIME_RANGE)
    top_tracks = response['items']
    while len(top_tracks) < response['total']:
        more_top_tracks = sp.current_user_top_tracks(limit=50, time_range=Config.TIME_RANGE, offset=len(top_tracks))['items']
        top_tracks += more_top_tracks
    return top_tracks    

def score_existing_playlists(target_playlists):
    # Check each playlist for liked tracks
    for i in range(len(target_playlists)):   
        num_liked_tracks = get_num_liked_tracks(target_playlists[i]['id'])
        add_score_to_tracks(target_playlists[i]['seed_tracks'], num_liked_tracks)
        
def get_num_liked_tracks(playlist_id):
    playlist = sp.playlist(playlist_id)
    track_ids = [track['track']['id'] for track in playlist['tracks']['items']]
    if len(track_ids) > 0: # Necessary to avoid error when playlist is empty on first execution
        num_liked_tracks = sum(sp.current_user_saved_tracks_contains(track_ids))
    else:
        return 0
    return num_liked_tracks    

def add_score_to_tracks(seed_tracks, score):
    if not os.path.exists('track_scores.csv'):
        with open('track_scores.csv', 'w+') as file:
            file.write('track_id,track_name,artist,liked_songs_yielded,times_served\n')
            file.close()
    score_df = pd.read_csv('track_scores.csv')
    for track in seed_tracks:
        if track['id'] in score_df.track_id:
            score_df.loc[score_df.track_id==track['id']]['liked_songs_yielded'] += score
            score_df.loc[score_df.track_id==track['id']]['times_served'] += 1
        else:
            new_row = pd.DataFrame.from_dict({'track_id': [track['id']], 'track_name': [track['name']], 'artist': [track['artist']], 'liked_songs_yielded': [score], 'times_served': [1]})
            score_df = pd.concat([score_df, new_row])
    score_df.to_csv('track_scores.csv', index=False)

def get_recommendations(seed_tracks, target_popularity, max_popularity):
    logging.info(f'getting recommendations from seed tracks {[track['name'] for track in seed_tracks]}')
    recs = []
    while len(recs) < 20:
        response = sp.recommendations(seed_tracks=[track['id'] for track in seed_tracks], target_popularity=target_popularity, max_popularity=max_popularity)
        recommended_tracks = response['tracks']
        logging.info(f'got recommendations {[[track['name'], track['artists'][0]['name']] for track in recommended_tracks]}')
        recommended_track_ids = [track['id'] for track in recommended_tracks]
        is_already_liked = sp.current_user_saved_tracks_contains(recommended_track_ids)
        is_new = [not liked for liked in is_already_liked]
        already_liked_tracks = list(compress(recommended_tracks, is_already_liked))
        if len(already_liked_tracks) > 0: 
            logging.info(f'removing already liked songs {[track['name'] for track in already_liked_tracks]}')
        recs += list(compress(recommended_tracks, is_new))
    recs = recs[:20]
    return recs

def make_playlist_from_recs(recs, seed_tracks, playlist):
    # Remove all tracks from playlist and add recs
    sp.playlist_replace_items(playlist['id'], [track['id'] for track in recs])
    track_names = [track['name'] for track in seed_tracks]
    track_artists = [[artist['name'] for artist in track['artists']] for track in seed_tracks]
    track_artists = [', '.join(artists) for artists in track_artists]
    track_info = [f'{track_names[i]} by {track_artists[i]}' for i in range(len(track_names))]
    new_description = f'Playlist created from seed tracks {" - ".join([track for track in track_info])}'
    sp.playlist_change_details(playlist['id'], description=new_description)

def update_seed_tracks(seed_tracks, playlist):
    seed_track_records = []
    for track in seed_tracks:
        artists = ', '.join([artist['name'] for artist in track['artists']])
        seed_track_records.append({'id': track['id'], 'name': track['name'], 'artist': artists})
    playlist['seed_tracks'] = seed_track_records

if __name__ == '__main__':
    find_hidden_gems(sample_size=Config.SAMPLE_SIZE, target_popularity=Config.TARGET_POPULARITY, max_popularity=Config.MAX_POPULARITY)