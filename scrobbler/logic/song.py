class Song:
    """Represents a song currently visible in the Apple Music app.

    Attributes:
        metadata (dict): Information about the song (e.g., title, artist, artwork, duration).
        state (dict): Current state of the song in the Apple Music app (e.g., playing status, playtime, timestamps).
    """

    def __init__(self):
        self.metadata = {}
        self.reset_metadata()

        self.state = {}
        self.reset_state()

    def __str__(self):
        return self.metadata.get('id', '')

    def reset_metadata(self) -> None:
        """Reset metadata to default empty values."""

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
        """Reset state to default empty values."""

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
        """Check if the current song metadata matches the last known state.

        Returns:
            bool: True if the song IDs match, False otherwise.
        """

        return self.metadata.get('id', '') == self.state.get('id', '')

    def is_scrobbable(self) -> bool:
        """Check if the song is eligible for scrobbling.

        Conditions:
        - The song must have a valid ID.
        - The playtime must be at least half of the song's duration.

        Returns:
            bool: True if scrobble conditions are met, False otherwise.
        """

        return self.state.get('id', '') and self.state.get('playtime', 0) >= self.state.get('duration', 0) // 2

    def is_rescrobbable(self) -> bool:
        """Check if the song is eligible for rescrobbling.

        Conditions:
        - Playtime is longer than the song's duration.
        - Duration comes from the Apple Music app (accurate source).

        Returns:
            bool: True if rescrobble conditions are met, False otherwise.
        """

        return self.state.get('is_app_duration', False) and self.state.get('playtime', 0) > self.state.get('duration', 0)

    def increase_playtime(self, cur_time: int) -> None:
        """Increase playtime if the song was previously playing.

        Args:
            cur_time (int): Current timestamp (e.g., time.time()).

        Notes:
            - Uses 'last_time_played' to calculate elapsed time since last check.
        """

        if self.state.get('last_time_played'):
            self.state['playtime'] += cur_time - self.state['last_time_played']
