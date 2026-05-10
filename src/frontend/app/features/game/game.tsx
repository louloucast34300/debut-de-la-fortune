"use client"

import { useEffect, useState } from "react"
import { useGameStore } from "@/app/stores/gameStore"
import { useWS } from "@/app/providers/WebSocketProvider"
import { StatePanel } from "./state-panel"
import { CagnottesTracker } from "./cagnottes-tracker"
import { PlayerTracker } from "./player-tracker"
import { LettersPanel } from "./letters-panel"
import { PenduTracker } from "./pendu-tracker"

export const Game = ({gameId, userId}:{gameId:string, userId: string}) => {
    const {currentGame, currentPlayer, letterResult} = useGameStore()
    const [infos, setInfos] = useState("")
    const {send, isReady} = useWS()

    useEffect(() => {
        if (!isReady) return
        send({ type: "start_game", game_id: gameId })
        setTimeout(() => {
            send({ type: "choose_started_player", game_id: gameId})
        }, 5000)
    }, [isReady])

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
        return <div>La game a bougé ..</div>
    }

    function handleWheelValue(gain: string | number){
        send({ type: "choose_wheel_value", game_id: gameId, current_gain: gain})
    }

    const isMyTurn = currentPlayer?.id === userId

    const letterNotif = letterResult
        ? letterResult.success
            ? isMyTurn
                ? `Bonne lettre ! +${Number(currentGame.party.current_gain) * letterResult.nbr_of_letter_found} €`
                : `${letterResult.player_name} — Bonne lettre !`
            : isMyTurn
                ? `${letterResult.player_name} — ${letterResult.message}`
                : letterResult.message 
        : null

    const letterNotifClass = letterResult?.success
        ? "game-letter-notif game-letter-notif--success"
        : "game-letter-notif game-letter-notif--error"

    return (
        <div className="game-page">
            <CagnottesTracker players={currentGame.players} currentPlayerId={currentPlayer?.id} />
            <div className="game-infos">{infos}</div>
            {letterNotif && <div className={letterNotifClass}>{letterNotif}</div>}
            <PlayerTracker currentPlayer={currentPlayer} currentGame={currentGame} />

            <div className="game-layout">
                <div className="game-layout__actions">
                    {currentGame.party.step === "choosing_random_player" && (
                        <div className="game-waiting">Choix du joueur qui commence...</div>
                    )}
                    {currentGame.party.step === "choosing_wheel_value" && (
                        isMyTurn ? (
                            <div className="wheel-section">
                                <span className="wheel-section__label">Tourne la roue !</span>
                                <div className="wheel-section__gains">
                                    {currentGame.party.wheel_gains.map((gain: string | number, idx: number) => (
                                        <button
                                            key={idx}
                                            className={`wheel-section__btn${gain === "banqueroot" ? " wheel-section__btn--banqueroot" : ""}`}
                                            onClick={() => handleWheelValue(gain)}
                                        >
                                            {gain}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        ) : (
                            <div className="game-waiting">Le joueur choisit une valeur...</div>
                        )
                    )}
                    {currentGame.party.step === "choosing_pendu_letter" && (
                        isMyTurn ? (
                            <LettersPanel gameId={gameId} />
                        ) : (
                            <div className="game-waiting">Le joueur choisit une lettre...</div>
                        )
                    )}
                </div>

                <div className="game-layout__pendu">
                    <PenduTracker currentGame={currentGame} />
                </div>
            </div>

            <StatePanel />
        </div>
    )
}