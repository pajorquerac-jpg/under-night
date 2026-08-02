import { useCallback, useMemo, useState } from "react";

import {
  ApiError,
  ApiInvalidResponseError,
  ApiNetworkError,
  ApiTimeoutError,
  sendAgentMessage,
} from "@/api/client";
import type {
  AgentConversationState,
  ChatMessage,
  SuggestedAction,
} from "@/types/api";

export type AgentChatController = {
  conversationId: string | null;
  messages: ChatMessage[];
  state: AgentConversationState | null;
  suggestedActions: SuggestedAction[];
  isSending: boolean;
  error: string | null;
  sendMessage: (message: string) => Promise<void>;
  retryMessage: (messageId: string) => Promise<void>;
  resetConversation: () => void;
};

const WELCOME_MESSAGE: ChatMessage = {
  id: "welcome",
  content:
    "Hola, soy el asistente de UnderNight. Cuéntame qué panorama están buscando y te ayudaré a organizar la salida.",
  createdAt: new Date().toISOString(),
  role: "assistant",
  status: "sent",
};

function createMessageId(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

function errorMessage(error: unknown) {
  if (error instanceof ApiTimeoutError) {
    return "Ollama tardó más de lo esperado. Puedes reintentar el mensaje.";
  }
  if (error instanceof ApiNetworkError) {
    return "No pude conectar con el backend. Revisa la URL de la API y tu red.";
  }
  if (error instanceof ApiInvalidResponseError) {
    return "La API respondió con un formato inesperado. Intenta nuevamente.";
  }
  if (error instanceof ApiError) {
    return error.message;
  }
  return "No pude enviar el mensaje. Intenta nuevamente.";
}

export function useAgentChat(): AgentChatController {
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME_MESSAGE]);
  const [state, setState] = useState<AgentConversationState | null>(null);
  const [suggestedActions, setSuggestedActions] = useState<SuggestedAction[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submitMessage = useCallback(
    async (content: string, existingMessageId?: string) => {
      const trimmed = content.trim();
      if (!trimmed || isSending) {
        return;
      }

      const userMessage: ChatMessage = {
        id: existingMessageId ?? createMessageId("user"),
        content: trimmed,
        createdAt: new Date().toISOString(),
        role: "user",
        status: "sending",
      };

      setError(null);
      setIsSending(true);
      setMessages((current) => {
        if (existingMessageId) {
          return current.map((message) =>
            message.id === existingMessageId ? userMessage : message,
          );
        }
        return [...current, userMessage];
      });

      try {
        const response = await sendAgentMessage({
          conversation_id: conversationId ?? undefined,
          message: trimmed,
        });

        const assistantMessage: ChatMessage = {
          id: createMessageId("assistant"),
          content: response.reply,
          createdAt: new Date().toISOString(),
          role: "assistant",
          status: "sent",
        };

        setConversationId(response.conversation_id);
        setState(response.state);
        setSuggestedActions(response.suggested_actions ?? []);
        setMessages((current) => [
          ...current.map((message) =>
            message.id === userMessage.id ? { ...message, status: "sent" as const } : message,
          ),
          assistantMessage,
        ]);
      } catch (requestError) {
        setError(errorMessage(requestError));
        setMessages((current) =>
          current.map((message) =>
            message.id === userMessage.id ? { ...message, status: "error" as const } : message,
          ),
        );
      } finally {
        setIsSending(false);
      }
    },
    [conversationId, isSending],
  );

  const retryMessage = useCallback(
    async (messageId: string) => {
      const message = messages.find((item) => item.id === messageId);
      if (!message || message.role !== "user" || message.status !== "error") {
        return;
      }
      await submitMessage(message.content, message.id);
    },
    [messages, submitMessage],
  );

  const resetConversation = useCallback(() => {
    setConversationId(null);
    setMessages([{ ...WELCOME_MESSAGE, createdAt: new Date().toISOString() }]);
    setState(null);
    setSuggestedActions([]);
    setIsSending(false);
    setError(null);
  }, []);

  return useMemo(
    () => ({
      conversationId,
      error,
      isSending,
      messages,
      resetConversation,
      retryMessage,
      sendMessage: submitMessage,
      state,
      suggestedActions,
    }),
    [
      conversationId,
      error,
      isSending,
      messages,
      resetConversation,
      retryMessage,
      state,
      submitMessage,
      suggestedActions,
    ],
  );
}
