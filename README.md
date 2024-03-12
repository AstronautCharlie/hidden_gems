# How do I use this? 

## Generate Playlists

### Set Environment Variables
Set `SPOTIPY_CLIENT_ID`, `SPOTIPY_CLIENT_SECRET`, and `SPOTIPY_REDIRECT_URL` environment variables to the appropriate values of your Spotify app (if you don't have one, create one first)

### Set Config Values (if desired)
Edit the `Config` class in `settings.py` to the values you desire. `SAMPLE_SIZE` is the number of tracks to be randomly sampled from the users top tracks (the time horizon of which is dictated by `TIME_RANGE`). ***NOTE*** this number cannot exceed 5 - the Spotify API will not accept recommendations with a seed track list of more than 5. You can set `TARGET_POPULARITY` and `MAX_POPULARITY` to whatever values you want between 0 and 100, though how Spotify calculates these are a black box 

### Set Playlist Values
Create 5 playlists and record their names/IDs in the `target_playlists.json` file in the following format:
```
[
    {
        "name": <name>,
        "id": <id>,
        "seed_tracks": []
    }, ...
]
```

### Run Script
Run `python find_hidden_gems.py`. This will populate the playlists created in the previous step with recommendations from random samples of your top songs. If this is not the first time you've run this command, it will test if you liked any of the recommendations from previous random samples, and credit those tracks with producing a good recommendation

## Listen to Playlists
Once you've generated the playlists, listen to them and like songs from them. Once you've listened to all of the playlists, wash, rinse, and repeat. Check out `track_scores.csv` to see which of your top tracks yielded the most likes. 

## Look at Scores
Check out `track_scores.csv` to see which seed tracks gave you the most liked songs. Don't edit this file manually! The code needs it to keep track of scores. 

# What to do next? 
Get recommendations based on artists as well as tracks