import socket
from threading import Thread

import pygame.event

from settings import settings
from model.Message import BaseMessage, TypeMessage as TypeMessageUser
from model.ServerMessage import ServerMessage, TypeServerMessage
from uuid import uuid4

from game.MainApp import MainApp
from json import loads

from events import *


is_start_game = False

MAX_PLAYER = 2

players: list[dict] = []

players_connection = 0


def get_client_message(connection: socket.socket):
    while True:
        data = connection.recv(1024)

        mes = loads(data)

        message = BaseMessage(**mes)

        if message.type_message == TypeMessageUser.REGISTRATION_PLAYER:
            id_player = uuid4()
            players.append({
                "uuid_player": id_player,
                "con": connection,
            })

            message_server = ServerMessage(
                type_message=TypeServerMessage.REGISTRATE_ACCEPT,
                body={
                    "uuid_player": id_player
                }
            )

            connection.sendall(message_server.model_dump_json().encode("UTF-8"))
        elif message.type_message == TypeMessageUser.MOVE_TANK:
            event_custom = pygame.event.Event(MOVE_TANK, dict={
                "uuid_user": message.uuid,
                "side": message.body["side"]
            })

            pygame.event.post(event_custom)
        elif message.type_message == TypeMessageUser.FIRE:
            event_custom = pygame.event.Event(FIRE, dict={
                "uuid_user": message.uuid,
            })

            pygame.event.post(event_custom)


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print(f"start server: {settings.server_host}:{settings.server_port}")
server.bind((settings.server_host, settings.server_port))
server.listen(MAX_PLAYER)


while players_connection < MAX_PLAYER:
    conn, addr = server.accept()

    print("Player connaction", addr)
    players_connection += 1
    Thread(target=get_client_message, args=(conn, ), daemon=True).start()

game = MainApp(players)
game.start_game()
print("server down")
