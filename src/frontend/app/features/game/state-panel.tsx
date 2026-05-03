import { useGameStore } from "@/app/stores/gameStore"

export function StatePanel () {
    const {currentGame, currentPlayer} = useGameStore()
    return (
        <div style={{  background: "#111", color: "#0f0", fontSize: "12px", maxWidth: "800px", maxHeight: "400px", overflow: "auto", zIndex: 9999 }}>
            <div>
                <strong>currentGame</strong>
                <pre>{JSON.stringify(currentGame, null, 2)}</pre>
            </div>
            <div>
                <strong>currentPlayer</strong>
                <pre>{JSON.stringify(currentPlayer, null, 2)}</pre>
            </div>
        </div>
    )
}