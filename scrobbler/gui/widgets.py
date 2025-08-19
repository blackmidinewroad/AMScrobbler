import customtkinter as ctk
from PIL import Image

from scrobbler.utils import make_circle


# GIF label class to display gifs
class GIFLabel(ctk.CTkLabel):
    def __init__(self, master, img, crop_circle=False, obj=False, **kwargs):
        self._gif_image = img if obj else Image.open(img)

        kwargs.setdefault('width', self._gif_image.width)
        kwargs.setdefault('height', self._gif_image.height)
        kwargs.setdefault('text', '')
        self._duration = kwargs.pop("duration", None) or self._gif_image.info["duration"]
        self.crop_circle = crop_circle

        super().__init__(master, **kwargs)

        self._frames = []
        for i in range(self._gif_image.n_frames):
            self._gif_image.seek(i)
            if self.crop_circle:
                self._frames.append(ctk.CTkImage(make_circle(self._gif_image).copy(), size=(self['width'], self['height'])))
            else:
                self._frames.append(ctk.CTkImage(self._gif_image.copy(), size=(self['width'], self['height'])))

        self._animate()

        if not obj:
            self._gif_image.close()

    def _animate(self, idx=0):
        self.configure(image=self._frames[idx])
        self.after(self._duration, self._animate, (idx + 1) % len(self._frames))
