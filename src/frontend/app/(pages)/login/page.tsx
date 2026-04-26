import LoginForm from "@/app/features/auth/login";
import Image from "next/image"

export default function LoginPage() {
    return (
        <main className="login-page">
            <div className="container">
                <div className="image-section image-cover">
                    <Image  
                        src="/images/login2.webp" 
                        alt="image du début de la fortune"
                        fill={true} 
                    />
                </div>
                <div className="form-section">
                    <LoginForm />
                </div>
            </div>
        </main>
    )
}