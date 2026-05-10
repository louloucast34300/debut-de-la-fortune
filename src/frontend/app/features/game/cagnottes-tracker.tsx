import type { Player } from "@/app/stores/gameStore"

export const CagnottesTracker = ({players, currentPlayerId}:{players:Player[], currentPlayerId?: string}) => {
    return (
        <header className="cagnotte-tracker">
            {players.map((player) => (
                <div
                    key={player.id}
                    className={`cagnotte-tracker__player${player.id === currentPlayerId ? " cagnotte-tracker__player--active" : ""}`}
                >
                    <span className="cagnotte-tracker__name">{player.name}</span>
                    <span className="cagnotte-tracker__amount">{player.cagnotte}</span>
                </div>
            ))}
        </header>
    )
}