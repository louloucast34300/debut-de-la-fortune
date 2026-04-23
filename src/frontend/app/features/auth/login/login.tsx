'use client'
import { useRef} from 'react'
import { login_action } from './login.server'

export default function LoginForm() {

    const formRef = useRef(null)

    async function handleSubmit(){
        if(formRef.current){
            const formData = new FormData(formRef.current)
            try{
                const response = await login_action(formData)
                console.log(response)
            }catch(e){
                
            }
        }
    }


    return (
        <div>
            <form ref={formRef}>
                <div>
                    <label htmlFor="email">
                        <input id="email" type="email" name="email" defaultValue={"louis.castel34@icloud.com"} />
                    </label>
                </div>
                <div>
                    <label htmlFor="password">
                        <input id="password" type="password" name="password" defaultValue={"Soleil34"} />
                    </label>
                </div>
                <button type="button" onClick={() => handleSubmit() }>Connexion</button>
            </form>
        </div>
    )
}