"use client"

import { createContext, useContext } from "react"
import { useWebSocket } from "@/app/hooks/useWebSocket"

interface WebSocketContextValue {
    send: (payload: object) => void
    isReady: boolean
}

const WebSocketContext = createContext<WebSocketContextValue | null>(null)

export function useWS() {
    const ctx = useContext(WebSocketContext)
    if (!ctx) throw new Error("useWS must be used within WebSocketProvider")
    return ctx
}

export default function WebSocketProvider({
    userId,
    accessToken,
    children,
}: {
    userId: string
    accessToken: string
    children: React.ReactNode
}) {
    const { send, isReady } = useWebSocket(userId, accessToken)

    return (
        <WebSocketContext.Provider value={{ send, isReady }}>
            {children}
        </WebSocketContext.Provider>
    )
}
