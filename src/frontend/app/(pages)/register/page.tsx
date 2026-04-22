import LoginForm from "@/app/features/auth/login/login";
import RegisterForm from "@/app/features/auth/register/register";


export default function RegisterPage() {
    return (
        <div>
            <h1>Register</h1>
            <RegisterForm />

            <h1>Connexion</h1>
            <LoginForm />
        </div>
    )
}