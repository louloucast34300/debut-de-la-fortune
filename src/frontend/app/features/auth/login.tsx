'use client'
import { useRef } from 'react'
import { login_action } from '@/app/features/auth/auth.servers'

export default function LoginForm() {

    const formRef = useRef<HTMLFormElement>(null)

    async function handleSubmit() {
        if (formRef.current) {
            const formData = new FormData(formRef.current)
            try {
                const response = await login_action(formData)
                console.log(response)
            } catch (e) {

            }
        }
    }

    return (
        <form ref={formRef} className="login-form">
            <p className="form-title">🎡 Connexion</p>
            <hr className="form-divider" />

            <div className="field">
                <label htmlFor="email">Email</label>
                <input
                    id="email"
                    type="email"
                    name="email"
                    placeholder="ton@email.com"
                    defaultValue={"louis.castel34@icloud.com"}
                />
            </div>

            <div className="field">
                <label htmlFor="password">Mot de passe</label>
                <input
                    id="password"
                    type="password"
                    name="password"
                    placeholder="••••••••"
                    defaultValue={"Soleil34"}
                />
            </div>

            <button type="button" className="btn-submit" onClick={handleSubmit}>
                🎰 Jouer !
            </button>

            <p className="form-footer">
                Pas encore inscrit ? <a href="/register">Rejoins la fortune →</a>
            </p>
        </form>
    )
}