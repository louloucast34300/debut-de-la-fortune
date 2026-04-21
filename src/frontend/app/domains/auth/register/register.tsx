'use client'
import {useRef} from 'react'
import {register_action} from "./register.server"

export default function Register() {
    const form = useRef<HTMLFormElement>(null)


    async function handleSubmit(){
        if (form.current) {
            const formData = new FormData(form.current)
            console.log(Object.fromEntries(formData));
            try{
                const response = await register_action(formData)
            }catch(e){

            }
        }
    }

    return (
        <div className="register">
            <form ref={form}>
                <div>
                    <label>pseudo</label>
                    <input type="text" name="pseudo" defaultValue={"le boss"}/>
                </div>
                <div>
                    <label>email</label>
                    <input type="text" name="email" defaultValue={"louis.castel34@icloud.com"}/>
                </div>
                <div>
                    <label>Mot de passe</label>
                    <input type="password" name="password" defaultValue={"Soleil34"}/>
                </div>
                <button type="button" onClick={handleSubmit}>submit</button>
            </form>
        </div>
    )
}