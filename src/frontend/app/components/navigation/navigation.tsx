import { LogoutButton } from "@/app/features/auth/logout";
import { ModaleMatchmaking } from "../modal-matchmaking/modal-matchmaking";

export function Navigation({userId, pseudo}:{userId:string, pseudo:string}){
    return (
        <div className="navbar-layout">
            <div className="navbar-container">
                <div className="navbar-brand">
                    <span className="navbar-logo">🎡 Le Début de la Fortune</span>
                    <nav>

                    </nav>
                </div>
                <div className="navbar-pseudo">
                    <span>{pseudo}</span>
                </div>
                <div className="navbar-actions">
                    <LogoutButton />
                    <ModaleMatchmaking userId={userId}/>
                </div>
            </div>
        </div>
    )
}