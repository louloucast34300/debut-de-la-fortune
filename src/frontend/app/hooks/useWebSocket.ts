"use client"

import { useEffect, useRef } from "react"
import { useMatchmaking } from "@/app/stores/matchmakingStore"

export function useWebSocket(userId: string, accessToken: string) {
    const wsRef = useRef<WebSocket | null>(null)
    const { setQueued, setMatchFound, setMatchReady, setRequeued, setPlayerAccepted, reset } = useMatchmaking()

    useEffect(() => {
        // Ouverture de la connexion
        const httpUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? ""
        const wsUrl = httpUrl.replace(/^http/, "ws")
        const ws = new WebSocket(`${wsUrl}/api/v1/ws/${userId}?token=${accessToken}`)
        wsRef.current = ws

        // Connexion établie
        ws.onopen = () => {
            console.log("WS connecté")
        }
        // Réception d'un message du backend , en fonction du message on met à jour un state , refresh les informations de la vue. 
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data)

            switch (data.type) {
                case "queued":
                    setQueued(true, data.count)
                    break
                case "match_found":
                    setMatchFound(data.proposal_id, data.player_ids)
                    break
                case "match_ready":
                    setMatchReady(data.game_id)
                    break
                case "requeued":
                    setRequeued(data.count)
                    break
                case "match_cancelled":
                    reset()
                    break
                case "player_accepted":
                    setPlayerAccepted(data.user_id)
                    break
            }
        }

        // Connexion fermée (serveur redémarré, réseau coupé ..)
        ws.onclose = (event: CloseEvent) => {
            console.log("WS fermé, code:", event.code)
        }
        // Erreur
        ws.onerror = (error) => {
            console.log("ws erreur", error)
        }
        return () => {
            ws.close()
        }
    }, [userId, accessToken])

    // envoi des actions du "front" ex: send({ type: "leave_queue" }) sur /api/v1/ws/${userId}?token=${accessToken}
    const send = (payload: object) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify(payload))
        }
    }
    return { send }
}