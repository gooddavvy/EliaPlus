from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass

import openai
from textual import work, log, on
from textual.app import ComposeResult
from textual.containers import VerticalScroll, Vertical, ScrollableContainer
from textual.css.query import NoMatches
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Input

from elia_chat.models import ChatData, ChatMessage
from elia_chat.widgets.agent_is_typing import AgentIsTyping
from elia_chat.widgets.chatbox import Chatbox
from elia_chat.widgets.chat_header import ChatHeader
from elia_chat.widgets.chat_options import (
    DEFAULT_MODEL,
    ChatOptions,
)


class Chat(Widget):
    chosen_model = reactive(DEFAULT_MODEL)

    def __init__(self) -> None:
        super().__init__()

        # The thread initially only contains the system message.
        self.chat_container: ScrollableContainer | None = None
        self.thread = ChatData(
            messages=[
                ChatMessage(
                    role="system",
                    content="You are a helpful assistant.",
                )
            ]
        )

    @dataclass
    class AgentResponseStarted(Message):
        pass

    @dataclass
    class AgentResponseComplete(Message):
        message: ChatMessage

    @property
    def is_empty(self) -> bool:
        """True if the conversation is empty, False otherwise."""
        return len(self.thread.messages) == 1  # Contains system message at first.

    def scroll_to_latest_message(self):
        if self.chat_container is not None:
            self.chat_container.refresh()
            self.chat_container.scroll_end(animate=False)

    async def new_user_message(self, content: str) -> None:
        user_message = ChatMessage(role="user", content=content)
        self.thread.messages.append(user_message)
        # If the thread was empty, and now it's not, remove the ConversationOptions.
        if len(self.thread.messages) == 2:
            log.debug(
                f"First user message received in "
                f"conversation with model {self.chosen_model.name!r}"
            )
            try:
                options = self.query_one(ChatOptions)
            except NoMatches:
                log.error("Couldn't remove ConversationOptions as it wasn't found.")
            else:
                await options.remove()
                log.debug("Removed ConversationOptions.")

        user_message_chatbox = Chatbox(user_message)
        start_time = time.time()

        assert (
            self.chat_container is not None
        ), "Textual has mounted container at this point in the lifecycle."

        await self.chat_container.mount(user_message_chatbox)
        self.scroll_to_latest_message()

        end_time = time.time()
        log.debug(f"Time to mount chatbox = {end_time - start_time}")
        # self.conversation_container.refresh(layout=True)
        log.debug()
        # self.check_idle()
        self.post_message(self.AgentResponseStarted())
        log.debug(f"Refreshing for new message {time.time()}")
        self.stream_agent_response()

    @work(exclusive=True)
    async def stream_agent_response(self) -> None:
        log.debug(f"Agent response stream starting {time.time()}")
        self.scroll_to_latest_message()
        streaming_response = await openai.ChatCompletion.acreate(
            model=self.chosen_model.name,
            messages=self.thread.messages,
            stream=True,
        )

        response_chatbox = Chatbox(
            message=ChatMessage(role="assistant", content=""),
            classes="assistant-message",
        )

        assert (
            self.chat_container is not None
        ), "Textual has mounted container at this point in the lifecycle."

        await self.chat_container.mount(response_chatbox)

        while True:
            # TODO: We need to handle RateLimitError in the worker.
            try:
                event = await streaming_response.__anext__()
                choice = event["choices"][0]
            except (StopAsyncIteration, StopIteration, IndexError):
                self.post_message(self.AgentResponseComplete(response_chatbox.message))
            else:
                finish_reason = choice.get("finish_reason")
                if finish_reason in {"stop", "length", "content_filter"}:
                    log.debug(
                        f"Agent response finished. Finish reason is {finish_reason!r}."
                    )
                    response_message = response_chatbox.message
                    self.post_message(self.AgentResponseComplete(response_message))
                    return
                response_chatbox.append_chunk(event)
                scroll_y = self.chat_container.scroll_y
                max_scroll_y = self.chat_container.max_scroll_y
                if scroll_y in range(max_scroll_y - 3, max_scroll_y + 1):
                    self.chat_container.scroll_end(animate=False)
            await asyncio.sleep(0.01)

    @on(AgentResponseComplete)
    def agent_finished_responding(self, event: AgentResponseComplete) -> None:
        # Ensure the thread is updated with the message from the agent
        self.thread.messages.append(event.message)

    def compose(self) -> ComposeResult:
        yield ChatHeader(title="Untitled Chat")
        with Vertical(id="chat-input-container"):
            yield Input(placeholder="[I] Enter your message here...", id="chat-input")
            yield AgentIsTyping()

        with VerticalScroll() as vertical_scroll:
            self.chat_container = vertical_scroll
            vertical_scroll.can_focus = False
            yield ChatOptions()

            # TODO - check if conversation is pre-existing.
            #  If it already exists, load it here.
            #  If it's a new empty conversation, show the
            #  options for a new conversation.