class Config:
    SEED_TYPES = ['track', 'artist']
    TIME_RANGES = ['short_term', 'medium_term']
    TARGET_POPULARITY = 20
    MAX_POPULARITY = 40
    SAMPLE_SIZE = 5 # How many tracks/artists to sample from top tracks/artists
    RECS_PER_SAMPLE = 5 # Number of recommendations to sample. Can't be higher than 100 due to Spotify API limitations
    REQUIRED_SCOPE = 'playlist-modify-private playlist-modify-public playlist-read-private user-library-read user-top-read'