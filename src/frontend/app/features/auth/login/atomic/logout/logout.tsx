'use client'
import {logout_action} from '../../login.server'


export function LogoutButton() {


    async function handleSubmit(){
        await logout_action()
    }

    return (
        <div>
            <button type="button" onClick={() => handleSubmit()}>Déconnexion</button>
        </div>
    )
}