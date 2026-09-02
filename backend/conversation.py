conversations = {}


def get_conversation(session_id):
    if session_id not in conversations:
        conversations[session_id] = []

    return conversations[session_id]


def add_message(session_id, role, content):
    conversation = get_conversation(session_id)

    conversation.append({
        "role": role,
        "content": content
    })

    return conversation


def clear_conversation(session_id):
    conversations.pop(session_id, None)