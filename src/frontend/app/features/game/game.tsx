"use client"

import { useEffect, useRef } from "react"
import { useGameStore } from "@/app/stores/gameStore"
import { useWS } from "@/app/providers/WebSocketProvider"

export const Game = ({gameId}:{gameId:string}) => {
    const {currentGame} = useGameStore()
    const {send, isReady} = useWS()

    useEffect(() => {
        if (!isReady) return
        console.log("gameID", gameId)
        send({ type: "start_game", game_id: gameId })
    }, [isReady])
    console.log(currentGame)

    if(!currentGame){
        return(
            <div>La game a bougé ..</div>
        )
    }
    return (
        <div>
            <div>Le joueur {currentGame.party.current_player + 1} commence !</div>
        </div>
    )
}