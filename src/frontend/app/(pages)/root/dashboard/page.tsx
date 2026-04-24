import QueueButton from "@/app/components/queue-button";
import { LogoutButton } from "@/app/features/auth/login/atomic/logout/logout";

export default async function DashboardPage() {


  return (
    <main>
        <h1>Déconnexion</h1>
        <LogoutButton />
        <h2>Rejoindre la file d'attente</h2>
        < QueueButton />
    </main>
  );
}
