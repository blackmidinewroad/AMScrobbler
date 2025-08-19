class Song:
    """Represents song that currently visible in Apple Music app.
    Has 2 main attributes - `metadata`: dict with information about the song (e.g. title, artist, artwork)
    and `state`: dict with the state of the song in AM app (e.g. playing, playtime).
    """

    def __init__(self):
        self.metadata = {}
        self.reset_metadata()

        self.state = {}
        self.reset_state()

    def __str__(self):
        return self.metadata['id']

    def reset_metadata(self) -> None:
        self.metadata.update(
            {
                'title': '',
                'artist': '',
                'id': '',
                'album': '',
                'artwork': None,
                'duration': 0,
                'is_app_duration': False,
                'playing': False,
            }
        )

    def reset_state(self) -> None:
        self.state.update(
            {
                'title': '',
                'artist': '',
                'id': '',
                'album': '',
                'artwork': None,
                'duration': 0,
                'is_app_duration': False,
                'playtime': 0,
                'started_playing': False,
                'started_playing_timestamp': None,
                'last_time_played': None,
                'playing': False,
            }
        )

    def is_same_song(self) -> bool:
        return self.metadata['id'] == self.state['id']

    def is_scrobbable(self) -> bool:
        """Check if it is possible to scrobble a song (it exists and playtime is more than a half of it's runtime)."""

        return self.state['id'] and (self.state['playtime'] >= self.state['duration'] // 2)

    def is_rescrobbable(self) -> bool:
        """Check if a song is rescrobbable - playtime is more than it's duration and duration is from the AM app
        (duration from other sources is not very accurate so rescrobbling can give unexpected results).
        """

        return (self.state['playtime'] > self.state['duration']) and self.state['is_app_duration']

    def increase_playtime(self, cur_time: int) -> None:
        """If last time checked song was playing - increase playtime by time now minus time then."""

        if self.state['last_time_played']:
            self.state['playtime'] += cur_time - self.state['last_time_played']
