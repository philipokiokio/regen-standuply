def filter_by_tagged(message: str):
    message_list = message.split(" ")
    dm_list = []

    for message in message_list:
        if "<@" in message:
            dm_list.append(message[2:13])
    return list(set({*dm_list}))
