'use client'
import { Game } from "@/app/stores/gameStore"

export const PenduTracker = ({currentGame}:{currentGame:Game}) => {
    const letters = currentGame.party.pendu.parsed_word.split("")

    return (
        <div className="pendu-tracker">
            {letters.map((char, idx) => (
                <div key={idx} className={`pendu-tracker__card${char !== "_" ? " pendu-tracker__card--revealed" : ""}`}>
                    <div className="pendu-tracker__card-inner">
                        <div className="pendu-tracker__card-front" />
                        <div className="pendu-tracker__card-back">{char.toUpperCase()}</div>
                    </div>
                </div>
            ))}
        </div>
    )
}