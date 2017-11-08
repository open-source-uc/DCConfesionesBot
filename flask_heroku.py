# coding=utf-8
import flask
import json
import requests

TOKEN = 'CENSURADO POR SEGURIDAD'

app = flask.Flask(__name__)


def id_generator():
    n = 1
    while True:
        yield n
        n += 1

messages = {}
template_admin = "**Nuevo Mensaje\tid:** {}\n{}"

message_id = id_generator()


def send_message(texto, id_, markdown=False):
    url = "https://api.telegram.org/bot{}/".format(TOKEN)
    params = {"method": "sendMessage",
              "text": texto,
              "chat_id": id_}

    if markdown:
        params["parse_mode"] = "Markdown"
        params["disable_web_page_preview"] = "True"

    return requests.get(url, params=(params))

admin_group = -313969292
public_gruop = -1001331104046


@app.route('/Bot', methods=["POST", "GET"])
def telegram_bot():

    try:
        if "edited_message" not in json.loads(flask.request.data):
            # Solo cuando le mandan un nuevo mensaje

            chat_id = int(json.loads(flask.request.data)["message"]["chat"]["id"])
            text = str(json.loads(flask.request.data)["message"]["text"])

            # Un nuevo mensaje que no de ninguno de los dos grupos
            if chat_id != admin_group and chat_id != public_gruop and not text.startswith("/"):

                # le mando el mensaje a los admin y guardo este con un id único
                id_ = next(message_id)
                messages[id_] = text
                send_message(template_admin.format(str(id_), text), admin_group, True)

            # Si el mensaje viene del grupo de admin
            elif chat_id == admin_group:

                if text.lower().startswith("/get"):
                    command, id_ = text.strip().split(" ")
                    id_ = int(id_)

                    if id_ in messages:
                        send_message(messages[id_], admin_group)

                elif text.lower().startswith("/all"):
                    text = ", ".join([str(x) for x in messages.keys()])
                    send_message(text, admin_group)

                elif text.lower().startswith("/response"):
                    text = text.replace("/response", "")
                    send_message("Bot: " + text, public_gruop)

                elif text.lower().startswith("/yes"):
                    try:
                        command, id_ = text.strip().split(" ")
                        id_ = int(id_)
                        if id_ in messages:
                            send_message(messages[id_],
                                         public_gruop,
                                         True)

                            del messages[id_]
                    except ValueError:
                        send_message("No se pudo procesar la respuesta",
                                     admin_group,
                                     True)
                elif text.lower().startswith("/no"):
                    try:
                        command, id_ = text.strip().split(" ")
                        id_ = int(id_)
                        if id_ in messages:
                            del messages[id_]
                            send_message("Mensaje con id {} fue rechazado".format(id_),
                                         admin_group,
                                         True)
                    except ValueError:
                        send_message("No se pudo procesar la respuesta",
                                     admin_group,
                                     True)
            return "None"
    except Exception as e:
        # Si es que se genera un error que no deja aceptar más mensajes
        return "None"

if __name__ == '__main__':
    app.run()

