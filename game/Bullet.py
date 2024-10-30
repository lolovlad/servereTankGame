from .Image import Image

import pygame
from json import dumps

from uuid import uuid4


class Bullet(pygame.sprite.Sprite):
    def __init__(self, tank):
        super().__init__()
        self._direction = tank.normal_vector.rotate(180)
        self.speed = tank.speed * 5
        self.img = Image('bullet.png')
        self.img.resize((20, 20))
        self.rect = self.img.img.get_rect()
        self.rect.center = tank.muzzle.rect.centerx, tank.muzzle.rect.centery
        self.position = pygame.math.Vector2(self.rect.centerx, self.rect.centery)
        self.is_live = True

        self.target_tank = tank
        self.uuid_object = str(uuid4())

    def __str__(self):
        obj = {
            "position": {
                "x": self.position.x,
                "y": self.position.y,
            },
            "type": "bullet",
            "uuid": self.uuid_object
        }
        return dumps(obj)

    @property
    def direction(self):
        return self._direction

    @direction.setter
    def direction(self, val):
        self._direction = pygame.math.Vector2(val)

    def move(self):
        self.position += self.direction.normalize() * self.speed
        self.rect.center = round(self.position.x), round(self.position.y)