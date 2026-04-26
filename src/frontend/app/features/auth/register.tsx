'use client'
import { useRef } from 'react'
import { register_action } from "@/app/features/auth/auth.servers"

export default function RegisterForm() {
    const formRef = useRef<HTMLFormElement>(null)

    async function handleSubmit() {
        if (formRef.current) {
            const formData = new FormData(formRef.current)
            console.log(Object.fromEntries(formData));
            try {
                const response = await register_action(formData)
            } catch (e) {

            }
        }
    }

    return (
        <form ref={formRef} className="register-form">
            <p className="form-title">🎟️ Inscription</p>
            <hr className="form-divider" />

            <div className="field">
                <label htmlFor="pseudo">Pseudo</label>
                <input
                    id="pseudo"
                    type="text"
                    name="pseudo"
                    placeholder="le boss"
                    defaultValue={"le boss"}
                />
            </div>

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
                🎰 C'est parti !
            </button>

            <p className="form-footer">
                Déjà inscrit ? <a href="/login">Connecte-toi →</a>
            </p>
        </form>
    )
}