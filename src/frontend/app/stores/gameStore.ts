import { create } from "zustand"


interface game{
    party:{
        state: string,
        current_player:number,
        current_gain: string,
        wheel_gains:[string|number],
        pendu:{
            secret_word:string,
            parsed_word:string
        },
    },
    players:Array<{
        id:string,
        name:string,
        cagnotte:number
    }>
}

interface GameStore{
    currentGame: game | null
    getCurrentGame:(game:game | null) => void
}

export const useGameStore = create<GameStore>((set) => ({
    currentGame : null,
    getCurrentGame:(game) => set({currentGame:game})
}))