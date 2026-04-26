'use client'
import { useState } from 'react'
import { surrender_action } from '@/app/features/game/game.servers'

export default function ButtonSurrender({ gameId }: { gameId: string }) {
    const [loading, setLoading] = useState(false)

    async function handleSurrender() {
        setLoading(true)
        await surrender_action(gameId)
    }

    return (
        <button type="button" onClick={handleSurrender} disabled={loading}>
            {loading ? 'Abandon...' : 'Abandonner'}
        </button>
    )
}
