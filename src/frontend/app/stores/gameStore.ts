import { create } from "zustand"

export interface Player {
    id: string
    name: string
    cagnotte: number
}
export interface Manche{
    id: number,
    word:string
}

export interface Game {
    party: {
        state: string
        step: string
        current_player: number
        current_gain: string
        current_manche: number
        wheel_gains: (string | number)[]
        pendu: {
            secret_word: string
            parsed_word: string
        }
    }
    players: Player[],
    manches: Manche[]
}

export interface LetterResult {
    success: boolean
    message: string
    nbr_of_letter_found: number
    code_error: number
    word_completed: boolean
    player_name: string
}

interface GameStore {
    currentGame: Game | null
    currentPlayer: Player | null
    letterResult: LetterResult | null
    getCurrentGame: (game: Game | null) => void
    setLetterResult: (result: LetterResult | null) => void
}

export const useGameStore = create<GameStore>((set) => ({
    currentGame: null,
    currentPlayer: null,
    letterResult: null,
    getCurrentGame: (game) => {
        if (!game) {
            set({ currentGame: null, currentPlayer: null })
            return
        }
        const player = game.players[game.party.current_player] ?? null
        set({ currentGame: game, currentPlayer: player })
    },
    setLetterResult: (result) => set({ letterResult: result }),
}))