import { create } from "zustand"

/**
@websocket "queued":
@action setQueued(true, data.count)
    
@websocket "match_found":
@action setMatchFound(data.proposal_id, data.player_ids)
    
@websocket "match_ready":
@action setMatchReady(data.game_id)
    
@websocket "requeued":
@action setRequeued(data.count)

@websocket case "match_cancelled":
@action reset()

@websocket case "player_accepted":
@action setPlayerAccepted(data.user_id)
 */

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

    setQueued:(inQueue, count) => set({ isInQueue: inQueue, queueCount: count, cancelledByOpponent: false }),
    setMatchFound: (proposalId, playerIds) => set({ proposalId, playerIds, acceptedIds: [], cancelledByOpponent: false }),
    setPlayerAccepted: (userId) => set((s) => ({ acceptedIds: [...s.acceptedIds, userId] })),
    setMatchReady: (gameId)=> set({gameId, proposalId: null}),
    setRequeued: (count) => set({ isInQueue: true, proposalId: null, playerIds: [], acceptedIds: [], cancelledByOpponent: true, queueCount: count }),
    reset: () => set({ isInQueue: false, queueCount: 0, proposalId: null, playerIds: [], acceptedIds: [], gameId: null, cancelledByOpponent: false })
}))