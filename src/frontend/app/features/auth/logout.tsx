'use client'
import {logout_action} from '@/app/features/auth/auth.servers'


export function LogoutButton() {


    async function handleSubmit(){
        await logout_action()
    }

    return (
        <div>
            <button className="btn-logout" type="button" onClick={() => handleSubmit()}>Déconnexion</button>
        </div>
    )
}