'use server'
import { cookies } from "next/headers"
import { redirect, RedirectType } from 'next/navigation'

export async function register_action(formData:FormData){
    const url = `${process.env.BACKEND_URL}/api/v1/auth/register`
    try{
        const response = await fetch(url, {
            method : 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(Object.fromEntries(formData))
        })
        const data = await response.json()
        console.log(data)
        if(!data.success){
            return {"success":false, "message":data.message}
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
    }catch(e){
        const errorMessage = e instanceof Error ? e.message : String(e)
        return {"success":false, "message":errorMessage}
    }
    redirect("/root/dashboard", RedirectType.push)
}

export async function get_user_action(){
    const url = `${process.env.BACKEND_URL}/api/v1/auth/user`
    const cookieStore = await cookies()
    const access_token = cookieStore.get('access_token')?.value
    try{
        const response = await fetch(url, {
            method: 'GET',
            cache: 'no-store',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${access_token}`
            }
        })
        const data = await response.json()
        if(!data.success){
            return {"success":false, "message":data.message}
        }
        data.data.access_token = access_token
        return data
    }catch(e){
        const errorMessage = e instanceof Error ? e.message : String(e)
        return {"success":false, "message":errorMessage}
    }
}