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

def find_hidden_gems(*, sample_type, time_range, i):
    logging.info(f'creating playlist from top {sample_type}s in {time_range.replace('_', ' ')} range')
    # Get top entities from user
    if sample_type == 'track': 
        f = sp.current_user_top_tracks
    elif sample_type == 'artist': 
        f = sp.current_user_top_artists
    else:
        raise ValueError(f'Invalid sample type {sample_type}')
    response = f(limit=50, time_range=time_range)
    total = response['total']
    top_entities = response['items']
    while len(top_entities) < total:
        more_top_entities = f(limit=50, time_range=time_range, offset=len(top_entities))['items']
        top_entities += more_top_entities

    logging.info(f'sampling from {total} {sample_type}s')
    # Randomly sample from top entities
    sample_indices = random.sample(range(len(top_entities)), Config.SAMPLE_SIZE)
    sample_entities = [top_entities[i] for i in sample_indices]
    logging.info(f'sample_entities: {[s["name"] for s in sample_entities]}')

    # Get recommendations from sampled entities, keeping track of which 
    # entity yielded each recommendation
    recs = {}
    #attributions = {}
    #recs = [] 
    for entity in sample_entities:
        entity_recs = get_recommendations(entity, sample_type, Config.RECS_PER_SAMPLE)
        logging.info(f'recommendations for seed {entity["name"]}: {[(rec["name"], rec["popularity"]) for rec in entity_recs]}')
        for rec in entity_recs:
            recs[rec['uri']] = entity
        #    attributions[rec['id']] = [entity['id']]
        #recs.extend(entity_recs)

    # Create new playlist from recommendations
    new_playlist_info = create_seeded_playlist(list(recs.keys()), sample_entities, sample_type, i)

    # Record recommendation attributions for playlist
    if not os.path.exists('attributions.json'):
        with open('attributions.json', 'w+') as file:
            file.write('{}')
            file.close()
    contents = json.load(open('attributions.json', 'r'))
    contents.update(recs)
    with open('attributions.json', 'w+') as file:
        file.write(json.dumps(contents))

    return new_playlist_info

def get_recommendations(sample, sample_type, recs_per_sample):
    kwargs = {'target_popularity': Config.TARGET_POPULARITY, 'max_popularity': Config.MAX_POPULARITY} 
    if sample_type == 'track':
        kwargs['seed_tracks'] = [sample['id']] 
    elif sample_type == 'artist':
        kwargs['seed_artists'] = [sample['id']] 
    recs = []
    while len(recs) < recs_per_sample:
        response = sp.recommendations(**kwargs)
        recommended_tracks = response['tracks']
        recommended_track_ids = [track['id'] for track in recommended_tracks]
        is_already_liked = sp.current_user_saved_tracks_contains(recommended_track_ids)
        is_new = [not liked for liked in is_already_liked]
        already_liked_tracks = list(compress(recommended_tracks, is_already_liked))
        if len(already_liked_tracks) > 0: 
            logging.info(f'removing already liked songs {[track['name'] for track in already_liked_tracks]}')
        recs += list(compress(recommended_tracks, is_new))
    recs = recs[:recs_per_sample]
    return recs

def create_seeded_playlist(track_uris, seed_entities, sample_type, i):
    name = f'Hidden Gems - #{i}'

    # Create description
    if sample_type == 'track':
        seed_names = [track['name'] for track in seed_entities]
        seed_artists = [[artist['name'] for artist in track['artists']] for track in seed_entities]
        seed_artists = [', '.join(artists) for artists in seed_artists]
        seed_info = [f'{seed_names[i]} by {seed_artists[i]}' for i in range(len(seed_names))]
        description = f'Playlist created from seed tracks {" - ".join([track for track in seed_info])}'
    elif sample_type == 'artist': 
        seed_names = [artist['name'] for artist in seed_entities]
        description = f'Playlist created from seed artists {", ".join([artist for artist in seed_names])}'

    new_playlist_info = sp.user_playlist_create(sp.me()['id'], name, public=False, description=description)

    # Add tracks to playlist
    sp.playlist_add_items(new_playlist_info['id'], track_uris)

    return new_playlist_info

def score_old_playlists():
    try:
        attributions = json.load(open('attributions.json', 'r'))
    except FileNotFoundError:
        logging.warning(f'No attribution file found - skipping scoring')
        return
    recs = list(attributions.keys())
    chunked_recs = [recs[i:i+50] for i in range(0, len(recs), 50)]
    liked_recs = []
    for chunk in chunked_recs:
        logging.info(f'checking recs {chunk}')
        is_liked_rec = sp.current_user_saved_tracks_contains(chunk)
        liked_recs.extend(list(compress(chunk, is_liked_rec)))
        logging.info(f'liked_recs: {liked_recs}')
        add_score_to_seeds(liked_recs, attributions)
    """
    # Separate attributions into those by track and those by artist
    track_attributions = []
    artist_attributions = []
    for rec, seed in attributions.items():
        if seed['type'] == 'track': 
            track_attributions.append({rec: seed})
        elif seed['type'] == 'artist': 
            artist_attributions.append({rec: seed})
        else:
            logging.error(f'Unexpected seed type: {seed["type"]}')
    
    # Add score to track seeds
    song_seeded_recs = list(track_attributions.keys())
    is_liked_rec = sp.current_user_saved_tracks_contains(song_seeded_recs)
    liked_recs = list(compress(song_seeded_recs, is_liked_rec))
    add_score_to_track_seeds(liked_recs, track_attributions)

    # Add score to artist seeds


    # Check each playlist for liked tracks
    for i in range(len(target_playlists)):   
        num_liked_tracks = get_num_liked_tracks(target_playlists[i]['id'])
        add_score_to_tracks(target_playlists[i]['seed_tracks'], num_liked_tracks)
    """

def add_score_to_seeds(liked_recs, attributions):
    # Todo: 
    # - sum up number of liked recs for each seed, including 0s
    # - add number of liked recs to score for each seed
    track_attributions = {}
    artist_attributions = {}

    # Sort attributions by seed type
    for liked_rec in liked_recs:
        if attributions[liked_rec]['type'] == 'track':
            track_attributions.update({liked_rec: attributions[liked_rec]})
        elif attributions[liked_rec]['type'] == 'artist':
            artist_attributions.update({liked_rec: attributions[liked_rec]})
        else:
            logging.error(f'Unexpected seed type: {attributions[liked_rec]["type"]}')
    
    # Add score to track seeds
    if not os.path.exists('track_seed_scores.csv'):
        track_score_df = pd.DataFrame(columns=['track_id', 'track_name', 'artist', 'liked_songs_yielded', 'times_served'])
    else:
        track_score_df = pd.read_csv('track_seed_scores.csv')
    for seed_track in list(track_attributions.values()):
        logging.info(f'seed track {seed_track["name"]} getting +1')
        if seed_track['id'] in track_score_df.track_id:
            track_score_df.loc[track_score_df.track_id==seed_track]['liked_songs_yielded'] += 1
            track_score_df.loc[track_score_df.track_id==seed_track]['times_served'] += 1
        else:
            new_row = pd.DataFrame.from_dict({'track_id': [seed_track['id']], 'track_name': [seed_track['name']], 'artist': [seed_track['artist']], 'liked_songs_yielded': [1], 'times_served': [1]})
            track_score_df = pd.concat([track_score_df, new_row])
    track_score_df.to_csv('track_seed_scores.csv', index=False)

    # Add score to artist seeds
    if not os.path.exists('artist_seed_scores.csv'):
        artist_score_df = pd.DataFrame(columns=['artist_id', 'artist_name', 'liked_songs_yielded', 'times_served'])
    else:
        artist_score_df = pd.read_csv('artist_seed_scores.csv')
    for seed_artist in list(artist_attributions.values()):
        logging.info(f'seed artist {seed_artist["name"]} getting +1')
        if seed_artist['id'] in artist_score_df.artist_id:
            artist_score_df.loc[artist_score_df.artist_id==seed_artist]['liked_songs_yielded'] += 1
            artist_score_df.loc[artist_score_df.artist_id==seed_artist]['times_served'] += 1
        else:
            new_row = pd.DataFrame.from_dict({'artist_id': [seed_artist['id']], 'artist_name': [seed_artist['name']], 'liked_songs_yielded': [1], 'times_served': [1]})
            artist_score_df = pd.concat([artist_score_df, new_row])

def cleanup():
    remove_old_playlists
    if os.path.exists('attributions.json'):
        os.remove('attributions.json')

def remove_old_playlists():
    try:
        with open('playlist_info.json', 'r') as file:
            playlists = json.load(file)
            for playlist in playlists:
                logging.info(f'deleting playlist {playlist["id "]}')
                sp.user_playlist_unfollow(sp.me()['id'], playlist['id'])
            file.close()
    except Exception as err:
        logging.warning(f'failed to delete old playlists :: {err}')

if __name__ == '__main__':
    score_old_playlists()
    cleanup()

    new_playlists = []
    i = 1
    for seed_type in Config.SEED_TYPES:
        for time_range in Config.TIME_RANGES:
            new_playlist_info = find_hidden_gems(sample_type=seed_type, time_range=time_range, i=i)
            new_playlists.append(new_playlist_info)
            i += 1
    
    with open('playlist_info.json', 'w+') as file:
        file.write(json.dumps(new_playlists))
        file.close()