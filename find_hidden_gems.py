import spotipy
import os
import random
from spotipy.oauth2 import SpotifyClientCredentials

os.environ['SPOTIPY_CLIENT_ID'] = '9d88e28b87f74a918458fad03748a14d'
os.environ['SPOTIPY_CLIENT_SECRET'] = '6661ad45ea274f96bb536799d6b76127'
os.environ['SPOTIPY_REDIRECT_URI'] = 'http://localhost:8888/callback'

target_playlists = [
    {
        'name': 'Hidden Gems #1',
        'id': '72Fpw57jgSZ286fNcdPR4K'
    }, {
        'name': 'Hidden Gems #2',
        'id': '1NnNrUGOEDOjm6jH33i74d'
    }, {
        'name': 'Hidden Gems #3', 
        'id': '7DltQr0lk7uwv3WZQu1SB3'
    }, {
        'name': 'Hidden Gems #4', 
        'id': '0n0DHOEcyj1fKaWBAcgBNY'
    }, {
        'name': 'Hidden Gems #5', 
        'id': '1OZIbuWIQ5GKrY8oox3XCz'
    }
]

def find_hidden_gems(track_ids, sample_size=5, target_popularity=20, max_popularity=40):
    # Score existing playlist before updating

    for i in range(len(target_playlists)):
        sample = random.sample(track_ids, sample_size)
        recs = get_recommendations(sample, target_popularity=target_popularity, max_popularity=max_popularity)
        make_playlist_from_recs(recs, target_playlists[i])

def get_recommendations(seed_tracks, target_popularity=20, max_popularity=40):
    sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
    recs = sp.recommendations(seed_tracks, target_popularity=target_popularity, max_popularity=max_popularity)
    return recs

seed_tracks = ['0kA01uE0B81UqJiNGjfxW1']#, '3oak8YSZn0sVs5u4BuEKtR', '0GO8y8jQk1PkHzS31d699N', '2McT9smAArZgp6jKdLnL0X', '3RznzRnsl8mzP63l4AF2M7', '7pyHJ5v2KpWHJuaELENETu', '4SNREfGS7BWkWaejcexMII', '0nJdcCGiQ1mKKTq8yaUCiH', '3kzbkZtBqamTgyO31DO1Sn', '2S3aGBv6UM6elRwOZJLPFr']
find_hidden_gems(seed_tracks)