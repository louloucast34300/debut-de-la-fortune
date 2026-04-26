import ButtonSurrender from '@/app/features/game/surrender-btn'

export default async function RoomPage({ params }: { params: { id_room: string } }){
    const { id_room } = await params
    return (
        <div>
            <div>ROOM {id_room}</div>
            <ButtonSurrender gameId={id_room} />
        </div>
    )
}