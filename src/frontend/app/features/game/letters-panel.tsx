'use client'
import { useState } from "react"
import { useWS } from "@/app/providers/WebSocketProvider"

const LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("")

export const LettersPanel = ({gameId}:{gameId:string}) => {
    const {send} = useWS()
    const [usedLetters, setUsedLetters] = useState<Set<string>>(new Set())

    function handleLetter(letter: string){
        if (usedLetters.has(letter)) return
        setUsedLetters(prev => new Set(prev).add(letter))
        send({ type: "choose_pendu_letter", game_id: gameId, letter: letter.toLowerCase()})
    }

    return (
        <div className="letters-panel">
            {LETTERS.map((letter) => (
                <button
                    key={letter}
                    className={`letters-panel__btn${usedLetters.has(letter) ? " letters-panel__btn--used" : ""}`}
                    onClick={() => handleLetter(letter)}
                >
                    {letter}
                </button>
            ))}
        </div>
    )
}