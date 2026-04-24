import { get_user_action } from "@/app/features/auth/register/register.server"
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
                <Navigation/>
                <div className="layout-content">
                    <h1>{user.data.pseudo}</h1>
                    {children}
                </div>
            </div>
        </WebSocketProvider>
    )
}