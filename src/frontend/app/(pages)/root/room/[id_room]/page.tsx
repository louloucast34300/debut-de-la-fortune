import ButtonSurrender from '@/app/components/button-surrender/button-surrender'

export default async function RoomPage({ params }: { params: { id_room: string } }){
    const { id_room } = await params
    return (
        <div>
            <div>ROOM {id_room}</div>
            <ButtonSurrender gameId={id_room} />
        </div>
    )
}