"use client"

import { useEffect, useRef, useState } from "react"
import { useGameStore } from "@/app/stores/gameStore"
import { useWS } from "@/app/providers/WebSocketProvider"
import { StatePanel } from "./state-panel"

export const Game = ({gameId, userId}:{gameId:string, userId: string}) => {
    const {currentGame, currentPlayer} = useGameStore()
    const [infos, setInfos] = useState("")
    const [ letter, setLetter ] = useState("")
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

    useEffect(() => {
        if(currentGame?.party.step === "game_over"){
            
            setInfos("Partie terminée !")
        } else if(currentGame?.party.step === "manche_completed"){
            setInfos("nouvelle manche dans 10 secondes")
        } else {
            setInfos("")
        }
    }, [currentGame?.party.step])


    if(!currentGame){
        return(
            <div>La game a bougé ..</div>
        )
    }
    console.log(currentPlayer?.id," ==", userId)

    async function handleWheelValue(gain:string | number){
        send({ type: "choose_wheel_value", game_id: gameId, current_gain:gain})
    }
    async function handleLetter(){
        send({ type: "choose_pendu_letter", game_id: gameId, letter:letter, user_id:userId})
    }
    return (
        <div>
            <div>Informations : {infos}</div>
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
                                <input type="text" onChange={(e) => setLetter(e.target.value)}/>
                                <button onClick={() => handleLetter()}>valider</button>
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