import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
 
// This function can be marked `async` if using `await` inside
export function proxy(request: NextRequest) {
    if(request.url === "/"){
        return NextResponse.redirect(new URL('/register', request.url))
    }
}

export const config = {
  matcher: '/:path*',
}