'use client'
import {useRef} from 'react'
import {register_action} from "./register.server"

export default function RegisterForm() {
    const formRef = useRef<HTMLFormElement>(null)


    async function handleSubmit(){
        if (formRef.current) {
            const formData = new FormData(formRef.current)
            console.log(Object.fromEntries(formData));
            try{
                const response = await register_action(formData)
            }catch(e){

            }
        }
    }

    return (
        <div className="register">
            <form ref={formRef}>
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