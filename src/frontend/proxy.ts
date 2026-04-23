import { NextResponse, NextRequest } from 'next/server'
import { jwtDecode } from 'jwt-decode'

export async function proxy(request: NextRequest) {
    // laisser passer les server actions Next.js
    if(request.headers.get('next-action')){
        return NextResponse.next()
    }

    const accessToken = request.cookies.get('access_token')?.value
    const refreshToken = request.cookies.get('refresh_token')?.value
    // Pas de token => redirect login
    if(!accessToken){
        return NextResponse.redirect(new URL('/register', request.url))
    }
    // Vérification de l'expiration
    const {exp} = jwtDecode<{exp:number}>(accessToken)
    const isExpired = Date.now() >= exp * 1000

    if(!isExpired){
        return NextResponse.next()
    }

    // access_token expiré => tenter le refresh
    if(!refreshToken){
        return NextResponse.redirect(new URL('/register', request.url))
    }

    // appel direct au backend pour éviter les problèmes de cookies dans le proxy
    const res = await fetch(`${process.env.BACKEND_URL}/api/v1/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken })
    })
    const data = await res.json()

    if(!data.success){
        return NextResponse.redirect(new URL('/register', request.url))
    }

    // poser les nouveaux cookies directement sur la response
    const response = NextResponse.next()
    response.cookies.set('access_token', data.access_token, {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'strict',
        maxAge: 60 * 60
    })
    response.cookies.set('refresh_token', data.refresh_token, {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'strict',
        maxAge: 60 * 60 * 24 * 30
    })
    return response
}

export const config = {
    matcher: ['/((?!register|_next/static|_next/image|favicon.ico).*)']
}