import pygame
from .Image import Image
from json import dumps


class Wall:
    def __init__(self, img, left, top, type_wall, size=(30, 30)):

        self.img = Image(img)
        self.img.resize(size)
        self.rect = self.img.img.get_rect()
        self.rect.left = left
        self.rect.top = top
        self.type_wall = type_wall

    def __str__(self):
        obj = {
            "img": self.img.name_img,
            "left": self.rect.left,
            "top": self.rect.top,
            "size": {
                "height": self.rect.height,
                "width": self.rect.width
            }
        }
        return dumps(obj)
