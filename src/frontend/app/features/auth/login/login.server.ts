'use server'
import { cookies } from "next/headers"
import { redirect, RedirectType } from 'next/navigation'


export async function login_action(formData: FormData) {
    const url = `${process.env.BACKEND_URL}/api/v1/auth/login`
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(Object.fromEntries(formData))
        })
        const data = await response.json()
        if (!data.success) {
            return { "success": false, "message": data.message }
        }
        const cookieStore = await cookies()
        cookieStore.set('access_token', data.access_token, {
            httpOnly: true,
            secure: process.env.NODE_ENV === 'production',
            sameSite: 'strict',
            maxAge: 60 * 60
        })
        cookieStore.set('refresh_token', data.refresh_token, {
            httpOnly: true,
            secure: process.env.NODE_ENV === 'production',
            sameSite: 'strict',
            maxAge: 60 * 60 * 24 * 30
        })

    } catch (e) {
        const errorMessage = e instanceof Error ? e.message : String(e)
        return { "success": false, "message": errorMessage }
    }
    redirect("/", RedirectType.push)
}


export async function logout_action() {

    const url = `${process.env.BACKEND_URL}/api/v1/auth/logout`
    const cookieStore = await cookies()
    const refresh_token = cookieStore.get('refresh_token')?.value

    cookieStore.delete("access_token")
    cookieStore.delete("refresh_token")

    if (refresh_token) {

        try {
            console.log("ici")
            await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh_token })
            })
        } catch (e) {
            const errorMessage = e instanceof Error ? e.message : String(e)
            return { "success": false, "message": errorMessage }
        }
    }
    redirect("/register", RedirectType.push)
}

