import { get_user_action } from "@/app/features/auth/auth.servers"
import WebSocketProvider from "@/app/providers/WebSocketProvider"
import { Navigation } from "@/app/components/navigation/navigation"
export const dynamic = 'force-dynamic'
export default async function UserLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    const user = await get_user_action()

    return (
        <WebSocketProvider userId={user.data.id} accessToken={user.data.access_token}>
            <div className="layout">
                <Navigation userId={user.data.id} pseudo={user.data.pseudo}/>
                <div className="layout-content">
                    {children}
                </div>
            </div>
        </WebSocketProvider>
    )
}