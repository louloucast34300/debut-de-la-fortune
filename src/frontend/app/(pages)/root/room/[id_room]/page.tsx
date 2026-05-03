import { get_user_action } from '@/app/features/auth/auth.servers'
import { Game } from '@/app/features/game/game'
import ButtonSurrender from '@/app/features/game/surrender-btn'

export default async function RoomPage({ params }: { params: { id_room: string } }){
    const { id_room } = await params
    const user = await get_user_action()

    return (
        <div>
            <div>ROOM {id_room}</div>
            <ButtonSurrender gameId={id_room} />
            <Game gameId={id_room} userId={user.data.id}/>
        </div>
    )
}