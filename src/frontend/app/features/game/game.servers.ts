'use server'
import { cookies } from "next/headers"
import { redirect } from "next/navigation"

export async function surrender_action(game_id: string) {
    const url = `${process.env.BACKEND_URL}/api/v1/game/surrender`
    const cookieStore = await cookies()
    const access_token = cookieStore.get('access_token')?.value

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${access_token}`
            },
            body: JSON.stringify({ game_id })
        })
        const data = await response.json()
        if (!data.success) {
            return { success: false, message: data.message }
        }
    } catch (e) {
        const errorMessage = e instanceof Error ? e.message : String(e)
        return { success: false, message: errorMessage }
    }

    redirect('/root/dashboard')
}
