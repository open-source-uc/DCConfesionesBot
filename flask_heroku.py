# coding=utf-8
import flask
import json
import requests
import os

TOKEN = os.environ["token"]

app = flask.Flask(__name__)


def id_generator():
    n = 1
    while True:
        yield n
        n += 1

messages = {}
template_admin = "*Nuevo Mensaje\tid:* {}\n{}"
template_public = "*DCConfesión #{} * \n{}"

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

admin_group = int(os.environ["admin_group"])
public_gruop = int(os.environ["public_gruop"])
channel = int(os.environ["channel"])

send_message("*Me han reiniciado :(*", admin_group, True)

tag_message = 1


@app.route('/Bot', methods=["POST", "GET"])
def telegram_bot():
    global tag_message

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
                    if len(messages.keys()) == 0:
                        send_message("No hay mensajes pendientes", admin_group)
                    else:
                        text = ", ".join([str(x) for x in messages.keys()])
                        send_message(text, admin_group)

                elif text.lower().startswith("/set"):
                    new_id = int(text.replace("/set ", ""))
                    tag_message = new_id
                    send_message("ID de los mensajes seteado en {}".format(tag_message), admin_group)

                elif text.lower().startswith("/r"):
                    text = text.replace("/r ", "")
                    send_message("*Admin: *" + text, public_gruop, True)
                    send_message("*Admin: *" + text, channel, True)

                elif text.lower().startswith("/yes"):
                    try:
                        command, id_ = text.strip().split(" ")
                        id_ = int(id_)
                        if id_ in messages:
                            send_message(template_public.format(tag_message, messages[id_]),
                                         public_gruop,
                                         True)
                            send_message(template_public.format(tag_message, messages[id_]),
                                         channel,
                                         True)

                            del messages[id_]
                            tag_message += 1

                    except ValueError:
                        send_message("No se pudo procesar la respuesta",
                                     admin_group,
                                     True)
                elif text.lower().startswith("/no all"):
                    messages.clear()
                    send_message("Mensajes eliminados",
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

        return "None"

    except Exception as e:
        print("ERROR EN EL BOT\n", e)
        # Si es que se genera un error que no deja aceptar más mensajes
        return "None"

if __name__ == '__main__':
    app.run()

