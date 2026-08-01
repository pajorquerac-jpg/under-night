from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.conversation import Conversation, ConversationMessage


def get_conversation(db: Session, conversation_id: str) -> Conversation | None:
    return db.get(Conversation, conversation_id)


def create_conversation(db: Session, conversation_id: str | None = None) -> Conversation:
    conversation = Conversation(id=conversation_id or str(uuid4()), state={}, stage="collecting")
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def get_or_create_conversation(db: Session, conversation_id: str | None) -> Conversation:
    if conversation_id is not None:
        existing = get_conversation(db, conversation_id)
        if existing is not None:
            return existing
    return create_conversation(db, conversation_id)


def list_messages(db: Session, conversation_id: str, limit: int = 20) -> list[ConversationMessage]:
    statement = (
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation_id)
        .order_by(ConversationMessage.created_at.desc(), ConversationMessage.id.desc())
        .limit(limit)
    )
    return list(reversed(db.scalars(statement).all()))


def add_message(
    db: Session,
    conversation_id: str,
    role: str,
    content: str,
    provider: str | None = None,
    model: str | None = None,
) -> ConversationMessage:
    message = ConversationMessage(
        content=content,
        conversation_id=conversation_id,
        model=model,
        provider=provider,
        role=role,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def update_conversation_state(
    db: Session,
    conversation: Conversation,
    state: dict[str, object],
    stage: str,
) -> Conversation:
    conversation.state = state
    conversation.stage = stage
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation
