"use client"

import { useMatchmaking } from "@/app/stores/matchmakingStore"
import { useWS } from "@/app/providers/WebSocketProvider"

export default function QueueButton() {
    const { isInQueue, queueCount } = useMatchmaking()
    const { send } = useWS()

    const handleClick = () => {
        if (isInQueue) {
            send({ type: "leave_queue" })
        } else {
            send({ type: "join_queue" })
        }
    }

    return (
        <button onClick={handleClick}>
            {isInQueue ? `En file (${queueCount})` : "Rejoindre la file"}
        </button>
    )
}
