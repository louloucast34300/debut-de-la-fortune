import { Game, Player } from "@/app/stores/gameStore"

export const PlayerTracker = ({currentPlayer, currentGame}:{currentPlayer:Player | null, currentGame:Game}) => {
    const action = (() => {
        switch (currentGame.party.step) {
            case "choosing_wheel_value":    return "Tourne la roue !"
            case "choosing_pendu_letter":   return "Choisis une lettre"
            case "manche_completed":        return "Manche terminée !"
            case "game_over":               return "Partie terminée !"
            default:                        return ""
        }
    })()

    return (
        <div className="player-tracker">
            <span className="player-tracker__name">{currentPlayer?.name}</span>
            <span className="player-tracker__action">{action}</span>
        </div>
    )
}