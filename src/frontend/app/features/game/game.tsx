"use client"

import { useEffect, useRef } from "react"
import { useGameStore } from "@/app/stores/gameStore"
import { useWS } from "@/app/providers/WebSocketProvider"
import { StatePanel } from "./state-panel"

export const Game = ({gameId, userId}:{gameId:string, userId: string}) => {
    const {currentGame, currentPlayer} = useGameStore()
    const {send, isReady} = useWS()

    useEffect(() => {
        if (!isReady) return
        console.log("gameID", gameId)
        send({ type: "start_game", game_id: gameId })
        setTimeout(() => {
            console.log("toto")
            send({ type: "choose_started_player", game_id: gameId})
        },5000)
    }, [isReady])
    console.log(currentGame)

    if(!currentGame){
        return(
            <div>La game a bougé ..</div>
        )
    }
    console.log(currentPlayer?.id," ==", userId)

    async function handleWheelValue(gain:string | number){
        send({ type: "choose_wheel_value", game_id: gameId, current_gain:gain})
    }
    return (
        <div>
            <div>
                {currentGame.party.step === "choosing_random_player" && <div> Choix du joueur qui commence ... </div>}
                {currentGame.party.step === "choosing_wheel_value" &&
                    (currentPlayer?.id === userId
                        ? 
                        (
                        <div>
                            <div>Choisir une valeur</div>
                            <div>
                            {currentGame.party.wheel_gains.map((gain: string | number, idx: number) => {
                                return (
                                    <button onClick={() => handleWheelValue(gain)} key={idx}>{gain}</button>
                                )
                            })}
                            </div>
                        </div>
                        )
                        : <div>le joueur est en train de choisir une value</div>)
                }
                {currentGame.party.step === "choosing_pendu_letter" &&
                    (currentPlayer?.id === userId
                        ? 
                        (
                        <div>
                            <div>Choisir une lettre</div>
                            <div>
                                <input type="text" />
                            </div>
                        </div>
                        )
                        : <div>le joueur est en train de choisir une lettre</div>)
                }
            </div>
            <div>
                <StatePanel />
            </div>
        </div>
    )
}