'use client'
import { useEffect, useState } from 'react';
import { Loader2 } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useMatchmaking } from '@/app/stores/matchmakingStore';
import { useWS } from '@/app/providers/WebSocketProvider';


export function ModaleMatchmaking({ userId }: { userId: string }) {
    const [open, setOpen] = useState(false)
    const [countdown, setCountdown] = useState(20)
    const { isInQueue, queueCount, proposalId, playerIds, acceptedIds, gameId, cancelledByOpponent, reset } = useMatchmaking()
    const { send } = useWS()
    const router = useRouter()

    // Countdown 20s quand match trouvé, auto-cancel à 0
    useEffect(() => {
        if (!proposalId) {
            setCountdown(20)
            return
        }
        setCountdown(20)
        const interval = setInterval(() => {
            setCountdown(prev => {
                if (prev <= 1) {
                    clearInterval(interval)
                    send({ type: "cancel_match", proposal_id: proposalId })
                    return 0
                }
                return prev - 1
            })
        }, 1000)
        return () => clearInterval(interval)
    }, [proposalId])

    // Redirect quand match prêt
    useEffect(() => {
        if (gameId) {
            reset()
            setOpen(false)
            router.push(`/root/room/${gameId}`)
        }
    }, [gameId])

    // Ouvrir la modale automatiquement quand match trouvé
    useEffect(() => {
        if (proposalId) setOpen(true)
    }, [proposalId])

    function handleSearch() {
        if (isInQueue) {
            send({ type: "leave_queue" })
        } else {
            send({ type: "join_queue" })
        }
    }

    function handleAccept() {
        send({ type: "accept_match", proposal_id: proposalId })
    }

    function handleCancel() {
        send({ type: "cancel_match", proposal_id: proposalId })
    }

    function renderInner() {
        if (proposalId) {
            const iAccepted = acceptedIds.includes(userId)
            return (
                <>
                    <div>Match trouvé ! ({countdown}s)</div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8, width: '100%' }}>
                        {playerIds.map((pid) => (
                            <div key={pid} style={{ display: 'flex', justifyContent: 'space-between' }}>
                                <span>{pid === userId ? 'Vous' : 'Adversaire'}</span>
                                <span>{acceptedIds.includes(pid) ? '✅' : '⏳'}</span>
                            </div>
                        ))}
                    </div>
                    {!iAccepted && (
                        <>
                            <button type="button" onClick={handleAccept}>Accepter</button>
                            <button type="button" onClick={handleCancel}>Refuser</button>
                        </>
                    )}
                </>
            )
        }
        if (isInQueue) {
            return (
                <>
                    {cancelledByOpponent && <div>Un adversaire a refusé</div>}
                    <div>Recherche en cours ({queueCount} joueur{queueCount > 1 ? 's' : ''}) <Loader2 className="animate-spin" /></div>
                    <button type="button" onClick={handleSearch}>Stopper la recherche</button>
                </>
            )
        }
        return (
            <>
                <div>Commencer une partie !</div>
                <button type="button" onClick={handleSearch}>C'est parti !</button>
            </>
        )
    }

    return (
        <div className="modale-match">
            <button type="button" onClick={() => setOpen(true)}>Rejoindre une partie</button>
            {open &&
                <div className="modale-match-layout" onClick={() => setOpen(false)}>
                    <div className="modale-match-inner" onClick={(e) => e.stopPropagation()}>
                        {renderInner()}
                    </div>
                </div>
            }
        </div>
    )
}