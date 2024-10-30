from .Tank import Tank
from .Wall import Wall
from .Bullet import Bullet
from .ObjectMap import ObjectMap
import pygame
from datetime import datetime
from random import randint

from model.ServerMessage import ServerMessage, TypeServerMessage
from socket import socket

from events import *
from json import dumps


class MainApp:
    def __init__(self, players: list[dict]):
        pygame.init()
        self.HIT_TANK_PLAYER_1 = pygame.USEREVENT + 1
        self.HIT_TANK_PLAYER_2 = pygame.USEREVENT + 2
        self.GAME_OVER = pygame.USEREVENT + 3

        self.SCREEN_HEIGHT_MENU = 180
        self.SCREEN_WIDTH, self.SCREEN_HEIGHT = 1620, 720
        self.FPS = 30
        self.clock = pygame.time.Clock()

        self.player_tank_1: Tank = None
        self.player_tank_2: Tank = None

        self.object_list_enemy = []
        self.object_list_wall = []
        self.object_list_bullet = []

        self.map_render = []

        self.position_players = {}

        self._is_game = True
        self._screen_game = True

        self._information = {"gray_tank.png": {
                                    "bullet": 0,
                                    "broke": 0,
                                    "hit_tank": 0},
                              "yellow_tank.png": {
                                  "bullet": 0,
                                  "broke": 0,
                                  "hit_tank": 0
                              },
                              "bullet_to_bullet": 0}

        self.__player: list[dict] = players

    def send_player_message(self, message: ServerMessage):
        for player in self.__player:
            sock: socket = player["con"]
            sock.sendall(f"START{message.model_dump_json()}END".encode("utf-8"))

    def start_game(self):
        self.send_player_message(ServerMessage(
            type_message=TypeServerMessage.START_GAME,
            body={}
        ))
        self.render_map()
        while self._is_game:
            object_send_message = []
            #server_message = ServerMessage(
            #    type_message=TypeServerMessage.VOID,
            #    body={}
            #)

            #    self.window.fill([0, 0, 0])
            self.get_event(object_send_message)
            self.move_object()
            self._hit_event(object_send_message)
            #    self.show_object()
            #    self.show_menu()

            self.get_state_object(object_send_message)

            self.send_player_message(ServerMessage(
                type_message=TypeServerMessage.UPDATE_OBJECTS,
                body={
                    "obj": object_send_message
                }
            ))
            self.clock.tick(self.FPS)
        self.game_over()

            #self.send_player_message(server_message)

    def game_over(self):
        text_in = ""
        if self.player_tank_1.live < self.player_tank_2.live:
            text_in = "Второй игрок победил "
        else:
            text_in = "Первый игрок победил"

            #text = font.render(text_in, True, (255, 255, 255), (0, 0, 0))
            #textRect = text.get_rect()
            #textRect.center = (self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 - 100)

            #text_1 = font.render("Отчет об окончании игры сгенерирован", True, (255, 255, 255), (0, 0, 0))
            #textRect_1 = text_1.get_rect()
            #textRect_1.center = (self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2)

        self.send_player_message(ServerMessage(
            type_message=TypeServerMessage.STOP_GAME,
            body={
                "message": text_in
            }
        ))

    def show_object(self):
        for object_game in self.object_list_enemy + self.object_list_wall + self.object_list_bullet:
            object_game.display()

    def get_state_object(self, q: list):
        for object_game in self.object_list_enemy + self.object_list_bullet:
            q.append(str(object_game))

    def move_object(self):
        for object_game in self.object_list_enemy + self.object_list_bullet:
            object_game.move()

    def get_event(self, q: list):
        event_list = pygame.event.get()

        for event in event_list:
            if event.type == MOVE_TANK:
                info = event.dict["dict"]

                tank = self.player_tank_1 if self.player_tank_1.is_target_tank(info["uuid_user"]) else self.player_tank_2

                self._move_tank_event(tank, info["side"])
            elif event.type == FIRE:
                uuid_player = event.dict["dict"]["uuid_user"]
                tank = self.player_tank_1 if self.player_tank_1.is_target_tank(uuid_player) else self.player_tank_2
                bullet = tank.fire()
                self.object_list_bullet.append(bullet)

            #if event.type == pygame.KEYDOWN:
            #    if event.key == pygame.K_SPACE:
            #        bullet = self.my_tank.fire()
            #        self._information[self.my_tank.path_img]["bullet"] += 1
            #        self.object_list_bullet.append(bullet)
            #    if event.key == pygame.K_p:
            #        bullet = self.enemy_tank.fire()
            #        self._information[self.enemy_tank.path_img]["bullet"] += 1
            #        self.object_list_bullet.append(bullet)
            if event.type == self.HIT_TANK_PLAYER_1:
                self.player_tank_1.set_new_position(self.position_players["my_tank"])
                q.append(str(self.player_tank_1))
            if event.type == self.HIT_TANK_PLAYER_2:
                self.player_tank_2.set_new_position(self.position_players["enemy_tank"])
                q.append(str(self.player_tank_2))
            if event.type == self.GAME_OVER:
                self._is_game = False

    def _move_tank_event(self, tank: Tank, side: str):
        if side == "up":
            tank.direction = (0, -1)
            tank.transform_direction = (0, 1)
        elif side == "down":
            tank.direction = (0, 1)
            tank.transform_direction = (0, -1)
        elif side == "left":
            tank.direction = (-1, 0)
            tank.transform_direction = (1, 0)
        elif side == "right":
            tank.direction = (1, 0)
            tank.transform_direction = (-1, 0)
        else:
            tank.direction = (0, 0)

    def _hit_event(self, q: list):
        self._hit_wall_tank()
        self._hit_bullet_object(q)

    def _hit_wall_tank(self):
        for enemy in self.object_list_enemy:
            id_walls = enemy.rect.collidelist(self.object_list_wall)
            if id_walls != -1:
                wall = self.object_list_wall[id_walls]
                range_hit = pygame.math.Vector2(wall.rect.centerx - enemy.rect.centerx,
                                                wall.rect.centery - enemy.rect.centery).length()
                enemy.reflect(wall.rect)

    def _hit_bullet_object(self, q):
        for i, bullet in enumerate(self.object_list_bullet):
            id_walls = bullet.rect.collidelist(self.object_list_wall)
            id_tank = bullet.rect.collidelist(self.object_list_enemy)
            id_bullet = bullet.rect.collidelist(self.object_list_bullet[:i] + self.object_list_bullet[i+1:])
            if id_walls != -1:
                wall = self.object_list_wall[id_walls]
                if wall.type_wall == 2:
                    wall = self.object_list_wall.pop(id_walls)
                    self._information[bullet.target_tank.path_img]["broke"] += 1

                    q.append(dumps({
                        "type": "wall",
                        "move": "destroy",
                        "position": {
                            "x": wall.rect.x,
                            "y": wall.rect.y
                        }
                    }))

                bul = self.object_list_bullet.pop(i)
                q.append(dumps({
                    "type": "bullet_dest",
                    "uuid": bul.uuid_object
                }))

            elif id_tank != -1:
                tank = self.object_list_enemy[id_tank]
                tank.live = 1
                q.append(dumps({
                    "type": "tank_live",
                    "uuid": tank.uuid,
                    "count": 1
                }))
                self._information[bullet.target_tank.path_img]["hit_tank"] += 1
                bul = self.object_list_bullet.pop(i)
                q.append(dumps({
                    "type": "bullet_dest",
                    "uuid": bul.uuid_object
                }))

            elif id_bullet != -1:
                self._information["bullet_to_bullet"] += 1
                self.object_list_bullet.pop(i)
                self.object_list_bullet.pop(id_bullet)


    def render_tank(self, type_tank, cell):
        if type_tank == 4:
            self.player_tank_1 = Tank("gray_tank.png",
                                      (0, 0),
                                      3,
                                      (35, 35),
                                      (cell[0] * 30, cell[1] * 30),
                                      self.__player[0]["uuid_player"],
                                      self.HIT_TANK_PLAYER_1,
                                      self.GAME_OVER)

            self.position_players["my_tank"] = (cell[0] * 30, cell[1] * 30)

            self.object_list_enemy.append(self.player_tank_1)
        if type_tank == 5:
            self.player_tank_2 = Tank("yellow_tank.png",
                                      (0, 0),
                                      3,
                                      (30, 30),
                                      (cell[0] * 30, cell[1] * 30),
                                      self.__player[1]["uuid_player"],
                                      self.HIT_TANK_PLAYER_2,
                                      self.GAME_OVER)

            self.position_players["enemy_tank"] = (cell[0] * 30, cell[1] * 30)

            self.object_list_enemy.append(self.player_tank_2)

    def render_map(self):
        with open("game/files/map.txt", "r") as file:
            lines = file.readlines()
            for line in lines:
                line = line.replace("\n", "")
                y = [int(x) for x in line]
                self.map_render.append(y)
            for y in range(self.SCREEN_HEIGHT // 30):
                for x in range(self.SCREEN_WIDTH // 30):
                    if self.map_render[y][x] == 1:
                        self.object_list_wall.append(Wall("metal_wall.png",
                                                          x * 30, y * 30,
                                                          self.map_render[y][x]))
                    elif self.map_render[y][x] == 2:
                        self.object_list_wall.append(Wall("break_wall.png",
                                                          x * 30, y * 30,
                                                          self.map_render[y][x]))
                    self.render_tank(self.map_render[y][x], (x, y))
            self.send_player_message(ServerMessage(
                type_message=TypeServerMessage.RENDER_MAP,
                body={
                    "map": [str(obj) for obj in self.object_list_wall],
                    "tank_players": [str(obj) for obj in self.object_list_enemy]
                }
            ))


    def last_id_result(self):
        with open("files/results.txt", "r", encoding="utf-8") as file:
            lines = file.readlines()
            if len(lines) > 0:
                id_result = lines[-1].split("|")[0]
                return int(id_result) + 1
            return 1

    def generate_file_results(self, name_file):
        with open(name_file, "w+", encoding="utf-8") as file:
            file.write("Итоги игры\n")
            sum_bullet = 0
            sum_wall = 0
            sum_hit = 0
            for key in self._information:
                if key == "gray_tank.png":
                    file.write("Статистика серого танка:\n")
                    file.write(f"Количества здоровья: {self.my_tank.live}\n")
                    file.write(f"Выпущенно снарядов за игру: {self._information[key]['bullet']}\n")
                    file.write("\tИз этих снарядов:\n")
                    file.write(f"\t\tСнаряды, сломавшие стены: {self._information[key]['broke']}\n")
                    file.write(f"\t\tСнаряды, попавшие в танк противника: {self._information[key]['hit_tank']}\n")

                    sum_bullet += self._information[key]['bullet']
                    sum_wall += self._information[key]['broke']
                    sum_hit += self._information[key]['hit_tank']
                elif key == "yellow_tank.png":
                    file.write("Статистика желтого танка:\n")
                    file.write(f"Количества здоровья: {self.enemy_tank.live}\n")
                    file.write(f"Выпущенно снарядов за игру: {self._information[key]['bullet']}\n")
                    file.write("\tИз этих снарядов:\n")
                    file.write(f"\t\tСнаряды, сломавшие стены: {self._information[key]['broke']}\n")
                    file.write(f"\t\tСнаряды, попавшие в танк противника: {self._information[key]['hit_tank']}\n")

                    sum_bullet += self._information[key]['bullet']
                    sum_wall += self._information[key]['broke']
                    sum_hit += self._information[key]['hit_tank']
                else:
                    file.write("\n")
                    file.write(f"Снаряды, попавшие в снаряды противника: {self._information[key]}\n")

            file.write("-" * 60 + "\n")
            file.write("Общая статистика\n")
            file.write(f"Выпущенно снарядов за игру: {sum_bullet}\n")
            file.write("\tИз этих снарядов:\n")
            file.write(f"\t\tСнаряды, сломавшие стены: {sum_wall}\n")
            file.write(f"\t\tСнаряды, попавшие в танк: {sum_hit}\n")
            file.write(f"Снаряды, попавшие в танк: {sum_hit}\n")
            if self.my_tank.live < self.enemy_tank.live:
                file.write(f"Победил жёлтый танк")
            else:
                file.write(f"Победил серый танк")

    def add_result_database(self):
        with open("files/results.txt", "a+", encoding="utf-8") as file:
            id_result = self.last_id_result() #ID результата игры
            path_file = f"files/results/{randint(1, 10000000)}.txt"
            self.generate_file_results(path_file)
            datetime_now = datetime.now()
            file.write(f"{id_result}|{datetime_now.strftime('%d/%m/%Y, %H:%M')}|{path_file}\n")