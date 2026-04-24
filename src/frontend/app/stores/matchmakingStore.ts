import { create } from "zustand"

interface MatchMakingStore{
    isInQueue: boolean,
    queueCount: number,
    proposalId: string | null,
    playerIds: string[],
    acceptedIds: string[],
    gameId: string | null,
    cancelledByOpponent: boolean,
    setQueued: (inQueue:boolean, count:number) => void,
    setMatchFound: (proposalId: string, playerIds: string[]) => void,
    setPlayerAccepted: (userId: string) => void,
    setMatchReady: (gameId: string) => void,
    setRequeued: (count:number) => void,
    reset: () => void
}

export const useMatchmaking = create<MatchMakingStore>((set) => ({
    isInQueue: false,
    queueCount: 0,
    proposalId: null,
    playerIds: [],
    acceptedIds: [],
    gameId: null,
    cancelledByOpponent: false,
    // send : "join_queue" -> réponse "queued"
    setQueued:(inQueue, count) => set({ isInQueue: inQueue, queueCount: count, cancelledByOpponent: false }),
    setMatchFound: (proposalId, playerIds) => set({ proposalId, playerIds, acceptedIds: [], cancelledByOpponent: false }),
    setPlayerAccepted: (userId) => set((s) => ({ acceptedIds: [...s.acceptedIds, userId] })),
    setMatchReady: (gameId)=> set({gameId, proposalId: null}),
    setRequeued: (count) => set({ isInQueue: true, proposalId: null, playerIds: [], acceptedIds: [], cancelledByOpponent: true, queueCount: count }),
    reset: () => set({ isInQueue: false, queueCount: 0, proposalId: null, playerIds: [], acceptedIds: [], gameId: null, cancelledByOpponent: false })
}))