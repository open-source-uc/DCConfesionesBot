# coding=utf-8
from flask import Flask, request
from json import loads as load_json
import os
import re
import requests
from sheets import get_sheet_info, write, write_message, get_sheet_message, delete_row, delete_all, write_message_accepted

# env vars
TOKEN = os.environ["token"]
admin_group = int(os.environ["admin_group"])
public_group = int(os.environ["public_group"])
channel = int(os.environ["channel"])

groups = (admin_group, public_group)

app = Flask(__name__)

cmd = r"(/[a-zA-Z]*)(?:\s)?(.*)"


def send_message(text, id_, markdown=True):
    url = "https://api.telegram.org/bot{}/".format(TOKEN)
    params = {
        "method": "sendMessage",
        "text": text,
        "chat_id": id_,
    }
    if markdown:
        params["parse_mode"] = "Markdown"
        params["disable_web_page_preview"] = "True"
    return requests.get(url, params=(params))


def send_photo(message_id, photo_id, id_, caption):
    url = "https://api.telegram.org/bot{}/".format(TOKEN)
    
    params = {
        "method": "sendPhoto",
        "photo": photo_id,
        "chat_id": id_,
        'caption': 'Nuevo Mensaje id: {}'.format(message_id)
    }
    if caption:
        params['caption'] += "\n\n{}".format(caption)

    return requests.get(url, params=(params))


def send_photo_public(message_id, photo_id, id_, caption):
    url = "https://api.telegram.org/bot{}/".format(TOKEN)
    params = {
        "method": "sendPhoto",
        "photo": photo_id,
        "chat_id": id_,
        'caption': 'DCConfesión #{}'.format(message_id)
    }
    if caption:
        params['caption'] += "\n\n{}".format(caption)

    return requests.get(url, params=(params))

# Responses
resp = {
    "completed": "Action Completed",
    "ignored": "Action Ignored",
    "error": "Error",
}

# Templates
template_admin = "*Nuevo Mensaje\tid:* {}\n{}"
template_public = "*DCConfesión #{} * \n{}"
template_admin_message = "*Admin:* {}"

datos = get_sheet_info()
messages = get_sheet_message()
print(messages)

tag_message = int(datos[0][0])
message_id = int(datos[0][1])
#send_message("*Me han reiniciado :(, Las confesiones anteriores se perdieron*".format(tag_message), admin_group, True)


@app.route("/Bot", methods=["POST", "GET"])
def telegram_bot():
    try:
        request_data = load_json(request.data)
        is_photo = False

        if "edited_message" in request_data:
            return resp["ignored"]

        chat_id = int(request_data["message"]["chat"]["id"])

        caption = None
        if 'photo' in request_data["message"]:
            text = str(request_data["message"]["photo"][-1]['file_id'])
            if 'caption' in request_data["message"]:
                caption = str(request_data["message"]['caption'])
            is_photo = True
        else:
            text = str(request_data["message"]["text"])

        # Un nuevo mensaje que no de ninguno de los dos grupos
        if chat_id not in groups and not text.startswith("/"):
            global message_id, tag_message
            # le mando el mensaje a los admin y guardo este con un id único
            message_id += 1
            id_ = message_id
            write([tag_message, message_id])
            write_message([message_id, text, is_photo, caption])
            messages[id_] = [text, is_photo, caption]
            if is_photo:
                send_photo(str(id_), text, admin_group, caption)
            else:
                send_message(template_admin.format(
                    str(id_),
                    text
                ), admin_group, True)
            print(messages)


            return resp["completed"]

        # Si el mensaje viene del grupo de admin
        elif chat_id == admin_group:
            match = re.search(cmd, text)
            if not match:
                return resp["ignored"]

            command = match.group(1)
            argument = match.group(2)

            def get_message(id_):
                id_ = int(id_)
                if id_ in messages:
                    send_message(messages[id_], admin_group)

            def get_all_messages(_):
                if not messages:
                    send_message("No hay mensajes pendientes", admin_group)
                else:
                    text = ", ".join([str(k) for k in messages])
                    send_message(text, admin_group)

            def set_tag(new_id):
                global tag_message, message_id
                tag_message = int(new_id)
                send_message(
                    "ID de los mensajes seteado en {}".format(tag_message),
                    admin_group,
                )
                write([tag_message, message_id])

            def admin_response(text):
                message = template_admin_message.format(text)
                send_message(message, public_group, True)
                send_message(message, channel, True)

            def approve_message(id_):
                global message_id, tag_message
                
                if not id_:
                    return

                elif argument == "all":
                    print("Aceptando todo")
                    for id_ in messages:
                        if messages[id_][1]:# is_photo
                            send_photo_public(tag_message, messages[id_][0], public_group, messages[id_][2])
                            send_photo_public(tag_message, messages[id_][0], channel, messages[id_][2])
                            write_message_accepted([tag_message, messages[id_][0], messages[id_][2]])

                        else:
                            message = template_public.format(
                                tag_message,
                                messages[id_][0]
                            )
                            send_message(message, public_group, True)
                            send_message(message, channel, True)
                            write_message_accepted([tag_message, messages[id_][0]])

                        tag_message += 1


                    messages.clear()
                    message_id = 0
                    write([tag_message, message_id])
                    # Eliminar mesaje de los pendientes, todos!!!
                    send_message("Mensajes aceptados", admin_group, True)
                    delete_all()
                    return 

                

                id_ = int(id_)
                if id_ not in messages:
                    return

                if messages[id_][1]:# is_photo
                    send_photo_public(tag_message, messages[id_][0], public_group, messages[id_][2])
                    send_photo_public(tag_message, messages[id_][0], channel, messages[id_][2])
                    write_message_accepted([tag_message, messages[id_][0], messages[id_][2]])

                else:
                    message = template_public.format(
                        tag_message,
                        messages[id_][0]
                    )
                    send_message(message, public_group, True)
                    send_message(message, channel, True)
                    write_message_accepted([tag_message, messages[id_][0]])

                del messages[id_]
                delete_row(id_)
                if len(messages) == 0:
                    message_id = 0
                # Eliminar mesaje de los pendientes
                tag_message += 1
                write([tag_message, message_id])

            def reject_messages(argument):
                global message_id, tag_message

                if not argument:
                    return
                elif argument == "all":
                    messages.clear()
                    message_id = 0
                    write([tag_message, message_id])
                    # Eliminar mesaje de los pendientes, todos!!!
                    send_message("Mensajes eliminados", admin_group, True)
                    delete_all()
                    return
                else:
                    id_ = int(argument)
                    if id_ not in messages:
                        return
                    del messages[id_]
                    send_message(
                        "Mensaje con id {} fue rechazado".format(id_),
                        admin_group,
                        True,
                    )
                    delete_row(id_)
                    if len(messages) == 0:
                        message_id = 0
                        write([tag_message, message_id])
                    # Eliminar mesaje de los pendientes

            def wrong_command(_):
                send_message("No existe este comando", admin_group, True)

            try:
                {
                    "/get": get_message,
                    "/all": get_all_messages,
                    "/set": set_tag,
                    "/r": admin_response,
                    "/yes": approve_message,
                    "/no": reject_messages,
                }.get(command, wrong_command)(argument)
            except ValueError:
                send_message(
                    "No se pudo procesar el comando",
                    admin_group,
                    True,
                 )
            return resp["completed"]
        
        return resp["ignored"]

    except Exception as e:
        print("ERROR EN EL BOT\n{}".format(e))
        # Si es que se genera un error que no deja aceptar más mensajes
        return resp["error"]
        

if __name__ == "__main__":
    app.run()
