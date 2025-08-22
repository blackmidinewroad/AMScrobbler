import customtkinter as ctk
from PIL import Image

from scrobbler.utils import make_circle


class GIFLabel(ctk.CTkLabel):
    """A label widget that displays and animates a GIF image frame by frame."""

    def __init__(self, master, gif: Image.Image, crop_circle: bool = False, **kwargs):
        kwargs.setdefault('width', gif.width)
        kwargs.setdefault('height', gif.height)
        kwargs.setdefault('text', '')

        super().__init__(master, **kwargs)

        self.gif = gif
        self.crop_circle = crop_circle
        self.duration = gif.info['duration']
        self.frames = []
        self._set_frames()

    def _set_frames(self) -> None:
        """Extract all frames of the GIF and store them as CTkImages."""

        for frame in range(self.gif.n_frames):
            self.gif.seek(frame)
            if self.crop_circle:
                self.frames.append(ctk.CTkImage(make_circle(self.gif).copy(), size=(self['width'], self['height'])))
            else:
                self.frames.append(ctk.CTkImage(self.gif.copy(), size=(self['width'], self['height'])))

    def animate(self, frame: int = 0) -> None:
        """Display the given GIF frame and schedule the next one.

        Args:
            frame (int, optional): Index of the frame to display. Defaults to 0.

        Notes:
            This method re-calls itself with `after()` to create a continuous animation loop while the widget is managed.
        """

        self.configure(image=self.frames[frame])
        if self.winfo_manager():
            self.after(self.duration, self.animate, (frame + 1) % len(self.frames))
